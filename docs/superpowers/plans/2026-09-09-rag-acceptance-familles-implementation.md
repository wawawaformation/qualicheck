# Jeu d'acceptance RAG à familles multiples — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Étendre `tests/acceptance/rag_acceptance.jsonl` et la logique de
`app/ingestion/rag_acceptance.py`/`scripts/check_rag_acceptance.py` pour
exprimer des cas à cibles multiples, des cas sans réponse attendue, et un
taux de réussite calculé par famille de cas plutôt que globalement.

**Architecture:** `evaluate_case` produit un verdict à 3 états
(`PASS`/`FAIL`/`PARTIEL`) à partir d'une liste de cibles plutôt qu'un entier
unique. `compute_taux_par_famille` regroupe les évaluations par champ
`famille` et calcule un taux par groupe, en excluant les `PARTIEL` du
dénominateur. `is_acceptable` compare chaque famille (hors `sans_reponse`)
au seuil du manifest. Le script d'orchestration ne change que sa couche de
logging/reporting — la boucle d'appel pgvector reste identique.

**Tech Stack:** Python 3, pytest, SQLAlchemy/pgvector (inchangés — aucune
nouvelle dépendance).

## Global Constraints

- `taux_reussite_minimum: 0.8`, `top_n: 3` — valeurs inchangées dans
  `app/ingestion/manifest.yml`, s'appliquent désormais par famille.
- Tests unitaires de `app/ingestion/rag_acceptance.py` : aucun appel réseau
  ni BDD réelle (cohérent avec `tests/unit/ingestion/test_rag_acceptance.py`
  existant — `query_top_n_numeros`/`summarize_dataset_versions` restent
  validées par exécution réelle uniquement, `make rag-acceptance`).
- `pytest`/`ruff` verts sur toute la suite avant de considérer une tâche
  terminée.
- Toute réalisation tracée dans `CHANGELOG.md` (racine du projet) une fois
  le plan exécuté.
- Spec de référence :
  `docs/superpowers/specs/2026-09-09-rag-acceptance-familles-design.md`.

---

### Task 1: `evaluate_case` — verdict à 3 états (PASS/FAIL/PARTIEL)

**Files:**
- Modify: `app/ingestion/rag_acceptance.py:35-42` (fonction `evaluate_case`)
- Test: `tests/unit/ingestion/test_rag_acceptance.py:37-56` (remplace les 2
  tests existants par 6 nouveaux)

**Interfaces:**
- Consumes: rien de nouveau (pure fonction, aucune dépendance externe)
- Produces: `evaluate_case(case: dict, numeros_retournes: list[int]) -> dict`
  où `case` a les clés `question: str`, `famille: str`,
  `numeros_regle_attendus: list[int]`. Le dict retourné a les clés
  `question`, `famille`, `numeros_regle_attendus`, `numeros_retournes`,
  `verdict: Literal["PASS", "FAIL", "PARTIEL"]`. Consommé par Task 2
  (`compute_taux_par_famille` lit `evaluation["famille"]` et
  `evaluation["verdict"]`) et par Task 5 (le script lit ces mêmes clés pour
  logger chaque cas).

- [ ] **Step 1: Écrire les tests qui échouent**

Remplacer les deux tests existants
`test_evaluate_case_success_when_expected_in_results` et
`test_evaluate_case_failure_when_expected_absent` (lignes 37-56 du fichier
de test) par :

