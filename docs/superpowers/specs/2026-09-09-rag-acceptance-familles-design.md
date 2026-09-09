---
title: "Design — Jeu d'acceptance RAG étendu (5 familles de cas durs)"
subtitle: "Étape 2 du plan retrieval US2 : amorce de spec en BDD, prérequis de format"
author: "David LEGRAND"
date: "Septembre 2026"
lang: fr-FR
---

## Contexte

Décision actée le 2026-09-08
(`jury/decisions/2026-09-08-mesurer-avant-mecanismes-retrieval.md`) : ne pas
ajouter de mécanisme de retrieval (RRF, décomposition, FTS hybride...) avant
que le jeu d'acceptance puisse mesurer son apport. Le jeu actuel
(`tests/acceptance/rag_acceptance.jsonl`, 17 cas, spec
`2026-07-26-rag-acceptance-jsonl-design.md`) ne peut pas arbitrer ce débat :
15 ou 16 cas sur 17 sont des paraphrases quasi directes de l'intitulé, à
cible unique, sur des sujets disjoints — un `recall@3` à 100% n'y mesure
qu'un problème facile.

Ce chantier construit l'instrument de mesure, pas les mécanismes eux-mêmes.
Écrire ces cas revient à spécifier le comportement attendu d'US2 en BDD :
c'est le chemin critique, pas de l'outillage (`TODO.md` § Étape 2).

Deux limites du format actuel bloquent l'écriture des cas durs :

- `numero_regle_attendue` (singulier, entier) ne sait exprimer ni plusieurs
  cibles acceptables, ni « aucune réponse attendue ».
- `query_top_n_numeros()` (`app/ingestion/rag_acceptance.py`) retourne
  toujours `top_n` résultats via pgvector — aucun mécanisme de refus
  n'existe. Un cas « sans réponse » est donc un échec garanti par
  construction, pas un signal de qualité du retrieval.

## Vue d'ensemble

```
tests/acceptance/rag_acceptance.jsonl (17 cas migrés + nouveaux cas durs)
  {question, famille, numeros_regle_attendus}
        ↓
scripts/check_rag_acceptance.py
  Pour chaque cas :
    - embedding réel de la question (EmbeddingClient.embed_batch)
    - recherche pgvector : ORDER BY embedding <=> vecteur LIMIT top_n
    - verdict PASS / FAIL / PARTIEL (evaluate_case)
        ↓
  Taux de réussite calculé PAR FAMILLE (pas global)
  - 4 familles à cible normale : comparées à taux_reussite_minimum (manifest.yml)
  - sans_reponse : toujours FAIL par construction, reportée à part, hors seuil
  - PARTIEL : exclu du taux binaire, compté à part
        ↓
  Code de sortie 0 (les 4 familles normales ≥ seuil) ou 1 sinon
```

Suite manuelle, toujours hors CI (coût réel API embeddings à chaque run) —
inchangé par rapport à la spec de 2026-07-26.

## Les 5 familles

Chaque famille isole un seul risque testé — ne pas les mélanger dans un
même cas.

