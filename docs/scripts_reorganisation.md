# Réorganisation du dossier `scripts/`

Carte Kanboard #44 · 2026-09-20 · décisions de David.

## Pourquoi

`scripts/` contenait **20 scripts à plat** (et `scripts/CLAUDE.md` n'en décrivait que 4), alors que sa règle est « uniquement les points d'entrée, aucune logique métier ». Trop d'éléments à retenir (loi de Miller), et de la logique métier (plus de 1 100 lignes de mesures) au mauvais endroit.

## Inventaire (avant)

| Famille | Scripts | Décision |
|---|---|---|
| Points d'entrée vivants | `migration`, `ingestion`, `embed_rules`, `enrich_again`, `create_db_audit`, `agent_cli`, `creer_cle_api_regles` | **restent** dans `scripts/` |
| Vérifications d'acceptance (appels réels) | `check_api_regles_acceptance`, `check_api_regles_dense_acceptance`, `check_rag_acceptance`, `rag_dense_acceptance` | **déplacées** vers `tests/acceptance/` |
| Campagnes de mesure | `mesure_scores_refus`, `mesure_variantes_chunks`, `mesure_combinaisons_chunks`, `mesure_multi_vecteurs_chunks`, `mesure_guardrail_perimetre` | **déplacées** vers `tests/mesures/` |
| Périmés | `ingestion_test`, `storage_smoke`, `dirty_retriever` | **supprimés** (l'historique reste dans Git) |
| Destructif | `clear_opquast_tables` | cible `make clear` **retirée** ; le script **reste**, avec une **confirmation** `[y/N]` ajoutée (décision de David) |

## Arborescence cible (piste 1, retenue)

```
scripts/                 7 points d'entrée + CLAUDE.md, à plat (la règle est respectée)
tests/acceptance/        jeux de données + les 4 vérifications qui les utilisent
tests/mesures/           les 5 campagnes de mesure
```

## Pourquoi ces suppressions

Les trois scripts supprimés écrivaient (ou lisaient) dans `POSTGRES_DB`, la vraie base de dev :

- `ingestion_test.py` remplaçait le référentiel réel par des bouchons (il appelait `clear_opquast_tables` puis insérait des règles factices) ;
- `storage_smoke.py` insérait un thème, un objectif et la règle n° 999 dès l'import, sans nettoyage ;
- `dirty_retriever.py` interrogeait la base avec un embedding Azure payant, remplacé par `POST /regles/dense`.

Les tests d'intégration du stockage (`tests/integration/ingestion/test_stockage_*.py`, sur `POSTGRES_TEST_DB`) couvrent ce que faisaient les deux premiers.

## Pourquoi `make clear` est retiré

Un seul appel effaçait les 245 règles enrichies, sans confirmation, sur `POSTGRES_DB`, alors que les régénérer coûte un appel LLM par règle. `ingestion.py` appelle déjà la même fonction (`app/ingestion/stockage.py::clear_opquast_tables`) avec confirmation quand c'est nécessaire.

## Ce qui a changé techniquement

- Les 9 scripts déplacés calculaient la racine du projet avec `parents[1]` ; à un niveau de plus, c'est `parents[2]`.
- Le `Makefile` : 9 cibles changent de chemin, la cible `clear` disparaît. Les noms des autres cibles sont inchangés, donc `cd-staging.yml` (qui lance `make api-regles-acceptance`) fonctionne sans modification.
- Les chemins cités dans les fichiers vivants sont mis à jour (`TODO.md`, commentaires de `app/`, fiches de travail du jury). Les plans, specs et décisions historiques restent tels quels : ce sont des instantanés.
- Pytest ne collecte pas les scripts déplacés (il ne cherche que `test_*.py`).

## Vérifié

Avant et après : 277 tests unitaires, 2 tests d'intégration `agent_us2`, `ruff` sur `app tests scripts`. Chacun des 9 scripts se charge sans exécution et retrouve sa racine, ses jeux de données et son dossier de rapports. Les 9 cibles `make` affichent le bon chemin (`make -n`).

## Le script `clear_opquast_tables.py` : gardé, avec une confirmation

Décision de David : ne pas le supprimer, mais lui ajouter une confirmation. Il annonce désormais « Cela va supprimer les N règle(s) de la base « X ». Confirmer ? [y/N] » (le nom de la base est là pour qu'on voie qu'on vise la vraie base de dev) et n'agit que sur un `y`. Entrée, « oui », ou une entrée standard fermée (pipe, cron) refusent. Même convention que `scripts/ingestion.py`. Couvert par 14 tests (`tests/unit/scripts/`), qui remplacent la base : aucun n'exécute de vidage réel.

## Module mort supprimé

`app/ingestion/dirty_retriever.py` (39 lignes, une fonction `query_top_n_regles`) ne servait plus qu'au script du même nom. Supprimé sur décision de David, après vérification qu'aucun code, test ni configuration ne le référençait. Rien ne reste à décider pour cette carte.
