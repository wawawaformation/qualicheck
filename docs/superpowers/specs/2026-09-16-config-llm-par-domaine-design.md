# Config LLM par domaine — design

2026-09-16

## Contexte

`app/ingestion/manifest.yml` et `app/ingestion/llm_client.py::load_manifest()`
portent tous les rôles LLM du projet (`enrichissement`, `embedding`,
`rag_acceptance`, `decomposition`, `jugement`, `guardrail`), alors que 3
d'entre eux (`decomposition`/`jugement`/`guardrail`) sont conceptuellement
`app/retrieval/`, pas `app/ingestion/` — simplement parce que
`load_manifest()` existait déjà là et que c'était le chemin de moindre
résistance à chaque ajout de rôle.

Le nom « manifest » est lui-même trompeur : le contenu est de la
configuration (modèles, prix, seuils, température), pas un manifeste au
sens habituel (inventaire figé, sommes de contrôle, versions gelées).
`app/api_regles/manifest.yml` porte le même problème de nom, sans le
problème de localisation (son contenu — port, CORS, clients API, licence —
est bien à sa place).

Dette actée sur la carte Kanboard #18 (4 constats datés 2026-09-11/13), dont
la priorité a été relevée par la veille personnelle (Infomaniak/Ollama comme
providers de plus en plus probables) : des changements de modèle/provider
sont attendus dès le dev, une config mal rangée devient un frein réel, pas
un défaut esthétique.

## Objectif

1. Renommer les deux fichiers de configuration LLM/API (`manifest.yml` →
   `config.yml`, `load_manifest()` → `load_config()`).
2. Scinder `app/ingestion/manifest.yml` en deux fichiers par domaine, pour
   que chaque rôle vive dans le module qui l'utilise réellement.
3. Coupure nette : pas de période de transition, pas d'alias de
   compatibilité — travail interne, sans consommateur externe.

## Hors périmètre

- Le contenu des rôles eux-mêmes (modèles, prix, prompts) ne change pas —
  déplacement, pas réécriture.
- `docs/superpowers/specs/` et `jury/decisions/` historiques ne sont pas
  retouchés — ils décrivent ce qui était vrai au moment où ils ont été
  écrits, pas l'état courant.
- Le module `EmbeddingClient` reste dans `app/ingestion/embedding.py` même
  s'il est aussi consommé par `app/retrieval/retrieval.py` — c'est un
  positionnement de module préexistant, distinct du sujet de ce chantier
  (la configuration, pas le code des clients).

## Architecture

Nouveau module dédié par domaine, sur le modèle de `app/api_regles/config.py`
qui existe déjà :

| Fichier module | Fichier config | Rôles | Statut |
| --- | --- | --- | --- |
| `app/ingestion/config.py` | `app/ingestion/config.yml` | `enrichissement`, `embedding` | Nouveau — extrait de `llm_client.py` |
| `app/retrieval/config.py` | `app/retrieval/config.yml` | `decomposition`, `jugement`, `guardrail`, `rag_acceptance` | Nouveau — n'existait pas, corrige la mauvaise localisation |
| `app/api_regles/config.py` | `app/api_regles/config.yml` | `api`, `cors`, `validation`, `clients`, `licence` | Existant — fichier et fonction renommés uniquement |