```python
def test_evaluate_case_pass_single_cible():
    """Un cas à cible unique réussit (PASS) si sa cible figure dans les résultats."""
    case = {"question": "Q1", "famille": "vocabulaire_source_opquast", "numeros_regle_attendus": [139]}

    result = evaluate_case(case, numeros_retournes=[42, 139, 7])

    assert result["verdict"] == "PASS"
    assert result["famille"] == "vocabulaire_source_opquast"
    assert result["numeros_regle_attendus"] == [139]
    assert result["numeros_retournes"] == [42, 139, 7]
    assert result["question"] == "Q1"


def test_evaluate_case_fail_single_cible_absente():
    """Un cas à cible unique échoue (FAIL) si sa cible est absente des résultats."""
    case = {"question": "Q1", "famille": "vocabulaire_source_opquast", "numeros_regle_attendus": [139]}

    result = evaluate_case(case, numeros_retournes=[42, 7, 8])

    assert result["verdict"] == "FAIL"


def test_evaluate_case_pass_toutes_cibles_multiples_trouvees():
    """Un cas à cibles multiples réussit (PASS) si toutes les cibles sont retrouvées."""
    case = {"question": "Q1", "famille": "regles_concurrentes", "numeros_regle_attendus": [58, 79]}

    result = evaluate_case(case, numeros_retournes=[58, 79, 152])

    assert result["verdict"] == "PASS"


def test_evaluate_case_partiel_certaines_cibles_trouvees():
    """Un cas à cibles multiples est PARTIEL si certaines cibles manquent."""
    case = {"question": "Q1", "famille": "regles_concurrentes", "numeros_regle_attendus": [58, 79, 152]}

    result = evaluate_case(case, numeros_retournes=[58, 152])

    assert result["verdict"] == "PARTIEL"


def test_evaluate_case_fail_aucune_cible_multiple_trouvee():
    """Un cas à cibles multiples échoue (FAIL) si aucune cible n'est retrouvée."""
    case = {"question": "Q1", "famille": "regles_concurrentes", "numeros_regle_attendus": [58, 79]}

    result = evaluate_case(case, numeros_retournes=[1, 2, 3])

    assert result["verdict"] == "FAIL"


def test_evaluate_case_fail_sans_reponse_attendue():
    """Un cas sans_reponse (numeros_regle_attendus vide) est toujours FAIL."""
    case = {"question": "Q1", "famille": "sans_reponse", "numeros_regle_attendus": []}

    result = evaluate_case(case, numeros_retournes=[1, 2, 3])

    assert result["verdict"] == "FAIL"
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -k evaluate_case -v`
Expected: FAIL (`KeyError: 'famille'` ou `KeyError: 'verdict'` selon
l'ancienne implémentation encore en place)

- [ ] **Step 3: Implémenter `evaluate_case`**

Remplacer la fonction existante (`app/ingestion/rag_acceptance.py:35-42`)
par :

```python
def evaluate_case(case: dict, numeros_retournes: list[int]) -> dict:
    """Évalue un cas : verdict PASS/FAIL/PARTIEL selon les cibles retrouvées.

    Un cas sans cible attendue (numeros_regle_attendus vide, famille
    sans_reponse) est toujours FAIL : aucun mécanisme de refus n'existe
    aujourd'hui dans le pipeline de retrieval.
    """
    attendus = case["numeros_regle_attendus"]
    trouves = [n for n in attendus if n in numeros_retournes]

    if not attendus:
        verdict = "FAIL"
    elif len(trouves) == len(attendus):
        verdict = "PASS"
    elif len(trouves) == 0:
        verdict = "FAIL"
    else:
        verdict = "PARTIEL"

    return {
        "question": case["question"],
        "famille": case["famille"],
        "numeros_regle_attendus": attendus,
        "numeros_retournes": numeros_retournes,
        "verdict": verdict,
    }
```

- [ ] **Step 4: Lancer les tests, vérifier qu'ils passent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -k evaluate_case -v`
Expected: 6 PASS

- [ ] **Step 5: Commit**

```bash
git add app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py
git commit -m "feat: evaluate_case supporte cibles multiples et verdict PARTIEL"
```

---

### Task 2: `compute_taux_par_famille` — remplace `compute_taux_reussite`

**Files:**
- Modify: `app/ingestion/rag_acceptance.py:45-47` (fonction
  `compute_taux_reussite` → `compute_taux_par_famille`)
- Test: `tests/unit/ingestion/test_rag_acceptance.py:58-67` (remplace
  `test_compute_taux_reussite_ratio`)

**Interfaces:**
- Consumes: `evaluation["famille"]`, `evaluation["verdict"]` (produits par
  Task 1)
- Produces: `compute_taux_par_famille(evaluations: list[dict]) ->
  dict[str, dict]`. Chaque valeur a les clés `taux: float`,
  `reussis: int`, `total: int`, `partiels: int`. Consommé par Task 3
  (`is_acceptable` lit `stats["taux"]` par famille) et Task 5 (le script
  logge `stats["reussis"]/stats["total"]`, `stats["taux"]`,
  `stats["partiels"]`).

- [ ] **Step 1: Écrire les tests qui échouent**

Remplacer `test_compute_taux_reussite_ratio` (lignes 58-67) par :

```python
def test_compute_taux_par_famille_un_seul_groupe():
    """Le taux d'une famille est le ratio PASS / (total - PARTIEL)."""
    evaluations = [
        {"famille": "vocabulaire_source_opquast", "verdict": "PASS"},
        {"famille": "vocabulaire_source_opquast", "verdict": "PASS"},
        {"famille": "vocabulaire_source_opquast", "verdict": "FAIL"},
    ]

    resultat = compute_taux_par_famille(evaluations)

    assert resultat["vocabulaire_source_opquast"] == {
        "taux": 2 / 3,
        "reussis": 2,
        "total": 3,
        "partiels": 0,
    }


def test_compute_taux_par_famille_exclut_les_partiels():
    """Les cas PARTIEL sont retirés du dénominateur, comptés à part."""
    evaluations = [
        {"famille": "regles_concurrentes", "verdict": "PASS"},
        {"famille": "regles_concurrentes", "verdict": "PARTIEL"},
        {"famille": "regles_concurrentes", "verdict": "FAIL"},
    ]

    resultat = compute_taux_par_famille(evaluations)

    assert resultat["regles_concurrentes"] == {
        "taux": 1 / 2,
        "reussis": 1,
        "total": 2,
        "partiels": 1,
    }


def test_compute_taux_par_famille_groupes_independants():
    """Chaque famille a son propre taux, indépendant des autres."""
    evaluations = [
        {"famille": "vocabulaire_source_opquast", "verdict": "PASS"},
        {"famille": "sans_reponse", "verdict": "FAIL"},
        {"famille": "sans_reponse", "verdict": "FAIL"},
    ]

    resultat = compute_taux_par_famille(evaluations)

    assert resultat["vocabulaire_source_opquast"]["taux"] == 1.0
    assert resultat["sans_reponse"]["taux"] == 0.0


def test_compute_taux_par_famille_uniquement_partiels_donne_zero():
    """Une famille entièrement composée de PARTIEL a un taux de 0.0 (pas de division par zéro)."""
    evaluations = [
        {"famille": "regles_concurrentes", "verdict": "PARTIEL"},
    ]

    resultat = compute_taux_par_famille(evaluations)

    assert resultat["regles_concurrentes"] == {
        "taux": 0.0,
        "reussis": 0,
        "total": 0,
        "partiels": 1,
    }
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -k compute_taux -v`
Expected: FAIL (`ImportError`/`NameError: compute_taux_par_famille` non
défini)

- [ ] **Step 3: Implémenter `compute_taux_par_famille`**

Remplacer `compute_taux_reussite` (`app/ingestion/rag_acceptance.py:45-47`)
par :

```python
def compute_taux_par_famille(evaluations: list[dict]) -> dict[str, dict]:
    """Calcule le taux de réussite par famille, en excluant les PARTIEL.

    Un cas PARTIEL ne compte ni comme succès ni comme échec : il est
    retiré du dénominateur pour ne pas fausser le taux binaire, mais son
    nombre est conservé (partiels) pour rester visible dans les logs.
    Une famille sans aucun cas PASS/FAIL (uniquement des PARTIEL) a un
    taux de 0.0 par convention — pas de division par zéro.
    """
    par_famille: dict[str, list[dict]] = {}
    for evaluation in evaluations:
        par_famille.setdefault(evaluation["famille"], []).append(evaluation)

    resultat = {}
    for famille, evals in par_famille.items():
        partiels = sum(1 for e in evals if e["verdict"] == "PARTIEL")
        non_partiels = [e for e in evals if e["verdict"] != "PARTIEL"]
        reussis = sum(1 for e in non_partiels if e["verdict"] == "PASS")
        total = len(non_partiels)
        taux = reussis / total if total > 0 else 0.0
        resultat[famille] = {"taux": taux, "reussis": reussis, "total": total, "partiels": partiels}
    return resultat
```

- [ ] **Step 4: Lancer les tests, vérifier qu'ils passent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -k compute_taux -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py
git commit -m "feat: compute_taux_par_famille remplace compute_taux_reussite"
```

---

### Task 3: `is_acceptable` — dict par famille, ignore `sans_reponse`

**Files:**
- Modify: `app/ingestion/rag_acceptance.py:50-52` (fonction `is_acceptable`)
- Test: `tests/unit/ingestion/test_rag_acceptance.py:70-77` (remplace les 2
  tests existants)

**Interfaces:**
- Consumes: `dict[str, dict]` produit par `compute_taux_par_famille` (Task
  2) — lit `stats["taux"]` pour chaque famille
- Produces: `is_acceptable(taux_par_famille: dict[str, dict], seuil: float)
  -> bool`. Consommé par Task 5 (le script appelle
  `is_acceptable(taux_par_famille, seuil)` pour décider du code de sortie).

- [ ] **Step 1: Écrire les tests qui échouent**

Remplacer `test_is_acceptable_true_when_taux_above_seuil` et
`test_is_acceptable_false_when_taux_below_seuil` (lignes 70-77) par :

```python
def test_is_acceptable_true_when_all_familles_above_seuil():
    """Le jeu est acceptable si toutes les familles atteignent le seuil."""
    taux_par_famille = {
        "vocabulaire_source_opquast": {"taux": 0.8, "reussis": 4, "total": 5, "partiels": 0},
        "regles_concurrentes": {"taux": 1.0, "reussis": 3, "total": 3, "partiels": 0},
    }

    assert is_acceptable(taux_par_famille, seuil=0.8) is True


def test_is_acceptable_false_when_one_famille_below_seuil():
    """Le jeu échoue si au moins une famille est sous le seuil."""
    taux_par_famille = {
        "vocabulaire_source_opquast": {"taux": 0.5, "reussis": 2, "total": 4, "partiels": 0},
        "regles_concurrentes": {"taux": 1.0, "reussis": 3, "total": 3, "partiels": 0},
    }

    assert is_acceptable(taux_par_famille, seuil=0.8) is False


def test_is_acceptable_ignores_sans_reponse_famille():
    """La famille sans_reponse n'entre jamais dans le calcul, même à 0%."""
    taux_par_famille = {
        "vocabulaire_source_opquast": {"taux": 1.0, "reussis": 4, "total": 4, "partiels": 0},
        "sans_reponse": {"taux": 0.0, "reussis": 0, "total": 2, "partiels": 0},
    }

    assert is_acceptable(taux_par_famille, seuil=0.8) is True
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -k is_acceptable -v`
Expected: FAIL (`TypeError` — l'ancienne signature attend `taux: float`,
pas un dict)

- [ ] **Step 3: Implémenter `is_acceptable`**

Remplacer la fonction existante (`app/ingestion/rag_acceptance.py:50-52`)
par :

```python
def is_acceptable(taux_par_famille: dict[str, dict], seuil: float) -> bool:
    """Le jeu est acceptable si chaque famille à cible normale atteint le seuil.

    La famille "sans_reponse" est toujours ignorée : son taux est nul par
    construction (aucun mécanisme de refus), ce n'est pas un défaut du
    retrieval mesuré par les autres familles.
    """
    for famille, stats in taux_par_famille.items():
        if famille == "sans_reponse":
            continue
        if stats["taux"] < seuil:
            return False
    return True
```

- [ ] **Step 4: Lancer les tests, vérifier qu'ils passent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -k is_acceptable -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py
git commit -m "feat: is_acceptable ignore la famille sans_reponse"
```

---

### Task 4: Migrer `tests/acceptance/rag_acceptance.jsonl` vers le nouveau format

**Files:**
- Modify: `tests/acceptance/rag_acceptance.jsonl` (reshape des 17 lignes,
  aucun contenu de question/cible ne change)

**Interfaces:**
- Consumes: rien (fichier de données brut)
- Produces: fichier JSONL où chaque ligne a les clés `question: str`,
  `famille: str` (toujours `"paraphrase_intitule"` pour ces 17 lignes),
  `numeros_regle_attendus: list[int]` (liste à un élément). Consommé par
  `load_cases()` (inchangée, générique) et donc par `scripts/check_rag_acceptance.py`
  (Task 5).

- [ ] **Step 1: Réécrire le fichier**

Remplacer tout le contenu de `tests/acceptance/rag_acceptance.jsonl` par
(reshape mécanique — questions et cibles identiques à l'existant, ordre
préservé) :

```json
{"question": "Peut-on souligner les titres ?", "famille": "paraphrase_intitule", "numeros_regle_attendus": [139]}
{"question": "Il faut mettre en rouge les infos de danger", "famille": "paraphrase_intitule", "numeros_regle_attendus": [181]}
{"question": "Le site doit-il être accessible uniquement en connexion sécurisée ?", "famille": "paraphrase_intitule", "numeros_regle_attendus": [197]}
{"question": "Faut-il décrire les images importantes pour les personnes qui ne peuvent pas les voir ?", "famille": "paraphrase_intitule", "numeros_regle_attendus": [118]}
{"question": "Où doit-on pouvoir trouver la politique de vie privée du site ?", "famille": "paraphrase_intitule", "numeros_regle_attendus": [15]}
{"question": "Un site marchand doit-il proposer plusieurs façons de payer ?", "famille": "paraphrase_intitule", "numeros_regle_attendus": [58]}
{"question": "Si un formulaire est refusé, faut-il montrer précisément quels champs posent problème ?", "famille": "paraphrase_intitule", "numeros_regle_attendus": [79]}
{"question": "Le site doit-il éviter les liens cassés en interne ?", "famille": "paraphrase_intitule", "numeros_regle_attendus": [152]}
{"question": "Les vidéos doivent-elles avoir des sous-titres ?", "famille": "paraphrase_intitule", "numeros_regle_attendus": [122]}
{"question": "Le site peut-il ouvrir des fenêtres popup pendant la navigation ?", "famille": "paraphrase_intitule", "numeros_regle_attendus": [154]}
{"question": "Le site doit-il avoir un moteur de recherche interne ?", "famille": "paraphrase_intitule", "numeros_regle_attendus": [168]}
{"question": "Sur mobile, les boutons doivent-ils être assez grands pour être touchés facilement ?", "famille": "paraphrase_intitule", "numeros_regle_attendus": [186]}
{"question": "Peut-on empêcher l'utilisateur de zoomer sur la page ?", "famille": "paraphrase_intitule", "numeros_regle_attendus": [193]}
{"question": "Faut-il fournir un plan du site pour les moteurs de recherche ?", "famille": "paraphrase_intitule", "numeros_regle_attendus": [220]}
{"question": "Le formulaire d'inscription doit-il accepter les adresses email avec un signe plus (+) dedans ?", "famille": "paraphrase_intitule", "numeros_regle_attendus": [24]}
{"question": "Les messages d'erreur doivent-ils être dans la même langue que le formulaire ?", "famille": "paraphrase_intitule", "numeros_regle_attendus": [82]}
{"question": "Le numéro SIRET (ou équivalent d'immatriculation légale) doit-il être affiché sur le site ?", "famille": "paraphrase_intitule", "numeros_regle_attendus": [106]}
```

- [ ] **Step 2: Vérifier la structure du fichier migré**

Run:
```bash
uv run python -c "
from pathlib import Path
from app.ingestion.rag_acceptance import load_cases
cases = load_cases(Path('tests/acceptance/rag_acceptance.jsonl'))
assert len(cases) == 17, f'attendu 17 cas, trouvé {len(cases)}'
for c in cases:
    assert set(c.keys()) == {'question', 'famille', 'numeros_regle_attendus'}, c
    assert c['famille'] == 'paraphrase_intitule'
    assert isinstance(c['numeros_regle_attendus'], list) and len(c['numeros_regle_attendus']) == 1
print('OK : 17 cas, structure conforme')
"
```
Expected: `OK : 17 cas, structure conforme`

- [ ] **Step 3: Commit**

```bash
git add tests/acceptance/rag_acceptance.jsonl
git commit -m "refactor: migre rag_acceptance.jsonl vers le format multi-cibles/famille"
```

---

### Task 5: Adapter `scripts/check_rag_acceptance.py` au nouveau reporting

**Files:**
- Modify: `scripts/check_rag_acceptance.py` (réécriture complète du fichier)

**Interfaces:**
- Consumes: `evaluate_case`, `compute_taux_par_famille`, `is_acceptable`
  (Tasks 1-3), `load_cases` (inchangée)
- Produces: comportement CLI inchangé côté appelant (`make rag-acceptance`,
  code de sortie 0/1) — seul le contenu des logs change.

- [ ] **Step 1: Réécrire le fichier**

Remplacer tout le contenu de `scripts/check_rag_acceptance.py` par :

```python
"""Point d'entrée pour rejouer le jeu d'acceptance RAG (retrieval sémantique).

Recalcule l'embedding réel de chaque question du jeu de cas
(tests/acceptance/rag_acceptance.jsonl), interroge pgvector (similarité
cosinus) et vérifie, par famille de cas, que les règles attendues figurent
dans le top_n déclaré dans app/ingestion/manifest.yml (section
rag_acceptance). Coût réel à chaque exécution (appel Azure embeddings),
volontairement hors CI — lancé à la demande via `make rag-acceptance`.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.embedding import EmbeddingClient  # noqa: E402
from app.ingestion.llm_client import load_manifest  # noqa: E402
from app.ingestion.rag_acceptance import (  # noqa: E402
    compute_taux_par_famille,
    evaluate_case,
    format_dataset_versions,
    is_acceptable,
    load_cases,
    query_top_n_numeros,
    summarize_dataset_versions,
)
from app.logging_config import setup_logging  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

CASES_PATH = Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance.jsonl"

FAMILLE_HORS_SEUIL = "sans_reponse"


def get_engine():
    """Construit l'engine SQLAlchemy depuis les variables .env."""
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url)


def main() -> None:
    setup_logging()
    load_dotenv()

    engine = get_engine()
    config = load_manifest()["rag_acceptance"]
    top_n = config["top_n"]
    seuil = config["taux_reussite_minimum"]

    logger.info("=== check_rag_acceptance : démarrage ===")
    progress_logger.info("=== check_rag_acceptance : démarrage ===")

    try:
        cases = load_cases(CASES_PATH)
        client = EmbeddingClient()
        vectors = client.embed_batch([case["question"] for case in cases])

        evaluations = []
        with Session(engine) as session:
            dataset_summary = format_dataset_versions(summarize_dataset_versions(session))
            progress_logger.info(f"check_rag_acceptance — Jeu de données : {dataset_summary}")

            for case, vector in zip(cases, vectors, strict=True):
                numeros_retournes = query_top_n_numeros(session, vector, top_n)
                evaluation = evaluate_case(case, numeros_retournes)
                evaluations.append(evaluation)
                progress_logger.info(
                    f"check_rag_acceptance — « {case['question']} » "
                    f"[{case['famille']}] (attendu {evaluation['numeros_regle_attendus']}, "
                    f"retourné {numeros_retournes}) — {evaluation['verdict']}"
                )

        taux_par_famille = compute_taux_par_famille(evaluations)
        for famille, stats in taux_par_famille.items():
            note = (
                " (hors seuil : pas de mécanisme de refus)"
                if famille == FAMILLE_HORS_SEUIL
                else ""
            )
            partiel_note = f", {stats['partiels']} PARTIEL" if stats["partiels"] else ""
            progress_logger.info(
                f"check_rag_acceptance — Famille {famille} : "
                f"{stats['reussis']}/{stats['total']} ({stats['taux']:.0%}){partiel_note}{note}"
            )

        role = load_manifest()["embedding"]
        cost = client.total_tokens * role["prix_entree_par_million"] / 1_000_000
        summary = (
            f"check_rag_acceptance — seuil {seuil:.0%}, tokens : {client.total_tokens}, "
            f"coût estimé : {cost:.4f} €"
        )
        logger.info(summary)
        progress_logger.info(summary)

    except Exception as e:
        logger.error("check_rag_acceptance : ÉCHEC (%s)", e)
        sys.exit(1)

    if not is_acceptable(taux_par_famille, seuil):
        logger.error("check_rag_acceptance : au moins une famille sous le seuil minimum")
        sys.exit(1)

    logger.info("=== check_rag_acceptance : succès ===")
    progress_logger.info("=== check_rag_acceptance : succès ===")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Vérifier la cohérence statique (pas d'appel réseau)**

Run: `uv run python -c "import ast; ast.parse(open('scripts/check_rag_acceptance.py').read())"`
Expected: aucune sortie (parse réussi, pas d'erreur de syntaxe)

Run: `uv run ruff check scripts/check_rag_acceptance.py app/ingestion/rag_acceptance.py`
Expected: `All checks passed!`

- [ ] **Step 3: Commit**

```bash
git add scripts/check_rag_acceptance.py
git commit -m "feat: check_rag_acceptance reporte le taux par famille"
```

---

### Task 6: Vérification finale de la suite

**Files:** aucun (validation transverse)

**Interfaces:** aucune — tâche de vérification pure.

- [ ] **Step 1: Lancer toute la suite de tests unitaires**

Run: `uv run pytest tests/unit/ -v`
Expected: tous les tests passent, y compris les 13 tests de
`tests/unit/ingestion/test_rag_acceptance.py` (6 `evaluate_case` + 4
`compute_taux_par_famille` + 3 `is_acceptable`), plus
`test_load_cases_parses_jsonl`, `test_format_dataset_versions_*` inchangés.

- [ ] **Step 2: Lancer `ruff` sur tout le dépôt**

Run: `uv run ruff check .`
Expected: `All checks passed!`

- [ ] **Step 3: Consigner dans `CHANGELOG.md`**

Ajouter une entrée en tête de fichier (format horodaté, plus récent en
premier — voir les entrées existantes) décrivant : migration du format
JSONL (`numero_regle_attendue` → `numeros_regle_attendus` + `famille`),
verdict à 3 états, taux par famille, migration des 17 cas historiques vers
`famille: paraphrase_intitule`, référence à la spec et à ce plan.

- [ ] **Step 4: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: trace la migration du jeu d'acceptance RAG vers les familles"
```

---

## Self-Review (fait avant remise du plan)

**Couverture de la spec** — chaque section a une tâche :
- Format JSONL étendu → Task 4
- `evaluate_case` 3 états → Task 1
- `compute_taux_par_famille` (exclusion PARTIEL) → Task 2
- `is_acceptable` ignore `sans_reponse` → Task 3
- `scripts/check_rag_acceptance.py` reporting par famille → Task 5
- Migration des 17 cas → Task 4
- `manifest.yml` : aucun changement de valeur requis par la spec — rien à
  faire, confirmé, pas une tâche manquante.
- Rédaction des nouveaux cas durs (5 familles) : explicitement hors
  périmètre de cette spec — pas de tâche ici, comme prévu.

**Cohérence des types/signatures** — vérifié : `evaluate_case` (Task 1)
produit `famille`/`verdict`, consommés tels quels par
`compute_taux_par_famille` (Task 2) ; celle-ci produit
`{taux, reussis, total, partiels}` par famille, consommé tel quel par
`is_acceptable` (Task 3) et par le script (Task 5). Aucune divergence de
nom trouvée.

**Placeholders** — aucun trouvé ; chaque step contient le code réel à
écrire.
