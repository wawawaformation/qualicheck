---
title: "Design — Script rag_dense_acceptance.py"
subtitle: "Comparer le recall par famille sur plusieurs top_n en une exécution"
author: "David LEGRAND"
date: "Septembre 2026"
lang: fr-FR
---

## Contexte

Suite de l'Étape 3 (mesure recall) du plan retrieval US2 —
`jury/decisions/2026-09-08-mesurer-avant-mecanismes-retrieval.md`. Un run
réel du `make rag-acceptance` (2026-09-09) à `top_n=3` (config
`manifest.yml`) échouait sur la famille `multi_sujets` (67%). Des tests
manuels en changeant `top_n` à 5, 10 puis 15 dans `manifest.yml` et en
relançant à chaque fois ont montré que `top_n` seul résout progressivement
la plupart des échecs, mais 3 cas persistent même à 15 : la règle 185
(`aria-expanded`) n'est jamais retrouvée, et 2 cas `multi_sujets` ne
retrouvent jamais une de leurs deux cibles (règles 106 et 107).

Ce script formalise cette exploration en une seule exécution plutôt que 4
runs manuels, et produit un rapport écrit pour ne pas reperdre l'analyse.

## Vue d'ensemble

```
tests/acceptance/rag_acceptance.jsonl (56 cas)
        ↓
scripts/rag_dense_acceptance.py
  1. embedding réel de chaque question (1 seul appel API, comme aujourd'hui)
  2. 1 requête pgvector par question, LIMIT 15 (le max de TOP_NS)
  3. pour chaque top_n de [3, 5, 10, 15] :
       troncature locale de la liste retournée (numeros_retournes[:top_n])
       evaluate_case() (réutilisée telle quelle, app/ingestion/rag_acceptance.py)
       compute_taux_par_famille() (réutilisée telle quelle)
        ↓
docs/eval/rag_dense_acceptance_YYYY-MM-DD.md
  - tableau agrégé : famille × top_n → taux
  - cas PARTIEL/FAIL à top_n=15 uniquement (échecs qui persistent malgré
    le top_n maximal — le signal utile, pas du bruit lié à un top_n trop
    petit)
```

Ce script ne modifie ni `app/ingestion/rag_acceptance.py`, ni
`scripts/check_rag_acceptance.py`, ni `manifest.yml` — c'est un script
d'exploration ponctuelle, distinct de l'instrument de mesure officiel de
l'Étape 3 (qui reste `check_rag_acceptance.py` à un seul `top_n` configuré).

Suite manuelle, hors CI (même logique que `check_rag_acceptance.py`) : un
seul appel réel à l'API Azure embeddings par exécution (~0€ sur 56
questions, comme les runs précédents).

## Modules

### `scripts/rag_dense_acceptance.py` (nouveau)

Constante locale, pas dans `manifest.yml` (exploration ponctuelle, pas une
config de production à faire varier) :

```python
TOP_NS = [3, 5, 10, 15]
```

1. Charge `tests/acceptance/rag_acceptance.jsonl` (`load_cases`, réutilisée).
2. Calcule l'embedding de chaque question (`EmbeddingClient.embed_batch`,
   réutilisé).
3. Pour chaque question : une requête pgvector avec `LIMIT max(TOP_NS)`
   (15), via `query_top_n_numeros` (réutilisée telle quelle avec
   `top_n=15`).
4. Pour chaque `top_n` de `TOP_NS` : tronque la liste retournée
   (`numeros_retournes[:top_n]`), appelle `evaluate_case(case,
   numeros_retournes_tronques)` (réutilisée), accumule les évaluations.
5. Pour chaque `top_n` : `compute_taux_par_famille(evaluations)`
   (réutilisée) — construit le tableau agrégé.
6. Construit la liste des cas `PARTIEL`/`FAIL` à `top_n=15` (dernière
   itération de la boucle du point 4).
7. Écrit le rapport Markdown dans
   `docs/eval/rag_dense_acceptance_<date du jour>.md`
   (`datetime.date.today().isoformat()`).
8. Logge le coût total (tokens embeddings), même format que les autres
   scripts.

### `docs/eval/` (nouveau dossier)

Rapports de mesure horodatés, committés dans git (historique conservé,
même logique que `jury/decisions/` et `CHANGELOG.md`).

Format du rapport :

```markdown
# Mesure recall — rag_dense_acceptance (2026-09-09)

## Taux de réussite par famille × top_n

| Famille | top_n=3 | top_n=5 | top_n=10 | top_n=15 |
|---|---|---|---|---|
| paraphrase_intitule | 100% | 100% | 100% | 100% |
| vocabulaire_source_opquast | 80% | 80% | 90% | 100% |
| ...

## Cas PARTIEL/FAIL persistants à top_n=15

- **FAIL** [vocabulaire_genere_llm] « Un menu qui se déplie... » — attendu
  [185], jamais retrouvée dans le top 15.
- ...

Coût : X tokens, Y €.
```

### `Makefile`

Nouvelle cible, section « Ingestion et données réelles » (à côté de
`rag-acceptance`) :

```makefile
## Compare le recall du RAG sur plusieurs top_n (3/5/10/15), rapport Markdown
rag-dense-acceptance:
	uv run python scripts/rag_dense_acceptance.py
```

## Tests / Validation

Le script lui-même n'a pas de test unitaire dédié — il n'ajoute aucune
logique nouvelle non déjà testée : `evaluate_case`, `compute_taux_par_famille`,
`load_cases`, `query_top_n_numeros` sont toutes réutilisées telles quelles,
déjà couvertes par `tests/unit/ingestion/test_rag_acceptance.py`. Seule la
troncature locale (`numeros_retournes[:top_n]`) et la génération du
Markdown sont nouvelles — trop simples et trop couplées à un run réel
(embeddings, BDD) pour justifier un test isolé ; validées par exécution
réelle (`make rag-dense-acceptance`), comme `check_rag_acceptance.py`.

Validation :
1. `ruff check scripts/rag_dense_acceptance.py` propre.
2. Exécution réelle contre les 245 règles en base (action manuelle de
   David, coût réel assumé).
3. Vérification visuelle du rapport généré dans `docs/eval/`.

## Gestion des erreurs

Même comportement que `check_rag_acceptance.py` : pas de fail-fast à
l'échelle d'un cas ; une erreur technique (API embeddings, BDD
inaccessible) reste fatale pour tout le run.

## Scope et limites (Hors périmètre — YAGNI)

- **Modification de `manifest.yml`/`check_rag_acceptance.py`** — aucune ;
  l'instrument de mesure officiel de l'Étape 3 reste inchangé, ce script
  est un complément d'exploration.
- **Choix définitif d'un `top_n` de production** — reste une décision de
  David après lecture du rapport, pas prise par ce script.
- **Résolution des 3 cas qui persistent à top_n=15** (règle 185, cas
  multi-sujets 106/107) — ce script les *documente*, il ne les corrige
  pas. Suite éventuelle : Étape 4 du plan retrieval (variantes de chunk),
  mais seulement sur ces cas précis si jugé utile.
- **Intégration CI** — suite manuelle uniquement, même logique que
  `check_rag_acceptance.py` (coût réel à chaque run).
