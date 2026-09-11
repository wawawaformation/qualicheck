# Mesure des combinaisons de chunk — Vague 3 (multi-vecteurs) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mesurer si un candidat à 3 vecteurs par règle (chunk complet + intitulé seul + guide_analyse seul, fusionnés à la requête en gardant le meilleur score) bat le chunk unique de production, en réutilisant le jeu réservé et le critère de décision déjà actés en vague 2.

**Architecture:** 3 types de vecteurs sont construits par règle avec les fonctions existantes (`build_chunk_text`, `build_variant_text`). À la requête, chaque type produit son propre top-N (via `retrieve_variante`, déjà fusionné sur les sous-questions) ; les 3 résultats sont fusionnés en gardant le meilleur score par règle (`fusionner_meilleur_score`, nouveau). Le jeu réservé déjà figé par la vague 2 est chargé (jamais retiré) ; le critère de décision de la vague 2 (`appliquer_critere_decision`) est réutilisé tel quel pour comparer `baseline` et `F_multi_vecteurs`.

**Tech Stack:** Python, numpy, SQLAlchemy (lecture seule), Azure OpenAI (embeddings + décomposition), pytest.

## Global Constraints

- Retry LLM : 3 tentatives avec backoff (déjà en place dans `DecompositionClient`/`EmbeddingClient`, réutilisés tels quels).
- Aucune écriture dans `regle.embedding` (colonne de production) — tous les vecteurs restent en mémoire.
- Pause de 20s entre lots d'embedding (rate limit Azure S0, incident vague 1) — reprise telle quelle.
- Traçage : `CHANGELOG.md` à la fin de ce plan, format `## [date] — [outil]`.
- Le CSV brut n'est jamais réécrit par-dessus un fichier annoté par David — chaque run produit un nouveau fichier horodaté.
- Le jeu réservé (`tests/acceptance/rag_acceptance_holdout.json`) n'est **jamais retiré** par cette vague — s'il n'existe pas (vague 2 jamais exécutée), le script s'arrête avec une erreur explicite plutôt que d'en créer un nouveau.
- Dimension d'embedding : 1536 (inchangée, `EmbeddingClient.EMBEDDING_DIMENSIONS`) — la dimension réduite est hors périmètre de cette vague.

---

## Contexte technique déjà vérifié dans le code

- `app/ingestion/chunking.py::build_chunk_text(rule) -> str` (baseline) et `build_variant_text(rule, champ) -> str | None` (vague 1, `intitule`/`guide_analyse` ne retournent jamais `None` — champs toujours renseignés sur les 245 règles) existent déjà. Aucune nouvelle fonction de construction de texte n'est nécessaire pour cette vague.
- `app/ingestion/rag_acceptance.py` contient déjà (lignes vérifiées) :
  - `retrieve_variante(sous_questions_vecteurs, vecteurs_regles, top_n) -> list[tuple[int, float]]` (ligne 194)
  - `mesurer_variante(nom_variante, vecteurs_regles, cases, sous_questions_vecteurs_par_cas, top_n, recall_ks) -> tuple[list[dict], list[dict]]` (ligne 216) — réutilisée telle quelle pour mesurer `baseline`.
  - `appliquer_critere_decision(mrr_exploration, mrr_reserve, nom_baseline="baseline") -> dict` (ligne 78) — déjà générique pour N candidats, aucune modification nécessaire.
  - `construire_resume_markdown_vague2(lignes_exploration, lignes_reserve, decision, horodatage) -> str` (ligne 305) — ce plan y ajoute un paramètre `titre` optionnel.
