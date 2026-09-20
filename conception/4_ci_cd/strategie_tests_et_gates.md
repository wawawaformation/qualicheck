# Stratégie de tests, gates et manifest de déploiement (LLMOps)

2026-09-20 · conçu et validé avec David (atelier carte Kanboard #45) —
**mixte** : certains éléments sont déjà réels, d'autres sont une cible pas
encore implémentée (signalé explicitement ci-dessous). Vocabulaire utilisé :
`docs/glossaire_tests.md`. Schéma : `conception/4_ci_cd/ci_cd_llmops.drawio`.

**État réel au 2026-09-20 (vérifié dans le dépôt, fait foi sur le reste du
document)** :

| Élément | État |
| --- | --- |
| `ci-feature.yml`, `ci-dev.yml` (Gitea + GitHub) | fait |
| `ci-acceptance.yml` sur tag (Gitea) | fait |
| Garde-fou de tag dans `cd-staging.yml` | fait mais **connu cassé**, cf. « Tag » |
| `ci-review.yml` + `scripts/review_pr.py` (revue LLM de PR) | fait, **à durcir** (cf. plan `docs/superpowers/plans/2026-09-20-revue-pr-llm-implementation.md`) |
| Gate à seuil `dev -> staging` | non implémenté |
| 2e image Docker (`api-business`) | non implémenté |
| Manifest de déploiement | non implémenté |
| Traces Langfuse pendant l'acceptance de PR | non implémenté |

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
  -> CI feature (lint + tests unitaires/intégration, LLM mocké)  [ci-feature.yml, fait]
  -> CI verte (gate)
  -> tag manuel (YYYY-MM-DD-<sha7>) quand la branche est prête   [cf. « Tag »]
  -> Acceptance (vrais tests, appels LLM réels)                   [ci-acceptance.yml, fait —
                                                                    déclenché par le push du tag]
  -> revue de code (PR, auto-revue + revue LLM ci-review.yml)
  -> merge sur dev
  -> gate à seuil (déclenché à la promotion dev -> staging, PAS à chaque push)
  -> déploiement staging (build+push 2 images + manifest)        [aujourd'hui : 1 seule image poussée,
                                                                    pas de manifest — écart, voir plus bas]
  -> recette / UAT sur staging (vérification humaine)
  -> prod (observabilité Langfuse, trafic réel)
```

## Tag comme précondition de promotion (décision, 2026-09-20)

**Décision** : aucune version ne peut être promue plus loin dans la chaîne
(dev -> staging -> prod) sans avoir été **taguée** au préalable sur sa
branche feature. Le tag est ce qui déclenche les vrais tests d'acceptance
(coûteux), pas le merge — ça découple le coût du rythme des merges et donne
un retour rapide dès qu'une branche est taguée, avant même le merge sur
`dev`.

- **Création du tag** : manuelle (`git tag` + push), décidée par David
  quand une branche feature est prête. Pas d'automatisation pour l'instant
  (YAGNI — pas de volume de contributeurs qui le justifie).
- **Format** : `YYYY-MM-DD-<sha7>` (ex. `2026-09-20-a1b2c3d`). Simple et
  traçable, sans présumer d'un schéma de versionnage sémantique formel —
  cohérent avec la décision déjà prise plus bas de ne pas utiliser de
  version sémantique (`v1.2.3`) tant qu'aucun processus de release formel
  n'existe.
- **Déclencheur des vrais tests d'acceptance** (`ci-acceptance.yml`, fait) :
  le push du tag lui-même, workflow séparé de `ci-feature.yml`/`ci-dev.yml`.
  Prépare un Postgres éphémère, importe le référentiel déjà embeddé, puis
  rejoue les tests d'acceptance qui en sont vraiment
  (`check_rag_acceptance.py`, `make api-regles-acceptance`,
  `make api-regles-dense-acceptance`) — pas `mesure_rag_dense.py`, qui reste
  une mesure, pas une acceptance (cf. plus bas).
- **Filtre du déclencheur — à resserrer** : le workflow écoute aujourd'hui
  `on: push: tags: '**'`, c'est-à-dire **tout** tag, alors que le format
  décidé est `YYYY-MM-DD-<sha7>`. Un tag sans rapport (documentation,
  release future, tag posé par erreur) déclencherait donc des appels LLM et
  embeddings réels payants. **Décision : resserrer le filtre** à
  `"20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*"` — le déclencheur coûteux doit
  suivre exactement la convention qui le justifie, sinon le découplage
  coût/merge décrit plus haut ne tient plus. Un glob suffit (Actions ne
  supporte pas les expressions régulières) ; il laisse passer un tag mal
  formé du même préfixe, ce qui est acceptable : le but est d'écarter les
  tags d'une autre nature, pas de valider une syntaxe.
- **Garde-fou avant déploiement staging — fait, mais connu cassé** :
  `cd-staging.yml` exécute `git describe --tags --exact-match ${{ github.sha }}`
  avant de construire/pousser les images. **Défaut connu** : ce contrôle
  porte sur le SHA du commit présent sur `staging`, alors que le tag est
  posé sur la branche feature. Si la promotion vers `staging` crée un commit
  de merge (merge non fast-forward), les deux SHA diffèrent et le garde-fou
  refuse **tout** déploiement. **Correction différée** (décision de David,
  2026-09-20) : rien ne se déploie sur `staging` tant que la carte **#32
  (C4 — authentification)** n'est pas faite, donc le défaut n'a aucun effet
  d'ici là. À reprendre en même temps que la reprise du déploiement staging
  (pistes : merge fast-forward imposé, ou contrôle sur un tag atteignable
  via `git describe --tags` sans `--exact-match`, ou tag reporté sur le
  commit de merge).
- **Données du Postgres éphémère** : `ci-acceptance.yml` importe
  `tests/fixtures/referentiel_embedde.sql` (référentiel déjà ingéré/embeddé,
  commité) plutôt que de relancer `make ingestion`/`make embed-rules` à
  chaque tag (245 appels LLM réels sinon, contraire à la règle projet
  "éviter les ré-ingestions complètes non nécessaires"). Ce fixture est
  **statique** : à régénérer manuellement (voir `tests/fixtures/README.md`)
  quand le référentiel change vraiment, sinon les tests d'acceptance
  tournent sur des données périmées.
- **Publication du fixture — question réglée (2026-09-20)** : ce fichier
  contient l'intégralité du référentiel Opquast et part sur le miroir
  GitHub public. David confirme que le référentiel est publiable
  (**CC BY-SA 4.0**) : pas d'obstacle à le versionner. Seule contrepartie
  restante, assumée : ~5 Mo ajoutés définitivement à l'historique Git à
  chaque régénération.

## Répartition mock / réel par étage (décision)

- **`tests/unit/`** : tout mocké.
- **`tests/integration/`** : composants réels assemblés (base de test, HTTP
  interne), **LLM mocké** même si le code appelle un LLM (ex.
  `tests/integration/agent_us2/test_repondre.py`, `@patch("app.agent_us2.loop.ChatOpenAI")`).
  On y teste le câblage, pas ce que le LLM décide.
- **`tests/acceptance/`** : LLM réel, coûte de l'argent — c'est là que le
  Gherkin est rejoué pour de vrai.
- **`tests/mesures/`** : pas de verdict, produit des métriques pour décider
  (ex. `mesure_scores_refus.py`). **Incohérence corrigée le 2026-09-20** :
  `tests/acceptance/rag_dense_acceptance.py` avait en réalité le profil
  d'une mesure (compare des `top_n`, produit un rapport Markdown, pas de
  pass/fail) — déplacé et renommé en `tests/mesures/mesure_rag_dense.py`.

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

## Revue automatisée additionnelle sur PR (décision, 2026-09-20)

**Écarté** : le Claude Code GitHub Action officiel — il n'authentifie qu'en
OIDC GitHub (App Registration + federated credential), une dépendance
GitHub incompatible avec Gitea, l'hébergeur principal du projet.

**Décision** : un script maison (`scripts/review_pr.py`), pas de nouveau
module `app/` (outil d'ops sans logique métier applicative, même exception
que `scripts/create_api_regles_key.py`).

- Récupère le diff `origin/<base>...HEAD`, l'envoie au LLM avec un prompt
  de relecture fixe, poste le résultat en commentaire sur la PR.
- **Modèle** : `kimi-k2.6`, même déploiement Azure que le rôle
  `enrichissement` (`app/ingestion/config.yml`) — pas de nouveau secret
  Azure, config dans `scripts/review_pr_config.yml` (rôle `revue`, même
  forme que les autres `config.yml` du dépôt). Écarté : les modèles Claude
  du projet Azure AI Foundry `dlegrandext-4532` — clé/config déjà obtenues
  mais devenues sans objet, ce chantier n'en a pas besoin pour l'instant.
- **Portabilité Gitea/GitHub** : le host est un paramètre (`--host
  gitea|github`), pas du code dupliqué — seul le contrat de l'API de
  commentaire diffère (URL de base, schéma du jeton), le reste (diff,
  prompt, appel LLM) est identique. Les deux sont implémentés.
- **Déclencheur et périmètre des hébergeurs** : `pull_request` vers `dev`.
  La CI (lint, tests unitaires/intégration) tourne sur Gitea **et** GitHub
  jusqu'à `dev` inclus (`ci-feature.yml`/`ci-dev.yml`/`ci-review.yml`
  dupliqués dans `.gitea/workflows/` et `.github/workflows/`) ; au-delà
  (tag, gate à seuil, déploiement staging) reste Gitea uniquement, propre à
  l'hôte de déploiement réel.
- **Garde-fou de coût** : au-delà de 60 000 caractères (~15k tokens), le
  diff est **tronqué** et le commentaire le dit en première ligne (revue
  partielle annoncée, jamais silencieuse). **Décision revue le 2026-09-20** :
  le code faisait à l'origine un `sys.exit(1)`, ce qui rendait la CI rouge
  pour une raison sans rapport avec la qualité du code. Une PR volumineuse
  n'est pas un défaut : elle mérite un avertissement, pas un blocage.
- **Verdict structuré et blocage** (décision de David, 2026-09-20) : le LLM
  rend un verdict `ok` / `mineur` / `bloquant`. `ok` et `mineur` sont
  informatifs (commentaire posté, CI verte) ; seul `bloquant` fait échouer
  la CI. **Principe unique** : seul un verdict `bloquant` explicitement rendu
  bloque. Toute défaillance de l'outil lui-même (réponse hors format après
  parsing, LLM injoignable après 3 tentatives, diff tronqué) reste non
  bloquante et laisse une trace explicite — un outil de revue en panne ne
  doit pas se transformer en gate.
- **Retry** : 3 tentatives avec backoff exponentiel sur l'appel LLM, comme
  tout appel LLM du projet (règle non négociable, `CLAUDE.md`).

**Statut** : implémenté dans cette session, mais le verdict structuré, le
retry, le test unitaire et le suivi de coût restent à faire. Plan
d'exécution détaillé :
`docs/superpowers/plans/2026-09-20-revue-pr-llm-implementation.md`.

## Hors périmètre (renvoyé à une autre carte)

Détection de dérive des métriques dans le temps (seuils évolutifs,
historique, standards/outils type OpenTelemetry Metrics) — carte Kanboard
#49, priorité basse. Ce document pose seulement la brique minimale (le
manifest cumulé) qui rendrait cette carte moins coûteuse à démarrer plus
tard.
