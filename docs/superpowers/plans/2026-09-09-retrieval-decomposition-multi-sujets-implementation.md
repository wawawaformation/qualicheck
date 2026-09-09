# Décomposition LLM des questions multi-sujets — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ajouter un mécanisme qui décompose une question multi-sujets en
sous-questions avant retrieval, pour que chaque sujet distinct retrouve
sa règle Opquast au lieu qu'un sujet écrase l'autre dans l'espace
vectoriel.

**Architecture:** Nouveau package `app/retrieval/` : un appel LLM structuré
(`decomposition.py`, `gpt-5.4-mini`) découpe la question en 1..N
sous-questions ; `retrieval.py` orchestre embedding + recherche pgvector
par sous-question + union simple des règles trouvées. Aucune boucle
agentique, aucun scoring de fusion — tout est déterministe et testable.

**Tech Stack:** Python, LangChain (`ChatOpenAI`, `JsonOutputParser`),
Pydantic, `tenacity` (retry), SQLAlchemy, pgvector.

## Global Constraints

- Retry LLM : 3 tentatives, backoff exponentiel 2s/4s/8s (règle projet
  non négociable, déjà appliquée à `LLMClient`/`EmbeddingClient`).
- Timeout de l'appel LLM de décomposition : **2s** explicite (paramètre
  `timeout` de `ChatOpenAI`) — différent des autres rôles car un
  utilisateur attend une réponse en direct, et la décomposition n'est
  qu'une étape parmi d'autres avant la réponse finale.
- Fail-open : après 3 échecs, `decomposer()` retombe sur `[question]`
  (traitée comme mono-sujet), jamais d'exception propagée à l'appelant.
- Fusion : union simple, dédoublonnée, ordre de première apparition — pas
  de RRF, pas de plafond après fusion.
- `query_top_n_numeros()` reste dans `app/ingestion/rag_acceptance.py`,
  réutilisée par import — ne pas la déplacer.
- Aucune valeur métier en dur : modèle/prix du rôle `decomposition` dans
  `app/ingestion/manifest.yml`, comme les rôles existants.
- Spec de référence : `docs/superpowers/specs/2026-09-09-retrieval-decomposition-multi-sujets-design.md`.

---

## Task 1: Scaffolding — package, prompt, rôle manifest

**Files:**
- Create: `app/retrieval/__init__.py` (vide)
- Create: `app/retrieval/prompts/decompose_question.md`
- Create: `tests/unit/retrieval/__init__.py` (vide)
- Modify: `app/ingestion/manifest.yml`

**Interfaces:**
- Produces: rôle `decomposition` dans le manifest (consommé par la
  Task 2), fichier prompt (consommé par la Task 2).

- [ ] **Step 1: Créer le package `app/retrieval/`**

```bash
mkdir -p app/retrieval/prompts tests/unit/retrieval
touch app/retrieval/__init__.py tests/unit/retrieval/__init__.py
```

- [ ] **Step 2: Écrire le prompt de décomposition**

Créer `app/retrieval/prompts/decompose_question.md` :

```markdown
Tu es un module de pré-traitement pour un moteur de recherche sémantique
qui interroge un référentiel de 245 règles de qualité web (Opquast). Une
règle correspond à un sujet précis (ex. « alternative textuelle des
images », « taille des zones cliquables »).

Ta tâche : décider si la question ci-dessous porte sur **un seul sujet**
ou sur **plusieurs sujets clairement distincts**, puis la découper en
conséquence.

- Si elle porte sur un seul sujet — même si elle mentionne plusieurs
  notions liées à ce même sujet — renvoie-la telle quelle, seule dans la
  liste.
- Si elle porte sur plusieurs sujets distincts (chacun correspondrait à
  une règle différente du référentiel), découpe-la en autant de
  sous-questions autonomes, compréhensibles isolément.

## Exemples

Question : « Sur mobile, faut-il des boutons assez grands et laisser
l'utilisateur agrandir la page ? »
Réponse : {"sous_questions": ["Sur mobile, faut-il des boutons assez grands ?", "Faut-il laisser l'utilisateur agrandir la page ?"]}

Question : « Chaque image porteuse d'information est-elle dotée d'une
alternative textuelle appropriée ? »
Réponse : {"sous_questions": ["Chaque image porteuse d'information est-elle dotée d'une alternative textuelle appropriée ?"]}

## Question à traiter

{question}

Réponds uniquement avec un objet JSON de la forme
{"sous_questions": ["...", "..."]}, sans aucun texte avant ou après.
```

