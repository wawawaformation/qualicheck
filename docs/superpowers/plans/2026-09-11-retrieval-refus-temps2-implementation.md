# Mécanisme de refus — Temps 2 (jugement LLM) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer le retour brut de `POST /regles/dense` par un retour filtré par jugement LLM : citer les règles qui répondent réellement à la question, ou `[]` si aucune ne répond — dernière branche du mécanisme de refus après l'échec mesuré du seuil de score (Temps 1).

**Architecture:** Un nouveau `JugementClient` (même patron que `DecompositionClient` existant : Azure OpenAI, sortie structurée JSON, retry 3x, fail-open) reçoit la question et le texte complet de chaque candidat déjà retourné par `retrieve()`, et renvoie les numéros jugés pertinents. L'endpoint `chercher_regles_dense` l'appelle après le chargement des règles et filtre la liste avant de construire la réponse. `is_acceptable()` inclut désormais `sans_reponse` dans son critère.

**Tech Stack:** Python, langchain-openai (ChatOpenAI), Azure OpenAI (gpt-5.4-mini), tenacity, pytest, FastAPI (TestClient).

## Global Constraints

- Retry LLM : 3 tentatives avec backoff exponentiel (2s/4s/8s), `reraise=True` puis capté par l'appelant — même convention que `DecompositionClient`.
- Fail-open : `JugementClient.juger()` ne lève jamais d'exception — après 3 échecs, retourne tous les candidats non filtrés.
- Un numéro halluciné par le LLM (absent du pool de candidats fournis) est filtré silencieusement, jamais retourné.
- Le contrat `response_model=list[RegleAvecScore]` de `/regles/dense` ne change pas de forme — seule la liste retournée change (filtrée).
- `200 + []` ne doit signifier qu'une seule chose (refus explicite) — jamais une panne technique déguisée. Toute panne (recherche vectorielle, construction des clients) continue de remonter en `503`, avant même d'atteindre le jugement.
- Traçage : `CHANGELOG.md` à la fin de ce plan.

---

## Contexte technique déjà vérifié dans le code

