# Mesure des variantes de chunk — Vague 1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mesurer MRR et recall@k pour 12 variantes de chunk (11 champs isolés + le chunk complet de production comme baseline) sur les 114 cas d'acceptance, sans jamais écrire dans `regle.embedding`, et produire un CSV détaillé (candidat par candidat) + un résumé Markdown agrégé dans `docs/eval/`.

**Architecture:** Décomposition et embedding des 114 questions calculés une seule fois puis figés. Pour chacune des 12 variantes : construction du texte par règle, vectorisation en mémoire, similarité cosinus calculée en numpy (pas de requête SQL pgvector), fusion multi-sous-questions identique à `retrieve()` (meilleur score gardé sur doublon), calcul de rang/MRR/recall@k, écriture CSV + Markdown.

**Tech Stack:** Python, numpy, SQLAlchemy (lecture seule), Azure OpenAI (embeddings + décomposition), pytest.

## Global Constraints

- Retry LLM : 3 tentatives avec backoff (déjà en place dans `DecompositionClient`/`EmbeddingClient`, réutilisés tels quels).
- Aucune écriture dans `regle.embedding` (colonne de production) — tous les vecteurs des variantes restent en mémoire le temps du run.
- Fichiers temporaires : `./tmp/` à la racine du dépôt, jamais `/tmp` système (non applicable ici — toutes les sorties sont des livrables dans `docs/eval/`, pas des fichiers jetables).
- Traçage : `CHANGELOG.md` à la fin de ce plan, format `## [date] — [outil]`.
- Le CSV brut n'est jamais réécrit par-dessus un fichier annoté par David — chaque run produit un nouveau fichier horodaté.

---

## Contexte technique déjà vérifié dans le code

