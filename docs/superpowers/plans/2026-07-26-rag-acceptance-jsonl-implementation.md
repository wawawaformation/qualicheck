# Jeu d'acceptance RAG (JSONL) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Formaliser en un jeu de test d'acceptance rejouable les vérifications manuelles de recherche sémantique RAG faites le 2026-07-26 (question en langage naturel → règle Opquast attendue via pgvector/cosinus).

**Architecture:** Un fichier JSONL de cas `{question, numero_regle_attendue}`, un module `app/ingestion/rag_acceptance.py` (logique pure + requête pgvector), un script CLI `scripts/check_rag_acceptance.py` (appel réel API embeddings + vérification), une cible Makefile dédiée. Suite volontairement hors CI, lancée à la demande.

**Tech Stack:** Python, SQLAlchemy + `pgvector.sqlalchemy` (`cosine_distance`), `EmbeddingClient` existant (`app/ingestion/embedding.py`), pytest.

## Global Constraints

- Spec de référence : `docs/superpowers/specs/2026-07-26-rag-acceptance-jsonl-design.md`
- `top_n` et `taux_reussite_minimum` sont déclarés dans `app/ingestion/manifest.yml` (section `rag_acceptance`), jamais codés en dur dans le script
- Chaque exécution du script coûte un appel réel à l'API Azure embeddings — assumé, pas de cache/enregistrement des embeddings de test
- Suite volontairement hors CI (pas de job automatique sur push/PR)
- Pas de fail-fast par cas : un cas en échec n'interrompt pas les suivants ; seule une erreur technique (API/BDD) interrompt tout le run
- Aucun `pytest-bdd`/fichier `.feature` réel — les scénarios Gherkin de la spec restent de la documentation
- Retry 3 tentatives/backoff déjà géré par `EmbeddingClient.embed_batch` (réutilisé tel quel, pas de nouvelle logique de retry)

---

## File Structure

- `tests/acceptance/rag_acceptance.jsonl` (nouveau) — jeu de cas, une ligne JSON par cas
- `app/ingestion/rag_acceptance.py` (nouveau) — logique testable : chargement des cas, requête pgvector, évaluation d'un cas, calcul du taux de réussite, comparaison au seuil
- `tests/unit/ingestion/test_rag_acceptance.py` (nouveau) — tests unitaires de la logique pure ci-dessus (mock non nécessaire, aucune I/O réseau/BDD dans ces tests)
- `scripts/check_rag_acceptance.py` (nouveau) — point d'entrée CLI, sur le modèle de `scripts/embed_rules.py`
- `app/ingestion/manifest.yml` (modifié) — nouvelle section `rag_acceptance`
- `Makefile` (modifié) — nouvelle cible `rag-acceptance`
- `CHANGELOG.md` (modifié) — entrée du chantier

---

### Task 1: Constitution du jeu de cas JSONL

**Files:**
- Create: `tests/acceptance/rag_acceptance.jsonl`

**Interfaces:**
- Produces: fichier JSONL lu par `load_cases()` (Task 2) — une ligne = `{"question": str, "numero_regle_attendue": int}`

- [ ] **Step 1: Relever un échantillon de règles couvrant des thématiques variées**

Run (nécessite `qualicheck-postgres` démarré) :

```bash
docker exec -it qualicheck-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "SELECT r.numero, r.intitule, string_agg(DISTINCT t.tag, ', ') AS tags
      FROM regle r
      LEFT JOIN regle_tag rt ON rt.regle_id = r.id
      LEFT JOIN tag t ON t.id = rt.tag_id
      GROUP BY r.numero, r.intitule
      ORDER BY r.numero;"
```

Expected: 245 lignes (numero, intitulé, tags) — sert à choisir des règles de thématiques différentes (accessibilité, formulaires, sécurité, mentions légales, images, liens, etc.), en évitant les règles 139 et 181 déjà prises.

- [ ] **Step 2: Rédiger ~13-18 candidats {question, numero_regle_attendue}**

Pour chaque règle retenue, formuler une question en langage naturel qui
**paraphrase** l'intitulé/la solution de la règle sans en reprendre le
vocabulaire exact (le test doit vérifier une correspondance sémantique,
pas un simple recouvrement de mots-clés). Présenter la liste complète des
candidats (question + numéro de règle + intitulé de la règle pour
vérification) à David pour validation avant de continuer.

- [ ] **Step 3: Point de contrôle — validation de David**

Attendre la validation explicite de David sur la liste de candidats
(accepter tel quel / modifier une question / écarter un candidat). Ne pas
passer à l'étape suivante sans cette validation.