- `app/retrieval/decomposition.py::DecompositionClient` est le patron à reproduire : `ChatOpenAI` construit dans `__init__` (`base_url`/`api_key` depuis l'env, `model` depuis `os.getenv(role["env_var"])`, `timeout=2`), `JsonOutputParser(pydantic_object=...)`, méthode privée `_appeler_llm` décorée `@retry(stop_after_attempt(3), wait_exponential(multiplier=2, min=2, max=8), reraise=True)`, méthode publique qui capte l'exception et fail-open. Compteurs `input_tokens`/`output_tokens` alimentés depuis `response.usage_metadata`.
- `app/ingestion/manifest.yml:49-59` porte le rôle `decomposition` (`gpt-5.4-mini`, `env_var: AZURE_MODEL_GPT_MINI`, prix). Le nouveau rôle `jugement` réutilise le **même** modèle et la **même** variable d'environnement (même déploiement Azure, deux prompts différents) — pas de nouveau secret à configurer.
- `app/ingestion/chunking.py::build_chunk_text(rule) -> str` construit le texte complet d'une règle à partir d'un objet portant `intitule`/`theme`/`contexte`/`solution`/`controle`/`guide_analyse`/`objectifs`/`tags`/`phases`. `app/api_regles/schemas.py::RegleRead` porte exactement ces attributs — compatible, mais **ce plan découple `JugementClient` de `RegleRead`** : `juger()` prend `list[tuple[int, str]]` (numéro, texte déjà construit), pas des objets `RegleRead` — plus simple à tester unitairement (pas besoin de construire un `RegleRead` complet dans les tests), et l'appelant (l'endpoint) reste seul responsable de choisir comment construire ce texte.
- `app/api_regles/regles.py:258-305` porte `chercher_regles_dense` : après `retrieve()` (dans un `try/except` qui remonte `503`), charge `regles_triees: list[RegleRead]` (déjà triées dans l'ordre de pertinence), puis construit `list[RegleAvecScore]`. Ce plan insère le jugement **après** ce tri, **avant** la construction de la réponse — donc après le `try/except` de `retrieve()` (le jugement ne doit jamais provoquer un `503` : il ne lève jamais, par construction).
- `tests/integration/api_regles/test_regles_dense.py` mocke déjà `retrieve`, `DecompositionClient`, `EmbeddingClient` sur les tests qui vont jusqu'au bout du chemin de succès (leurs `__init__` appellent `ChatOpenAI`/`OpenAI`, qui échouent sans secrets Azure — absents de la CI). Seuls 2 tests existants vont jusqu'au bout du chemin de succès et doivent ajouter un mock de `JugementClient` : `test_dense_retourne_les_regles_dans_l_ordre_de_pertinence` et `test_dense_journalise_la_question_et_le_client`. Les autres tests existants (401, 422, 503 sur `retrieve()`, 503 sur construction de `DecompositionClient`) échouent **avant** d'atteindre le jugement — aucun changement nécessaire sur ceux-là.
- `app/ingestion/rag_acceptance.py:502-514` porte `is_acceptable()`, qui ignore aujourd'hui la famille `sans_reponse` (boucle `if famille == "sans_reponse": continue`).
- `scripts/check_api_regles_dense_acceptance.py` rejoue les 114 cas via `POST /regles/dense` en HTTP réel (nécessite `make api-regles` dans un terminal dédié) — c'est l'outil de validation finale de ce chantier, déjà existant, aucune modification de code nécessaire.

---

### Task 1 : `JugementClient` — client LLM de jugement de pertinence

**Files:**
- Create: `app/retrieval/jugement.py`
- Create: `app/retrieval/prompts/juger_pertinence.md`
- Modify: `app/ingestion/manifest.yml` (ajout du rôle `jugement`)
- Test: `tests/unit/retrieval/test_jugement.py`

**Interfaces:**
- Produces: `JugementClient.juger(question: str, candidats: list[tuple[int, str]]) -> list[int]`. `candidats` : liste de `(numéro, texte du chunk)`. Retourne les numéros jugés pertinents (sous-ensemble des numéros de `candidats`, jamais un numéro absent), `[]` si aucun. Ne lève jamais d'exception (fail-open interne).

- [ ] **Step 1 : Écrire le prompt**

Créer `app/retrieval/prompts/juger_pertinence.md` :

```markdown
Tu es un module de filtrage pour un moteur de question-réponse qui
s'appuie sur un référentiel de 245 règles de qualité web (Opquast). Une
recherche sémantique a déjà sélectionné les règles ci-dessous comme
candidates possibles à une question — certaines peuvent ne pas répondre
réellement à la question : la recherche sémantique retourne toujours
des candidats, même hors sujet.

Ta tâche : parmi les règles candidates ci-dessous, indique lesquelles
répondent réellement à la question posée.

- Si une ou plusieurs règles répondent réellement, renvoie leurs numéros.
- Si aucune règle candidate ne répond réellement à la question, renvoie
  une liste vide.
- Ne renvoie jamais un numéro qui n'apparaît pas dans les règles
  candidates ci-dessous.

## Question posée

{question}

## Règles candidates

{candidats}

Réponds uniquement avec un objet JSON de la forme
{"numeros_pertinents": [12, 45]} (ou {"numeros_pertinents": []} si
aucune règle candidate ne répond réellement), sans aucun texte avant ou
après.
```

- [ ] **Step 2 : Ajouter le rôle `jugement` au manifeste**

Ajouter à la fin de `app/ingestion/manifest.yml` :

```yaml

jugement:
  modele: gpt-5.4-mini
  env_var: AZURE_MODEL_GPT_MINI
  # Meme modele/variable d'environnement que le role decomposition (meme
  # deploiement Azure, prompt different) - juge la pertinence des
  # candidats retournes par retrieve() avant citation. Voir
  # docs/superpowers/specs/2026-09-11-retrieval-refus-temps2-design.md.
  prix_entree_par_million: 0.15
  prix_sortie_par_million: 0.60
```

- [ ] **Step 3 : Écrire les tests (ils doivent échouer)**

Créer `tests/unit/retrieval/test_jugement.py` :

```python
"""
Tests unitaires pour app/retrieval/jugement.py

Teste le jugement LLM de pertinence des candidats — LLM entièrement
mocké, même patron que tests/unit/retrieval/test_decomposition.py.
"""

from unittest.mock import MagicMock, patch

from app.retrieval.jugement import JugementClient


def _mock_response(numeros_pertinents: list[int], input_tokens: int, output_tokens: int):
    response = MagicMock()
    numeros_json = ", ".join(str(n) for n in numeros_pertinents)
    response.content = f'{{"numeros_pertinents": [{numeros_json}]}}'
    response.usage_metadata = {"input_tokens": input_tokens, "output_tokens": output_tokens}
    return response


class TestJugementClient:
    """Tests du client de jugement."""

    @patch("app.retrieval.jugement.ChatOpenAI")
    def test_juger_retient_les_numeros_pertinents(self, mock_llm_class):
        """Les numéros jugés pertinents par le LLM sont retournés."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _mock_response(
            [12], input_tokens=200, output_tokens=10
        )

        client = JugementClient()
        resultat = client.juger(
            "Question ?", [(12, "Texte de la règle 12"), (45, "Texte de la règle 45")]
        )

        assert resultat == [12]
        assert client.input_tokens == 200
        assert client.output_tokens == 10

    @patch("app.retrieval.jugement.ChatOpenAI")
    def test_juger_liste_vide_si_aucun_candidat_pertinent(self, mock_llm_class):
        """Aucun candidat pertinent : liste vide (refus)."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _mock_response(
            [], input_tokens=200, output_tokens=5
        )

        client = JugementClient()
        resultat = client.juger("Question hors sujet ?", [(12, "Texte de la règle 12")])

        assert resultat == []

    @patch("app.retrieval.jugement.ChatOpenAI")
    def test_juger_filtre_un_numero_hallucine_hors_du_pool(self, mock_llm_class):
        """Un numéro halluciné par le LLM, absent des candidats fournis, est filtré."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = _mock_response(
            [12, 999], input_tokens=200, output_tokens=10
        )

        client = JugementClient()
        resultat = client.juger("Question ?", [(12, "Texte de la règle 12")])

        assert resultat == [12]

    @patch("tenacity.nap.time.sleep")
    @patch("app.retrieval.jugement.ChatOpenAI")
    def test_juger_reessaie_puis_reussit(self, mock_llm_class, mock_sleep):
        """Réessaie après échec, puis réussit (3 tentatives max)."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.side_effect = [
            TimeoutError("Request timed out"),
            TimeoutError("Request timed out"),
            _mock_response([12], input_tokens=200, output_tokens=10),
        ]

        client = JugementClient()
        resultat = client.juger("Question ?", [(12, "Texte de la règle 12")])

        assert mock_llm_instance.invoke.call_count == 3
        assert mock_sleep.call_count == 2
        assert resultat == [12]

    @patch("tenacity.nap.time.sleep")
    @patch("app.retrieval.jugement.ChatOpenAI")
    def test_juger_fail_open_apres_3_echecs(self, mock_llm_class, mock_sleep):
        """Après 3 échecs, retombe sur tous les candidats non filtrés."""
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.side_effect = TimeoutError("Request timed out")

        client = JugementClient()
        resultat = client.juger(
            "Question ?", [(12, "Texte de la règle 12"), (45, "Texte de la règle 45")]
        )

        assert mock_llm_instance.invoke.call_count == 3
        assert resultat == [12, 45]
```

- [ ] **Step 4 : Lancer les tests, vérifier qu'ils échouent**

Run: `uv run pytest tests/unit/retrieval/test_jugement.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.retrieval.jugement'`)