- [ ] **Step 3: Ajouter le rôle `decomposition` au manifest**

Dans `app/ingestion/manifest.yml`, ajouter après la section `rag_acceptance` :

```yaml
decomposition:
  modele: gpt-5.4-mini
  env_var: AZURE_MODEL_GPT_MINI
  # Timeout applicatif distinct (2s, pas 30s comme le benchmark) : appel
  # dans le chemin d'une requête utilisateur en direct (US2), pas un
  # traitement batch offline. Voir docs/superpowers/specs/
  # 2026-09-09-retrieval-decomposition-multi-sujets-design.md.
  # Tarifs à corriger dès la première facture Azure réelle (même logique
  # que le rôle embedding).
  prix_entree_par_million: 0.15
  prix_sortie_par_million: 0.60
```

- [ ] **Step 4: Vérifier que le manifest se charge**

Run: `uv run python -c "from app.ingestion.llm_client import load_manifest; print(load_manifest()['decomposition'])"`
Expected: affiche le dict `{'modele': 'gpt-5.4-mini', 'env_var': 'AZURE_MODEL_GPT_MINI', ...}`

- [ ] **Step 5: Lint**

Run: `uv run ruff check .`
Expected: `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add app/retrieval/ tests/unit/retrieval/__init__.py app/ingestion/manifest.yml
git commit -m "feat: scaffolding app/retrieval/, role manifest decomposition"
```

---

## Task 2: `DecompositionClient` (décomposition LLM, TDD)

**Files:**
- Create: `app/retrieval/decomposition.py`
- Test: `tests/unit/retrieval/test_decomposition.py`

**Interfaces:**
- Consumes: `load_manifest()` (`app.ingestion.llm_client`), prompt
  `app/retrieval/prompts/decompose_question.md` (Task 1).
- Produces: `DecompositionOutput` (Pydantic, champ `sous_questions:
  list[str]`), `DecompositionClient.decomposer(question: str) ->
  list[str]`, attributs `input_tokens`/`output_tokens` (int, cumulés).
  Consommé par la Task 3 (`retrieve()`) et la Task 4
  (`check_rag_acceptance.py`).

- [ ] **Step 1: Écrire le test du cas mono-sujet**

Créer `tests/unit/retrieval/test_decomposition.py` :

```python
"""
Tests unitaires pour app/retrieval/decomposition.py

Teste la décomposition LLM d'une question en sous-questions — LLM
entièrement mocké, même patron que tests/unit/ingestion/test_enrichment.py.
"""

from unittest.mock import MagicMock, patch

from app.retrieval.decomposition import DecompositionClient


def _mock_response(sous_questions: list[str], input_tokens: int, output_tokens: int):
    response = MagicMock()
    questions_json = ", ".join(f'"{q}"' for q in sous_questions)
    response.content = f'{{"sous_questions": [{questions_json}]}}'
    response.usage_metadata = {"input_tokens": input_tokens, "output_tokens": output_tokens}
    return response


class TestDecompositionClient:
    """Tests du client de décomposition."""

    @patch("app.retrieval.decomposition.ChatOpenAI")
    def test_decomposer_question_mono_sujet_retourne_liste_a_un_element(self, mock_llm_class):
        """Une question mono-sujet est retournée telle quelle, seule dans la liste."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _mock_response(
            ["Chaque image porteuse d'information a-t-elle une alternative textuelle ?"],
            input_tokens=80,
            output_tokens=20,
        )

        client = DecompositionClient()
        resultat = client.decomposer(
            "Chaque image porteuse d'information a-t-elle une alternative textuelle ?"
        )

        assert resultat == ["Chaque image porteuse d'information a-t-elle une alternative textuelle ?"]
        assert client.input_tokens == 80
        assert client.output_tokens == 20
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/retrieval/test_decomposition.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.retrieval.decomposition'`