| Famille | Ce qu'elle teste | Cibles |
| --- | --- | --- |
| `vocabulaire_source_opquast` | Terme technique présent dans `solution`/`controle`/`tags`/`phases` (texte Opquast **brut**, source de vérité éditoriale), absent de l'`intitule` | 1 |
| `vocabulaire_genere_llm` | Terme technique présent **uniquement** dans `guide_analyse` (généré par le LLM d'enrichissement, `enrich_rule.md`) | 1 |
| `multi_sujets` | Une question touchant plusieurs thèmes/règles à la fois — seul vrai cas d'usage d'une décomposition, volontairement **non construite** (cf. décision jury) | 1..n |
| `sans_reponse` | Question méthodologique hors périmètre des 245 règles Opquast — teste le « je ne sais pas » honnête | 0 (toujours `[]`) |
| `regles_concurrentes` | Plusieurs règles voisines légitimement pertinentes — teste la précision, jamais mesurée par un `recall@3` à cible unique | 1..n |

**Contrainte transverse (`vocabulaire_source_opquast` et `vocabulaire_genere_llm`
uniquement)** : la question ne doit jamais contenir littéralement le terme
technique visé (ex. ne pas écrire « Faut-il un attribut `alt` ? » pour
tester `alt=`). Sinon le test mesure un matching lexical déguisé en test
sémantique, pas la dilution réellement en cause.

**Hors chunk, hors périmètre de ces familles** : `theme` et `objectifs` ne
sont pas inclus dans `build_chunk_text()` — un cas dont le vocabulaire ne
vivrait que dans ces deux champs ne testerait aucune dilution (absence
totale de signal, pas un texte noyé). Suivi séparément : carte Kanboard #8,
non urgente, conditionnelle à un échec mesuré à l'Étape 4 du plan retrieval.

## Format JSONL

```json
{"question": "Peut-on souligner les titres ?", "famille": "paraphrase_intitule", "numeros_regle_attendus": [139]}
{"question": "Le numéro SIRET doit-il être affiché sur le site ?", "famille": "vocabulaire_genere_llm", "numeros_regle_attendus": [106]}
{"question": "...", "famille": "regles_concurrentes", "numeros_regle_attendus": [58, 79, 152]}
{"question": "...", "famille": "sans_reponse", "numeros_regle_attendus": []}
```

- `numero_regle_attendue` (entier) → `numeros_regle_attendus` (liste
  d'entiers, jamais vide sauf pour `sans_reponse`).
- Nouveau champ `famille` : une des 6 valeurs — les 5 ci-dessus, plus
  `paraphrase_intitule` pour les 17 cas historiques (paraphrases directes
  de l'intitulé, cas facile assumé — cf. Migration ci-dessous).

### Migration des 17 cas existants

Reshape mécanique, sans jugement métier à refaire : chaque ligne
`{question, numero_regle_attendue: N}` devient
`{question, famille: "paraphrase_intitule", numeros_regle_attendus: [N]}`.
Le contenu des questions et les cibles ne changent pas — seule la forme du
JSON évolue. Le cas #17 (SIRET, terme littéral dans la question) reste tel
quel dans cette famille : il n'est pas soumis à la contrainte « pas de terme
littéral », propre aux deux familles vocabulaire.

## Modifications

### `app/ingestion/rag_acceptance.py`

- `evaluate_case(case, numeros_retournes) -> dict` : calcule un verdict à 3
  états à partir de `numeros_regle_attendus` :
  - `numeros_regle_attendus == []` → toujours `"FAIL"` (aucun mécanisme de
    refus disponible, documenté comme tel).
  - toutes les cibles présentes dans `numeros_retournes` → `"PASS"`.
  - aucune cible présente → `"FAIL"`.
  - certaines cibles présentes, pas toutes → `"PARTIEL"`.
- `compute_taux_par_famille(evaluations) -> dict[str, dict]` (remplace
  `compute_taux_reussite`) : regroupe les évaluations par `famille`, calcule
  pour chacune `reussis / (total - partiels)` en excluant les verdicts
  `PARTIEL` du dénominateur, et retourne aussi le compte de `PARTIEL` par
  famille pour l'affichage.
- `is_acceptable(taux_par_famille, seuil) -> bool` : vérifie que chaque
  famille **hors `sans_reponse`** atteint `seuil`. `sans_reponse` n'entre
  jamais dans ce calcul (son taux attendu est 0%, documenté, jamais comparé
  au seuil).

### `scripts/check_rag_acceptance.py`

- Log par cas : question, famille, cibles attendues, cibles retournées,
  verdict (`PASS`/`FAIL`/`PARTIEL`).
- Résumé final : un taux par famille (les 4 familles normales comparées au
  seuil, `sans_reponse` affichée séparément avec sa mention "attendu, pas de
  mécanisme de refus"), puis le verdict global (`0`/`1`) basé uniquement sur
  les 4 familles normales.

### `app/ingestion/manifest.yml`

Aucun changement de valeur : `top_n: 3` et `taux_reussite_minimum: 0.8`
restent la référence, mais s'appliquent désormais **à chaque famille
normale indépendamment** plutôt qu'à un taux global unique.

### `tests/acceptance/rag_acceptance.jsonl`

Migration des 17 lignes existantes (format), puis ajout des nouveaux cas
durs — proposition (assistant, appuyée sur des requêtes réelles en base,
pas d'invention de vocabulaire à l'aveugle) puis validation (David),
même schéma que les 17 cas initiaux. Session ultérieure, hors périmètre de
cette spec.

## Tests / Validation

```gherkin
Fonctionnalité : Jeu d'acceptance RAG à familles multiples

  Scénario : Un cas à cible unique réussit
    Étant donné un cas de la famille "vocabulaire_source_opquast" avec une cible attendue
    Quand la cible figure parmi les résultats retournés
    Alors le verdict est "PASS"

  Scénario : Un cas à cibles multiples réussit partiellement
    Étant donné un cas de la famille "regles_concurrentes" avec 3 cibles attendues
    Quand seules 2 des 3 cibles figurent parmi les résultats retournés
    Alors le verdict est "PARTIEL"
    Et ce cas est exclu du calcul du taux de réussite de sa famille

  Scénario : Un cas sans réponse attendue échoue toujours
    Étant donné un cas de la famille "sans_reponse" (numeros_regle_attendus vide)
    Quand le retrieval retourne top_n résultats (comportement actuel, sans mécanisme de refus)
    Alors le verdict est "FAIL"
    Et ce cas n'entre pas dans le calcul du taux des familles à cible normale

  Scénario : Le jeu est globalement acceptable si chaque famille normale dépasse le seuil
    Étant donné les 4 familles à cible normale, chacune avec son propre taux de réussite
    Quand chaque taux est comparé au "taux_reussite_minimum" déclaré dans le manifest
    Alors le run réussit seulement si les 4 familles l'atteignent toutes
```

Validation technique :

1. `app/ingestion/rag_acceptance.py` : tests unitaires purs (aucun réseau ni
   BDD) — un cas par verdict (`PASS`/`FAIL`/`PARTIEL`), le cas `[]` toujours
   `FAIL`, le regroupement par famille, l'exclusion des `PARTIEL` du calcul.
2. `load_cases` : test de rétrocompatibilité — un JSONL avec le nouveau
   format se charge correctement (les 17 cas migrés servent de fixture
   réelle).
3. `make rag-acceptance` : exécution réelle contre les 245 règles en base,
   action manuelle de David, hors périmètre de l'implémentation elle-même.
4. `pytest`/`ruff` verts sur le reste de la suite.

## Gestion des erreurs

Inchangé par rapport à la spec de 2026-07-26 : pas de fail-fast à l'échelle
du cas (un cas en échec n'interrompt pas les suivants) ; une erreur
technique (API embeddings, BDD inaccessible) reste fatale pour tout le run.

## Scope et limites (Hors périmètre — YAGNI)

- **Rédaction effective des nouveaux cas durs** — proposition/validation en
  session ultérieure, pas cette spec (qui ne couvre que le format et le
  calcul).
- **Mécanisme de refus réel pour `sans_reponse`** — non construit ; la
  famille documente un manque, elle ne le comble pas (cohérent avec « ne pas
  ajouter de mécanisme avant mesure »).
- **`theme`/`objectifs` dans le chunk vectorisé** — suivi par la carte
  Kanboard #8, hors périmètre ici.
- **Décomposition en sous-requêtes, RRF, FTS hybride, HyDE, reformulation
  LLM** — explicitement écartés par la décision jury du 2026-09-08 tant
  qu'aucun échec mesuré ne les justifie.
- **Étape 3 (mesurer `recall@3/5/10/15`)** — chantier suivant, une fois les
  cas écrits et validés.