- [ ] **Step 5 : Implémenter `JugementClient`**

Créer `app/retrieval/jugement.py` :

```python
"""
Client LLM pour le jugement de pertinence des candidats retrouvés par le
retrieval (Temps 2 du mécanisme de refus). Voir
docs/superpowers/specs/2026-09-11-retrieval-refus-temps2-design.md.
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

PROMPT_PATH = Path(__file__).parent / "prompts" / "juger_pertinence.md"


class JugementOutput(BaseModel):
    """Structure attendue de la réponse LLM."""

    numeros_pertinents: list[int]


class JugementClient:
    """Client pour le jugement LLM de pertinence des candidats retrouvés."""

    def __init__(self):
        """Initialise le client Azure OpenAI (rôle jugement, timeout 2s)."""
        manifest = load_manifest()
        role = manifest["jugement"]

        self.llm = ChatOpenAI(
            base_url=os.getenv("AZURE_AI_ENDPOINT"),
            api_key=os.getenv("AZURE_AI_API_KEY"),
            model=os.getenv(role["env_var"]),
            timeout=2,
        )
        self.parser = JsonOutputParser(pydantic_object=JugementOutput)
        self.input_tokens = 0
        self.output_tokens = 0

    def _construire_prompt(self, question: str, candidats: list[tuple[int, str]]) -> str:
        with open(PROMPT_PATH, encoding="utf-8") as f:
            prompt_text = f.read()
        candidats_texte = "\n\n".join(
            f"### Règle {numero}\n{texte}" for numero, texte in candidats
        )
        prompt_text = prompt_text.replace("{question}", question)
        prompt_text = prompt_text.replace("{candidats}", candidats_texte)
        return prompt_text

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        reraise=True,
    )
    def _appeler_llm(self, question: str, candidats: list[tuple[int, str]]) -> list[int]:
        prompt = self._construire_prompt(question, candidats)
        response = self.llm.invoke(prompt)
        parsed = self.parser.parse(response.content)

        usage = response.usage_metadata or {}
        self.input_tokens += usage.get("input_tokens", 0)
        self.output_tokens += usage.get("output_tokens", 0)

        return parsed["numeros_pertinents"]

    def juger(self, question: str, candidats: list[tuple[int, str]]) -> list[int]:
        """Juge lesquels des candidats répondent vraiment à la question.

        Retourne les numéros jugés pertinents (liste vide si aucun). Un
        numéro halluciné par le LLM hors du pool de candidats fournis
        est filtré silencieusement. Retente automatiquement jusqu'à 3
        fois en cas d'erreur, avec backoff exponentiel (2s, 4s, 8s).
        Après 3 échecs, fail-open : retourne tous les candidats non
        filtrés plutôt que de refuser par accident technique.
        """
        numeros_valides = {numero for numero, _ in candidats}
        try:
            numeros_juges = self._appeler_llm(question, candidats)
            return [n for n in numeros_juges if n in numeros_valides]
        except Exception:
            logger.warning(
                f"jugement : échec après 3 tentatives pour « {question} », "
                "fail-open (candidats non filtrés)"
            )
            return [numero for numero, _ in candidats]
```