- [ ] **Step 3: Implémenter `DecompositionClient` (cas nominal, sans retry/fail-open)**

Créer `app/retrieval/decomposition.py` :

```python
"""
Client LLM pour la décomposition des questions multi-sujets.

Découpe une question utilisateur en 1..N sous-questions avant retrieval,
pour que chaque sujet distinct interroge pgvector séparément. Voir
docs/superpowers/specs/2026-09-09-retrieval-decomposition-multi-sujets-design.md.
"""

import logging
import os
from pathlib import Path

from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from app.ingestion.llm_client import load_manifest

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "decompose_question.md"


class DecompositionOutput(BaseModel):
    """Structure attendue de la réponse LLM."""

    sous_questions: list[str]


class DecompositionClient:
    """Client pour la décomposition LLM d'une question en sous-questions."""

    def __init__(self):
        """Initialise le client Azure OpenAI (rôle decomposition, timeout 2s)."""
        manifest = load_manifest()
        role = manifest["decomposition"]

        self.llm = ChatOpenAI(
            base_url=os.getenv("AZURE_AI_ENDPOINT"),
            api_key=os.getenv("AZURE_AI_API_KEY"),
            model=os.getenv(role["env_var"]),
            timeout=2,
        )
        self.parser = JsonOutputParser(pydantic_object=DecompositionOutput)
        self.input_tokens = 0
        self.output_tokens = 0

    def _charger_prompt(self, question: str) -> str:
        with open(PROMPT_PATH, encoding="utf-8") as f:
            prompt_text = f.read()
        return prompt_text.replace("{question}", question)

    def decomposer(self, question: str) -> list[str]:
        """Découpe une question en sous-questions (1 élément si mono-sujet)."""
        prompt = self._charger_prompt(question)
        response = self.llm.invoke(prompt)
        parsed = self.parser.parse(response.content)

        usage = response.usage_metadata or {}
        self.input_tokens += usage.get("input_tokens", 0)
        self.output_tokens += usage.get("output_tokens", 0)

        return parsed["sous_questions"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/retrieval/test_decomposition.py -v`
Expected: PASS

- [ ] **Step 5: Écrire le test du cas multi-sujets**

Ajouter à `tests/unit/retrieval/test_decomposition.py` :

```python
    @patch("app.retrieval.decomposition.ChatOpenAI")
    def test_decomposer_question_multi_sujets_retourne_n_sous_questions(self, mock_llm_class):
        """Une question multi-sujets est découpée en plusieurs sous-questions."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _mock_response(
            [
                "Sur mobile, faut-il des boutons assez grands ?",
                "Faut-il laisser l'utilisateur agrandir la page ?",
            ],
            input_tokens=90,
            output_tokens=40,
        )

        client = DecompositionClient()
        resultat = client.decomposer(
            "Sur mobile, faut-il des boutons assez grands et laisser l'utilisateur agrandir la page ?"
        )

        assert resultat == [
            "Sur mobile, faut-il des boutons assez grands ?",
            "Faut-il laisser l'utilisateur agrandir la page ?",
        ]
```

Run: `uv run pytest tests/unit/retrieval/test_decomposition.py -v`
Expected: PASS (aucun changement d'implémentation nécessaire, le code du
Step 3 gère déjà N éléments)

- [ ] **Step 6: Écrire le test de retry + fail-open**

Ajouter à `tests/unit/retrieval/test_decomposition.py` :