- `app/ingestion/chunking.py::build_chunk_text(rule) -> str` existe déjà : 9 champs (intitulé, thème, contexte, solution, contrôle, guide d'analyse, objectifs, tags, phases), listes jointes par `", "`.
- `app/ingestion/stockage.py::load_enriched_rules_from_db(session) -> EnrichedRules` charge les 245 règles depuis la BDD sous forme d'objets `EnrichedRule` (un seul aller-retour BDD par collection N:N, pas 245 requêtes) — déjà utilisée par `scripts/embed_rules.py`. `EnrichedRules.regles` donne la liste.
- `EnrichedRule` (`app/ingestion/schema.py`) porte tous les champs nécessaires comme attributs directs : `number` (pas `numero`), `intitule`, `theme` (déjà résolu en libellé string), `contexte` (peut être `None`), `solution`, `controle`, `objectifs`/`tags`/`phases` (`list[str]`), `strategie_analyse`, `strategie_justification`, `guide_analyse`. Validé en base : `objectifs`/`phases` toujours non-vides sur les 245 règles (validateur Pydantic à la construction), `tags` vide pour 64/245 règles.
- `scripts/embed_rules.py:60-67` — pattern de vectorisation par lots (`BATCH_SIZE = 50`, boucle `embed_batch` + association `numero → vecteur`).
- `app/ingestion/rag_acceptance.py` contient déjà `load_cases()`, `query_top_n_numeros()`, `metriques_scores()`, `evaluate_case()` — ce plan y ajoute les fonctions de mesure de la vague 1.
- `app/retrieval/retrieval.py::retrieve()` — la logique de fusion multi-sous-questions (top_n par sous-question, union avec meilleur score gardé sur doublon) y est implémentée pour pgvector ; ce plan la réimplémente en numpy dans `rag_acceptance.py` (pas de dépendance croisée, la logique est courte et le calcul diffère — cosinus en mémoire, pas SQL).
- Convention `scripts/` = points d'entrée seuls, toute logique testable vit dans `app/`.
- Aucun test unitaire n'existe pour les scripts couplés à Azure réel (`check_rag_acceptance.py`, `rag_dense_acceptance.py`, `mesure_scores_refus.py`) — convention documentée dans `tests/unit/ingestion/test_rag_acceptance.py`. Ce plan suit la même règle pour `scripts/mesure_variantes_chunks.py`.

---

### Task 1: `build_variant_text()` — texte d'un seul champ, pour l'étude d'ablation

**Files:**
- Modify: `app/ingestion/chunking.py`
- Modify: `tests/unit/ingestion/test_chunking.py` (existe déjà — contient
  `_rule(contexte=None)`, un helper qui construit un vrai `EnrichedRule`,
  et 2 tests pour `build_chunk_text`. À étendre, pas à réécrire.)

**Interfaces:**
- Produces: `build_variant_text(rule, champ: str) -> str | None`. `rule` est un objet portant les mêmes attributs qu'`EnrichedRule` (`intitule`, `theme`, `contexte`, `solution`, `controle`, `objectifs`, `tags`, `phases`, `strategie_analyse`, `strategie_justification`, `guide_analyse`). Retourne `None` si le champ est vide/absent — signal pour exclure la règle de cette variante.

**Contrainte connue** : `EnrichedRule` valide via Pydantic que `objectifs`
et `phases` ne sont jamais vides (`RuleAggregation.non_empty_list`,
`app/ingestion/schema.py:41-46`) — impossible de construire une instance
réelle avec ces listes vides. Seul `tags` peut être vide (pas de
validateur dessus, cohérent avec les 64/245 règles réelles sans tag). Le
test « liste vide → None » se fait donc uniquement sur `tags`.

- [ ] **Step 1: Étendre le helper `_rule()` existant avec des paramètres
  optionnels (rétrocompatible avec les 2 appels existants)**

Remplacer, en tête de `tests/unit/ingestion/test_chunking.py` :

```python
def _rule(contexte=None):
    return EnrichedRule(
        id=1, number=1, intitule="Les images ont un attribut alt",
        theme="Contenus", contexte=contexte,
        solution="Ajouter alt descriptif", controle="Vérifier alt présent",
        objectifs=["Accessibilité"], tags=["HTML", "Images"], phases=["Intégration"],
        slug="images-alt",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Parcourez le DOM et vérifiez l'attribut alt.",
    )
```

par :

```python
def _rule(contexte=None, objectifs=None, tags=None, phases=None):
    return EnrichedRule(
        id=1, number=1, intitule="Les images ont un attribut alt",
        theme="Contenus", contexte=contexte,
        solution="Ajouter alt descriptif", controle="Vérifier alt présent",
        objectifs=objectifs if objectifs is not None else ["Accessibilité"],
        tags=tags if tags is not None else ["HTML", "Images"],
        phases=phases if phases is not None else ["Intégration"],
        slug="images-alt",
        strategie_analyse="statique", strategie_justification="Justif",
        guide_analyse="Parcourez le DOM et vérifiez l'attribut alt.",
    )
```

(les 2 tests existants appellent `_rule(contexte=...)` par mot-clé, donc
inchangés par cet ajout de paramètres optionnels)

- [ ] **Step 2: Écrire les tests (ils doivent échouer)**

Ajouter à la fin de `tests/unit/ingestion/test_chunking.py` :

```python
from app.ingestion.chunking import build_variant_text


def test_build_variant_text_champ_scalaire_renseigne():
    """Un champ texte simple renvoie sa valeur telle quelle."""
    rule = _rule()

    assert build_variant_text(rule, "intitule") == "Les images ont un attribut alt"


def test_build_variant_text_champ_liste_jointe():
    """Une liste (objectifs/tags/phases) est jointe par ', ', même
    convention que build_chunk_text()."""
    rule = _rule(objectifs=["Un", "Deux", "Trois"])

    assert build_variant_text(rule, "objectifs") == "Un, Deux, Trois"


def test_build_variant_text_champ_nullable_vide():
    """Un champ nullable à None retourne None (règle exclue de la variante)."""
    rule = _rule(contexte=None)

    assert build_variant_text(rule, "contexte") is None


def test_build_variant_text_liste_vide():
    """Une liste vide (tags, le seul champ liste sans contrainte de
    non-vacuité) retourne None."""
    rule = _rule(tags=[])

    assert build_variant_text(rule, "tags") is None


def test_build_variant_text_tous_les_champs_de_la_vague_1():
    """Les 11 champs de la vague 1 sont tous lisibles sans erreur."""
    rule = _rule(contexte="Contexte présent")
    champs = [
        "intitule", "theme", "contexte", "solution", "controle",
        "objectifs", "tags", "phases",
        "strategie_analyse", "strategie_justification", "guide_analyse",
    ]

    for champ in champs:
        assert build_variant_text(rule, champ) is not None
```

Ajouter `from app.ingestion.chunking import build_variant_text` doit
remplacer l'import existant `from app.ingestion.chunking import
build_chunk_text` par un import combiné :
`from app.ingestion.chunking import build_chunk_text, build_variant_text`
(un seul import en tête de fichier, pas deux lignes séparées).

- [ ] **Step 3: Lancer les tests, vérifier qu'ils échouent**

Run: `uv run pytest tests/unit/ingestion/test_chunking.py -v`
Expected: FAIL (`ImportError: cannot import name 'build_variant_text'`)
— les 2 tests existants doivent, eux, continuer à passer (le helper
`_rule()` reste rétrocompatible).

- [ ] **Step 4: Implémenter la fonction**

Ajouter dans `app/ingestion/chunking.py`, après `build_chunk_text()` :

```python
def build_variant_text(rule, champ: str) -> str | None:
    """
    Texte d'un seul champ de la règle, pour l'étude d'ablation des
    variantes de chunk (scripts/mesure_variantes_chunks.py, voir
    docs/superpowers/specs/2026-09-11-mesure-chunks-vague1-design.md).

    Args:
        rule: objet portant les mêmes attributs qu'EnrichedRule
        champ: nom de l'attribut à extraire (ex. "intitule", "guide_analyse")

    Returns:
        Le texte du champ, ou None s'il est vide/absent — la règle est
        alors exclue de cette variante (pas de texte vide envoyé à l'API
        d'embedding).
    """
    valeur = getattr(rule, champ)
    if isinstance(valeur, list):
        return ", ".join(valeur) if valeur else None
    return valeur if valeur else None
```

- [ ] **Step 5: Lancer les tests, vérifier qu'ils passent**

Run: `uv run pytest tests/unit/ingestion/test_chunking.py -v`
Expected: PASS (5 tests)

- [ ] **Step 6: Commit**

```bash
git add app/ingestion/chunking.py tests/unit/ingestion/test_chunking.py
git commit -m "feat: build_variant_text pour l'etude d'ablation des chunks"
```

---

### Task 2: Fonctions de mesure pures (rang, MRR, recall@k, similarité, fusion)

**Files:**
- Modify: `app/ingestion/rag_acceptance.py`
- Test: `tests/unit/ingestion/test_rag_acceptance.py`

**Interfaces:**
- Produces:
  - `rang_meilleure_cible(candidats_tries: list[int], cibles: list[int]) -> int | None`
  - `calculer_mrr(rangs: list[int | None]) -> float`
  - `calculer_recall_a_k(candidats_tries: list[int], cibles: list[int], k: int) -> float`
  - `cosine_similarity_matrix(vecteur_question: list[float], vecteurs_regles: dict[int, list[float]]) -> list[tuple[int, float]]`
  - `retrieve_variante(sous_questions_vecteurs: list[list[float]], vecteurs_regles: dict[int, list[float]], top_n: int) -> list[tuple[int, float]]`

- [ ] **Step 1: Écrire les tests (ils doivent échouer)**

Ajouter à la fin de `tests/unit/ingestion/test_rag_acceptance.py` :

```python
from app.ingestion.rag_acceptance import (
    calculer_mrr,
    calculer_recall_a_k,
    cosine_similarity_matrix,
    rang_meilleure_cible,
    retrieve_variante,
)


def test_rang_meilleure_cible_trouvee():
    """Retourne le rang (1-indexé) de la première cible rencontrée."""
    candidats_tries = [42, 139, 7, 200]

    assert rang_meilleure_cible(candidats_tries, [139]) == 2


def test_rang_meilleure_cible_la_plus_haute_gagne():
    """À cibles multiples, le rang retenu est celui de la mieux placée."""
    candidats_tries = [42, 139, 7, 200]

    assert rang_meilleure_cible(candidats_tries, [200, 139]) == 2


def test_rang_meilleure_cible_absente():
    """Aucune cible dans les candidats retourne None."""
    candidats_tries = [42, 7, 8]

    assert rang_meilleure_cible(candidats_tries, [139]) is None


def test_calculer_mrr_moyenne_des_inverses():
    """MRR = moyenne de 1/rang."""
    rangs = [1, 2, 4]

    assert calculer_mrr(rangs) == pytest.approx((1 / 1 + 1 / 2 + 1 / 4) / 3)


def test_calculer_mrr_cible_absente_contribue_zero():
    """Une cible absente (rang None) contribue 0 au MRR, pas une erreur."""
    rangs = [1, None]

    assert calculer_mrr(rangs) == pytest.approx((1 / 1 + 0.0) / 2)


def test_calculer_mrr_liste_vide():
    """Une liste vide retourne 0.0 (pas de division par zéro)."""
    assert calculer_mrr([]) == 0.0


def test_calculer_recall_a_k_cible_unique_trouvee():
    """Cible unique dans le top-k : recall = 1.0."""
    candidats_tries = [1, 2, 3, 4, 5]

    assert calculer_recall_a_k(candidats_tries, [3], k=5) == 1.0


def test_calculer_recall_a_k_cible_unique_hors_top_k():
    """Cible unique hors du top-k : recall = 0.0."""
    candidats_tries = [1, 2, 3, 4, 5]

    assert calculer_recall_a_k(candidats_tries, [5], k=3) == 0.0


def test_calculer_recall_a_k_cibles_multiples_fraction():
    """Cibles multiples : fraction retrouvée dans le top-k."""
    candidats_tries = [1, 2, 3, 4, 5]

    assert calculer_recall_a_k(candidats_tries, [1, 5], k=3) == pytest.approx(0.5)


def test_cosine_similarity_matrix_trie_par_score_decroissant():
    """Les règles sont triées par similarité cosinus décroissante."""
    vecteur_question = [1.0, 0.0]
    vecteurs_regles = {1: [1.0, 0.0], 2: [0.0, 1.0], 3: [0.5, 0.5]}

    resultat = cosine_similarity_matrix(vecteur_question, vecteurs_regles)

    numeros = [n for n, _ in resultat]
    assert numeros == [1, 3, 2]
    assert resultat[0] == (1, pytest.approx(1.0))
    assert resultat[2] == (2, pytest.approx(0.0, abs=1e-9))


def test_retrieve_variante_union_garde_le_meilleur_score():
    """Une règle trouvée par deux sous-questions garde le meilleur score."""
    vecteurs_regles = {5: [1.0, 0.5]}
    sous_questions_vecteurs = [[1.0, 0.0], [0.5, 1.0]]

    resultat = retrieve_variante(sous_questions_vecteurs, vecteurs_regles, top_n=15)

    assert resultat == [(5, pytest.approx(0.894427, abs=1e-5))]


def test_retrieve_variante_fusionne_deux_sous_questions():
    """Deux sous-questions ciblant des règles différentes ramènent les deux,
    dans l'ordre de première apparition."""
    vecteurs_regles = {10: [1.0, 0.0], 20: [0.0, 1.0]}
    sous_questions_vecteurs = [[1.0, 0.0], [0.6, 0.8]]

    resultat = retrieve_variante(sous_questions_vecteurs, vecteurs_regles, top_n=2)

    assert resultat == [(10, pytest.approx(1.0)), (20, pytest.approx(0.8))]
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -v`
Expected: FAIL (`ImportError` — aucune des 5 fonctions n'existe encore)

- [ ] **Step 3: Implémenter les fonctions**

Ajouter en tête de `app/ingestion/rag_acceptance.py` l'import numpy :

```python
import numpy as np
```

Ajouter, après `metriques_scores()` :

```python
def rang_meilleure_cible(candidats_tries: list[int], cibles: list[int]) -> int | None:
    """Rang (1-indexé) de la première cible rencontrée dans les candidats
    déjà triés par pertinence décroissante. None si aucune cible n'y figure."""
    for rang, numero in enumerate(candidats_tries, start=1):
        if numero in cibles:
            return rang
    return None


def calculer_mrr(rangs: list[int | None]) -> float:
    """Mean Reciprocal Rank : moyenne de 1/rang, 0 pour une cible absente
    (rang None). 0.0 sur une liste vide (pas de division par zéro)."""
    if not rangs:
        return 0.0
    return sum(1 / rang if rang is not None else 0.0 for rang in rangs) / len(rangs)


def calculer_recall_a_k(candidats_tries: list[int], cibles: list[int], k: int) -> float:
    """Proportion des cibles présentes dans les k premiers candidats.
    0.0 si cibles est vide (pas de division par zéro)."""
    if not cibles:
        return 0.0
    top_k = set(candidats_tries[:k])
    trouves = sum(1 for cible in cibles if cible in top_k)
    return trouves / len(cibles)


def cosine_similarity_matrix(
    vecteur_question: list[float], vecteurs_regles: dict[int, list[float]]
) -> list[tuple[int, float]]:
    """Similarité cosinus entre un vecteur question et un ensemble de
    vecteurs de règles, calculée en numpy (pas de requête SQL). Retourne
    les (numéro, score) triés par similarité décroissante."""
    numeros = list(vecteurs_regles.keys())
    matrice = np.array([vecteurs_regles[numero] for numero in numeros])
    q = np.array(vecteur_question)
    normes = np.linalg.norm(matrice, axis=1) * np.linalg.norm(q)
    scores = (matrice @ q) / normes
    resultat = sorted(zip(numeros, scores.tolist(), strict=True), key=lambda t: t[1], reverse=True)
    return resultat


def retrieve_variante(
    sous_questions_vecteurs: list[list[float]],
    vecteurs_regles: dict[int, list[float]],
    top_n: int,
) -> list[tuple[int, float]]:
    """Même logique de fusion que app.retrieval.retrieval.retrieve(), en
    numpy plutôt que pgvector : top_n par sous-question, union
    dédoublonnée en gardant le meilleur score, ordre de première
    apparition."""
    ordre: list[int] = []
    meilleurs_scores: dict[int, float] = {}
    for vecteur in sous_questions_vecteurs:
        top = cosine_similarity_matrix(vecteur, vecteurs_regles)[:top_n]
        for numero, score in top:
            if numero not in meilleurs_scores:
                ordre.append(numero)
                meilleurs_scores[numero] = score
            elif score > meilleurs_scores[numero]:
                meilleurs_scores[numero] = score
    return [(numero, meilleurs_scores[numero]) for numero in ordre]
```

- [ ] **Step 4: Lancer les tests, vérifier qu'ils passent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -v`
Expected: PASS (toutes les nouvelles + anciennes assertions)

- [ ] **Step 5: Lint**

Run: `uv run ruff check app/ingestion/rag_acceptance.py tests/unit/ingestion/`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py
git commit -m "feat: fonctions de mesure MRR/recall@k et fusion numpy pour la vague 1"
```

---

### Task 3: Committer la dépendance numpy

**Files:**
- Modify: `pyproject.toml` (déjà modifié, non commité — vérifier l'état)
- Modify: `uv.lock` (déjà régénéré, non commité — vérifier l'état)

**Interfaces:** aucune (dépendance seulement).

- [ ] **Step 1: Vérifier l'état actuel**

Run: `git diff pyproject.toml | head -20`
Expected : une ligne ajoutée `"numpy>=2.5.3",` dans `dependencies`.

- [ ] **Step 2: Vérifier que le lock est à jour**

Run: `uv lock --check`
Expected: pas d'erreur (le lock déjà présent dans l'arbre de travail est cohérent avec `pyproject.toml`). Si erreur, lancer `uv lock` puis relancer la vérification.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: ajoute numpy (similarite cosinus en memoire pour la mesure des chunks)"
```

---

### Task 4: Script `scripts/mesure_variantes_chunks.py` + cible Makefile

**Files:**
- Create: `scripts/mesure_variantes_chunks.py`
- Modify: `Makefile` (après la cible `mesure-scores-refus`)

**Interfaces:**
- Consumes: `build_chunk_text`, `build_variant_text` (Task 1) ; `load_cases`, `rang_meilleure_cible`, `calculer_mrr`, `calculer_recall_a_k`, `retrieve_variante` (Task 2) ; `load_enriched_rules_from_db` (existant, `app/ingestion/stockage.py`) ; `DecompositionClient`, `EmbeddingClient` (existants).
- Pas de test unitaire dédié (même convention que `check_rag_acceptance.py`/`rag_dense_acceptance.py`/`mesure_scores_refus.py` : couplé à Azure réel, validé par exécution réelle).

- [ ] **Step 1: Écrire le script**

```python
"""Mesure MRR et recall@k pour 12 variantes de chunk (11 champs isolés +
le chunk complet de production comme baseline) sur les 114 cas
d'acceptance — vague 1 du protocole de mesure des chunks. Voir
docs/superpowers/specs/2026-09-11-mesure-chunks-vague1-design.md.

Aucune écriture dans regle.embedding : tous les vecteurs des variantes
restent en mémoire, la similarité est calculée en numpy (pas de requête
SQL pgvector). Décomposition et embedding des 114 questions calculés une
seule fois, réutilisés pour les 12 variantes.

Coût réel (~0,011 €), volontairement hors CI — lancé à la demande via
`make mesure-variantes-chunks`.
"""

import csv
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.chunking import build_chunk_text, build_variant_text  # noqa: E402
from app.ingestion.embedding import EmbeddingClient  # noqa: E402
from app.ingestion.llm_client import load_manifest  # noqa: E402
from app.ingestion.rag_acceptance import (  # noqa: E402
    calculer_mrr,
    calculer_recall_a_k,
    load_cases,
    rang_meilleure_cible,
    retrieve_variante,
)
from app.ingestion.stockage import load_enriched_rules_from_db  # noqa: E402
from app.logging_config import setup_logging  # noqa: E402
from app.retrieval.decomposition import DecompositionClient  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

CASES_PATH = Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance.jsonl"
REPORT_DIR = Path(__file__).resolve().parents[1] / "docs" / "eval"

BATCH_SIZE = 50
TOP_N = 15
RECALL_KS = [1, 3, 5, 10, 15]

CHAMPS_ISOLES = [
    "intitule",
    "theme",
    "contexte",
    "solution",
    "controle",
    "objectifs",
    "tags",
    "phases",
    "strategie_analyse",
    "strategie_justification",
    "guide_analyse",
]


def get_engine():
    """Construit l'engine SQLAlchemy depuis les variables .env."""
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url)


def vectoriser_variante(regles, champ: str | None, embedding_client: EmbeddingClient) -> dict:
    """Construit le texte de chaque règle pour une variante puis vectorise
    par lots de BATCH_SIZE. champ=None signifie la baseline
    (build_chunk_text). Règles à texte vide exclues (pas de texte envoyé
    à l'API)."""
    textes_par_numero = {}
    for rule in regles:
        texte = build_chunk_text(rule) if champ is None else build_variant_text(rule, champ)
        if texte is not None:
            textes_par_numero[rule.number] = texte

    numeros_ordonnes = list(textes_par_numero.keys())
    vecteurs_regles: dict[int, list[float]] = {}
    for i in range(0, len(numeros_ordonnes), BATCH_SIZE):
        lot_numeros = numeros_ordonnes[i : i + BATCH_SIZE]
        lot_textes = [textes_par_numero[n] for n in lot_numeros]
        lot_vecteurs = embedding_client.embed_batch(lot_textes)
        for numero, vecteur in zip(lot_numeros, lot_vecteurs, strict=True):
            vecteurs_regles[numero] = vecteur

    return vecteurs_regles


def mesurer_variante(
    nom_variante: str,
    vecteurs_regles: dict,
    cases: list[dict],
    sous_questions_vecteurs_par_cas: list[list[list[float]]],
) -> tuple[list[dict], list[dict]]:
    """Mesure une variante sur les 114 cas. Retourne (lignes_csv,
    lignes_resume_par_famille)."""
    lignes_csv = []
    rangs_par_famille: dict[str, list] = {}
    recalls_par_famille: dict[str, dict[int, list]] = {}

    for case, sous_questions_vecteurs in zip(cases, sous_questions_vecteurs_par_cas, strict=True):
        candidats = retrieve_variante(sous_questions_vecteurs, vecteurs_regles, top_n=TOP_N)
        candidats_tries = sorted(candidats, key=lambda t: t[1], reverse=True)
        numeros_tries = [numero for numero, _ in candidats_tries]

        cibles = case["numeros_regle_attendus"]
        cibles_valides = [c for c in cibles if c in vecteurs_regles]

        for rang, (numero, score) in enumerate(candidats_tries, start=1):
            lignes_csv.append(
                {
                    "variante": nom_variante,
                    "question": case["question"],
                    "famille": case["famille"],
                    "numeros_attendus": ";".join(str(c) for c in cibles),
                    "numero_retourne": numero,
                    "rang": rang,
                    "cosinus": f"{score:.6f}",
                    "est_cible": "oui" if numero in cibles else "non",
                }
            )

        if not cibles_valides:
            continue  # cas exclu pour cette variante (ex. cible sans tag, variante "tags")

        famille = case["famille"]
        rang = rang_meilleure_cible(numeros_tries, cibles_valides)
        rangs_par_famille.setdefault(famille, []).append(rang)
        for k in RECALL_KS:
            recalls_par_famille.setdefault(famille, {}).setdefault(k, []).append(
                calculer_recall_a_k(numeros_tries, cibles_valides, k)
            )

    lignes_resume = []
    for famille in rangs_par_famille:
        mrr = calculer_mrr(rangs_par_famille[famille])
        ligne = {"variante": nom_variante, "famille": famille, "mrr": mrr}
        for k in RECALL_KS:
            valeurs = recalls_par_famille[famille][k]
            ligne[f"recall_{k}"] = sum(valeurs) / len(valeurs)
        lignes_resume.append(ligne)
        progress_logger.info(
            f"mesure_variantes_chunks — {nom_variante} / {famille} : "
            f"MRR={mrr:.3f} recall@5={ligne['recall_5']:.3f}"
        )

    return lignes_csv, lignes_resume


def ecrire_csv(chemin: Path, lignes: list[dict]) -> None:
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "variante",
                "question",
                "famille",
                "numeros_attendus",
                "numero_retourne",
                "rang",
                "cosinus",
                "est_cible",
            ],
        )
        writer.writeheader()
        writer.writerows(lignes)


def ecrire_resume_markdown(chemin: Path, lignes: list[dict], horodatage: datetime) -> None:
    entete = (
        "| Variante | Famille | MRR | recall@1 | recall@3 | recall@5 | "
        "recall@10 | recall@15 |"
    )
    separateur = "|---|---|---|---|---|---|---|---|"
    corps = [
        f"| {r['variante']} | {r['famille']} | {r['mrr']:.3f} | "
        f"{r['recall_1']:.3f} | {r['recall_3']:.3f} | {r['recall_5']:.3f} | "
        f"{r['recall_10']:.3f} | {r['recall_15']:.3f} |"
        for r in lignes
    ]
    contenu = (
        f"# Mesure des variantes de chunk — vague 1 "
        f"({horodatage.strftime('%Y-%m-%d %H:%M')})\n\n"
        f"{entete}\n{separateur}\n" + "\n".join(corps) + "\n"
    )
    chemin.write_text(contenu, encoding="utf-8")


def main() -> None:
    setup_logging()
    load_dotenv()

    engine = get_engine()
    cases = load_cases(CASES_PATH)

    logger.info("=== mesure_variantes_chunks : démarrage ===")
    progress_logger.info("=== mesure_variantes_chunks : démarrage ===")

    with Session(engine) as session:
        enriched_rules = load_enriched_rules_from_db(session)
    regles = enriched_rules.regles

    decomposition_client = DecompositionClient()
    embedding_client = EmbeddingClient()

    # Décomposition + embedding des 114 questions, une seule fois — figés
    # et réutilisés pour les 12 variantes.
    sous_questions_vecteurs_par_cas = []
    for case in cases:
        sous_questions = decomposition_client.decomposer(case["question"])
        vecteurs = embedding_client.embed_batch(sous_questions)
        sous_questions_vecteurs_par_cas.append(vecteurs)

    progress_logger.info(
        f"mesure_variantes_chunks — décomposition des {len(cases)} cas terminée "
        f"({decomposition_client.input_tokens}+{decomposition_client.output_tokens} tokens)"
    )

    toutes_lignes_csv = []
    tous_lignes_resume = []

    variantes = [("baseline", None)] + [(champ, champ) for champ in CHAMPS_ISOLES]

    for nom_variante, champ in variantes:
        vecteurs_regles = vectoriser_variante(regles, champ, embedding_client)
        progress_logger.info(
            f"mesure_variantes_chunks — variante {nom_variante} : "
            f"{len(vecteurs_regles)}/{len(regles)} règles vectorisées"
        )

        lignes_csv, lignes_resume = mesurer_variante(
            nom_variante, vecteurs_regles, cases, sous_questions_vecteurs_par_cas
        )
        toutes_lignes_csv.extend(lignes_csv)
        tous_lignes_resume.extend(lignes_resume)

    horodatage = datetime.now()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    suffixe = horodatage.strftime("%Y-%m-%d_%H%M%S")

    csv_path = REPORT_DIR / f"mesure_variantes_chunks_{suffixe}.csv"
    ecrire_csv(csv_path, toutes_lignes_csv)

    md_path = REPORT_DIR / f"mesure_variantes_chunks_{suffixe}.md"
    ecrire_resume_markdown(md_path, tous_lignes_resume, horodatage)

    embedding_role = load_manifest()["embedding"]
    decomposition_role = load_manifest()["decomposition"]
    embedding_cost = (
        embedding_client.total_tokens * embedding_role["prix_entree_par_million"] / 1_000_000
    )
    decomposition_cost = (
        decomposition_client.input_tokens
        * decomposition_role["prix_entree_par_million"]
        / 1_000_000
        + decomposition_client.output_tokens
        * decomposition_role["prix_sortie_par_million"]
        / 1_000_000
    )
    cost = embedding_cost + decomposition_cost
    summary = (
        f"mesure_variantes_chunks — tokens embedding : {embedding_client.total_tokens}, "
        f"tokens décomposition : {decomposition_client.input_tokens}+"
        f"{decomposition_client.output_tokens}, coût estimé : {cost:.4f} €"
    )
    logger.info(summary)
    progress_logger.info(summary)

    logger.info(f"=== mesure_variantes_chunks : rapports écrits dans {csv_path} et {md_path} ===")
    progress_logger.info(
        f"=== mesure_variantes_chunks : rapports écrits dans {csv_path} et {md_path} ==="
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Ajouter la cible Makefile**

Dans `Makefile`, mettre à jour la ligne `.PHONY` :

```makefile
.PHONY: up up-db up-staging down migration downgrade migration-test ingestion clear export_sql import_sql test test-unit test-integration test-migration psql enrich-again embed-rules rag-acceptance rag-dense-acceptance mesure-scores-refus mesure-variantes-chunks api-regles api-regles-acceptance api-regles-dense-acceptance regles-api-client-install regles-api-client regles-api-client-test
```

Puis, juste après la cible `mesure-scores-refus` :

```makefile

## Mesure MRR/recall@k pour 12 variantes de chunk (11 champs isoles +
## baseline) sur les 114 cas d'acceptance — vague 1 du protocole de mesure
mesure-variantes-chunks:
	uv run python scripts/mesure_variantes_chunks.py
```

- [ ] **Step 3: Vérifier la syntaxe du script sans l'exécuter**

Run: `uv run python -c "import ast; ast.parse(open('scripts/mesure_variantes_chunks.py').read())"`
Expected: aucune erreur

- [ ] **Step 4: Lint**

Run: `uv run ruff check scripts/mesure_variantes_chunks.py`
Expected: `All checks passed!`

- [ ] **Step 5: Commit**

```bash
git add scripts/mesure_variantes_chunks.py Makefile
git commit -m "feat: script mesure_variantes_chunks (make mesure-variantes-chunks)"
```

---

### Task 5: Exécuter la mesure réelle (coût réel, hors CI) — étape manuelle

**Pas de code produit par cette tâche.**

- [ ] **Step 1: Vérifier les prérequis**

`.env` avec les secrets Azure présents (déjà vérifié pour le chantier refus le même jour), `POSTGRES_DB` migrée et contenant les 245 règles enrichies (pas besoin d'embeddings à jour dans `regle.embedding` — ce script ne les lit pas, il revectorise tout lui-même).

- [ ] **Step 2: Confirmer le coût avec David avant de lancer**

Ce run coûte réellement de l'argent (~0,011 €, décomposition + embedding de 114 questions + vectorisation de 245 règles × 12 variantes) — redemander confirmation explicite au moment de l'exécuter, même si déjà budgété dans la spec.

- [ ] **Step 3: Lancer la mesure**

Run: `make mesure-variantes-chunks`
Expected: deux fichiers créés dans `docs/eval/` (`mesure_variantes_chunks_<horodatage>.csv` et `.md`), coût affiché dans les logs.

- [ ] **Step 4: Vérifier le volume du CSV**

Run: `wc -l docs/eval/mesure_variantes_chunks_*.csv | tail -1`
Expected: de l'ordre de 19000 lignes (+1 pour l'en-tête) — 114 cas × ~15 candidats × 12 variantes, un peu plus pour les cas multi-sujets non plafonnés après fusion.

- [ ] **Step 5: Tracer dans CHANGELOG.md**

Ajouter une entrée `## [date] — Claude Code` résumant : 12 variantes mesurées, volume du CSV, coût réel observé, et un aperçu des variantes qui se distinguent (MRR le plus haut/bas par famille, lu dans le `.md` généré) — sans tirer de conclusion sur un choix de chunk (hors périmètre de cette spec, réservé à la vague 2).

---

## Self-Review (déjà appliqué en rédigeant ce plan)

- **Couverture de la spec** : les 12 variantes (Task 4, `vectoriser_variante` + boucle `variantes`), la gestion des champs vides pour `tags` (Task 1 `build_variant_text` retourne `None` ; Task 4 `mesurer_variante` filtre `cibles_valides`), le MRR « meilleure cible » (Task 2 `rang_meilleure_cible`), le recall@k en fraction (Task 2 `calculer_recall_a_k`), le CSV format long + résumé Markdown (Task 4 `ecrire_csv`/`ecrire_resume_markdown`), aucune écriture dans `regle.embedding` (Task 2/4 : tout reste en `dict` Python), le commit de `numpy` (Task 3) — tout couvert.
- **Cohérence des types** : `vecteurs_regles: dict[int, list[float]]` cohérent entre `vectoriser_variante` (Task 4), `cosine_similarity_matrix`/`retrieve_variante` (Task 2) ; `candidats_tries: list[int]` cohérent entre `rang_meilleure_cible`/`calculer_recall_a_k` (Task 2) et leur appel dans `mesurer_variante` (Task 4).
- **Pas de placeholder** : le script complet de la Task 4 est donné intégralement, pas de fonction esquissée.