Chaque module expose `load_config() -> dict`, même signature partout — 3
fonctions distinctes de même nom dans 3 modules différents, comme
aujourd'hui `app/ingestion/llm_client.py::load_manifest()` et
`app/api_regles/config.py::load_manifest()` coexistent déjà sous le même nom
sans collision (l'import se fait toujours par chemin de module explicite).

`app/ingestion/llm_client.py` ne garde que la classe `LLMClient` (le client
LLM d'enrichissement) ; il importe `load_config` depuis `.config` au lieu de
le définir lui-même.

`rag_acceptance` rejoint `app/retrieval/config.yml` : toutes ses
utilisations actuelles (`scripts/check_rag_acceptance.py`,
`scripts/check_api_regles_dense_acceptance.py`, `app/api_regles/regles.py`)
sont côté retrieval, aucune côté ingestion.

## Répartition exacte du contenu actuel

`app/ingestion/manifest.yml` (état au 2026-09-16) contient 6 sections :
`enrichissement`, `embedding`, `rag_acceptance`, `decomposition`, `jugement`,
`guardrail`, chacune avec ses commentaires de justification (prix, choix de
seuil, historique des décisions). Ces commentaires sont conservés tels
quels — ils documentent des décisions passées, pas la structure du fichier.

- `app/ingestion/config.yml` reçoit : `enrichissement`, `embedding`.
- `app/retrieval/config.yml` reçoit : `rag_acceptance`, `decomposition`,
  `jugement`, `guardrail` (dans cet ordre — `rag_acceptance` en premier
  car c'est le seul rôle qui n'est pas un client LLM à proprement parler,
  distinction déjà présente dans l'ordre actuel du fichier).
- `app/api_regles/manifest.yml` → `app/api_regles/config.yml`, contenu
  identique.

Les deux fichiers actuels ont un commentaire d'en-tête auto-référentiel
(`# Aucun historique ici : git s'en charge (git log manifest.yml).`) — à
corriger en `git log config.yml` dans chacun des 3 nouveaux fichiers.

## Migration des appelants

**Un seul domaine** (import direct, sans alias) :

- `app/retrieval/decomposition.py`, `jugement.py`, `guardrail.py` →
  `from app.retrieval.config import load_config`
- `app/ingestion/embedding.py`, `enrich_again.py`, `llm_client.py` →
  `from app.ingestion.config import load_config`
- `app/api_regles/regles.py` (lit `rag_acceptance`) →
  `from app.retrieval.config import load_config`
- `scripts/embed_rules.py`, `scripts/ingestion.py` →
  `app.ingestion.config`
- `scripts/mesure_guardrail_perimetre.py`, `scripts/check_rag_acceptance.py`,
  `scripts/check_api_regles_dense_acceptance.py`,
  `scripts/rag_dense_acceptance.py` → `app.retrieval.config`

**Deux domaines** (les 3 scripts de mesure de chunks lisent `embedding` ET
`decomposition` dans le même run) :

- `scripts/mesure_variantes_chunks.py`, `mesure_multi_vecteurs_chunks.py`,
  `mesure_combinaisons_chunks.py` :

  ```python
  from app.ingestion.config import load_config as load_ingestion_config
  from app.retrieval.config import load_config as load_retrieval_config
  ```

**Makefile** (ligne 149, extraction du port pour l'API) :

```make
API_REGLES_PORT = $(shell grep 'port:' app/api_regles/config.yml | tr -d ' ' | cut -d: -f2)
```

**Docs de référence vivantes** (pas les décisions historiques) :
`docs/agent/03_references_impl.md`, `docs/agent/04_contexte_actif.md` —
chemins mis à jour vers les nouveaux fichiers.

## Tests

- Les tests qui exercent `load_manifest()` sont déplacés vers l'emplacement
  du domaine testé et adaptés :
  - `tests/unit/ingestion/test_enrichment.py::test_load_manifest_reads_enrichissement_role`
    → adapté sur place (reste en ingestion), renommé
    `test_load_config_reads_enrichissement_role`.
  - Les tests actuels de `app/api_regles/config.py`
    (`tests/unit/api_regles/test_config.py`) sont adaptés sur place — même
    module, juste le nom de fichier/fonction sous-jacent qui change.
  - Pas de test dédié existant pour le futur `app/retrieval/config.py` — un
    test minimal est ajouté (lecture des 4 rôles) dans un nouveau
    `tests/unit/retrieval/test_config.py`.
- Les docstrings et noms de tests mentionnant « manifeste » sont renommés
  en « config » par cohérence (ex. `test_le_manifeste_expose_le_port` →
  `test_la_config_expose_le_port`), pas seulement les imports — laisser du
  vocabulaire obsolète dans les noms de tests serait exactement le genre de
  confusion que ce chantier existe pour éliminer.
- Aucun changement de comportement testable : les valeurs lues restent les
  mêmes, seule leur provenance (fichier, module) change. La suite complète
  doit rester verte avant/après.

## Traçage

`CHANGELOG.md` à l'exécution du plan ; `TODO.md` (pas d'entrée existante à
fermer, ce chantier n'était pas dans la section « Retrieval US2 ») ; carte
Kanboard #18 fermée avec le résultat ; pas de mémoire assistant dédiée à
créer — ce chantier ne change pas de décision produit, juste
l'organisation du code.
