# POST /regles/dense Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Exposer le RAG sémantique (`app/retrieval/retrieve()`) via un
nouvel endpoint `POST /regles/dense` dans l'API données existante, avec
authentification, validation et gestion d'erreur cohérentes avec le reste
du router.

**Architecture:** Un nouveau schéma Pydantic (`RegleDenseQuery`) valide la
question en entrée ; l'endpoint appelle `retrieve()` (déjà construit,
inchangé) avec des clients LLM/embedding neufs par requête, recharge les
règles trouvées via `_charger_regles()` (déjà existant), les réordonne
selon la pertinence, et répond `list[RegleRead]` — même schéma de sortie
que `GET /regles`/`GET /regles/{numero}`.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, `app.retrieval.retrieve()`,
`app.ingestion.embedding.EmbeddingClient`,
`app.retrieval.decomposition.DecompositionClient`.

## Global Constraints

- Spec de référence : `docs/superpowers/specs/2026-09-10-api-regles-dense-design.md`.
- `POST /regles/dense`, corps `{"question": "..."}`, jeton Bearer requis
  (`require_bearer`).
- `top_n` vient de `app/ingestion/manifest.yml` → `rag_acceptance.top_n`
  (jamais de paramètre client).
- Nouveau `DecompositionClient`/`EmbeddingClient` par requête (pas de
  singleton partagé).
- Réponse : `list[RegleRead]`, réordonnée selon l'ordre de pertinence de
  `retrieve()` (la clause SQL `IN (...)` ne garantit aucun ordre).
- Erreur : `decomposer()` ne lève jamais (fail-open interne) ; un échec
  d'`embed_batch()`/de la requête pgvector → `503`, jamais une 500 nue.
- `question` : non vide, ≤ `config.QUESTION_MAX_LENGTH` (nouvelle clé
  manifest, valeur 500) → sinon `422` (validation Pydantic native).
- Tests d'intégration : `tests/integration/api_regles/` (pas
  `tests/unit/`), même fixtures (`client`, `session`) que
  `test_regles.py` — nécessite `POSTGRES_TEST_DB` migrée
  (`make migration-test`). `retrieve()` est mocké (patché sur
  `app.api_regles.regles.retrieve`) : aucun appel LLM réel dans les tests
  automatisés.
- Acceptance manuelle hors CI : nouveau script + cible Makefile, jamais
  ajoutée à `tests/acceptance/api_regles_acceptance.jsonl` (jeu rejoué
  automatiquement par `cd-staging.yml`).

---

## Task 1: Configuration — `question_max_length`

**Files:**
- Modify: `app/api_regles/manifest.yml`
- Modify: `app/api_regles/config.py`
- Test: `tests/unit/api_regles/test_config.py`

**Interfaces:**
- Produces: `config.QUESTION_MAX_LENGTH: int`, consommé par la Task 2
  (`RegleDenseQuery`).

- [ ] **Step 1: Écrire le test de la nouvelle constante de config**

Lire `tests/unit/api_regles/test_config.py` pour repérer le style exact
des tests existants (probablement un test par constante, vérifiant le
type et/ou la valeur chargée depuis le manifeste). Ajouter, en suivant le
même style :

```python
def test_question_max_length_est_un_entier_positif():
    assert isinstance(config.QUESTION_MAX_LENGTH, int)
    assert config.QUESTION_MAX_LENGTH > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/api_regles/test_config.py -v`
Expected: FAIL — `AttributeError: module 'app.api_regles.config' has no
attribute 'QUESTION_MAX_LENGTH'`

- [ ] **Step 3: Ajouter la clé au manifeste**

Dans `app/api_regles/manifest.yml`, section `validation` :

```yaml
validation:
  # Longueur maximale d'une review_note : borne le coût en tokens du prochain
  # enrich_again autant que la surface d'injection de prompt.
  review_note_max_length: 2000
  # Longueur maximale d'une question envoyée à POST /regles/dense — chaque
  # appel a un coût réel (LLM + embedding), cette borne écarte un payload
  # abusif sans gêner un usage normal (la plus longue question du jeu
  # d'acceptance fait ~150 caractères).
  question_max_length: 500
```

- [ ] **Step 4: Exposer la constante dans config.py**

Dans `app/api_regles/config.py`, ajouter après `REVIEW_NOTE_MAX_LENGTH` :

```python
QUESTION_MAX_LENGTH: int = _MANIFEST["validation"]["question_max_length"]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/unit/api_regles/test_config.py -v`
Expected: PASS

- [ ] **Step 6: Lint**

