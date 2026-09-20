# Stratégie de tests, gates et manifest de déploiement (LLMOps)

2026-09-20 · conçu et validé avec David (atelier carte Kanboard #45) —
**mixte** : certains éléments sont déjà réels (`ci-dev.yml`, `cd-staging.yml`
existants), d'autres sont une cible pas encore implémentée (signalé
explicitement ci-dessous). Vocabulaire utilisé : `docs/glossaire_tests.md`.
Schéma : `conception/4_ci_cd/ci_cd_llmops.drawio`.

**Bloqué par la carte #32** ("C4 — Authentification de l'utilisateur", pas
démarrée) : tout ce qui touche au déploiement de `api-business` (agent US2)
sur `staging` — 2e image Docker, manifest, recette — n'a pas de sens tant
que l'API n'a pas d'authentification (n'importe qui pourrait l'utiliser sur
un serveur de préprod exposé). Ce document reste donc une spec, pas un
prérequis d'implémentation immédiate.

## Contexte

Avant cet atelier, la distinction entre test d'intégration (LLM mocké) et
test d'acceptance (LLM réel) n'était pas nommée explicitement, et le rôle de
`staging` (recette humaine, pas des tests automatisés) n'était pas écrit
nulle part. Objectif : fixer la chaîne complète, ce qui la déclenche, et ce
qu'elle produit — pour que n'importe quel agent ou humain sache où ajouter
un nouveau test sans redemander.

## Chaîne complète

```
branche feature
  -> CI (lint + tests unitaires/intégration, LLM mocké)      [déjà réel, ci-dev.yml]
  -> CI verte (gate)
  -> revue de code (PR, auto-revue)
  -> merge sur dev
  -> Acceptance (Gherkin réel, appels LLM réels)              [dossier tests/acceptance/ existe déjà,
                                                                mais pas encore branché comme étape
                                                                systématique post-merge dev — à faire]
  -> gate à seuil (déclenché à la promotion dev -> staging, PAS à chaque push)
  -> déploiement staging (build+push 2 images + manifest)     [aujourd'hui : 1 seule image poussée,
                                                                pas de manifest — écart, voir plus bas]
  -> recette / UAT sur staging (vérification humaine)
  -> prod (observabilité Langfuse, trafic réel)
```

## Répartition mock / réel par étage (décision)

- **`tests/unit/`** : tout mocké.
- **`tests/integration/`** : composants réels assemblés (base de test, HTTP
  interne), **LLM mocké** même si le code appelle un LLM (ex.
  `tests/integration/agent_us2/test_repondre.py`, `@patch("app.agent_us2.loop.ChatOpenAI")`).
  On y teste le câblage, pas ce que le LLM décide.
- **`tests/acceptance/`** : LLM réel, coûte de l'argent — c'est là que le
  Gherkin est rejoué pour de vrai.
- **`tests/mesures/`** : pas de verdict, produit des métriques pour décider
  (ex. `mesure_scores_refus.py`). **Incohérence repérée, non corrigée** :
  `tests/acceptance/rag_dense_acceptance.py` a en réalité le profil d'une
  mesure (compare des `top_n`, produit un rapport Markdown, pas de
  pass/fail) — mal nommé/mal rangé, à corriger une autre fois si demandé.

## Gate à seuil sur `dev -> staging`

**Décision** : gater la promotion `dev -> staging` avec un seuil chiffré
sur une mesure existante, plutôt qu'à chaque push sur `dev` (coût des
appels LLM/embeddings réels sinon récurrent à chaque commit).

- Dès qu'un seuil est fixé, la mesure devient un test d'acceptance avec
  critère chiffré (elle sort du glossaire strict de la "mesure" sans
  verdict).
- **Seuil retrieval, prêt à utiliser** : le protocole retrieval conclu
  (mémoire `protocole_mesure_retrieval`, 3 vagues, 2026-09-11) donne
  recall@5 = 0,921 (exploration) / 0,903 (réservé) sur le chunk de
  production actuel — base défendable pour un plancher avec marge (ex.
  ≥ 0,85), pas un chiffre inventé.
- **Autres mesures (refus, guardrail)** : ne pas leur fixer de seuil tant
  qu'un protocole aussi rigoureux (jeu réservé, critère écrit d'avance,
  cf. `protocole_mesure_retrieval`) n'existe pas pour elles.
- **Non implémenté** : aucun gate à seuil n'est branché dans les workflows
  aujourd'hui. `ci-dev.yml`/`cd-staging.yml` ne rejouent que
  `tests/unit tests/integration`.