- `scripts/mesure_combinaisons_chunks.py` (vague 2) contient `HOLDOUT_PATH` et `charger_ou_creer_jeu_reserve()` — **pas importés** par le nouveau script (convention du projet : chaque script sous `scripts/` est autonome, pas de `__init__.py` dans `scripts/`, aucun script n'en importe un autre à ce jour). Ce plan écrit un équivalent en lecture seule (`charger_jeu_reserve_existant`) directement dans le nouveau script.
- Convention `scripts/` = points d'entrée seuls, toute logique testable vit dans `app/`. Aucun test unitaire pour les scripts couplés à Azure réel — ce plan suit la même règle pour `scripts/mesure_multi_vecteurs_chunks.py`.

---

### Task 1: `fusionner_meilleur_score()` — fusion générique de plusieurs listes de candidats

**Files:**
- Modify: `app/ingestion/rag_acceptance.py`
- Test: `tests/unit/ingestion/test_rag_acceptance.py`

**Interfaces:**
- Produces: `fusionner_meilleur_score(resultats: list[list[tuple[int, float]]]) -> list[tuple[int, float]]`.

- [ ] **Step 1: Écrire les tests (ils doivent échouer)**

Ajouter dans `tests/unit/ingestion/test_rag_acceptance.py`, à la fin du bloc d'import existant (`from app.ingestion.rag_acceptance import (...)`), ajouter `fusionner_meilleur_score` à la liste importée :

```python
from app.ingestion.rag_acceptance import (
    appliquer_critere_decision,
    calculer_mrr,
    calculer_recall_a_k,
    candidat_regresse,
    compute_taux_par_famille,
    construire_resume_markdown,
    construire_resume_markdown_vague2,
    cosine_similarity_matrix,
    evaluate_case,
    format_dataset_versions,
    fusionner_meilleur_score,
    is_acceptable,
    load_cases,
    mesurer_variante,
    metriques_scores,
    mrr_moyen_non_pondere,
    rang_meilleure_cible,
    retrieve_variante,
    tirer_jeu_reserve,
)
```

Puis ajouter à la fin du fichier :

```python
def test_fusionner_meilleur_score_garde_le_meilleur_sur_chevauchement():
    """Une règle présente dans plusieurs listes garde son meilleur score."""
    resultats = [[(1, 0.5), (2, 0.3)], [(1, 0.8), (3, 0.4)]]

    assert fusionner_meilleur_score(resultats) == [(1, 0.8), (2, 0.3), (3, 0.4)]


def test_fusionner_meilleur_score_union_sans_chevauchement():
    """Des listes disjointes produisent l'union complète."""
    resultats = [[(1, 0.5)], [(2, 0.3)]]

    assert fusionner_meilleur_score(resultats) == [(1, 0.5), (2, 0.3)]


def test_fusionner_meilleur_score_ordre_premiere_apparition():
    """L'ordre suit la première apparition entre les listes, pas le score."""
    resultats = [[(2, 0.1)], [(1, 0.9)]]

    assert fusionner_meilleur_score(resultats) == [(2, 0.1), (1, 0.9)]


def test_fusionner_meilleur_score_liste_vide():
    """Aucune liste à fusionner retourne une liste vide."""
    assert fusionner_meilleur_score([]) == []
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -v`
Expected: FAIL (`ImportError: cannot import name 'fusionner_meilleur_score'`)

- [ ] **Step 3: Implémenter la fonction**

Ajouter dans `app/ingestion/rag_acceptance.py`, après `retrieve_variante()` (ligne 213, avant `mesurer_variante`) :

```python
def fusionner_meilleur_score(
    resultats: list[list[tuple[int, float]]],
) -> list[tuple[int, float]]:
    """Fusionne plusieurs listes de (numéro, score) déjà produites (ex.
    une par type de vecteur via retrieve_variante), en gardant le
    meilleur score par règle. Ordre de première apparition entre les
    listes, dans l'ordre donné — même principe que la fusion déjà dans
    retrieve_variante, généralisé à des listes déjà calculées."""
    ordre: list[int] = []
    meilleurs_scores: dict[int, float] = {}
    for resultat in resultats:
        for numero, score in resultat:
            if numero not in meilleurs_scores:
                ordre.append(numero)
                meilleurs_scores[numero] = score
            elif score > meilleurs_scores[numero]:
                meilleurs_scores[numero] = score
    return [(numero, meilleurs_scores[numero]) for numero in ordre]
```

- [ ] **Step 4: Lancer les tests, vérifier qu'ils passent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -v`
Expected: PASS

- [ ] **Step 5: Lint**

Run: `uv run ruff check app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py
git commit -m "feat: fusionner_meilleur_score pour la fusion multi-vecteurs (vague 3)"
```

---

### Task 2: `mesurer_candidat_fusion()` — mesure d'un candidat à plusieurs vecteurs par règle

**Files:**
- Modify: `app/ingestion/rag_acceptance.py`
- Test: `tests/unit/ingestion/test_rag_acceptance.py`

**Interfaces:**
- Consumes: `retrieve_variante`, `fusionner_meilleur_score` (Task 1), `rang_meilleure_cible`, `calculer_mrr`, `calculer_recall_a_k` (existants).
- Produces: `mesurer_candidat_fusion(nom_candidat: str, vecteurs_par_type: dict[str, dict[int, list[float]]], cases: list[dict], sous_questions_vecteurs_par_cas: list[list[list[float]]], top_n: int, recall_ks: list[int]) -> tuple[list[dict], list[dict]]`.

- [ ] **Step 1: Écrire les tests (ils doivent échouer)**

Ajouter `mesurer_candidat_fusion` à l'import existant de `test_rag_acceptance.py` (même bloc que Task 1, ordre alphabétique — juste après `mesurer_variante`) :

```python
    mesurer_candidat_fusion,
    mesurer_variante,
```

Puis ajouter à la fin du fichier :

```python
def test_mesurer_candidat_fusion_cible_trouvee_via_fusion():
    """La fusion de deux types de vecteur retrouve la cible ; le MRR et
    le recall de sa famille sont alimentés."""
    vecteurs_par_type = {
        "baseline": {1: [1.0, 0.0], 2: [0.0, 1.0]},
        "intitule": {1: [0.0, 1.0], 2: [1.0, 0.0]},
    }
    cases = [{"question": "Q1", "famille": "fam_a", "numeros_regle_attendus": [1]}]
    sous_questions_vecteurs_par_cas = [[[1.0, 0.0]]]

    lignes_csv, lignes_resume = mesurer_candidat_fusion(
        "F_multi_vecteurs",
        vecteurs_par_type,
        cases,
        sous_questions_vecteurs_par_cas,
        top_n=2,
        recall_ks=[1],
    )

    assert lignes_resume == [
        {"variante": "F_multi_vecteurs", "famille": "fam_a", "mrr": 1.0, "recall_1": 1.0}
    ]
    assert len(lignes_csv) == 2


def test_mesurer_candidat_fusion_garde_le_meilleur_score_entre_types():
    """Une règle retrouvée par deux types de vecteur garde le meilleur des
    deux scores dans le CSV."""
    vecteurs_par_type = {
        "baseline": {1: [1.0, 0.0]},
        "intitule": {1: [0.6, 0.8]},
    }
    cases = [{"question": "Q1", "famille": "fam_a", "numeros_regle_attendus": [1]}]
    sous_questions_vecteurs_par_cas = [[[1.0, 0.0]]]

    lignes_csv, _ = mesurer_candidat_fusion(
        "F_multi_vecteurs",
        vecteurs_par_type,
        cases,
        sous_questions_vecteurs_par_cas,
        top_n=2,
        recall_ks=[1],
    )

    assert len(lignes_csv) == 1
    assert lignes_csv[0]["cosinus"] == "1.000000"


def test_mesurer_candidat_fusion_cible_absente_de_tous_les_types():
    """Aucune cible retrouvée par aucun type : cas exclu du résumé, présent
    dans le CSV avec est_cible=non."""
    vecteurs_par_type = {"baseline": {1: [1.0, 0.0], 2: [0.0, 1.0]}}
    cases = [{"question": "Q1", "famille": "fam_a", "numeros_regle_attendus": [99]}]
    sous_questions_vecteurs_par_cas = [[[1.0, 0.0]]]

    lignes_csv, lignes_resume = mesurer_candidat_fusion(
        "F_multi_vecteurs",
        vecteurs_par_type,
        cases,
        sous_questions_vecteurs_par_cas,
        top_n=2,
        recall_ks=[1],
    )

    assert lignes_resume == []
    assert len(lignes_csv) == 2
    assert all(ligne["est_cible"] == "non" for ligne in lignes_csv)
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -v`
Expected: FAIL (`ImportError: cannot import name 'mesurer_candidat_fusion'`)

- [ ] **Step 3: Implémenter la fonction**

Ajouter dans `app/ingestion/rag_acceptance.py`, après `mesurer_variante()` (juste avant `construire_resume_markdown`) :

```python
def mesurer_candidat_fusion(
    nom_candidat: str,
    vecteurs_par_type: dict[str, dict[int, list[float]]],
    cases: list[dict],
    sous_questions_vecteurs_par_cas: list[list[list[float]]],
    top_n: int,
    recall_ks: list[int],
) -> tuple[list[dict], list[dict]]:
    """Comme mesurer_variante, mais pour un candidat à plusieurs vecteurs
    par règle (un par type de chunk, ex. règle complète/intitulé/guide
    d'analyse) : chaque type est cherché séparément (retrieve_variante)
    puis fusionné en gardant le meilleur score par règle
    (fusionner_meilleur_score). Retourne (lignes_csv,
    lignes_resume_par_famille).

    Pure : aucun appel réseau, BDD ni log.
    """
    lignes_csv = []
    rangs_par_famille: dict[str, list] = {}
    recalls_par_famille: dict[str, dict[int, list]] = {}
    numeros_disponibles = next(iter(vecteurs_par_type.values()))

    for case, sous_questions_vecteurs in zip(cases, sous_questions_vecteurs_par_cas, strict=True):
        resultats_par_type = [
            retrieve_variante(sous_questions_vecteurs, vecteurs_regles, top_n=top_n)
            for vecteurs_regles in vecteurs_par_type.values()
        ]
        candidats = fusionner_meilleur_score(resultats_par_type)
        candidats_tries = sorted(candidats, key=lambda t: t[1], reverse=True)
        numeros_tries = [numero for numero, _ in candidats_tries]

        cibles = case["numeros_regle_attendus"]
        cibles_valides = [c for c in cibles if c in numeros_disponibles]
        cibles_mesurees_str = ";".join(str(c) for c in cibles_valides)

        for rang, (numero, score) in enumerate(candidats_tries, start=1):
            lignes_csv.append(
                {
                    "variante": nom_candidat,
                    "question": case["question"],
                    "famille": case["famille"],
                    "numeros_attendus": ";".join(str(c) for c in cibles),
                    "cibles_mesurees": cibles_mesurees_str,
                    "numero_retourne": numero,
                    "rang": rang,
                    "cosinus": f"{score:.6f}",
                    "est_cible": "oui" if numero in cibles else "non",
                }
            )

        if not cibles_valides:
            continue

        famille = case["famille"]
        rang = rang_meilleure_cible(numeros_tries, cibles_valides)
        rangs_par_famille.setdefault(famille, []).append(rang)
        for k in recall_ks:
            recalls_par_famille.setdefault(famille, {}).setdefault(k, []).append(
                calculer_recall_a_k(numeros_tries, cibles_valides, k)
            )

    lignes_resume = []
    for famille in rangs_par_famille:
        mrr = calculer_mrr(rangs_par_famille[famille])
        ligne = {"variante": nom_candidat, "famille": famille, "mrr": mrr}
        for k in recall_ks:
            valeurs = recalls_par_famille[famille][k]
            ligne[f"recall_{k}"] = sum(valeurs) / len(valeurs)
        lignes_resume.append(ligne)

    return lignes_csv, lignes_resume
```

- [ ] **Step 4: Lancer les tests, vérifier qu'ils passent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -v`
Expected: PASS

- [ ] **Step 5: Lint**

Run: `uv run ruff check app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py
git commit -m "feat: mesurer_candidat_fusion pour les candidats multi-vecteurs (vague 3)"
```

---

### Task 3: `construire_resume_markdown_vague2()` — paramètre `titre` optionnel

**Files:**
- Modify: `app/ingestion/rag_acceptance.py`
- Test: `tests/unit/ingestion/test_rag_acceptance.py`

**Interfaces:**
- Produces (signature modifiée, rétrocompatible) : `construire_resume_markdown_vague2(lignes_exploration: list[dict], lignes_reserve: list[dict], decision: dict, horodatage: datetime, titre: str | None = None) -> str`.

- [ ] **Step 1: Écrire les tests (ils doivent échouer)**

Ajouter à la fin de `tests/unit/ingestion/test_rag_acceptance.py` (après les tests `construire_resume_markdown_vague2_*` existants) :

```python
def test_construire_resume_markdown_vague2_titre_personnalise():
    """Un titre personnalisé remplace le titre par défaut de la vague 2."""
    ligne = _ligne_resume_exemple()
    decision = {
        "candidats_elimines": [],
        "gagnant_provisoire": "baseline",
        "choix_retenu": "baseline",
        "valide": True,
    }

    resultat = construire_resume_markdown_vague2(
        [ligne],
        [ligne],
        decision,
        datetime(2026, 9, 11, 10, 0),
        titre="Mesure multi-vecteurs — vague 3",
    )

    assert resultat.startswith("# Mesure multi-vecteurs — vague 3")


def test_construire_resume_markdown_vague2_titre_par_defaut_inchange():
    """Sans titre fourni, le texte reste celui de la vague 2 (non-régression)."""
    ligne = _ligne_resume_exemple()
    decision = {
        "candidats_elimines": [],
        "gagnant_provisoire": "baseline",
        "choix_retenu": "baseline",
        "valide": True,
    }

    resultat = construire_resume_markdown_vague2(
        [ligne], [ligne], decision, datetime(2026, 9, 11, 10, 0)
    )

    assert resultat.startswith("# Mesure des combinaisons de chunk — vague 2")
```

`_ligne_resume_exemple()` existe déjà dans le fichier (ajoutée en vague 2, juste avant les tests `construire_resume_markdown_vague2_*`) — pas besoin de la redéfinir.

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -v -k titre`
Expected: le test `test_construire_resume_markdown_vague2_titre_personnalise` FAIL
(`TypeError: construire_resume_markdown_vague2() got an unexpected keyword
argument 'titre'`) — le second test (`titre_par_defaut_inchange`) PASSE déjà
avec la fonction actuelle : c'est un test de non-régression ajouté par
anticipation, pas un test qui doit échouer avant l'implémentation.

- [ ] **Step 3: Modifier la fonction**

Dans `app/ingestion/rag_acceptance.py`, remplacer la signature et le retour de `construire_resume_markdown_vague2` :

```python
def construire_resume_markdown_vague2(
    lignes_exploration: list[dict],
    lignes_reserve: list[dict],
    decision: dict,
    horodatage: datetime,
    titre: str | None = None,
) -> str:
    """Construit le texte Markdown du résumé d'une vague de mesure à
    critère de décision (vague 2 et suivantes) : tableau MRR/recall@k sur
    le jeu d'exploration, tableau sur le jeu réservé, et la conclusion du
    critère de décision. `titre` par défaut : celui de la vague 2
    (docs/superpowers/specs/2026-09-11-mesure-chunks-vague2-design.md) —
    une vague suivante (ex. vague 3) passe son propre titre. Pure : pas
    d'écriture disque (voir scripts/mesure_combinaisons_chunks.py::ecrire_resume_markdown)."""
    titre_effectif = titre if titre is not None else "Mesure des combinaisons de chunk — vague 2"
    entete = (
        "| Variante | Famille | MRR | recall@1 | recall@3 | recall@5 | "
        "recall@10 | recall@15 |"
    )
    separateur = "|---|---|---|---|---|---|---|---|"

    def tableau(lignes: list[dict]) -> str:
        corps = [
            f"| {r['variante']} | {r['famille']} | {r['mrr']:.3f} | "
            f"{r['recall_1']:.3f} | {r['recall_3']:.3f} | {r['recall_5']:.3f} | "
            f"{r['recall_10']:.3f} | {r['recall_15']:.3f} |"
            for r in lignes
        ]
        return f"{entete}\n{separateur}\n" + "\n".join(corps) + "\n"

    candidats_elimines = decision["candidats_elimines"]
    conclusion = (
        f"Candidats éliminés (régression vs baseline sur au moins une "
        f"famille, jeu d'exploration) : "
        f"{', '.join(candidats_elimines) if candidats_elimines else 'aucun'}.\n\n"
        f"Gagnant provisoire (MRR moyen non pondéré le plus haut, jeu "
        f"d'exploration) : **{decision['gagnant_provisoire']}**.\n\n"
        f"Validation sur le jeu réservé : "
        f"{'confirmée' if decision['valide'] else 'NON confirmée'}.\n\n"
        f"**Choix retenu : {decision['choix_retenu']}**"
    )

    return (
        f"# {titre_effectif} "
        f"({horodatage.strftime('%Y-%m-%d %H:%M')})\n\n"
        f"## Jeu d'exploration\n\n{tableau(lignes_exploration)}\n"
        f"## Jeu réservé\n\n{tableau(lignes_reserve)}\n"
        f"## Décision\n\n{conclusion}\n"
    )
```

- [ ] **Step 4: Lancer les tests, vérifier qu'ils passent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -v`
Expected: PASS (toutes les anciennes assertions de la vague 2 sur cette fonction restent vraies : le titre par défaut ne change pas)

- [ ] **Step 5: Lint**

Run: `uv run ruff check app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py
git commit -m "feat: parametre titre optionnel sur construire_resume_markdown_vague2"
```

---

### Task 4: Script `scripts/mesure_multi_vecteurs_chunks.py` + cible Makefile

**Files:**
- Create: `scripts/mesure_multi_vecteurs_chunks.py`
- Modify: `Makefile:1` (ligne `.PHONY`), après la cible `mesure-combinaisons-chunks`

**Interfaces:**
- Consumes: `build_chunk_text`, `build_variant_text` (existants) ; `load_cases`, `mesurer_variante`, `mesurer_candidat_fusion` (Task 2), `appliquer_critere_decision`, `construire_resume_markdown_vague2` (Task 3) ; `load_enriched_rules_from_db`, `DecompositionClient`, `EmbeddingClient` (existants).
- Pas de test unitaire dédié (même convention que les vagues 1 et 2).

- [ ] **Step 1: Écrire le script**

```python
"""Mesure MRR et recall@k pour un candidat à 3 vecteurs par règle (chunk
complet + intitulé seul + guide_analyse seul, fusionnés à la requête en
gardant le meilleur score par règle) contre la baseline — vague 3 du
protocole de mesure des chunks. Réutilise le jeu réservé et le critère
de décision déjà actés en vague 2. Voir
docs/superpowers/specs/2026-09-11-mesure-chunks-vague3-design.md.

Aucune écriture dans regle.embedding : tous les vecteurs restent en
mémoire, la similarité est calculée en numpy (pas de requête SQL
pgvector). Décomposition et embedding des 114 questions calculés une
seule fois.

Coût réel estimé 0,010-0,015 €, volontairement hors CI — lancé à la
demande via `make mesure-multi-vecteurs-chunks`.
"""

import json
import logging
import os
import sys
import time
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
    appliquer_critere_decision,
    construire_resume_markdown_vague2,
    load_cases,
    mesurer_candidat_fusion,
    mesurer_variante,
)
from app.ingestion.stockage import load_enriched_rules_from_db  # noqa: E402
from app.logging_config import setup_logging  # noqa: E402
from app.retrieval.decomposition import DecompositionClient  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

CASES_PATH = Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance.jsonl"
HOLDOUT_PATH = (
    Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance_holdout.json"
)
REPORT_DIR = Path(__file__).resolve().parents[1] / "docs" / "eval"

BATCH_SIZE = 50
TOP_N = 15
RECALL_KS = [1, 3, 5, 10, 15]
NOM_CANDIDAT_FUSION = "F_multi_vecteurs"

# type de vecteur -> champ (None = baseline, build_chunk_text)
TYPES_VECTEURS = {
    "baseline": None,
    "intitule": "intitule",
    "guide_analyse": "guide_analyse",
}


def get_engine():
    """Construit l'engine SQLAlchemy depuis les variables .env."""
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url)


def charger_jeu_reserve_existant(cases: list[dict]) -> tuple[list[dict], list[dict]]:
    """Charge le jeu réservé déjà figé par la vague 2
    (tests/acceptance/rag_acceptance_holdout.json) — ne le tire jamais.
    Ce fichier doit déjà exister (vague 2 exécutée avant cette vague)."""
    if not HOLDOUT_PATH.exists():
        raise FileNotFoundError(
            f"{HOLDOUT_PATH} introuvable — la vague 2 "
            "(make mesure-combinaisons-chunks) doit avoir été exécutée "
            "au moins une fois avant cette vague."
        )
    questions_reserve = set(json.loads(HOLDOUT_PATH.read_text(encoding="utf-8")))
    reserve = [c for c in cases if c["question"] in questions_reserve]
    exploration = [c for c in cases if c["question"] not in questions_reserve]
    return exploration, reserve


def vectoriser_type(
    regles, champ: str | None, embedding_client: EmbeddingClient
) -> dict[int, list[float]]:
    """Construit le texte de chaque règle pour un type de vecteur (baseline
    si champ=None, sinon un champ isolé via build_variant_text) puis
    vectorise par lots de BATCH_SIZE."""
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
        # Pause entre lots : évite le RateLimitReached Azure (tier S0),
        # rencontré lors de la vague 1 (scripts/mesure_variantes_chunks.py).
        time.sleep(20)

    return vecteurs_regles


def ecrire_csv(chemin: Path, lignes: list[dict]) -> None:
    import csv

    with open(chemin, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "variante",
                "sous_ensemble",
                "question",
                "famille",
                "numeros_attendus",
                "cibles_mesurees",
                "numero_retourne",
                "rang",
                "cosinus",
                "est_cible",
            ],
        )
        writer.writeheader()
        writer.writerows(lignes)


def ecrire_resume_markdown(
    chemin: Path,
    lignes_exploration: list[dict],
    lignes_reserve: list[dict],
    decision: dict,
    horodatage: datetime,
) -> None:
    chemin.write_text(
        construire_resume_markdown_vague2(
            lignes_exploration,
            lignes_reserve,
            decision,
            horodatage,
            titre="Mesure multi-vecteurs — vague 3",
        ),
        encoding="utf-8",
    )


def main() -> None:
    setup_logging()
    load_dotenv()

    engine = get_engine()
    cases = load_cases(CASES_PATH)
    exploration_cases, reserve_cases = charger_jeu_reserve_existant(cases)

    logger.info("=== mesure_multi_vecteurs_chunks : démarrage ===")
    progress_logger.info(
        f"mesure_multi_vecteurs_chunks — jeu d'exploration : {len(exploration_cases)} cas, "
        f"jeu réservé : {len(reserve_cases)} cas"
    )

    with Session(engine) as session:
        enriched_rules = load_enriched_rules_from_db(session)
    regles = enriched_rules.regles

    decomposition_client = DecompositionClient()
    embedding_client = EmbeddingClient()

    vecteurs_par_question: dict[str, list[list[float]]] = {}
    for case in cases:
        sous_questions = decomposition_client.decomposer(case["question"])
        vecteurs_par_question[case["question"]] = embedding_client.embed_batch(sous_questions)

    progress_logger.info(
        f"mesure_multi_vecteurs_chunks — décomposition des {len(cases)} cas terminée "
        f"({decomposition_client.input_tokens}+{decomposition_client.output_tokens} tokens)"
    )

    vecteurs_par_type: dict[str, dict[int, list[float]]] = {}
    for nom_type, champ in TYPES_VECTEURS.items():
        vecteurs_par_type[nom_type] = vectoriser_type(regles, champ, embedding_client)
        progress_logger.info(
            f"mesure_multi_vecteurs_chunks — type {nom_type} : "
            f"{len(vecteurs_par_type[nom_type])}/{len(regles)} règles vectorisées"
        )

    vecteurs_exploration = [vecteurs_par_question[c["question"]] for c in exploration_cases]
    vecteurs_reserve = [vecteurs_par_question[c["question"]] for c in reserve_cases]

    lignes_csv_baseline_exploration, lignes_resume_baseline_exploration = mesurer_variante(
        "baseline", vecteurs_par_type["baseline"], exploration_cases, vecteurs_exploration,
        TOP_N, RECALL_KS,
    )
    lignes_csv_baseline_reserve, lignes_resume_baseline_reserve = mesurer_variante(
        "baseline", vecteurs_par_type["baseline"], reserve_cases, vecteurs_reserve,
        TOP_N, RECALL_KS,
    )

    lignes_csv_fusion_exploration, lignes_resume_fusion_exploration = mesurer_candidat_fusion(
        NOM_CANDIDAT_FUSION, vecteurs_par_type, exploration_cases, vecteurs_exploration,
        TOP_N, RECALL_KS,
    )
    lignes_csv_fusion_reserve, lignes_resume_fusion_reserve = mesurer_candidat_fusion(
        NOM_CANDIDAT_FUSION, vecteurs_par_type, reserve_cases, vecteurs_reserve,
        TOP_N, RECALL_KS,
    )

    for ligne in lignes_csv_baseline_exploration:
        ligne["sous_ensemble"] = "exploration"
    for ligne in lignes_csv_baseline_reserve:
        ligne["sous_ensemble"] = "reserve"
    for ligne in lignes_csv_fusion_exploration:
        ligne["sous_ensemble"] = "exploration"
    for ligne in lignes_csv_fusion_reserve:
        ligne["sous_ensemble"] = "reserve"

    toutes_lignes_csv = (
        lignes_csv_baseline_exploration
        + lignes_csv_baseline_reserve
        + lignes_csv_fusion_exploration
        + lignes_csv_fusion_reserve
    )

    mrr_exploration = {
        "baseline": {ligne["famille"]: ligne["mrr"] for ligne in lignes_resume_baseline_exploration},
        NOM_CANDIDAT_FUSION: {
            ligne["famille"]: ligne["mrr"] for ligne in lignes_resume_fusion_exploration
        },
    }
    mrr_reserve = {
        "baseline": {ligne["famille"]: ligne["mrr"] for ligne in lignes_resume_baseline_reserve},
        NOM_CANDIDAT_FUSION: {
            ligne["famille"]: ligne["mrr"] for ligne in lignes_resume_fusion_reserve
        },
    }
    decision = appliquer_critere_decision(mrr_exploration, mrr_reserve)
    progress_logger.info(f"mesure_multi_vecteurs_chunks — décision : {decision}")

    tous_lignes_resume_exploration = (
        lignes_resume_baseline_exploration + lignes_resume_fusion_exploration
    )
    tous_lignes_resume_reserve = lignes_resume_baseline_reserve + lignes_resume_fusion_reserve

    horodatage = datetime.now()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    suffixe = horodatage.strftime("%Y-%m-%d_%H%M%S")

    csv_path = REPORT_DIR / f"mesure_multi_vecteurs_chunks_{suffixe}.csv"
    ecrire_csv(csv_path, toutes_lignes_csv)

    md_path = REPORT_DIR / f"mesure_multi_vecteurs_chunks_{suffixe}.md"
    ecrire_resume_markdown(
        md_path, tous_lignes_resume_exploration, tous_lignes_resume_reserve, decision, horodatage
    )

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
        f"mesure_multi_vecteurs_chunks — tokens embedding : {embedding_client.total_tokens}, "
        f"tokens décomposition : {decomposition_client.input_tokens}+"
        f"{decomposition_client.output_tokens}, coût estimé : {cost:.4f} €"
    )
    logger.info(summary)
    progress_logger.info(summary)

    logger.info(
        f"=== mesure_multi_vecteurs_chunks : rapports écrits dans {csv_path} et {md_path} ==="
    )
    progress_logger.info(
        f"=== mesure_multi_vecteurs_chunks : rapports écrits dans {csv_path} et {md_path} ==="
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Ajouter la cible Makefile**

Dans `Makefile`, remplacer la ligne `.PHONY` (ligne 1) :

```makefile
.PHONY: up up-db up-staging down migration downgrade migration-test ingestion clear export_sql import_sql test test-unit test-integration test-migration psql enrich-again embed-rules rag-acceptance rag-dense-acceptance mesure-scores-refus mesure-variantes-chunks mesure-combinaisons-chunks mesure-multi-vecteurs-chunks api-regles api-regles-acceptance api-regles-dense-acceptance regles-api-client-install regles-api-client regles-api-client-test
```

Puis, juste après la cible `mesure-combinaisons-chunks` :

```makefile

## Mesure MRR/recall@k pour un candidat a 3 vecteurs par regle (complet +
## intitule + guide_analyse, fusionnes) contre la baseline — vague 3
mesure-multi-vecteurs-chunks:
	uv run python scripts/mesure_multi_vecteurs_chunks.py
```

- [ ] **Step 3: Vérifier la syntaxe du script sans l'exécuter**

Run: `uv run python -c "import ast; ast.parse(open('scripts/mesure_multi_vecteurs_chunks.py').read())"`
Expected: aucune erreur

- [ ] **Step 4: Lint**

Run: `uv run ruff check scripts/mesure_multi_vecteurs_chunks.py`
Expected: `All checks passed!` — si `E402`/`E501` apparaît, corriger en repliant la ligne concernée sur plusieurs lignes (même style que le reste du fichier), sans changer le comportement.

- [ ] **Step 5: Commit**

```bash
git add scripts/mesure_multi_vecteurs_chunks.py Makefile
git commit -m "feat: script mesure_multi_vecteurs_chunks (make mesure-multi-vecteurs-chunks)"
```

---

### Task 5: Exécuter la mesure réelle (coût réel, hors CI) — étape manuelle

**Pas de code produit par cette tâche.**

- [ ] **Step 1: Vérifier les prérequis**

`.env` avec les secrets Azure présents ; `POSTGRES_DB` migrée avec les 245 règles enrichies ; `tests/acceptance/rag_acceptance_holdout.json` doit déjà exister (créé par la vague 2 — vérifier avec `test -f tests/acceptance/rag_acceptance_holdout.json && echo present`).

- [ ] **Step 2: Confirmer le coût avec David avant de lancer**

Ce run coûte réellement de l'argent (~0,010-0,015 €, décomposition des 114 questions + vectorisation de 245 règles × 3 types de vecteur) — redemander confirmation explicite au moment de l'exécuter.

- [ ] **Step 3: Lancer la mesure**

Run: `make mesure-multi-vecteurs-chunks`
Expected: deux fichiers créés dans `docs/eval/` (`mesure_multi_vecteurs_chunks_<horodatage>.csv` et `.md`), coût affiché dans les logs. Le fichier `rag_acceptance_holdout.json` n'est **pas modifié** (vérifiable par `git status` : aucune modification sur ce fichier).

- [ ] **Step 4: Lire la conclusion du résumé Markdown**

Run: `tail -20 docs/eval/mesure_multi_vecteurs_chunks_*.md`
Expected: la section "## Décision" affiche si `F_multi_vecteurs` est éliminé ou gagnant provisoire, si la validation sur le jeu réservé est confirmée, et le choix retenu (`baseline` ou `F_multi_vecteurs`).

- [ ] **Step 5: Tracer dans CHANGELOG.md**

Ajouter une entrée `## [date] — Claude Code` résumant : le candidat mesuré (3 vecteurs, fusion meilleur score), le coût réel observé, et la conclusion du critère de décision — copiée depuis la section "Décision" du résumé Markdown, sans interprétation supplémentaire.

- [ ] **Step 6: Mettre à jour TODO.md et la mémoire assistant**

Dans `TODO.md`, mettre à jour la ligne "Vague 3" (actuellement marquée sans objet) avec le résultat réel. Mettre à jour la mémoire assistant `protocole_mesure_retrieval.md` avec le résultat (candidat retenu ou statu quo confirmé une seconde fois), et noter explicitement si l'hypothèse de la dimension d'embedding réduite reste à mesurer ou devient sans objet (si `F_multi_vecteurs` est déjà éliminé, l'optimisation de sa dimension ne se posera plus).

---

## Self-Review (déjà appliqué en rédigeant ce plan)

- **Couverture de la spec** : le candidat unique `F_multi_vecteurs` à 3 types de vecteurs (Task 4, `TYPES_VECTEURS` + boucle de vectorisation), la fusion meilleur-score-par-règle (Task 1 `fusionner_meilleur_score`, appelée par Task 2 `mesurer_candidat_fusion`), la réutilisation stricte du jeu réservé existant sans jamais le retirer (Task 4 `charger_jeu_reserve_existant`, lève une erreur explicite si absent plutôt que d'en créer un), la réutilisation du critère de décision générique (Task 4, `appliquer_critere_decision` appelé sans modification), le titre personnalisé du résumé Markdown (Task 3), aucune écriture dans `regle.embedding`, dimension d'embedding inchangée (1536, non touchée) — tout couvert. L'hypothèse de dimension réduite reste explicitement hors périmètre, comme prévu par la spec.
- **Cohérence des types** : `vecteurs_par_type: dict[str, dict[int, list[float]]]` cohérent entre `mesurer_candidat_fusion` (Task 2) et sa construction dans `main()` (Task 4) ; le candidat `baseline` est mesuré avec `mesurer_variante` (signature existante, inchangée) en passant `vecteurs_par_type["baseline"]` (un `dict[int, list[float]]` simple, pas le dict complet) ; `mrr_exploration`/`mrr_reserve: dict[str, dict[str, float]]` avec les clés `"baseline"` et `NOM_CANDIDAT_FUSION` cohérent avec la signature déjà existante d'`appliquer_critere_decision`.
- **Pas de placeholder** : le script complet de la Task 4 est donné intégralement, pas de fonction esquissée.