- [ ] **Step 6 : Lancer les tests, vérifier qu'ils passent**

Run: `uv run pytest tests/unit/retrieval/test_jugement.py -v`
Expected: PASS (5 tests)

- [ ] **Step 7 : Lint**

Run: `uv run ruff check app/retrieval/jugement.py tests/unit/retrieval/test_jugement.py`
Expected: `All checks passed!`

- [ ] **Step 8 : Commit**

```bash
git add app/retrieval/jugement.py app/retrieval/prompts/juger_pertinence.md app/ingestion/manifest.yml tests/unit/retrieval/test_jugement.py
git commit -m "feat: JugementClient, jugement LLM de pertinence des candidats retrouves"
```

---

### Task 2 : Intégration dans `POST /regles/dense`

**Files:**
- Modify: `app/api_regles/regles.py:258-305` (endpoint `chercher_regles_dense`)
- Modify: `tests/integration/api_regles/test_regles_dense.py`

**Interfaces:**
- Consumes: `JugementClient.juger(question, candidats) -> list[int]` (Task 1) ; `build_chunk_text` (existant, `app.ingestion.chunking`).

- [ ] **Step 1 : Ajouter les imports nécessaires**

Dans `app/api_regles/regles.py`, ajouter aux imports existants :

```python
from app.ingestion.chunking import build_chunk_text
from app.retrieval.jugement import JugementClient
```

- [ ] **Step 2 : Modifier l'endpoint**

Remplacer, dans `chercher_regles_dense` :

```python
    numeros = [numero for numero, _ in resultat]
    scores = dict(resultat)

    requete_orm = session.query(Regle, Theme.theme).filter(
        Theme.id == Regle.theme_id, Regle.numero.in_(numeros)
    )
    regles = _charger_regles(session, requete_orm)

    # Réordonne selon l'ordre de pertinence de retrieve() — la requête SQL
    # IN (...) ne garantit aucun ordre.
    position = {numero: i for i, numero in enumerate(numeros)}
    regles_triees = sorted(regles, key=lambda r: position[r.numero])
    return [RegleAvecScore(regle=r, score=scores[r.numero]) for r in regles_triees]
```