- [ ] **Step 4: Écrire le fichier JSONL**

Créer `tests/acceptance/rag_acceptance.jsonl` avec, sur les deux premières
lignes, les cas déjà vérifiés manuellement le 2026-07-26 :

```json
{"question": "Peut-on souligner les titres ?", "numero_regle_attendue": 139}
{"question": "Il faut mettre en rouge les infos de danger", "numero_regle_attendue": 181}
```

Puis une ligne par candidat validé à l'étape 3 (même format, un objet
JSON par ligne, pas de tableau englobant).

- [ ] **Step 5: Vérifier que le fichier est un JSONL valide**

Run:

```bash
uv run python -c "
import json
with open('tests/acceptance/rag_acceptance.jsonl', encoding='utf-8') as f:
    cases = [json.loads(line) for line in f if line.strip()]
assert all({'question', 'numero_regle_attendue'} <= c.keys() for c in cases)
print(f'{len(cases)} cas chargés')
"
```

Expected: `N cas chargés` (N entre 15 et 20), aucune exception.

- [ ] **Step 6: Commit**

```bash
git add tests/acceptance/rag_acceptance.jsonl
git commit -m "$(cat <<'EOF'
test: add RAG acceptance case set (JSONL)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Module `app/ingestion/rag_acceptance.py`

**Files:**
- Create: `app/ingestion/rag_acceptance.py`
- Test: `tests/unit/ingestion/test_rag_acceptance.py`

**Interfaces:**
- Consumes: `tests/acceptance/rag_acceptance.jsonl` (Task 1) ; `app.models.referentiel.Regle` (`numero: int`, `embedding: Vector(1536)`, déjà existant)
- Produces (utilisé par Task 3) :
  - `load_cases(jsonl_path: Path) -> list[dict]`
  - `query_top_n_numeros(session: Session, vector: list[float], top_n: int) -> list[int]`
  - `evaluate_case(case: dict, numeros_retournes: list[int]) -> dict` — retourne `{"question": str, "numero_regle_attendue": int, "numeros_retournes": list[int], "reussi": bool}`
  - `compute_taux_reussite(evaluations: list[dict]) -> float`
  - `is_acceptable(taux: float, seuil: float) -> bool`

- [ ] **Step 1: Écrire les tests unitaires (échouent à l'import)**

Créer `tests/unit/ingestion/test_rag_acceptance.py` :

```python
"""
Tests unitaires pour app/ingestion/rag_acceptance.py

Logique pure (load_cases, evaluate_case, compute_taux_reussite,
is_acceptable) — aucun appel réseau ni BDD réelle. query_top_n_numeros
n'est pas testée ici (nécessite une base réellement vectorisée), validée
par exécution réelle via `make rag-acceptance`.
"""

from app.ingestion.rag_acceptance import (
    compute_taux_reussite,
    evaluate_case,
    is_acceptable,
    load_cases,
)


def test_load_cases_parses_jsonl(tmp_path):
    """load_cases lit un fichier JSONL, une entrée par ligne."""
    jsonl_path = tmp_path / "cases.jsonl"
    jsonl_path.write_text(
        '{"question": "Q1", "numero_regle_attendue": 1}\n'
        '{"question": "Q2", "numero_regle_attendue": 2}\n',
        encoding="utf-8",
    )

    cases = load_cases(jsonl_path)

    assert cases == [
        {"question": "Q1", "numero_regle_attendue": 1},
        {"question": "Q2", "numero_regle_attendue": 2},
    ]


def test_evaluate_case_success_when_expected_in_results():
    """Un cas réussit si numero_regle_attendue figure dans les résultats."""
    case = {"question": "Q1", "numero_regle_attendue": 139}

    result = evaluate_case(case, numeros_retournes=[42, 139, 7])

    assert result["reussi"] is True
    assert result["numeros_retournes"] == [42, 139, 7]
    assert result["question"] == "Q1"
    assert result["numero_regle_attendue"] == 139


def test_evaluate_case_failure_when_expected_absent():
    """Un cas échoue si numero_regle_attendue est absent des résultats."""
    case = {"question": "Q1", "numero_regle_attendue": 139}

    result = evaluate_case(case, numeros_retournes=[42, 7, 8])

    assert result["reussi"] is False


def test_compute_taux_reussite_ratio():
    """Le taux de réussite est le ratio cas réussis / total."""
    evaluations = [
        {"reussi": True},
        {"reussi": True},
        {"reussi": False},
        {"reussi": True},
    ]

    assert compute_taux_reussite(evaluations) == 0.75