Run: `uv run ruff check .`
Expected: `All checks passed!`

- [ ] **Step 7: Commit**

```bash
git add app/api_regles/manifest.yml app/api_regles/config.py tests/unit/api_regles/test_config.py
git commit -m "feat: ajoute question_max_length a la config api_regles"
```

---

## Task 2: Schéma `RegleDenseQuery`

**Files:**
- Modify: `app/api_regles/schemas.py`
- Test: `tests/unit/api_regles/test_schemas.py`

**Interfaces:**
- Consumes: `config.QUESTION_MAX_LENGTH` (Task 1).
- Produces: `RegleDenseQuery` (Pydantic, champ `question: str`, validé),
  consommé par la Task 3 (corps de `POST /regles/dense`).

- [ ] **Step 1: Écrire les tests du schéma**

Lire `tests/unit/api_regles/test_schemas.py` pour le style exact des
tests de `ReglePatch` (probablement une classe `TestReglePatch` ou
similaire). Ajouter, dans le même fichier :

```python
class TestRegleDenseQuery:
    """Tests du schéma de la requête POST /regles/dense."""

    def test_question_valide_est_acceptee(self):
        requete = RegleDenseQuery(question="Faut-il un attribut alt ?")
        assert requete.question == "Faut-il un attribut alt ?"

    def test_question_vide_est_refusee(self):
        with pytest.raises(ValidationError):
            RegleDenseQuery(question="")

    def test_question_uniquement_des_espaces_est_refusee(self):
        with pytest.raises(ValidationError):
            RegleDenseQuery(question="   ")

    def test_question_trop_longue_est_refusee(self):
        with pytest.raises(ValidationError):
            RegleDenseQuery(question="a" * (config.QUESTION_MAX_LENGTH + 1))

    def test_question_est_nettoyee_des_espaces_en_bord(self):
        requete = RegleDenseQuery(question="  Une question ?  ")
        assert requete.question == "Une question ?"
```

