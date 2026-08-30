# CD staging sur Gitea Actions : pipeline image (build → registre → déploiement)

2026-08-30 · conception validée, implémentation à venir

## Contexte

L'essai non destructif de migration vers Gitea
(`jury/decisions/2026-08-29-hebergement-git-gitea.md`) a validé `ci-dev.yml`
sur la branche `dev` : job de tests, sans déploiement réel. `cd-staging.yml`
est d'une autre nature — il déploie réellement sur `cloclo` (conteneurs
Docker, fichiers servis par Caddy) — et la décision Gitea notait déjà qu'un
simple copier-coller suffirait puisque `runs-on: [self-hosted, cloclo]`
correspond déjà à un label existant du runner.

En pratique, un copier-coller pur perpétue le mode de déploiement actuel :
clone du dépôt puis build direct de l'image sur la machine cible
(`make up` → `docker compose up -d --build`). Ce mode ne prépare rien pour la
bascule de `main` vers l'hébergement Infomaniak (déjà actée comme un besoin
réel, cf. `docs/developpement/ci.md`), qui nécessitera de déployer sur une
machine distincte de celle qui construit l'image.

## Décision

Faire évoluer `cd-staging.yml` (côté Gitea uniquement — `cd-staging.yml`
GitHub reste inchangé et actif tant que l'essai n'est pas validé) vers un
pipeline **image** : une image `api-regles` est construite et poussée vers le
registre de conteneurs OCI intégré à Gitea, puis tirée pour être déployée —
même si build et déploiement s'exécutent aujourd'hui sur la même machine
(`cloclo`). Le pipeline est conçu **comme si** les deux étapes étaient sur des
machines distinctes (aucun raccourci qui profiterait de leur colocalisation
actuelle, ex. réutilisation du cache de build local) : c'est ce qui le rend
directement réutilisable pour la bascule Infomaniak plus tard.

> **Correction du 2026-08-30** : la section Architecture ci-dessous décrivait
> initialement un job `deploy` en `runs-on: [self-hosted, cloclo]`, en
> partant de l'hypothèse que ce label exécute le job directement sur la
> machine physique `cloclo` (comme le faisait l'ancien runner GitHub, un
> processus natif). Épreuve des faits : le runner Gitea (`act_runner`) est
> lui-même déployé comme conteneur Docker, donc son mode « host » exécute en
> réalité le job **dans ce conteneur** (Alpine minimal, presque aucun outil
> présent), pas sur l'hôte physique — d'où des échecs en cascade (Node
> absent pour `actions/checkout@v4`, puis `docker`/`curl`/`make` absents,
> puis des chemins hôte comme `/srv/docker/qualicheck-staging-override/`
> injoignables sans montages explicites). Une image de runner personnalisée
> a été construite pour combler ces manques, mais elle recréait par
> configuration ce qu'un runner natif a nativement — et surtout, elle
> attachait le déploiement à une seule machine (`cloclo`), alors que le
> besoin réel exprimé est de **pouvoir déployer sur n'importe quel hôte**
> (`cloclo` aujourd'hui, Infomaniak demain, potentiellement d'autres).
> Décision révisée : le job `deploy` tourne sur un runner générique
> (`ubuntu-latest`, le même que `build`) et se contente d'un **SSH vers
> l'hôte cible** pour y exécuter les commandes Docker — changer d'hôte
> devient un changement de secrets (`DEPLOY_HOST`/`DEPLOY_USER`/
> `DEPLOY_SSH_KEY`), pas une reconfiguration de runner. L'image de runner
> personnalisée a été annulée (retour à `gitea/act_runner:latest` tel quel).
> Section Architecture mise à jour en conséquence.

## Schéma

![Pipeline CD staging — build, registre, déploiement](cd_staging_gitea_pipeline.png)

*Job `build` : construit l'image et la pousse vers le registre. Registre OCI
Gitea : stocke l'image, aucun déploiement n'y a lieu (`«node»`, pas
`«execution environment»`). Job `deploy` : tire l'image et démarre le
conteneur — ne reconstruit jamais l'image lui-même.*

## Architecture

**Job `build`** (nouveau, `runs-on: ubuntu-latest` → conteneur docker via
`act_runner`) :

1. Checkout
2. `docker login git.david-legrand.fr` (secrets `REGISTRY_USER` /
   `REGISTRY_TOKEN` — jeton Gitea scope `package: écriture`)
3. `docker build -t git.david-legrand.fr/david/qualicheck-api-regles:${{ github.sha }} .`
4. `docker push git.david-legrand.fr/david/qualicheck-api-regles:${{ github.sha }}`

**Job `deploy`** (`needs: build`, `runs-on: ubuntu-latest` — runner
générique, pas de label attaché à un hôte précis) :

1. Écrit la clé SSH dédiée au déploiement (secret `DEPLOY_SSH_KEY`) dans le
   runner éphémère, référence l'hôte cible via `DEPLOY_HOST`/`DEPLOY_USER`