par :

```python
    numeros = [numero for numero, _ in resultat]
    scores = dict(resultat)

    requete_orm = session.query(Regle, Theme.theme).filter(
        Theme.id == Regle.theme_id, Regle.numero.in_(numeros)
    )
    regles = _charger_regles(session, requete_orm)

    # Réordonne selon l'ordre de pertinence de retrieve() — la requête SQL
    # IN (...) ne garantit aucun ordre.
    position = {numero: i for i, numero in enumerate(numeros)}
    regles_triees = sorted(regles, key=lambda r: position[r.numero])

    # Jugement LLM de pertinence — filtre le pool brut retourné par
    # retrieve() avant citation. Ne lève jamais (fail-open interne à
    # JugementClient) : jamais de 503 provoqué ici. Voir
    # docs/superpowers/specs/2026-09-11-retrieval-refus-temps2-design.md.
    jugement_client = JugementClient()
    candidats = [(r.numero, build_chunk_text(r)) for r in regles_triees]
    numeros_pertinents = set(jugement_client.juger(requete.question, candidats))
    regles_retenues = [r for r in regles_triees if r.numero in numeros_pertinents]

    return [RegleAvecScore(regle=r, score=scores[r.numero]) for r in regles_retenues]
```

Mettre à jour aussi la docstring de `chercher_regles_dense` — remplacer :

```python
    """
    Recherche sémantique : décompose la question, vectorise, interroge
    pgvector, fusionne. Voir app/retrieval/retrieval.py::retrieve().

    Chaque appel a un coût réel (LLM + embedding) — jeton Bearer requis,
    contrairement aux autres lectures de ce router. Le score de similarité
    (1 - distance cosinus) est renvoyé pour chaque règle.
    """
```

par :

```python
    """
    Recherche sémantique : décompose la question, vectorise, interroge
    pgvector, fusionne, puis un jugement LLM filtre les candidats
    réellement pertinents (liste vide si aucun — refus explicite). Voir
    app/retrieval/retrieval.py::retrieve() et
    app/retrieval/jugement.py::JugementClient.

    Chaque appel a un coût réel (LLM décomposition + embedding + LLM
    jugement) — jeton Bearer requis, contrairement aux autres lectures
    de ce router. Le score de similarité (1 - distance cosinus) reste
    renvoyé pour chaque règle citée, à titre informatif — ce n'est plus
    le critère de pertinence.
    """
```

- [ ] **Step 3 : Mettre à jour les 2 tests existants qui vont jusqu'au bout du chemin de succès**

Dans `tests/integration/api_regles/test_regles_dense.py`, remplacer :

```python
@patch("app.api_regles.regles.EmbeddingClient")
@patch("app.api_regles.regles.DecompositionClient")
@patch("app.api_regles.regles.retrieve")
def test_dense_retourne_les_regles_dans_l_ordre_de_pertinence(
    mock_retrieve, mock_decomposition_client, mock_embedding_client, client, jeu_de_regles
):
    """La réponse suit l'ordre de retrieve(), pas l'ordre numéro, et embarque le score.

    DecompositionClient/EmbeddingClient sont mockés en plus de retrieve() :
    l'endpoint les construit pour de vrai avant d'appeler retrieve(), et leur
    __init__ appelle ChatOpenAI/OpenAI (échoue sans les secrets Azure, absents
    de la CI par construction).
    """
    mock_retrieve.return_value = [(3, 0.8), (1, 0.5)]

    reponse = client.post(
        "/regles/dense",
        json={"question": "Question de test"},
        headers=_entetes(),
    )

    assert reponse.status_code == 200
    corps = reponse.json()
    assert [item["regle"]["numero"] for item in corps] == [3, 1]
    assert [item["score"] for item in corps] == [0.8, 0.5]
```

par :