Ajouter les imports nécessaires en tête de fichier si absents :
`from pydantic import ValidationError` (et `pytest` si pas déjà importé),
`from app.api_regles import config`, `from app.api_regles.schemas import
RegleDenseQuery` (ou adapter l'import groupé existant).

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/api_regles/test_schemas.py -v`
Expected: FAIL — `ImportError: cannot import name 'RegleDenseQuery'`

- [ ] **Step 3: Implémenter le schéma**

Dans `app/api_regles/schemas.py`, ajouter après `ReglePatch` :

```python
class RegleDenseQuery(BaseModel):
    """Question en langage naturel pour la recherche sémantique (POST /regles/dense)."""

    question: str

    @field_validator("question")
    @classmethod
    def valider_la_question(cls, valeur: str) -> str:
        valeur = valeur.strip()
        if not valeur:
            raise ValueError("question ne peut pas être vide")
        if len(valeur) > config.QUESTION_MAX_LENGTH:
            raise ValueError(f"question dépasse {config.QUESTION_MAX_LENGTH} caractères")
        return valeur
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/api_regles/test_schemas.py -v`
Expected: PASS

- [ ] **Step 5: Lint**

Run: `uv run ruff check .`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add app/api_regles/schemas.py tests/unit/api_regles/test_schemas.py
git commit -m "feat: schema RegleDenseQuery pour POST /regles/dense"
```

---

## Task 3: Endpoint `POST /regles/dense`

**Files:**
- Modify: `app/api_regles/regles.py`
- Modify: `app/api_regles/main.py`
- Test: `tests/integration/api_regles/test_regles_dense.py`

**Interfaces:**
- Consumes: `RegleDenseQuery` (Task 2), `retrieve()`
  (`app.retrieval.retrieval`), `DecompositionClient`
  (`app.retrieval.decomposition`), `EmbeddingClient`
  (`app.ingestion.embedding`), `load_manifest()`
  (`app.ingestion.llm_client`), `_charger_regles()` (déjà existant dans
  `regles.py`), `require_bearer()` (déjà existant).
- Produces: route `POST /regles/dense` testable en HTTP.

- [ ] **Step 1: Écrire le test du cas nominal**

Créer `tests/integration/api_regles/test_regles_dense.py`, en reprenant
les fixtures `session`/`client`/`jeu_de_regles` de
`tests/integration/api_regles/test_regles.py` (copier les 3 fixtures et
la fonction `_database_url()` à l'identique, ou factoriser dans un
`conftest.py` partagé si le projet le permet déjà — vérifier d'abord si
`tests/integration/api_regles/conftest.py` existe ; sinon dupliquer,
cohérent avec le reste du projet qui ne factorise pas encore ces
fixtures) :

```python
"""
Tests d'intégration de POST /regles/dense.

retrieve() est mocké : jamais d'appel LLM réel dans ces tests. Nécessite
qualicheck-postgres démarré et POSTGRES_TEST_DB migrée (make migration-test).
"""

from unittest.mock import patch

from app.api_regles.auth import require_bearer


def _entetes_dev():
    return {"Authorization": "Bearer jeton-de-test"}


@patch("app.api_regles.regles.retrieve")
def test_dense_retourne_les_regles_dans_l_ordre_de_pertinence(
    mock_retrieve, client, jeu_de_regles
):
    """La réponse suit l'ordre de retrieve(), pas l'ordre numéro."""
    mock_retrieve.return_value = [3, 1]

    reponse = client.post(
        "/regles/dense",
        json={"question": "Question de test"},
        headers=_entetes_dev(),
    )

    assert reponse.status_code == 200
    numeros = [r["numero"] for r in reponse.json()]
    assert numeros == [3, 1]


@patch("app.api_regles.regles.retrieve")
def test_dense_sans_jeton_donne_401(mock_retrieve, client, jeu_de_regles):
    reponse = client.post("/regles/dense", json={"question": "Question de test"})

    assert reponse.status_code == 401
    mock_retrieve.assert_not_called()


@patch("app.api_regles.regles.retrieve")
def test_dense_question_vide_donne_422(mock_retrieve, client, jeu_de_regles):
    reponse = client.post(
        "/regles/dense", json={"question": ""}, headers=_entetes_dev()
    )

    assert reponse.status_code == 422
    mock_retrieve.assert_not_called()


@patch("app.api_regles.regles.retrieve")
def test_dense_echec_retrieve_donne_503(mock_retrieve, client, jeu_de_regles):
    mock_retrieve.side_effect = RuntimeError("embedding indisponible")

    reponse = client.post(
        "/regles/dense",
        json={"question": "Question de test"},
        headers=_entetes_dev(),
    )

    assert reponse.status_code == 503


@patch("app.api_regles.regles.retrieve")
def test_dense_journalise_la_question_et_le_client(
    mock_retrieve, client, jeu_de_regles, caplog
):
    mock_retrieve.return_value = [1]

    client.post(
        "/regles/dense",
        json={"question": "Question de test"},
        headers=_entetes_dev(),
    )

    assert "dev" in caplog.text
    assert "Question de test" in caplog.text
```

Adapter les 4 fixtures manquantes (`session`, `client`, `jeu_de_regles`,
constante `JETON`) en les copiant depuis `test_regles.py` si aucun
`conftest.py` partagé n'existe — vérifier d'abord.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/integration/api_regles/test_regles_dense.py -v`
Expected: FAIL — `404 Not Found` sur `/regles/dense` (route inexistante)

- [ ] **Step 3: Implémenter l'endpoint**

Dans `app/api_regles/regles.py`, ajouter les imports en tête de fichier :

```python
from app.ingestion.embedding import EmbeddingClient
from app.ingestion.llm_client import load_manifest
from app.api_regles.schemas import OutilFiltre, RegleDenseQuery, ReglePatch, RegleRead, ReviewStatusFiltre
from app.retrieval.decomposition import DecompositionClient
from app.retrieval.retrieval import retrieve
```

(fusionner avec l'import existant de `app.api_regles.schemas` plutôt que
d'en dupliquer un — ajouter `RegleDenseQuery` à la liste existante).

Puis, après la route `annoter_regle` (fin de fichier) :

```python
@router.post("/dense", response_model=list[RegleRead])
def chercher_regles_dense(
    requete: RegleDenseQuery,
    session: Session = Depends(get_session_referentiel),
    client_nom: str = Depends(require_bearer),
) -> list[RegleRead]:
    """
    Recherche sémantique : décompose la question, vectorise, interroge
    pgvector, fusionne. Voir app/retrieval/retrieval.py::retrieve().

    Chaque appel a un coût réel (LLM + embedding) — jeton Bearer requis,
    contrairement aux autres lectures de ce router.
    """
    top_n = load_manifest()["rag_acceptance"]["top_n"]
    decomposition_client = DecompositionClient()
    embedding_client = EmbeddingClient()

    logger.info("Recherche dense par %s : « %s »", client_nom, requete.question)

    try:
        numeros = retrieve(
            session=session,
            question=requete.question,
            top_n=top_n,
            decomposition_client=decomposition_client,
            embedding_client=embedding_client,
        )
    except Exception as e:
        logger.error("Recherche dense — échec (%s)", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Recherche sémantique indisponible",
        ) from e

    requete_orm = session.query(Regle, Theme.theme).filter(
        Theme.id == Regle.theme_id, Regle.numero.in_(numeros)
    )
    resultats = _charger_regles(session, requete_orm)

    # Réordonne selon l'ordre de pertinence de retrieve() — la requête SQL
    # IN (...) ne garantit aucun ordre.
    position = {numero: i for i, numero in enumerate(numeros)}
    return sorted(resultats, key=lambda r: position[r.numero])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/integration/api_regles/test_regles_dense.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Mettre à jour CORS pour autoriser POST**

Dans `app/api_regles/main.py`, remplacer :

```python
    allow_methods=["GET", "PATCH"],
```

par :

```python
    allow_methods=["GET", "PATCH", "POST"],
```

- [ ] **Step 6: Run full unit + integration suite**

Run: `uv run pytest tests/unit tests/integration -v`
Expected: tous PASS (nécessite `POSTGRES_TEST_DB` migrée — `make
migration-test` si besoin)

- [ ] **Step 7: Lint**

Run: `uv run ruff check .`
Expected: `All checks passed!`

- [ ] **Step 8: Commit**

```bash
git add app/api_regles/regles.py app/api_regles/main.py tests/integration/api_regles/test_regles_dense.py
git commit -m "feat: endpoint POST /regles/dense (RAG semantique expose en HTTP)"
```

---

## Task 4: Acceptance manuelle (hors CI) + Makefile

**Files:**
- Create: `scripts/check_api_regles_dense_acceptance.py`
- Modify: `Makefile`

**Interfaces:**
- Consumes: `tests/acceptance/rag_acceptance.jsonl` (99 cas existants,
  inchangé), `evaluate_case`/`compute_taux_par_famille`/`is_acceptable`
  (`app.ingestion.rag_acceptance`), `app.api_regles.config`
  (`clients_tokens()`, `PORT`).

- [ ] **Step 1: Écrire le script d'acceptance HTTP**

Créer `scripts/check_api_regles_dense_acceptance.py` :

```python
"""Rejoue le jeu d'acceptance RAG via POST /regles/dense en HTTP réel.

Nécessite l'API réellement démarrée (make api-regles, dans un terminal
dédié). Réutilise tests/acceptance/rag_acceptance.jsonl (99 cas, aucune
duplication) : vérifie que le contrat HTTP bout-en-bout produit le même
résultat que l'appel direct à retrieve() (scripts/check_rag_acceptance.py).

Coût réel à chaque exécution (décomposition LLM + embedding pour chaque
cas) — volontairement hors CI, jamais ajouté au jeu automatique
tests/acceptance/api_regles_acceptance.jsonl (rejoué par cd-staging.yml à
chaque déploiement). Lancé à la demande via `make api-regles-dense-acceptance`.
"""

import logging
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api_regles import config  # noqa: E402
from app.ingestion.llm_client import load_manifest  # noqa: E402
from app.ingestion.rag_acceptance import (  # noqa: E402
    compute_taux_par_famille,
    is_acceptable,
    load_cases,
)
from app.logging_config import setup_logging  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

CASES_PATH = Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance.jsonl"


def _entetes() -> dict[str, str]:
    return {"Authorization": f"Bearer {config.clients_tokens()['dev']}"}


def _evaluer_cas_http(client: httpx.Client, base_url: str, case: dict) -> dict:
    """Appelle POST /regles/dense et construit la même structure d'évaluation
    que app.ingestion.rag_acceptance.evaluate_case (verdict PASS/FAIL/PARTIEL)."""
    reponse = client.post(
        f"{base_url}/regles/dense",
        json={"question": case["question"]},
        headers=_entetes(),
        timeout=30,
    )
    reponse.raise_for_status()
    numeros_retournes = [regle["numero"] for regle in reponse.json()]

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


def main() -> None:
    setup_logging()
    load_dotenv()

    base_url = f"http://localhost:{config.PORT}"

    logger.info("=== check_api_regles_dense_acceptance : démarrage ===")
    progress_logger.info("=== check_api_regles_dense_acceptance : démarrage ===")

    try:
        cases = load_cases(CASES_PATH)

        with httpx.Client() as client:
            evaluations = [_evaluer_cas_http(client, base_url, case) for case in cases]
            for evaluation in evaluations:
                progress_logger.info(
                    f"check_api_regles_dense_acceptance — « {evaluation['question']} » "
                    f"[{evaluation['famille']}] (attendu {evaluation['numeros_regle_attendus']}, "
                    f"retourné {evaluation['numeros_retournes']}) — {evaluation['verdict']}"
                )

        taux_par_famille = compute_taux_par_famille(evaluations)
        for famille, stats in taux_par_famille.items():
            partiel_note = f", {stats['partiels']} PARTIEL" if stats["partiels"] else ""
            progress_logger.info(
                f"check_api_regles_dense_acceptance — Famille {famille} : "
                f"{stats['reussis']}/{stats['total']} ({stats['taux']:.0%}){partiel_note}"
            )

    except Exception as e:
        logger.error("check_api_regles_dense_acceptance : ÉCHEC (%s)", e)
        sys.exit(1)

    seuil = 0.9  # même seuil que app/ingestion/manifest.yml::rag_acceptance
    if not is_acceptable(taux_par_famille, seuil):
        logger.error("check_api_regles_dense_acceptance : au moins une famille sous le seuil")
        sys.exit(1)

    logger.info("=== check_api_regles_dense_acceptance : succès ===")
    progress_logger.info("=== check_api_regles_dense_acceptance : succès ===")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Ajouter la cible Makefile**

Dans `Makefile`, après la cible `api-regles-acceptance` :

```makefile
## Rejoue le jeu d'acceptance RAG (99 cas, tests/acceptance/rag_acceptance.jsonl)
## via POST /regles/dense en HTTP reel — necessite make api-regles demarre
## dans un autre terminal. Cout reel (LLM + embedding) a chaque execution,
## volontairement hors CI, comme make rag-acceptance.
api-regles-dense-acceptance:
	uv run python scripts/check_api_regles_dense_acceptance.py
```

Ajouter `api-regles-dense-acceptance` à la ligne `.PHONY` en tête de
fichier, à côté de `api-regles-acceptance`.

- [ ] **Step 3: Lint**

Run: `uv run ruff check .`
Expected: `All checks passed!`

- [ ] **Step 4: Vérification manuelle réelle**

Dans un premier terminal : `make api-regles` (laisser tourner).
Dans un second terminal : `make api-regles-dense-acceptance`.

Expected: le script se termine avec `=== ... : succès ===`, un taux par
famille loggé pour chacune des 7 familles, cohérent avec le dernier run
de `make rag-acceptance` (`docs/eval/`, CHANGELOG.md 2026-09-09) — pas de
régression liée au passage par HTTP plutôt qu'un appel direct à
`retrieve()`.

- [ ] **Step 5: Tracer dans CHANGELOG.md et TODO.md**

Ajouter une entrée `CHANGELOG.md` (nouvelle date du jour) décrivant
l'endpoint livré et le résultat de la vérification manuelle (Step 4).
Dans `TODO.md`, marquer la ligne « Prochaine étape : API HTTP intégrant
le RAG (carte #14) » comme faite (`[x]`), avec le résultat mesuré.

- [ ] **Step 6: Commit**

```bash
git add scripts/check_api_regles_dense_acceptance.py Makefile CHANGELOG.md TODO.md
git commit -m "feat: acceptance manuelle HTTP pour POST /regles/dense (make api-regles-dense-acceptance)"
```

---

## Self-Review (déjà appliqué en rédigeant ce plan)

- **Couverture de la spec** : config (Task 1), schéma (Task 2), endpoint
  avec CORS/gestion d'erreur/log (Task 3), acceptance manuelle et
  traçage (Task 4). Le point « hors périmètre » de la spec (top_n
  client, rate limiting, révision de `?q=`, ajout au jeu automatique)
  n'a volontairement aucune tâche correspondante.
- **Type consistency** : `RegleDenseQuery.question: str` (Task 2)
  consommé tel quel par `requete.question` (Task 3) ;
  `retrieve(session, question, top_n, decomposition_client,
  embedding_client) -> list[int]` (déjà existant, inchangé) appelé avec
  les mêmes noms de paramètres dans l'endpoint (Task 3) et documenté
  dans les contraintes globales.
- **Pas de placeholder** : le seuil `0.9` du script d'acceptance (Task 4)
  est dupliqué en dur plutôt que lu depuis `app/ingestion/manifest.yml`
  volontairement précisé en commentaire (« même seuil que ... ») — pas
  un oubli, un choix explicite pour ne pas faire dépendre
  `app/api_regles/` (déjà chargé de secrets Azure) du manifeste
  `app/ingestion/` pour une seule constante de comparaison ; à corriger
  si ça devient gênant en pratique.