def test_is_acceptable_true_when_taux_above_seuil():
    """is_acceptable est vrai si le taux atteint ou dépasse le seuil."""
    assert is_acceptable(taux=0.8, seuil=0.8) is True


def test_is_acceptable_false_when_taux_below_seuil():
    """is_acceptable est faux si le taux est strictement sous le seuil."""
    assert is_acceptable(taux=0.7, seuil=0.8) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -v`
Expected: `ModuleNotFoundError: No module named 'app.ingestion.rag_acceptance'` (ou `ImportError`)

- [ ] **Step 3: Implémenter `app/ingestion/rag_acceptance.py`**

```python
"""
Jeu d'acceptance RAG : vérifie que la recherche sémantique pgvector
retrouve la bonne règle Opquast pour une question en langage naturel.

Formalise les vérifications manuelles du 2026-07-26 — voir
docs/superpowers/specs/2026-07-26-rag-acceptance-jsonl-design.md.
"""

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.referentiel import Regle


def load_cases(jsonl_path: Path) -> list[dict]:
    """Charge le jeu de cas d'acceptance RAG depuis un fichier JSONL."""
    with open(jsonl_path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def query_top_n_numeros(session: Session, vector: list[float], top_n: int) -> list[int]:
    """Retourne les numéros des top_n règles les plus proches du vecteur (similarité cosinus)."""
    resultats = (
        session.query(Regle.numero)
        .order_by(Regle.embedding.cosine_distance(vector))
        .limit(top_n)
        .all()
    )
    return [numero for (numero,) in resultats]


def evaluate_case(case: dict, numeros_retournes: list[int]) -> dict:
    """Évalue un cas : la règle attendue figure-t-elle dans les résultats retournés ?"""
    return {
        "question": case["question"],
        "numero_regle_attendue": case["numero_regle_attendue"],
        "numeros_retournes": numeros_retournes,
        "reussi": case["numero_regle_attendue"] in numeros_retournes,
    }


def compute_taux_reussite(evaluations: list[dict]) -> float:
    """Calcule la proportion de cas réussis parmi les évaluations."""
    return sum(1 for e in evaluations if e["reussi"]) / len(evaluations)


def is_acceptable(taux: float, seuil: float) -> bool:
    """Le taux de réussite global atteint-il le seuil minimum déclaré dans le manifest ?"""
    return taux >= seuil
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -v`
Expected: 6 passed

- [ ] **Step 5: Ruff**

Run: `uv run ruff check app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py
git commit -m "$(cat <<'EOF'
feat: add app/ingestion/rag_acceptance.py

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Script CLI, manifest et cible Makefile

**Files:**
- Create: `scripts/check_rag_acceptance.py`
- Modify: `app/ingestion/manifest.yml`
- Modify: `Makefile`

**Interfaces:**
- Consumes: `load_cases`, `query_top_n_numeros`, `evaluate_case`, `compute_taux_reussite`, `is_acceptable` (Task 2) ; `EmbeddingClient` (`app/ingestion/embedding.py`, déjà existant : `embed_batch(texts: list[str]) -> list[list[float]]`, `total_tokens: int`) ; `load_manifest()` (`app/ingestion/llm_client.py`, déjà existant)

- [ ] **Step 1: Ajouter la section `rag_acceptance` à `app/ingestion/manifest.yml`**

Ajouter à la fin du fichier :

```yaml

rag_acceptance:
  # Nombre de résultats pgvector considérés par cas (marge par rapport au
  # top 2 observé lors des vérifications manuelles du 2026-07-26)
  top_n: 3
  # Proportion minimale de cas réussis pour que la suite soit globalement
  # acceptable — le rappel imparfait du RAG est déjà assumé, voir
  # docs/jury/decisions/2026-07-25-rag-us2-petit-corpus.md
  taux_reussite_minimum: 0.8
```

- [ ] **Step 2: Écrire `scripts/check_rag_acceptance.py`**

```python
"""Point d'entrée pour rejouer le jeu d'acceptance RAG (retrieval sémantique).

Recalcule l'embedding réel de chaque question du jeu de cas
(tests/acceptance/rag_acceptance.jsonl), interroge pgvector (similarité
cosinus) et vérifie que la règle attendue figure dans le top_n déclaré
dans app/ingestion/manifest.yml (section rag_acceptance). Coût réel à
chaque exécution (appel Azure embeddings), volontairement hors CI —
lancé à la demande via `make rag-acceptance`.
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
    compute_taux_reussite,
    evaluate_case,
    is_acceptable,
    load_cases,
    query_top_n_numeros,
)
from app.logging_config import setup_logging  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

CASES_PATH = Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance.jsonl"


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
            for case, vector in zip(cases, vectors, strict=True):
                numeros_retournes = query_top_n_numeros(session, vector, top_n)
                evaluation = evaluate_case(case, numeros_retournes)
                evaluations.append(evaluation)
                statut = "OK" if evaluation["reussi"] else "ÉCHEC"
                progress_logger.info(
                    f"check_rag_acceptance — « {case['question']} » "
                    f"(règle {case['numero_regle_attendue']} attendue, "
                    f"retournées {numeros_retournes}) — {statut}"
                )

        taux = compute_taux_reussite(evaluations)
        role = load_manifest()["embedding"]
        cost = client.total_tokens * role["prix_entree_par_million"] / 1_000_000
        summary = (
            f"check_rag_acceptance — Taux de réussite : {taux:.0%} "
            f"(seuil {seuil:.0%}), tokens : {client.total_tokens}, "
            f"coût estimé : {cost:.4f} €"
        )
        logger.info(summary)
        progress_logger.info(summary)

    except Exception as e:
        logger.error("check_rag_acceptance : ÉCHEC (%s)", e)
        sys.exit(1)

    if not is_acceptable(taux, seuil):
        logger.error("check_rag_acceptance : taux de réussite sous le seuil minimum")
        sys.exit(1)

    logger.info("=== check_rag_acceptance : succès ===")
    progress_logger.info("=== check_rag_acceptance : succès ===")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Vérifier la syntaxe (sans exécuter)**

Run: `uv run ruff check scripts/check_rag_acceptance.py app/ingestion/manifest.yml`
Expected: `All checks passed!`

Run: `uv run python -m py_compile scripts/check_rag_acceptance.py`
Expected: aucune sortie, code de sortie 0

- [ ] **Step 4: Ajouter la cible Makefile**

Dans `Makefile`, section « Ingestion et données réelles », après `embed-rules` :

```makefile

## Rejoue le jeu d'acceptance RAG (tests/acceptance/rag_acceptance.jsonl) :
## appel réel à l'API embeddings, coût réel, volontairement hors CI
rag-acceptance:
	uv run python scripts/check_rag_acceptance.py
```

Mettre à jour la ligne `.PHONY` pour y ajouter `rag-acceptance`.

- [ ] **Step 5: Commit**

```bash
git add scripts/check_rag_acceptance.py app/ingestion/manifest.yml Makefile
git commit -m "$(cat <<'EOF'
feat: add scripts/check_rag_acceptance.py and make rag-acceptance

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Documentation et validation finale

**Files:**
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: rien (tâche de clôture)

- [ ] **Step 1: Lancer la suite complète de tests et ruff**

Run: `uv run pytest tests/ -v`
Expected: tous les tests passent (aucun `FAILED`)

Run: `uv run ruff check`
Expected: `All checks passed!`

- [ ] **Step 2: Ajouter une entrée `CHANGELOG.md`**

Ajouter une entrée datée (2026-07-26, Claude Code) décrivant : spec
(`docs/superpowers/specs/2026-07-26-rag-acceptance-jsonl-design.md`) et
plan (`docs/superpowers/plans/2026-07-26-rag-acceptance-jsonl-implementation.md`)
; le fichier `tests/acceptance/rag_acceptance.jsonl` (nombre de cas final) ;
`app/ingestion/rag_acceptance.py` (`load_cases`, `query_top_n_numeros`,
`evaluate_case`, `compute_taux_reussite`, `is_acceptable`) ; la section
`rag_acceptance` de `manifest.yml` (`top_n`, `taux_reussite_minimum`) ;
`scripts/check_rag_acceptance.py` et `make rag-acceptance` — préciser
explicitement si `make rag-acceptance` a été exécuté pour de vrai dans le
cadre de ce chantier ou si son premier lancement réel reste une décision
délibérée de David (même logique que `make embed-rules`).

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "$(cat <<'EOF'
docs: changelog entry for RAG acceptance JSONL suite

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Fin de plan

Après la Task 4, utiliser `superpowers:finishing-a-development-branch` —
pas de nouvelle branche (travail sur `feature`, comme les chantiers
précédents). Le premier lancement réel de `make rag-acceptance` (contre
les 245 vraies règles) reste une décision et une action de David, hors
périmètre de ce plan.