```python
@patch("app.api_regles.regles.JugementClient")
@patch("app.api_regles.regles.EmbeddingClient")
@patch("app.api_regles.regles.DecompositionClient")
@patch("app.api_regles.regles.retrieve")
def test_dense_retourne_les_regles_dans_l_ordre_de_pertinence(
    mock_retrieve,
    mock_decomposition_client,
    mock_embedding_client,
    mock_jugement_client,
    client,
    jeu_de_regles,
):
    """La réponse suit l'ordre de retrieve(), pas l'ordre numéro, et embarque le score.

    DecompositionClient/EmbeddingClient/JugementClient sont mockés en plus de
    retrieve() : l'endpoint les construit pour de vrai avant/après retrieve(),
    et leur __init__ appelle ChatOpenAI/OpenAI (échoue sans les secrets Azure,
    absents de la CI par construction). JugementClient.juger() retourne les 2
    numéros pour que ce test vérifie l'ordre/le score, pas le filtrage (voir
    test_dense_filtre_les_regles_non_pertinentes pour le filtrage).
    """
    mock_retrieve.return_value = [(3, 0.8), (1, 0.5)]
    mock_jugement_client.return_value.juger.return_value = [3, 1]

    reponse = client.post(
        "/regles/dense",
        json={"question": "Question de test"},
        headers=_entetes(),
    )

    assert reponse.status_code == 200
    corps = reponse.json()
    assert [item["regle"]["numero"] for item in corps] == [3, 1]
    assert [item["score"] for item in corps] == [0.8, 0.5]
```

Puis remplacer :

```python
@patch("app.api_regles.regles.EmbeddingClient")
@patch("app.api_regles.regles.DecompositionClient")
@patch("app.api_regles.regles.retrieve")
def test_dense_journalise_la_question_et_le_client(
    mock_retrieve, mock_decomposition_client, mock_embedding_client, client, jeu_de_regles, caplog
):
    mock_retrieve.return_value = [(1, 0.9)]

    with caplog.at_level("INFO", logger="app.api_regles.regles"):
        client.post(
            "/regles/dense",
            json={"question": "Question de test"},
            headers=_entetes(),
        )

    assert "dev" in caplog.text
    assert "Question de test" in caplog.text
```

par :

```python
@patch("app.api_regles.regles.JugementClient")
@patch("app.api_regles.regles.EmbeddingClient")
@patch("app.api_regles.regles.DecompositionClient")
@patch("app.api_regles.regles.retrieve")
def test_dense_journalise_la_question_et_le_client(
    mock_retrieve,
    mock_decomposition_client,
    mock_embedding_client,
    mock_jugement_client,
    client,
    jeu_de_regles,
    caplog,
):
    mock_retrieve.return_value = [(1, 0.9)]
    mock_jugement_client.return_value.juger.return_value = [1]

    with caplog.at_level("INFO", logger="app.api_regles.regles"):
        client.post(
            "/regles/dense",
            json={"question": "Question de test"},
            headers=_entetes(),
        )

    assert "dev" in caplog.text
    assert "Question de test" in caplog.text
```

- [ ] **Step 4 : Ajouter 2 nouveaux tests (filtrage et refus)**

Ajouter à la fin de `tests/integration/api_regles/test_regles_dense.py` :

```python
@patch("app.api_regles.regles.JugementClient")
@patch("app.api_regles.regles.EmbeddingClient")
@patch("app.api_regles.regles.DecompositionClient")
@patch("app.api_regles.regles.retrieve")
def test_dense_filtre_les_regles_non_pertinentes(
    mock_retrieve,
    mock_decomposition_client,
    mock_embedding_client,
    mock_jugement_client,
    client,
    jeu_de_regles,
):
    """Le jugement LLM peut retenir un sous-ensemble strict des candidats
    retournés par retrieve() — la règle 3 est écartée."""
    mock_retrieve.return_value = [(3, 0.8), (1, 0.5)]
    mock_jugement_client.return_value.juger.return_value = [1]

    reponse = client.post(
        "/regles/dense",
        json={"question": "Question de test"},
        headers=_entetes(),
    )

    assert reponse.status_code == 200
    corps = reponse.json()
    assert [item["regle"]["numero"] for item in corps] == [1]


@patch("app.api_regles.regles.JugementClient")
@patch("app.api_regles.regles.EmbeddingClient")
@patch("app.api_regles.regles.DecompositionClient")
@patch("app.api_regles.regles.retrieve")
def test_dense_jugement_vide_donne_200_liste_vide(
    mock_retrieve,
    mock_decomposition_client,
    mock_embedding_client,
    mock_jugement_client,
    client,
    jeu_de_regles,
):
    """Aucun candidat jugé pertinent : 200 avec une liste vide (refus
    explicite), pas une erreur."""
    mock_retrieve.return_value = [(3, 0.8), (1, 0.5)]
    mock_jugement_client.return_value.juger.return_value = []

    reponse = client.post(
        "/regles/dense",
        json={"question": "Question hors sujet"},
        headers=_entetes(),
    )

    assert reponse.status_code == 200
    assert reponse.json() == []
```