```python
    @patch("tenacity.nap.time.sleep")
    @patch("app.retrieval.decomposition.ChatOpenAI")
    def test_decomposer_reessaie_puis_reussit(self, mock_llm_class, mock_sleep):
        """Réessaie après échec, puis réussit (3 tentatives max)."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.side_effect = [
            TimeoutError("Request timed out"),
            TimeoutError("Request timed out"),
            _mock_response(["question"], input_tokens=10, output_tokens=5),
        ]

        client = DecompositionClient()
        resultat = client.decomposer("question")

        assert mock_llm_instance.invoke.call_count == 3
        assert mock_sleep.call_count == 2
        assert resultat == ["question"]

    @patch("tenacity.nap.time.sleep")
    @patch("app.retrieval.decomposition.ChatOpenAI")
    def test_decomposer_fail_open_apres_3_echecs(self, mock_llm_class, mock_sleep):
        """Après 3 échecs, retombe sur [question] plutôt que de lever une exception."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.side_effect = TimeoutError("Request timed out")

        client = DecompositionClient()
        resultat = client.decomposer("Ma question originale ?")

        assert mock_llm_instance.invoke.call_count == 3
        assert resultat == ["Ma question originale ?"]
```

- [ ] **Step 7: Run tests to verify they fail**

Run: `uv run pytest tests/unit/retrieval/test_decomposition.py -v`
Expected: les 2 nouveaux tests FAIL — pas de retry (`call_count == 1`),
pas de fail-open (l'exception `TimeoutError` remonte à l'appelant)

- [ ] **Step 8: Ajouter retry + fail-open**

Modifier `app/retrieval/decomposition.py` : renommer la méthode `decomposer`
en `_appeler_llm` (privée, décorée du retry), et créer une nouvelle
méthode publique `decomposer` qui capture l'échec final :

```python
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        reraise=True,
    )
    def _appeler_llm(self, question: str) -> list[str]:
        prompt = self._charger_prompt(question)
        response = self.llm.invoke(prompt)
        parsed = self.parser.parse(response.content)

        usage = response.usage_metadata or {}
        self.input_tokens += usage.get("input_tokens", 0)
        self.output_tokens += usage.get("output_tokens", 0)

        return parsed["sous_questions"]

    def decomposer(self, question: str) -> list[str]:
        """Découpe une question en sous-questions (1 élément si mono-sujet).

        Retente automatiquement jusqu'à 3 fois en cas d'erreur (timeout ou
        JSON malformé), avec backoff exponentiel (2s, 4s, 8s). Après 3
        échecs, fail-open : retombe sur [question] telle quelle plutôt que
        de faire échouer toute la réponse à l'utilisateur.
        """
        try:
            return self._appeler_llm(question)
        except Exception:
            logger.warning(
                f"decomposition : échec après 3 tentatives pour « {question} », "
                "fail-open (traitée comme mono-sujet)"
            )
            return [question]
```

Supprimer l'ancienne méthode `decomposer` du Step 3 (remplacée par les
deux méthodes ci-dessus).

- [ ] **Step 9: Run all decomposition tests to verify they pass**

Run: `uv run pytest tests/unit/retrieval/test_decomposition.py -v`
Expected: 4 tests PASS

- [ ] **Step 10: Lint**

Run: `uv run ruff check .`
Expected: `All checks passed!`

- [ ] **Step 11: Commit**

```bash
git add app/retrieval/decomposition.py tests/unit/retrieval/test_decomposition.py
git commit -m "feat: DecompositionClient - decoupe une question en sous-questions"
```

---

## Task 3: `retrieve()` — orchestration embedding + pgvector + union

**Files:**
- Create: `app/retrieval/retrieval.py`
- Test: `tests/unit/retrieval/test_retrieval.py`

**Interfaces:**
- Consumes: `DecompositionClient.decomposer(question: str) -> list[str]`
  (Task 2) ; `EmbeddingClient.embed_batch(texts: list[str]) ->
  list[list[float]]` (`app.ingestion.embedding`, déjà existant) ;
  `query_top_n_numeros(session: Session, vector: list[float], top_n: int)
  -> list[int]` (`app.ingestion.rag_acceptance`, déjà existant).
