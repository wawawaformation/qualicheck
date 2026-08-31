---
title: "Mise au point du déploiement SSH-push sur Gitea Actions"
subtitle: "cd-staging.yml — échecs successifs, cause identifiée à chaque fois par les logs réels"
author: "David LEGRAND"
date: "Août 2026"
lang: fr-FR
---

## Objectif de ce document

Le passage de `cd-staging.yml` à un déploiement SSH-push (voir
`conception/4_ci_cd/cd_staging.md`) a nécessité
plusieurs itérations avant un run réellement réussi, chacune diagnostiquée à
partir des logs du run précédent plutôt que supposée. Ce document trace ces
incidents pour qu'ils ne se reproduisent pas silencieusement ailleurs (le
premier, en particulier, produisait un job marqué **réussi** alors que le
déploiement n'avait pas eu lieu).

Fichier concerné : `.gitea/workflows/cd-staging.yml`, job `deploy`.

## Incident 1 — Script tronqué silencieusement, job marqué réussi

**Symptôme** : le job `deploy` se termine avec succès en quelques secondes,
mais le conteneur `api-regles` sur `cloclo` reste sur l'ancienne image
(vérifié via `docker inspect` : date de création antérieure au run). Le log
s'arrête net juste après le démarrage de Postgres — aucune trace de
`make migration`, `make up-staging`, du health check ni de l'acceptance,
et pourtant `🏁 Job succeeded`.

**Cause** : le script de déploiement est envoyé via un heredoc SSH
(`ssh ... bash -s <<'REMOTE' ... REMOTE`), dont le contenu transite comme
stdin de la commande `ssh`. La boucle d'attente Postgres invoque
`docker compose exec -T postgres pg_isready ...` sans rediriger son entrée
— cette commande hérite du même stdin que le script parent et en consomme
une partie, faisant croire à bash que le script se termine plus tôt qu'il
ne le devrait. Aucune erreur n'est levée : les lignes restantes sont
simplement absorbées comme entrée par `docker exec` plutôt qu'interprétées.

**Correction** : rediriger explicitement l'entrée de cette commande depuis
`/dev/null` :

```bash
until docker compose exec -T postgres pg_isready -U "$POSTGRES_USER" < /dev/null; do
```

**Leçon** : toute commande interactive ou qui touche à `stdin`, exécutée à
l'intérieur d'un script lui-même reçu via un pipe/heredoc, doit isoler son
entrée explicitement — sinon un job peut réussir sans avoir rien fait.

## Incident 2 — `uv` introuvable en session SSH non-interactive

**Symptôme** (après le fix de l'incident 1) : `make migration` échoue avec
`make: uv: Aucun fichier ou dossier de ce nom` (exit 127), alors que `uv`
est bien installé sur `cloclo` (`~/.local/bin/uv`, confirmé manuellement).

**Cause** : `ssh hôte 'bash -s'` lance un shell **non interactif**, qui ne
source ni `~/.bashrc` ni `~/.profile` — c'est justement dans ces fichiers
que l'installeur `uv` ajoute `~/.local/bin` au `PATH`. Le `PATH` hérité par
la session SSH ne contient donc pas ce répertoire.

**Correction** : exporter le `PATH` explicitement en tête du script distant :

```bash
export PATH="$HOME/.local/bin:$PATH"
```

**Leçon** : un outil qui fonctionne « à la main » en SSH interactif peut
échouer silencieusement en SSH non-interactif (scripts, CI) — le `PATH`
n'est jamais garanti identique entre les deux.

## Incident 3 — Secrets Postgres et FASTAPI_API_KEY désynchronisés de la base réelle

**Symptôme** (après le fix de l'incident 2) : `make migration` échoue avec
`password authentication failed for user`. Une fois corrigé (voir
ci-dessous), le conteneur `api-regles` redémarre ensuite en boucle avec
`RuntimeError: FASTAPI_API_KEY absente ou vide dans .env`.

**Cause** : la base Postgres de staging existe depuis le 2026-08-02 (premier
déploiement réel) et son rôle a été créé une fois pour toutes avec un nom et
un mot de passe précis (`qualicheck_staging`). Les secrets `POSTGRES_USER`/
`POSTGRES_DB` créés côté Gitea utilisaient une valeur différente
(`qualicheck`, un choix générique fait au moment de la configuration des
secrets, sans vérifier la base réelle) — changer ces variables d'environnement
ne change pas rétroactivement les identifiants déjà enregistrés dans les
données persistées du conteneur Postgres. Les secrets
`FASTAPI_API_KEY`/`FASTAPI_API_KEY_ELIE`/`FASTAPI_API_KEY_DAVID`/
`FASTAPI_API_KEY_FORMATEUR`, eux, n'avaient simplement jamais été créés côté
Gitea (oubliés lors de la migration des secrets `POSTGRES_*`).

**Correction** : les deux jeux de secrets Postgres n'étant récupérables
nulle part une fois écrits (ni sur GitHub, ni sur Gitea — les secrets sont
en écriture seule sur les deux plateformes), les valeurs réelles ont été
relues depuis l'ancien `.env` généré sur `cloclo` par le précédent pipeline
GitHub (`/srv/docker/qualicheck-staging/qualicheck/qualicheck/.env`), qui
contenait encore les identifiants effectivement utilisés par la base et les
clients API. Les 7 secrets ont été recréés côté Gitea à partir de ces
valeurs exactes (`tea actions secrets create`).

**Leçon** : migrer des secrets d'une plateforme CI à une autre exige de
vérifier leur valeur contre l'état réel du système qu'ils authentifient
(une base déjà initialisée, ici), pas seulement de recréer une entrée du
même nom avec une valeur plausible.

## Incident 4 — `upload-artifact@v4`/`download-artifact@v4` non supportés par Gitea Actions

**Contexte** : ajout du déploiement du client `regles_api_client` (statique,
transmis du job `build` au job `deploy` via un artefact de workflow — voir
`conception/4_ci_cd/cd_staging.md`).

**Symptôme** : l'étape `actions/upload-artifact@v4` échoue immédiatement :

```text
::error::@actions/artifact v2.0.0+, upload-artifact@v4+ and
download-artifact@v4+ are not currently supported on GHES.
```

**Cause** : à partir de la v4, ces actions utilisent une nouvelle API
d'artefacts (basée sur Twirp) qui détecte si elle tourne sur github.com ou
sur un serveur tiers (GHES — GitHub Enterprise Server — ou toute plateforme
qui imite son API, dont Gitea) et refuse explicitement de fonctionner hors
de github.com. Ce n'était pas couvert par la vérification empirique
préalable (le risque identifié portait sur `services:`, pas sur les
artefacts).

**Correction** : verrouiller sur la version précédente, qui utilise
l'ancienne API compatible :

```yaml
uses: actions/upload-artifact@v3   # pas @v4
uses: actions/download-artifact@v3 # pas @v4
```

**Leçon** : la compatibilité « ~90 % avec la syntaxe GitHub Actions » de
Gitea Actions ne dit rien des versions précises des actions tierces — une
action `uses: owner/repo@vX` peut avoir des versions majeures qui cessent
volontairement de fonctionner hors de github.com, indépendamment de la
syntaxe du workflow.

## Résultat

Après ces corrections, le pipeline complet (image `api-regles` + client
`regles_api_client`) réussit de bout en bout : image poussée au registre,
base migrée avec les bons identifiants, conteneur `api-regles` sain avec la
nouvelle image, API répondant en HTTP 200 sur
`https://regles.qualicheck.koabana.fr/regles`, client statique publié via
artefact + `scp`.