- [ ] **Step 5 : Lancer les tests d'intégration**

Nécessite `qualicheck-postgres` démarré et `POSTGRES_TEST_DB` migrée.

Run: `uv run pytest tests/integration/api_regles/test_regles_dense.py -v`
Expected: PASS (7 tests : 5 existants adaptés/inchangés + 2 nouveaux)

- [ ] **Step 6 : Lint**

Run: `uv run ruff check app/api_regles/regles.py tests/integration/api_regles/test_regles_dense.py`
Expected: `All checks passed!`

- [ ] **Step 7 : Commit**

```bash
git add app/api_regles/regles.py tests/integration/api_regles/test_regles_dense.py
git commit -m "feat: integre le jugement LLM dans POST /regles/dense"
```

---

### Task 3 : `is_acceptable()` inclut désormais `sans_reponse`

**Files:**
- Modify: `app/ingestion/rag_acceptance.py:502-514`
- Modify: `tests/unit/ingestion/test_rag_acceptance.py`

**Interfaces:**
- Produces (signature inchangée) : `is_acceptable(taux_par_famille: dict[str, dict], seuil: float) -> bool` — ne traite plus `sans_reponse` différemment des autres familles.

- [ ] **Step 1 : Remplacer le test existant (il doit échouer après le Step 2, réussir après le Step 3)**

Dans `tests/unit/ingestion/test_rag_acceptance.py`, remplacer :

```python
def test_is_acceptable_ignores_sans_reponse_famille():
    """La famille sans_reponse n'entre jamais dans le calcul, même à 0%."""
    taux_par_famille = {
        "vocabulaire_source_opquast": {"taux": 1.0, "reussis": 4, "total": 4, "partiels": 0},
        "sans_reponse": {"taux": 0.0, "reussis": 0, "total": 2, "partiels": 0},
    }

    assert is_acceptable(taux_par_famille, seuil=0.8) is True
```

par :

```python
def test_is_acceptable_sans_reponse_compte_comme_les_autres():
    """Depuis le Temps 2 du mécanisme de refus, sans_reponse est une
    famille comme les autres : sous le seuil, elle fait échouer le jeu."""
    taux_par_famille = {
        "vocabulaire_source_opquast": {"taux": 1.0, "reussis": 4, "total": 4, "partiels": 0},
        "sans_reponse": {"taux": 0.0, "reussis": 0, "total": 2, "partiels": 0},
    }

    assert is_acceptable(taux_par_famille, seuil=0.8) is False


def test_is_acceptable_sans_reponse_au_seuil_est_accepte():
    """sans_reponse au-dessus du seuil n'empêche pas l'acceptation."""
    taux_par_famille = {
        "vocabulaire_source_opquast": {"taux": 1.0, "reussis": 4, "total": 4, "partiels": 0},
        "sans_reponse": {"taux": 0.9, "reussis": 18, "total": 20, "partiels": 0},
    }

    assert is_acceptable(taux_par_famille, seuil=0.8) is True
```

- [ ] **Step 2 : Lancer les tests, vérifier que le nouveau test échoue**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -v -k is_acceptable`
Expected: `test_is_acceptable_sans_reponse_compte_comme_les_autres` FAIL (l'implémentation actuelle ignore encore `sans_reponse`, retourne `True`)

- [ ] **Step 3 : Modifier `is_acceptable()`**

Dans `app/ingestion/rag_acceptance.py`, remplacer :

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

par :

```python
def is_acceptable(taux_par_famille: dict[str, dict], seuil: float) -> bool:
    """Le jeu est acceptable si chaque famille atteint le seuil.

    Depuis le Temps 2 du mécanisme de refus (jugement LLM,
    docs/superpowers/specs/2026-09-11-retrieval-refus-temps2-design.md),
    "sans_reponse" est une famille comme les autres : un vrai mécanisme
    existe désormais pour la traiter, elle n'est plus exclue par
    construction.
    """
    for stats in taux_par_famille.values():
        if stats["taux"] < seuil:
            return False
    return True
