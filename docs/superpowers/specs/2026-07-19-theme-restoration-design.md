---
title: "Design — Restauration de theme et assouplissement de tags"
subtitle: "Correction d'une erreur d'analyse précédente, basée sur inspection des vraies données API Opquast"
author: "David LEGRAND"
date: "Juillet 2026"
lang: fr-FR
---

## Contexte

Un commit antérieur (`fix: remove erroneous theme/theme_id from MCD`) a supprimé la table `theme` et la colonne `regle.theme_id`, en supposant que la relation thématique était un doublon de `tag`. Cette hypothèse était fausse.

En inspectant les vraies données de l'API Opquast (`https://api.opquast.com/checklist/public/`), sur les 245 règles :

| Champ API | Cardinalité observée | Conclusion |
|---|---|---|
| `metadata.Thématiques` | toujours exactement 1 valeur (245/245) | relation 1-N simple, jamais 0, jamais plusieurs |
| `metadata.Tags` | 0 à N valeurs, vide sur 64/245 | many-to-many, **optionnel** |
| `goal` (objectifs) | toujours ≥1 valeur (1 à 6) | many-to-many, obligatoire — inchangé |
| `metadata.Phases projet` | 1 à 3 valeurs, 108/245 en ont plusieurs | many-to-many, obligatoire — inchangé |

`Thématiques` et `Tags` sont deux champs distincts de l'API — `Thématiques` n'est pas un doublon de `Tags`. Ce document corrige le schéma en conséquence.

## Périmètre

Ce correctif touche du code déjà committé sur les Étapes 1 (Acquisition), 2 (Agrégation) et 4 (Stockage), ainsi que le schéma BDD (migration, models). Il ne modifie pas l'Étape 3 (Enrichissement) au-delà de l'héritage automatique du champ `theme` par `EnrichedRule`.

## Modèles Pydantic (`app/ingestion/schema.py`)

### RuleAcquisition

Ajout du champ `theme: str`, extrait de `metadata.Thématiques[0]` (liste à un seul élément côté API, mais champ scalaire côté modèle — reflète la vraie cardinalité 1-N).

### RuleAggregation

- Ajout de `theme: str`, inclus dans le validateur `non_empty_string` (comme `intitule`/`solution`/`controle` — toujours obligatoire, confirmé 245/245).
- `tags` retiré du validateur `non_empty_list` — devient optionnel, liste vide acceptée sans erreur.

```python
@field_validator("objectifs", "phases")
@classmethod
def non_empty_list(cls, v): ...

@field_validator("intitule", "theme", "solution", "controle")
@classmethod
def non_empty_string(cls, v): ...
```

### EnrichedRule

Aucun changement direct — hérite de `RuleAggregation`, récupère `theme` automatiquement.

## Acquisition (`app/ingestion/acquisition.py`)

Dans `fetch_api()`, ajout du mapping :

```python
theme=rule["metadata"]["Thématiques"][0],
```

## Schéma BDD

### Migration Alembic (0001, modifiée directement)

Toujours jamais mergée dans `main` — corrigée sur place, pas de migration 0002 :

```python
op.create_table(
    "theme",
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("theme", sa.String(64), nullable=False, unique=True),
)
```

Sur `regle`, réintroduction de :
```python
sa.Column("theme_id", sa.Integer, sa.ForeignKey("theme.id"), nullable=False),
```

`downgrade()` : réintroduction de `op.drop_table("theme")` (placé avant `objectif`/`phase`/`tag`, dans l'ordre inverse des FK).

### Models SQLAlchemy (`app/models/referentiel.py`)

Réintroduction de `class Theme(Base)` et de `Regle.theme_id` (FK NOT NULL vers `theme.id`).

## Stockage (`app/ingestion/stockage.py`)

Dans `upsert_rule()`, résolution du thème via `get_or_create()` (même patron que `Objectif`/`Phase`/`Tag`) :

```python
theme = get_or_create(session, Theme, theme=enriched_rule.theme)
regle.theme_id = theme.id
```

Contrairement à `objectifs`/`phases`/`tags`, pas de table d'association ni de delete-then-recreate — `theme_id` est une simple FK mise à jour à chaque upsert, comme les autres champs scalaires de `Regle`.

## Tests impactés

- `tests/unit/ingestion/test_acquisition.py` : mock de réponse API à enrichir avec `metadata.Thématiques`.
- `tests/unit/ingestion/test_aggregation.py` : toutes les constructions de `Rule`/`RuleAggregation` dans les fixtures doivent inclure `theme=...`. Le test qui vérifiait qu'une liste `tags` vide lève une erreur doit être retiré ou inversé (vérifier que `tags=[]` est désormais accepté).
- `tests/unit/ingestion/test_enrichment.py` : toutes les constructions de `Rule`/`EnrichedRule` doivent inclure `theme=...`.
- `tests/migration/test_migration.py` : `TABLES_ATTENDUES` repasse à 14 tables (theme réintroduite).

## Migration réelle et données existantes

1. `make downgrade` puis `make migration` pour appliquer le schéma corrigé.
2. Les 3 règles déjà stockées (numéros 1, 3, 4, issues de la validation Étape 4) l'ont été **sans** `theme_id` — colonne qui n'existait pas à l'époque. Après le downgrade, elles disparaissent avec le reste du schéma ; elles seront re-créées en relançant le pipeline dessus si besoin, ou simplement laissées de côté jusqu'à une ingestion complète ultérieure.

## Convention de nommage

- Champ Pydantic/SQL : `theme` (pas `thematique`) — un seul terme cohérent à travers tout le pipeline (API → Pydantic → SQL), même si l'API expose la clé `Thématiques`.

## Documents de conception déjà corrigés

`conception/1_BDD/bdd.md`, `conception/2_ingestion/{ingestion.md,MLD_qualicheck.md}`, `conception/annexes/MLD_qualicheck.md`, `conception/conception.md` — corrigés dans un commit précédent à celui-ci. Les fichiers `.drawio` n'ont jamais été modifiés lors du retrait erroné et sont donc déjà cohérents avec cette restauration.

## Hors scope

- Pas de nouvelle exploration des autres champs `metadata` de l'API (au-delà de Tags/Thématiques/Phases déjà vérifiés) — à réévaluer seulement si un besoin similaire apparaît.
- Pas de ré-ingestion complète des 245 règles dans ce chantier — seule la correction du schéma et du code est couverte ici.
