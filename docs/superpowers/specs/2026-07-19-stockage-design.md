---
title: "Design — Étape 4 : Stockage"
subtitle: "Upsert PostgreSQL des EnrichedRules, tables de référence, orchestrateur ingestion.py"
author: "David LEGRAND"
date: "Juillet 2026"
lang: fr-FR
---

## Contexte

Correctif préalable : le MCD initial contenait une erreur — la table `theme` et la colonne `regle.theme_id` (FK NOT NULL) ne devaient pas exister, la relation thématique étant déjà couverte par `tag`. Corrigé directement dans la migration 0001 (jamais mergée dans `main`), voir commit `fix: remove erroneous theme/theme_id from MCD`.

## Vue d'ensemble

L'Étape 4 persiste chaque `EnrichedRule` (collection `EnrichedRules`, sortie de l'Étape 3) dans PostgreSQL : table `regle` + tables de référence `objectif`, `phase`, `tag` et leurs associations many-to-many.

```
EnrichedRules (collection Étape 3)
  ↓
store_rules(session, enriched_rules: EnrichedRules) -> None
  ↓
  UNE transaction globale (rollback complet si échec) :
    Pour chaque EnrichedRule :
      - get_or_create(Objectif, objectif=...) pour chaque objectif
      - get_or_create(Phase, phase=...) pour chaque phase
      - get_or_create(Tag, tag=...) pour chaque tag
      - upsert_rule() : INSERT si numero absent, UPDATE complet si présent
      - Synchronise les tables d'association (objectif_regle, phase_regle, regle_tag)
    commit()
```

La colonne `embedding` de `regle` reste `NULL` à cette étape — elle sera écrite plus tard (Étape 7, simple `UPDATE`), après chunking (Étape 5) et embedding (Étape 6).

## Modules

### `app/ingestion/stockage.py`

Nom de fichier en français (cohérent avec `acquisition.py`), code en anglais.

**`get_or_create(session, model, **kwargs) -> Model`**
Fonction générique réutilisée pour `Objectif`, `Phase`, `Tag` : cherche une ligne existante par les critères passés (ex. `tag="HTML"`), la crée si absente. Idempotent — pas de pré-remplissage nécessaire, gère automatiquement les nouvelles valeurs Opquast.

**`upsert_rule(session, enriched_rule: EnrichedRule) -> Regle`**
Cherche `Regle` par `numero`. Si absente : `INSERT`. Si présente : `UPDATE` complet de tous les champs (`intitule`, `solution`, `controle`, `strategie_analyse`, `strategie_justification`, `strategie_source`, `guide_analyse`, `llm_provider`) — cohérent avec le principe « relance depuis le début » de `ingestion.md`. Ne touche pas à `embedding` (hors scope).

**`store_rules(session, enriched_rules: EnrichedRules) -> None`**
Orchestration :
1. Ouvre une transaction unique pour toute la collection.
2. Pour chaque `EnrichedRule` : résout/crée les tables de référence, upsert la règle, synchronise les associations.
3. En cas d'exception sur une règle : `session.rollback()`, log erreur, relève l'exception (fail-fast, tout-ou-rien — aucune règle partiellement stockée).
4. Si tout réussit : `session.commit()`, log de synthèse.

**Logging** :
- Erreur : `logger.error(f"Règle {numero} — stockage : KO ({raison})")`
- Succès global : `logger.info(f"Stockage : {n} règles stockées")`

### `scripts/ingestion.py` (nouveau, version partielle)

Point d'entrée CLI qui orchestre les étapes existantes du pipeline :

```
1. acquire_rules()        → liste de dicts
2. aggregate_rules(...)   → Rules
3. enrich_rules(...)      → EnrichedRules
4. store_rules(...)       → persistance PostgreSQL
```

- Fail-fast : arrêt immédiat si une étape échoue, log explicite (étape concernée, raison), code de sortie non-nul (`sys.exit(1)`).
- Log de début/fin pour chaque étape.
- Connexion DB via SQLAlchemy `Session`, configuration lue depuis `.env` (variables déjà en place : `POSTGRES_HOST`, `POSTGRES_PORT`, etc.).
- S'arrête après le Stockage — Chunking (Étape 5), Embedding (Étape 6), Indexation (Étape 7) seront ajoutés dans une session future, complétant ce même script.

## Gestion des erreurs

Fail-fast cohérent avec le reste du pipeline : toute exception (validation, DB, LLM) interrompt immédiatement l'exécution. Pas de récupération partielle — conforme au principe décrit dans `ingestion.md` (« pas de stockage partiel »).

## Tests / Validation

**Pas de suite pytest pour cette étape.** Validation par exécution réelle :

1. Lancer `scripts/ingestion.py` (potentiellement sur un sous-ensemble de règles, pour limiter les appels LLM payants pendant la validation).
2. Suivre les logs (`logs/ingestion.log`) pour confirmer le déroulement étape par étape.
3. Inspecter directement les tables PostgreSQL (`psql` ou requêtes SQL) : `regle`, `objectif`, `phase`, `tag` et leurs tables d'association, pour vérifier que les données sont cohérentes.

Raison : la logique de `stockage.py` (upsert SQL, contraintes FK, transactions) n'a de sens qu'avec une vraie base — mocker SQLAlchemy serait fragile et peu représentatif. Les logs granulaires déjà en place (Étapes 1-4) permettent de diagnostiquer un échec sans suite de tests dédiée.

## Convention de nommage

- Code : anglais (`get_or_create`, `upsert_rule`, `store_rules`)
- Docs/comments/logs : français
- Nom de fichier `stockage.py` : français, cohérent avec `acquisition.py` (mais `aggregation.py`/`enrichment.py` sont en anglais suite au renommage de l'Étape 3 — incohérence assumée, à trancher plus tard si besoin)

## Scope et limites (MVP)

✅ Inclus :
- `get_or_create`, `upsert_rule`, `store_rules`
- Transaction globale, fail-fast, logging
- `scripts/ingestion.py` version partielle (Étapes 1-4)

❌ Exclus (post-MVP / sessions futures) :
- Écriture de `embedding` (Étape 7)
- Chunking (Étape 5), Embedding (Étape 6)
- Tests pytest automatisés pour le stockage
- Cache local pour reprise partielle (déjà écarté en v1 dans `ingestion.md`)