```

- [ ] **Step 4 : Lancer les tests, vérifier qu'ils passent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -v`
Expected: PASS (toutes les assertions, y compris les 2 nouvelles)

- [ ] **Step 5 : Lint**

Run: `uv run ruff check app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py`
Expected: `All checks passed!`

- [ ] **Step 6 : Commit**

```bash
git add app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py
git commit -m "feat: is_acceptable inclut desormais sans_reponse dans le critere"
```

---

### Task 4 : Exécuter l'acceptance réelle (coût réel, hors CI) — étape manuelle

**Pas de code produit par cette tâche.**

- [ ] **Step 1 : Lancer la suite complète (unitaires + intégration)**

Run: `uv run pytest tests/unit tests/integration -q`
Expected: tous les tests passent (y compris les nouveaux des Tasks 1-3).

- [ ] **Step 2 : Démarrer l'API dans un terminal dédié**

Run: `make api-regles`
Expected: l'API écoute sur le port du manifeste (`app/api_regles/manifest.yml`).

- [ ] **Step 3 : Confirmer le coût avec David avant de lancer**

Ce run coûte réellement de l'argent (décomposition + embedding + jugement pour chacun des 114 cas, un ordre de grandeur comparable aux mesures précédentes ~0,01-0,02 €) — redemander confirmation explicite au moment de l'exécuter.

- [ ] **Step 4 : Lancer l'acceptance réelle**

Run (dans un second terminal) : `make api-regles-dense-acceptance`
Expected : un rapport écrit dans `docs/eval/` avec le taux de réussite par famille, y compris `sans_reponse` désormais mesurée pour de vrai.

- [ ] **Step 5 : Lire la conclusion**

Vérifier si `sans_reponse` et les autres familles atteignent le seuil garde-fou (90 %, `taux_reussite_minimum` du manifeste). Si `sans_reponse` échoue : regarder si ce sont des faux refus (règle valide non citée) ou des vrais manques (règle jamais dans le pool initial, hors périmètre de ce mécanisme).

- [ ] **Step 6 : Tracer dans CHANGELOG.md**

Ajouter une entrée `## [date] — Claude Code` résumant : le mécanisme implémenté, le coût réel observé, le taux par famille (en particulier `sans_reponse`), et la conclusion (mécanisme adopté / à ajuster).

- [ ] **Step 7 : Mettre à jour TODO.md et la mémoire assistant**

Dans `TODO.md`, passer "Temps 2 (construction)" de `[ ]` à `[x]` avec un résumé du résultat. Mettre à jour la mémoire assistant si pertinent (le chantier retrieval/refus est alors clos dans son intégralité, Temps 1 + Temps 2).

---

## Self-Review (déjà appliqué en rédigeant ce plan)

- **Couverture de la spec** : `JugementClient` avec sortie structurée, fail-open, garde-fou anti-hallucination de numéro (Task 1) ; intégration dans `/regles/dense` modifié en place, contrat `RegleAvecScore` inchangé de forme, score cosinus conservé (Task 2) ; `200 + []` = refus explicite jamais confondu avec une panne (Task 2, le jugement ne peut jamais lever) ; `is_acceptable()` sans exclusion de `sans_reponse` (Task 3) ; validation par exécution réelle sur les 114 cas via `/regles/dense` (Task 4) — tout couvert. Hors périmètre respecté : aucune modification de `retrieve()`, aucun classement/score de pertinence ajouté, aucune touche à la couche agent.
- **Cohérence des types** : `JugementClient.juger(question: str, candidats: list[tuple[int, str]]) -> list[int]` cohérent entre sa définition (Task 1) et son usage dans l'endpoint (Task 2, `candidats = [(r.numero, build_chunk_text(r)) for r in regles_triees]`) ; `is_acceptable(taux_par_famille: dict[str, dict], seuil: float) -> bool` signature inchangée (Task 3).
- **Pas de placeholder** : le code complet de `JugementClient`, du prompt, et des modifications de l'endpoint est donné intégralement dans les tâches, pas de fonction esquissée.