- Produces: `retrieve(session, question, top_n, decomposition_client,
  embedding_client) -> list[int]`. Consommé par la Task 4.

- [ ] **Step 1: Écrire le test d'union/dédoublonnage**

Créer `tests/unit/retrieval/test_retrieval.py` :

```python
"""
Tests unitaires pour app/retrieval/retrieval.py

Teste l'orchestration décomposition → embedding → pgvector → union.
Tous les clients et la session sont mockés.
"""

from unittest.mock import MagicMock, patch

from app.retrieval.retrieval import retrieve


class TestRetrieve:
    """Tests de l'orchestration retrieve()."""

    @patch("app.retrieval.retrieval.query_top_n_numeros")
    def test_retrieve_union_dedoublonne_sur_plusieurs_sous_questions(self, mock_query):
        """Les résultats de chaque sous-question sont fusionnés sans doublon."""
        decomposition_client = MagicMock()
        decomposition_client.decomposer.return_value = ["sous-question A", "sous-question B"]
        embedding_client = MagicMock()
        embedding_client.embed_batch.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_query.side_effect = [[1, 2, 3], [3, 4, 5]]
        session = MagicMock()

        resultat = retrieve(
            session=session,
            question="question originale multi-sujets",
            top_n=15,
            decomposition_client=decomposition_client,
            embedding_client=embedding_client,
        )

        assert resultat == [1, 2, 3, 4, 5]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/retrieval/test_retrieval.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.retrieval.retrieval'`

- [ ] **Step 3: Implémenter `retrieve()`**

Créer `app/retrieval/retrieval.py` :

```python
"""
Orchestration du retrieval : décomposition, embedding, recherche pgvector,
union. Voir docs/superpowers/specs/2026-09-09-retrieval-decomposition-multi-sujets-design.md.
"""

from sqlalchemy.orm import Session

from app.ingestion.embedding import EmbeddingClient
from app.ingestion.rag_acceptance import query_top_n_numeros
from app.retrieval.decomposition import DecompositionClient


def retrieve(
    session: Session,
    question: str,
    top_n: int,
    decomposition_client: DecompositionClient,
    embedding_client: EmbeddingClient,
) -> list[int]:
    """Retrouve les numéros de règle pertinents pour une question.

    Décompose la question en 1..N sous-questions, vectorise toutes les
    sous-questions en un seul appel embed_batch, interroge pgvector
    (top_n) une fois par sous-question, puis fusionne par union simple
    dédoublonnée (ordre de première apparition). Pas de plafond après
    fusion : la taille du résultat varie selon le nombre de sous-questions.
    """
    sous_questions = decomposition_client.decomposer(question)
    vectors = embedding_client.embed_batch(sous_questions)

    numeros: list[int] = []
    vus: set[int] = set()
    for vector in vectors:
        for numero in query_top_n_numeros(session, vector, top_n):
            if numero not in vus:
                vus.add(numero)
                numeros.append(numero)

    return numeros
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/retrieval/test_retrieval.py -v`
Expected: PASS

- [ ] **Step 5: Écrire le test du cas mono-sujet (régression)**

Ajouter à `tests/unit/retrieval/test_retrieval.py` :

