# Script rag_dense_acceptance.py Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Un nouveau script qui compare le recall du jeu d'acceptance RAG
sur plusieurs `top_n` (3/5/10/15) en une seule exécution, et écrit un
rapport Markdown horodaté dans `docs/eval/`.

**Architecture:** Une seule requête pgvector par question à `LIMIT 15`
(le max de `TOP_NS`), puis troncature locale de la liste retournée pour
chaque `top_n` de `TOP_NS`. Réutilise telles quelles `load_cases`,
`evaluate_case`, `query_top_n_numeros`, `compute_taux_par_famille` de
`app/ingestion/rag_acceptance.py` — aucune modification de ce module ni de
`scripts/check_rag_acceptance.py`.

**Tech Stack:** Python 3, SQLAlchemy/pgvector, `EmbeddingClient` — mêmes
dépendances que `check_rag_acceptance.py`, aucune nouvelle.

## Global Constraints

- Aucune modification de `app/ingestion/rag_acceptance.py`,
  `scripts/check_rag_acceptance.py`, ni `app/ingestion/manifest.yml` — le
  script est autonome, `TOP_NS = [3, 5, 10, 15]` est une constante locale.
- Suite manuelle, hors CI (coût réel API embeddings à chaque run,
  ~0€ sur 56 questions).
- `ruff` propre avant de considérer une tâche terminée.
- Toute réalisation tracée dans `CHANGELOG.md` une fois le plan exécuté.
- Spec de référence :
  `docs/superpowers/specs/2026-09-09-rag-dense-acceptance-design.md`.

---

### Task 1: Écrire `scripts/rag_dense_acceptance.py`

**Files:**
- Create: `scripts/rag_dense_acceptance.py`

**Interfaces:**
- Consumes : `load_cases(jsonl_path) -> list[dict]`,
  `query_top_n_numeros(session, vector, top_n) -> list[int]`,
  `evaluate_case(case, numeros_retournes) -> dict`,
  `compute_taux_par_famille(evaluations) -> dict[str, dict]` (toutes de
  `app/ingestion/rag_acceptance.py`, inchangées) ; `EmbeddingClient` et
  `load_manifest` (de `app/ingestion/embedding.py` et
  `app/ingestion/llm_client.py`, inchangés).
- Produces : script exécutable en CLI (`python
  scripts/rag_dense_acceptance.py`), écrit un fichier dans `docs/eval/`.
  Consommé par Task 2 (cible Makefile) et Task 3 (exécution réelle).

- [ ] **Step 1: Écrire le fichier complet**

```python
"""Compare le recall du RAG sur plusieurs top_n (3/5/10/15) en une exécution.

Rejoue tests/acceptance/rag_acceptance.jsonl une seule fois (un seul appel
API embeddings, une seule requête pgvector par question à LIMIT 15), puis
tronque localement pour chaque top_n de TOP_NS. Produit un rapport Markdown
horodaté dans docs/eval/. Exploration ponctuelle, distincte de l'instrument
de mesure officiel de l'Étape 3 (scripts/check_rag_acceptance.py, inchangé)
— voir docs/superpowers/specs/2026-09-09-rag-dense-acceptance-design.md.
"""

import logging
import os
import sys
from datetime import date
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
    load_cases,
    query_top_n_numeros,
)
from app.logging_config import setup_logging  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

CASES_PATH = Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance.jsonl"
REPORT_DIR = Path(__file__).resolve().parents[1] / "docs" / "eval"

TOP_NS = [3, 5, 10, 15]


def get_engine():
    """Construit l'engine SQLAlchemy depuis les variables .env."""
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url)


def build_report(taux_par_top_n: dict[int, dict], evaluations_top15: list[dict]) -> str:
    """Construit le rapport Markdown : tableau agrégé + cas PARTIEL/FAIL à top_n=15."""
    familles = list(taux_par_top_n[TOP_NS[0]].keys())

    entete = "| Famille | " + " | ".join(f"top_n={n}" for n in TOP_NS) + " |"
    separateur = "|---|" + "|".join("---" for _ in TOP_NS) + "|"
    lignes = [entete, separateur]
    for famille in familles:
        valeurs = [f"{taux_par_top_n[n][famille]['taux']:.0%}" for n in TOP_NS]
        lignes.append(f"| {famille} | " + " | ".join(valeurs) + " |")
    tableau = "\n".join(lignes)

    echecs = [e for e in evaluations_top15 if e["verdict"] in ("FAIL", "PARTIEL")]
    lignes_echecs = [
        f"- **{e['verdict']}** [{e['famille']}] « {e['question']} » — "
        f"attendu {e['numeros_regle_attendus']}, retourné {e['numeros_retournes']}"
        for e in echecs
    ]
    section_echecs = "\n".join(lignes_echecs) if lignes_echecs else "Aucun."

    return (
        f"# Mesure recall — rag_dense_acceptance ({date.today().isoformat()})\n\n"
        f"## Taux de réussite par famille × top_n\n\n{tableau}\n\n"
        f"## Cas PARTIEL/FAIL persistants à top_n=15\n\n{section_echecs}\n"
    )


def main() -> None:
    setup_logging()
    load_dotenv()

    engine = get_engine()
    top_n_max = max(TOP_NS)

    logger.info("=== rag_dense_acceptance : démarrage ===")
    progress_logger.info("=== rag_dense_acceptance : démarrage ===")

    cases = load_cases(CASES_PATH)
    client = EmbeddingClient()
    vectors = client.embed_batch([case["question"] for case in cases])

    resultats_par_top_n: dict[int, list[dict]] = {n: [] for n in TOP_NS}
    with Session(engine) as session:
        for case, vector in zip(cases, vectors, strict=True):
            numeros_retournes_max = query_top_n_numeros(session, vector, top_n_max)
            for n in TOP_NS:
                evaluation = evaluate_case(case, numeros_retournes_max[:n])
                resultats_par_top_n[n].append(evaluation)
                progress_logger.info(
                    f"rag_dense_acceptance — « {case['question']} » "
                    f"[{case['famille']}] top_n={n} — {evaluation['verdict']}"
                )

    taux_par_top_n = {n: compute_taux_par_famille(resultats_par_top_n[n]) for n in TOP_NS}

    role = load_manifest()["embedding"]
    cost = client.total_tokens * role["prix_entree_par_million"] / 1_000_000
    progress_logger.info(
        f"rag_dense_acceptance — tokens : {client.total_tokens}, coût estimé : {cost:.4f} €"
    )

    rapport = build_report(taux_par_top_n, resultats_par_top_n[top_n_max])
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"rag_dense_acceptance_{date.today().isoformat()}.md"
    report_path.write_text(rapport, encoding="utf-8")

    logger.info(f"=== rag_dense_acceptance : rapport écrit dans {report_path} ===")
    progress_logger.info(f"=== rag_dense_acceptance : rapport écrit dans {report_path} ===")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Vérifier la syntaxe (pas d'appel réseau)**

Run: `uv run python -c "import ast; ast.parse(open('scripts/rag_dense_acceptance.py').read())"`
Expected: aucune sortie (parse réussi)

- [ ] **Step 3: Lancer ruff**

Run: `uv run ruff check scripts/rag_dense_acceptance.py`
Expected: `All checks passed!`

- [ ] **Step 4: Commit**

```bash
git add scripts/rag_dense_acceptance.py
git commit -m "feat: ajoute rag_dense_acceptance.py (compare top_n 3/5/10/15)"
```

---

### Task 2: Ajouter la cible Makefile

**Files:**
- Modify: `Makefile` (section « Ingestion et données réelles », à côté de
  la cible `rag-acceptance`)

**Interfaces:**
- Consumes: `scripts/rag_dense_acceptance.py` (Task 1)
- Produces: cible `make rag-dense-acceptance`, consommée par Task 3.

- [ ] **Step 1: Ajouter la cible**

À la suite de la cible `rag-acceptance` existante (`Makefile:112-113`),
ajouter :

```makefile
## Compare le recall du RAG sur plusieurs top_n (3/5/10/15), rapport Markdown
rag-dense-acceptance:
	uv run python scripts/rag_dense_acceptance.py