## Images Docker et registre

**Existant** : deux services applicatifs dans `docker-compose.yml`
(`api-regles` port 8880, `api-business` = agent US2 port 8882), construits
depuis le même `Dockerfile`, différenciés par la commande. `cd-staging.yml`
ne construit et pousse aujourd'hui **qu'une seule image**
(`qualicheck-api-regles:${{ github.sha }}`) vers le registre Gitea
(`git.david-legrand.fr`) — `api-business` n'a pas d'étape de build/push
dédiée. **Écart identifié, pas corrigé.**

**Cible décidée** :

- Construire et pousser **deux images**, une par service :
  `qualicheck-api-regles` et `qualicheck-api-business`.
- Étiquettes pour chacune :
  - `:{sha}` — précis, immuable, relie une image à un commit exact (donc à
    une trace Langfuse, un run CI, une PR). Déjà en place pour
    `api-regles`, à ajouter pour `api-business`.
  - `:staging-latest` — tag flottant pratique pour identifier "l'image
    actuellement en staging" sans connaître le SHA.
  - Pas de version sémantique (`v1.2.3`) : aucun processus de release
    formel n'existe encore dans ce projet — prématuré (YAGNI).

## Manifest de déploiement (cible, non implémenté)

À chaque promotion `dev -> staging`, générer un manifest (ex.
`deploy-manifest.json`) contenant :

- SHA du commit déployé.
- Horodatage du déploiement (existe déjà en variable `DEPLOYED_AT` dans
  `.env` sur l'hôte, mais ne survit pas ailleurs — à dupliquer dans le
  manifest).
- Les tags des deux images poussées.
- Versions de modèles utilisées (`AZURE_MODEL_GPT_MINI`,
  `AZURE_MODEL_TEXT_EMBEDDING_SMALL`).
- Version de migration Alembic appliquée.
- Résultat du gate à seuil (ex. recall@5 mesuré à cette promotion).

Ce manifest, cumulé dans le temps, amorce aussi la détection de dérive
(carte Kanboard #49, hors périmètre de cette carte) sans outillage
supplémentaire (pas besoin d'OpenTelemetry Metrics pour un premier
historique {sha, date, métriques}).

## Rôle de `staging` : recette, pas des tests automatisés

`staging` déploie une préprod pour une vérification **humaine** (recette /
UAT, ex. Élie Sloïm) — pas pour rejouer des mesures ou de l'acceptance une
deuxième fois. Les mesures/acceptance utilisent déjà le même LLM réel que
sur `dev` ; les rejouer après déploiement doublerait le coût sans rien
vérifier de plus (le déploiement lui-même n'affecte pas ces chiffres).

**Existant** : `make api-regles-acceptance` tourne déjà automatiquement à
chaque déploiement staging (`cd-staging.yml`) — possible sans risque car ce
jeu ne coûte rien (aucun appel LLM, un seul `PATCH` réversible). Ce n'est
pas une exception à la règle ci-dessus, juste un cas où le coût est nul.

## Observabilité (Langfuse)

- **Prod** : trafic réel d'utilisateurs, déjà outillé
  (`app/observability/tracing.py`, `OTEL_EXPORTER=otlp`).
- **Sur une PR (cible, non implémenté)** : David veut aussi observer les
  traces Langfuse générées pendant l'étape Acceptance d'une PR, pour juger
  le comportement réel du LLM en même temps que la revue du diff.
  Prérequis techniques identifiés, pas encore faits :
  1. Configurer `OTEL_EXPORTER=otlp` + secrets Langfuse pendant l'étape
     Acceptance en CI (aujourd'hui la CI n'exporte que du local/rien).
  2. Un `APP_ENV` distinct (ex. `ci`/`pr`) pour ne pas mélanger ces traces
     avec `dev`/`staging`/`prod` dans Langfuse.

## Idée non actée : revue automatisée additionnelle

Ajouter une revue automatisée par Claude Code GitHub Action (backend Azure
AI Foundry, payé par la formation, pas l'abonnement personnel de David) en
complément de l'auto-revue humaine sur la PR. Pas de workflow existant pour
ça — à concevoir séparément si retenu.

## Hors périmètre (renvoyé à une autre carte)

Détection de dérive des métriques dans le temps (seuils évolutifs,
historique, standards/outils type OpenTelemetry Metrics) — carte Kanboard
#49, priorité basse. Ce document pose seulement la brique minimale (le
manifest cumulé) qui rendrait cette carte moins coûteuse à démarrer plus
tard.