2. Ouvre une session SSH vers l'hôte cible et y exécute, à distance :
   - Clone (si absent) ou `fetch` + `reset --hard ${{ github.sha }}` d'un
     dossier de déploiement dédié (`/srv/docker/qualicheck-staging-deploy/`
     sur `cloclo`) — **pas** de réutilisation de l'ancien checkout laissé
     par le runner GitHub, pour repartir d'un état maîtrisé
   - Écrit le `.env` (mêmes secrets qu'avant, + `API_REGLES_IMAGE`)
   - `docker login` puis `docker compose pull api-regles`
   - `make up-db`, attente Postgres, `make migration`, `make up-staging`
     (nouvelle cible, sans `--build`), attente de santé de l'API, `make
     api-regles-acceptance`

Aucun outil autre que `ssh` n'est requis sur le runner lui-même — tout ce
dont dépendent les commandes de déploiement (`docker`, `make`, `uv`, `curl`)
doit exister sur l'hôte **cible**, pas sur le runner. C'est déjà le cas sur
`cloclo`, hérité de l'ancien runner GitHub natif.

Build et publication du client `regles_api_client` : voir section « Hors
périmètre ».

**Tag** : SHA du commit (`${{ github.sha }}`) uniquement — pas de tag
flottant `staging`. Traçabilité exacte de ce qui tourne, rollback possible
vers n'importe quel commit passé en repointant `API_REGLES_IMAGE`.

## Composants à modifier

- `.gitea/workflows/cd-staging.yml` (nouveau, dans le dépôt) : deux jobs
  décrits ci-dessus.
- `Makefile` (dans le dépôt) : nouvelle cible `up-staging` (`docker compose
  up -d`, sans `--build`) — `make up` reste inchangé pour le développement
  local, qui doit continuer à builder directement.
- `docker-compose.override.yml` (sur `cloclo`, hors dépôt,
  `/srv/docker/qualicheck-staging-override/`) : le service `api-regles`
  reçoit `image: ${API_REGLES_IMAGE}` en plus du réseau `cloudnet` déjà
  présent.
- Paire de clés SSH dédiée au déploiement CI (générée le 2026-08-30,
  distincte des clés personnelles) : clé publique ajoutée aux
  `authorized_keys` de l'utilisateur de déploiement sur `cloclo`.
- Secrets Actions Gitea du dépôt `qualicheck` : `REGISTRY_USER`,
  `REGISTRY_TOKEN` (registre d'images), `DEPLOY_HOST`, `DEPLOY_USER`,
  `DEPLOY_SSH_KEY` (déploiement SSH) — nouveaux, en plus des secrets déjà en
  place pour `ci-dev.yml`.

## Gestion des erreurs

- Si `docker push` échoue (job `build`) : le job `deploy` ne démarre pas
  (`needs: build`), aucune tentative de déploiement sur une image absente du
  registre.
- Si `docker compose pull` échoue (job `deploy`, ex. image absente ou
  problème réseau vers le registre) : le déploiement s'arrête avant toute
  migration ou redémarrage de conteneur — pas de risque de repartir sur une
  version incohérente.
- Le garde-fou existant (rejeu de la suite d'acceptance après démarrage)
  reste inchangé et continue de couvrir les régressions fonctionnelles,
  indépendamment de l'origine de l'image (build local vs image tirée).
- Si la connexion SSH vers l'hôte cible échoue (`DEPLOY_HOST` injoignable,
  clé refusée) : le job `deploy` échoue avant toute action sur l'hôte,
  `set -e` dans le script distant garantit aussi qu'une commande en échec
  interrompt la suite (pas de migration lancée sur un pull raté, par
  exemple).

## Hors périmètre

- Bascule effective de `main`/Infomaniak sur ce même modèle : pas traitée
  ici, seulement préparée (le pipeline sera transposable tel quel).
- Politique de rétention/nettoyage des images poussées sur le registre
  Gitea (une image par commit, jamais purgée) : à traiter si l'espace disque
  devient un problème réel, pas avant.
- **Séparation des déploiements par service** : dès que la stack accueillera
  un second service applicatif construit (ex. `api_business` pour US1/US2,
  éventuellement un conteneur ChromaDB), il faudra éviter qu'un push sur
  `staging` touchant uniquement ce second service ne redéploie inutilement
  `api-regles` (et inversement). Préoccupation identifiée le 2026-08-30, pas
  traitée maintenant faute de second service réel à filtrer contre — un
  filtre `paths:` ajouté sans cible concrète serait spéculatif. Le socle
  actuel (image nommée `qualicheck-api-regles`, dossier de conception dédié,
  `docker compose pull api-regles` déjà ciblé sur ce seul service plutôt que
  sur toute la stack) est déjà pensé pour permettre cette séparation le
  moment venu : ajouter un fichier `.gitea/workflows/cd-staging-<service>.yml`
  dédié par service, chacun avec un filtre `on: push: paths:` restreint à
  son propre périmètre (ex. `app/api_regles/**`), plutôt que d'étendre ce
  fichier pour couvrir plusieurs services.
- **Build et publication du client `regles_api_client`** : retirés de
  `cd-staging.yml` le 2026-08-30 (étaient hérités tel quel de l'ancien
  pipeline GitHub, dans le job `deploy`). Ce n'est pas un abandon — le
  déploiement du client n'est simplement pas prioritaire à ce stade, et sa
  présence dans `deploy` était en tension avec le principe du job allégé
  (orchestration Docker uniquement, sans Node ni npm). À réintroduire plus
  tard, probablement dans le job `build` (qui dispose déjà de Node), avec le
  résultat transmis à `deploy` via un artefact de workflow plutôt que
  reconstruit sur place — non implémenté pour l'instant.