```python
    @patch("app.retrieval.retrieval.query_top_n_numeros")
    def test_retrieve_mono_sujet_une_seule_recherche(self, mock_query):
        """Une seule sous-question déclenche une seule recherche pgvector."""
        decomposition_client = MagicMock()
        decomposition_client.decomposer.return_value = ["question mono-sujet"]
        embedding_client = MagicMock()
        embedding_client.embed_batch.return_value = [[0.5, 0.6]]
        mock_query.return_value = [10, 20, 30]
        session = MagicMock()

        resultat = retrieve(
            session=session,
            question="question mono-sujet",
            top_n=15,
            decomposition_client=decomposition_client,
            embedding_client=embedding_client,
        )

        assert resultat == [10, 20, 30]
        assert mock_query.call_count == 1
        embedding_client.embed_batch.assert_called_once_with(["question mono-sujet"])
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/unit/retrieval/test_retrieval.py -v`
Expected: PASS (aucun changement d'implémentation nécessaire)

- [ ] **Step 7: Lint**

Run: `uv run ruff check .`
Expected: `All checks passed!`

- [ ] **Step 8: Commit**

```bash
git add app/retrieval/retrieval.py tests/unit/retrieval/test_retrieval.py
git commit -m "feat: retrieve() - decompose, embed, interroge pgvector, fusionne"
```

---

## Task 4: Intégration à `check_rag_acceptance.py` + traçabilité

**Files:**
- Modify: `scripts/check_rag_acceptance.py`
- Modify: `CHANGELOG.md`
- Modify: `TODO.md`

**Interfaces:**
- Consumes: `retrieve()` (Task 3), `DecompositionClient` (Task 2).

- [ ] **Step 1: Remplacer l'appel direct à `query_top_n_numeros` par `retrieve()`**

Dans `scripts/check_rag_acceptance.py` :

Remplacer l'import :

```python
from app.ingestion.rag_acceptance import (  # noqa: E402
    compute_taux_par_famille,
    evaluate_case,
    format_dataset_versions,
    is_acceptable,
    load_cases,
    query_top_n_numeros,
)
```

par :

```python
from app.ingestion.rag_acceptance import (  # noqa: E402
    compute_taux_par_famille,
    evaluate_case,
    format_dataset_versions,
    is_acceptable,
    load_cases,
)
from app.retrieval.decomposition import DecompositionClient  # noqa: E402
from app.retrieval.retrieval import retrieve  # noqa: E402
```

Remplacer, dans `main()`, le bloc :

```python
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
```

par :

```python
    try:
        cases = load_cases(CASES_PATH)
        embedding_client = EmbeddingClient()
        decomposition_client = DecompositionClient()

        evaluations = []
        with Session(engine) as session:
            dataset_summary = format_dataset_versions(summarize_dataset_versions(session))
            progress_logger.info(f"check_rag_acceptance — Jeu de données : {dataset_summary}")

            for case in cases:
                numeros_retournes = retrieve(
                    session=session,
                    question=case["question"],
                    top_n=top_n,
                    decomposition_client=decomposition_client,
                    embedding_client=embedding_client,
                )
                evaluation = evaluate_case(case, numeros_retournes)
                evaluations.append(evaluation)
                progress_logger.info(
                    f"check_rag_acceptance — « {case['question']} » "
                    f"[{case['famille']}] (attendu {evaluation['numeros_regle_attendus']}, "
                    f"retourné {numeros_retournes}) — {evaluation['verdict']}"
                )
```

- [ ] **Step 2: Mettre à jour le calcul de coût pour inclure la décomposition**

Remplacer, plus bas dans `main()` :

```python
        role = load_manifest()["embedding"]
        cost = client.total_tokens * role["prix_entree_par_million"] / 1_000_000
        summary = (
            f"check_rag_acceptance — seuil {seuil:.0%}, tokens : {client.total_tokens}, "
            f"coût estimé : {cost:.4f} €"
        )
```

par :

```python
        manifest = load_manifest()
        embedding_role = manifest["embedding"]
        decomposition_role = manifest["decomposition"]
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
            f"check_rag_acceptance — seuil {seuil:.0%}, "
            f"tokens embedding : {embedding_client.total_tokens}, "
            f"tokens décomposition : {decomposition_client.input_tokens}+"
            f"{decomposition_client.output_tokens}, coût estimé : {cost:.4f} €"
        )
```

- [ ] **Step 3: Vérifier que les tests unitaires existants passent toujours**

Run: `uv run pytest -q`
Expected: tous les tests PASS (aucun test unitaire n'exécute
`check_rag_acceptance.py` — c'est un script à coût réel, testé
manuellement à l'étape suivante)

- [ ] **Step 4: Lint**

Run: `uv run ruff check .`
Expected: `All checks passed!`

- [ ] **Step 5: Lancer la mesure réelle**

Run: `make rag-acceptance`
Expected: le script s'exécute sans erreur, log un verdict PASS/FAIL/PARTIEL
par cas et un taux par famille en fin d'exécution, exit code 0 si toutes
les familles (hors `sans_reponse`) sont au-dessus du seuil de 80% —
comparer les taux par famille à `docs/eval/rag_dense_acceptance_2026-09-09_150745.md`
(dernière mesure sans décomposition) pour confirmer l'absence de
régression sur les 97 cas mono-sujet et l'amélioration sur `multi_sujets`
(2 cas actuellement `PARTIEL`, règles 106/107 et 107/46 non retrouvées
ensemble)

- [ ] **Step 6: Tracer dans CHANGELOG.md**

Ajouter en tête de `CHANGELOG.md` (nouvelle entrée du jour, ou nouvelle
« Part » si une entrée du jour existe déjà) :

```markdown
- **Mécanisme de décomposition LLM des questions multi-sujets** (carte
  Kanboard #10) — nouveau package `app/retrieval/` (`decomposition.py`,
  `retrieval.py`), `scripts/check_rag_acceptance.py` bascule sur
  `retrieve()` pour les 99 cas. Résultat mesuré : [à compléter avec le
  taux obtenu à l'Step 5, en particulier sur `multi_sujets`].
```

- [ ] **Step 7: Mettre à jour TODO.md**

Dans `TODO.md`, section « Retrieval US2 », ajouter sous la recommandation
2 (déjà cochée) :

```markdown
  - [x] **Recommandation 3 — mécanisme de décomposition LLM pour
    `multi_sujets`** (2026-09-09, carte Kanboard #10) — `D`/`A`
    - `app/retrieval/` (decomposition.py, retrieval.py) — un appel LLM
      structuré (gpt-5.4-mini, pas d'agent ReAct) découpe la question,
      union simple des résultats pgvector par sous-question.
      `scripts/check_rag_acceptance.py` bascule entièrement sur
      `retrieve()` (test de non-régression grandeur nature sur les 97
      cas mono-sujet). Spec :
      `docs/superpowers/specs/2026-09-09-retrieval-decomposition-multi-sujets-design.md`.
    - Résultat mesuré : [à compléter avec le taux `multi_sujets` obtenu
      à l'Step 5].
```

- [ ] **Step 8: Commit**

```bash
git add scripts/check_rag_acceptance.py CHANGELOG.md TODO.md
git commit -m "feat: check_rag_acceptance utilise retrieve() (decomposition multi-sujets)"
```

---

## Self-Review (déjà appliqué en rédigeant ce plan)

- **Couverture de la spec** : architecture (Task 1), `decomposition.py`
  (Task 2), `retrieval.py` (Task 3), intégration + fail-open + timeout +
  coût (Task 2/4), tests unitaires des deux modules (Task 2/3),
  acceptance réelle (Task 4). Aucune section de la spec sans tâche
  correspondante.
- **Type consistency** : `DecompositionClient.decomposer(question: str)
  -> list[str]` (Task 2) utilisé tel quel dans `retrieve()` (Task 3) et
  dans `check_rag_acceptance.py` (Task 4) ; `retrieve(session, question,
  top_n, decomposition_client, embedding_client) -> list[int]` (Task 3)
  utilisé tel quel dans `check_rag_acceptance.py` (Task 4).
- **Pas de placeholder** dans le code livré — seuls les 2 endroits où le
  résultat dépend d'une exécution réelle (`make rag-acceptance`, Task 4
  Steps 6-7) sont explicitement marqués « à compléter avec le taux
  obtenu », ce qui est un résultat de mesure, pas un détail d'implémentation
  manquant.