```

- [ ] **Step 2: Vérifier la cible sans l'exécuter**

Run: `make -n rag-dense-acceptance`
Expected: affiche `uv run python scripts/rag_dense_acceptance.py` sans
l'exécuter (`-n` = dry-run de `make`)

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "feat: ajoute la cible make rag-dense-acceptance"
```

---

### Task 3: Exécution réelle, vérification du rapport, commit

**Files:**
- Create (généré par le script, pas écrit à la main) :
  `docs/eval/rag_dense_acceptance_<date du jour>.md`

**Interfaces:** aucune — tâche d'exécution et de vérification.

- [ ] **Step 1: Lancer le script réel (coût réel, action manuelle)**

Run: `make rag-dense-acceptance`
Expected: le script se termine sans erreur, logge le coût (tokens/€), et
affiche le chemin du rapport écrit dans `docs/eval/`.

- [ ] **Step 2: Relire le rapport généré**

Ouvrir `docs/eval/rag_dense_acceptance_<date>.md` et vérifier :
- le tableau contient les 6 familles (`paraphrase_intitule`,
  `vocabulaire_source_opquast`, `vocabulaire_genere_llm`, `multi_sujets`,
  `sans_reponse`, `regles_concurrentes`) × les 4 colonnes `top_n`
- la section des cas persistants à `top_n=15` n'est pas vide (au moins les
  3 cas déjà identifiés manuellement : règle 185, et les 2 cas
  `multi_sujets` sur les règles 106/107)

- [ ] **Step 3: Commit du rapport**

```bash
git add docs/eval/
git commit -m "docs: rapport rag_dense_acceptance (comparaison top_n 3/5/10/15)"
```

---

## Self-Review (fait avant remise du plan)

**Couverture de la spec** :
- Script autonome, aucune modification des modules existants → Task 1
- Cible Makefile → Task 2
- Rapport Markdown horodaté dans `docs/eval/` → Task 1 (génération) +
  Task 3 (exécution réelle + vérification)
- Pas de test unitaire dédié : décision explicite de la spec (§ Tests /
  Validation) — toute la logique réutilisée est déjà testée dans
  `tests/unit/ingestion/test_rag_acceptance.py`, confirmé, pas une tâche
  manquante.

**Cohérence des types/signatures** — vérifié : `build_report` reçoit
`taux_par_top_n: dict[int, dict]` (sortie de `compute_taux_par_famille`
par `top_n`) et `evaluations_top15: list[dict]` (sorties de
`evaluate_case`, mêmes clés que celles produites par le module existant :
`question`, `famille`, `numeros_regle_attendus`, `numeros_retournes`,
`verdict`). Aucune divergence de nom avec `app/ingestion/rag_acceptance.py`.

**Placeholders** — aucun trouvé ; le code de Task 1 est complet et
exécutable tel quel.
