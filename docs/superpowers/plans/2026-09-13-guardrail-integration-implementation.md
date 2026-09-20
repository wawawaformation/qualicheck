# Guardrail de périmètre — intégration en premier maillon d'`api_regles` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Intégrer `GuardrailClient` (déjà écrit et mesuré à 100%/97,9% isolément) comme premier maillon de `POST /regles/dense` — hors périmètre, retour `[]` immédiat sans appeler décomposition/retrieval/jugement — et alléger le prompt de `JugementClient` en conséquence (son rôle se réduit à la sélection parmi des candidats déjà dans le périmètre).

**Architecture:** `chercher_regles_dense` appelle `GuardrailClient().est_dans_le_perimetre(question)` juste après son log initial, avant même `top_n`. Construction et appel du guardrail sont englobés dans un petit `try/except` qui fail-open (considère la question dans le périmètre) en cas de panne — jamais un 500 brut, jamais un refus par accident technique. Le reste de la fonction (decompose/retrieve/jugement) est strictement inchangé si la question est dans le périmètre.

**Tech Stack:** Python, FastAPI, pytest (TestClient), unittest.mock.

## Global Constraints

- `GuardrailClient.est_dans_le_perimetre()` ne lève jamais (fail-open interne déjà testé, `tests/unit/retrieval/test_guardrail.py`) — mais **sa construction** (`GuardrailClient()`) peut lever, comme `DecompositionClient()` l'a fait en staging le 2026-09-10 (secret Azure manquant). Ce plan couvre ce cas explicitement — la spec ne le prévoyait pas.
- Le contrat `response_model=list[RegleAvecScore]` de `/regles/dense` ne change pas de forme.
- `200 + []` ne doit signifier qu'une seule chose (refus explicite du guardrail ou du jugement) — jamais une panne technique déguisée.
- Traçage : `CHANGELOG.md` à la fin de ce plan.

---

## Contexte technique déjà vérifié dans le code

- `app/api_regles/regles.py::chercher_regles_dense` (état actuel, vérifié) :
  ```python
  def chercher_regles_dense(...) -> list[RegleAvecScore]:
      """..."""
      top_n = load_manifest()["rag_acceptance"]["top_n"]

      logger.info("Recherche dense par %s : « %s »", client_nom, requete.question)

      try:
          decomposition_client = DecompositionClient()
          embedding_client = EmbeddingClient()
          resultat = retrieve(...)
      except Exception as e:
          logger.error("Recherche dense — échec (%s)", e)
          raise HTTPException(status_code=503, detail="Recherche sémantique indisponible") from e

      numeros = [numero for numero, _ in resultat]
      scores = dict(resultat)
      requete_orm = session.query(Regle, Theme.theme).filter(...)
      regles = _charger_regles(session, requete_orm)
      position = {numero: i for i, numero in enumerate(numeros)}
      regles_triees = sorted(regles, key=lambda r: position[r.numero])

      jugement_client = JugementClient()
      candidats = [(r.numero, build_chunk_text(r)) for r in regles_triees]
      numeros_pertinents = set(jugement_client.juger(requete.question, candidats))
      regles_retenues = [r for r in regles_triees if r.numero in numeros_pertinents]

      return [RegleAvecScore(regle=r, score=scores[r.numero]) for r in regles_retenues]
  ```
- Imports actuels de `app/api_regles/regles.py` (ordre alphabétique dans le bloc `app.retrieval`) :
  `from app.retrieval.decomposition import DecompositionClient` puis
  `from app.retrieval.jugement import JugementClient` puis
  `from app.retrieval.retrieval import retrieve`.
- `app/retrieval/guardrail.py::GuardrailClient.est_dans_le_perimetre(question: str) -> bool` existe déjà (fail-open interne sur échec d'appel après 3 tentatives). Son `__init__` lit `load_manifest()["guardrail"]` puis construit `ChatOpenAI(...)` — même surface de panne que `DecompositionClient.__init__` (variable d'env absente, etc.), qui a causé un `500` brut en staging avant d'être corrigé (`test_dense_echec_construction_client_donne_503`, existant).
- `tests/integration/api_regles/test_regles_dense.py` a 8 tests. `test_dense_sans_jeton_donne_401` et `test_dense_question_vide_donne_422` échouent avant le corps de la fonction (dépendances FastAPI : auth et validation Pydantic) — **aucun changement nécessaire** sur ces deux-là. Les 6 autres vont jusqu'au corps de la fonction et ont besoin d'un mock `GuardrailClient` supplémentaire pour ne pas construire un vrai client Azure (échoue sans secrets, absents de la CI) :
  `test_dense_retourne_les_regles_dans_l_ordre_de_pertinence`,
  `test_dense_echec_retrieve_donne_503`,
  `test_dense_echec_construction_client_donne_503`,
  `test_dense_journalise_la_question_et_le_client`,
  `test_dense_filtre_les_regles_non_pertinentes`,
  `test_dense_jugement_vide_donne_200_liste_vide`.
- `app/retrieval/prompts/juger_pertinence.md` contient actuellement des exemples sur la distinction Opquast-organisme/VPTCS/gestion de projet — à retirer (rôle transféré au guardrail). Aucun test n'assert sur le contenu littéral de ce fichier (recherché, confirmé absent).
- `app/ingestion/rag_acceptance.py::is_acceptable()` exclut actuellement `sans_reponse` de son seuil garde-fou (`if famille == "sans_reponse": continue`).

---

### Task 1 : Guardrail en premier maillon de `chercher_regles_dense`

**Files:**
- Modify: `app/api_regles/regles.py`
- Modify: `tests/integration/api_regles/test_regles_dense.py`

**Interfaces:**
- Consumes: `GuardrailClient.est_dans_le_perimetre(question: str) -> bool` (existant, `app/retrieval/guardrail.py`).

- [ ] **Step 1 : Écrire les tests (ils doivent échouer)**

Dans `tests/integration/api_regles/test_regles_dense.py`, ajouter `GuardrailClient` au mock de chaque test qui va jusqu'au corps de la fonction. Remplacer les 6 blocs suivants.

Remplacer :

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

par :

```python
@patch("app.api_regles.regles.JugementClient")
@patch("app.api_regles.regles.EmbeddingClient")
@patch("app.api_regles.regles.DecompositionClient")
@patch("app.api_regles.regles.retrieve")
@patch("app.api_regles.regles.GuardrailClient")
def test_dense_retourne_les_regles_dans_l_ordre_de_pertinence(
    mock_guardrail_client,
    mock_retrieve,
    mock_decomposition_client,
    mock_embedding_client,
    mock_jugement_client,
    client,
    jeu_de_regles,
):
    """La réponse suit l'ordre de retrieve(), pas l'ordre numéro, et embarque le score.

    GuardrailClient/DecompositionClient/EmbeddingClient/JugementClient sont
    mockés en plus de retrieve() : l'endpoint les construit pour de vrai
    avant/après retrieve(), et leur __init__ appelle ChatOpenAI/OpenAI (échoue
    sans les secrets Azure, absents de la CI par construction). Le guardrail
    laisse passer (question dans le périmètre) pour que ce test vérifie
    l'ordre/le score, pas le guardrail (voir
    test_dense_guardrail_hors_perimetre_retourne_liste_vide pour ça).
    JugementClient.juger() retourne les 2 numéros pour que ce test vérifie
    l'ordre/le score, pas le filtrage (voir
    test_dense_filtre_les_regles_non_pertinentes pour le filtrage).
    """
    mock_guardrail_client.return_value.est_dans_le_perimetre.return_value = True
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

Remplacer :

```python
@patch("app.api_regles.regles.EmbeddingClient")
@patch("app.api_regles.regles.DecompositionClient")
@patch("app.api_regles.regles.retrieve")
def test_dense_echec_retrieve_donne_503(
    mock_retrieve, mock_decomposition_client, mock_embedding_client, client, jeu_de_regles
):
    mock_retrieve.side_effect = RuntimeError("embedding indisponible")

    reponse = client.post(
        "/regles/dense",
        json={"question": "Question de test"},
        headers=_entetes(),
    )

    assert reponse.status_code == 503
```

par :

```python
@patch("app.api_regles.regles.EmbeddingClient")
@patch("app.api_regles.regles.DecompositionClient")
@patch("app.api_regles.regles.retrieve")
@patch("app.api_regles.regles.GuardrailClient")
def test_dense_echec_retrieve_donne_503(
    mock_guardrail_client,
    mock_retrieve,
    mock_decomposition_client,
    mock_embedding_client,
    client,
    jeu_de_regles,
):
    mock_guardrail_client.return_value.est_dans_le_perimetre.return_value = True
    mock_retrieve.side_effect = RuntimeError("embedding indisponible")

    reponse = client.post(
        "/regles/dense",
        json={"question": "Question de test"},
        headers=_entetes(),
    )

    assert reponse.status_code == 503
```

Remplacer :

```python
@patch("app.api_regles.regles.DecompositionClient")
def test_dense_echec_construction_client_donne_503(
    mock_decomposition_client, client, jeu_de_regles
):
    """Une config manquante (ex. variable d'env absente) donne 503, pas un 500 brut.

    Reproduit le bug staging du 2026-09-10 : AZURE_MODEL_GPT_MINI absent des
    secrets Gitea faisait échouer DecompositionClient() avant le try/except,
    donc un 500 non maîtrisé au lieu du 503 annoncé par cet endpoint.
    """
    mock_decomposition_client.side_effect = RuntimeError("AZURE_MODEL_GPT_MINI manquant")

    reponse = client.post(
        "/regles/dense",
        json={"question": "Question de test"},
        headers=_entetes(),
    )

    assert reponse.status_code == 503
```

par :

```python
@patch("app.api_regles.regles.DecompositionClient")
@patch("app.api_regles.regles.GuardrailClient")
def test_dense_echec_construction_client_donne_503(
    mock_guardrail_client, mock_decomposition_client, client, jeu_de_regles
):
    """Une config manquante (ex. variable d'env absente) donne 503, pas un 500 brut.

    Reproduit le bug staging du 2026-09-10 : AZURE_MODEL_GPT_MINI absent des
    secrets Gitea faisait échouer DecompositionClient() avant le try/except,
    donc un 500 non maîtrisé au lieu du 503 annoncé par cet endpoint.
    """
    mock_guardrail_client.return_value.est_dans_le_perimetre.return_value = True
    mock_decomposition_client.side_effect = RuntimeError("AZURE_MODEL_GPT_MINI manquant")

    reponse = client.post(
        "/regles/dense",
        json={"question": "Question de test"},
        headers=_entetes(),
    )

    assert reponse.status_code == 503
```

Remplacer :

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

par :

```python
@patch("app.api_regles.regles.JugementClient")
@patch("app.api_regles.regles.EmbeddingClient")
@patch("app.api_regles.regles.DecompositionClient")
@patch("app.api_regles.regles.retrieve")
@patch("app.api_regles.regles.GuardrailClient")
def test_dense_journalise_la_question_et_le_client(
    mock_guardrail_client,
    mock_retrieve,
    mock_decomposition_client,
    mock_embedding_client,
    mock_jugement_client,
    client,
    jeu_de_regles,
    caplog,
):
    mock_guardrail_client.return_value.est_dans_le_perimetre.return_value = True
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

Remplacer :

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
```

par :

```python
@patch("app.api_regles.regles.JugementClient")
@patch("app.api_regles.regles.EmbeddingClient")
@patch("app.api_regles.regles.DecompositionClient")
@patch("app.api_regles.regles.retrieve")
@patch("app.api_regles.regles.GuardrailClient")
def test_dense_filtre_les_regles_non_pertinentes(
    mock_guardrail_client,
    mock_retrieve,
    mock_decomposition_client,
    mock_embedding_client,
    mock_jugement_client,
    client,
    jeu_de_regles,
):
    """Le jugement LLM peut retenir un sous-ensemble strict des candidats
    retournés par retrieve() — la règle 3 est écartée."""
    mock_guardrail_client.return_value.est_dans_le_perimetre.return_value = True
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
```

Remplacer :

```python
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

par :

```python
@patch("app.api_regles.regles.JugementClient")
@patch("app.api_regles.regles.EmbeddingClient")
@patch("app.api_regles.regles.DecompositionClient")
@patch("app.api_regles.regles.retrieve")
@patch("app.api_regles.regles.GuardrailClient")
def test_dense_jugement_vide_donne_200_liste_vide(
    mock_guardrail_client,
    mock_retrieve,
    mock_decomposition_client,
    mock_embedding_client,
    mock_jugement_client,
    client,
    jeu_de_regles,
):
    """Aucun candidat jugé pertinent : 200 avec une liste vide (refus
    explicite), pas une erreur. Le guardrail laisse passer (question dans
    le périmètre) — c'est le jugement en aval qui refuse ici, pas le
    guardrail (voir test_dense_guardrail_hors_perimetre_retourne_liste_vide
    pour le refus au guardrail)."""
    mock_guardrail_client.return_value.est_dans_le_perimetre.return_value = True
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

Ajouter à la fin du fichier ces 2 nouveaux tests :

```python
@patch("app.api_regles.regles.JugementClient")
@patch("app.api_regles.regles.EmbeddingClient")
@patch("app.api_regles.regles.DecompositionClient")
@patch("app.api_regles.regles.retrieve")
@patch("app.api_regles.regles.GuardrailClient")
def test_dense_guardrail_hors_perimetre_retourne_liste_vide(
    mock_guardrail_client,
    mock_retrieve,
    mock_decomposition_client,
    mock_embedding_client,
    mock_jugement_client,
    client,
    jeu_de_regles,
    caplog,
):
    """Question hors périmètre selon le guardrail : 200 + [] immédiat, sans
    appeler décomposition/retrieval/jugement (court-circuit complet)."""
    mock_guardrail_client.return_value.est_dans_le_perimetre.return_value = False

    with caplog.at_level("INFO", logger="app.api_regles.regles"):
        reponse = client.post(
            "/regles/dense",
            json={"question": "Quelle est la meilleure recette de tarte ?"},
            headers=_entetes(),
        )

    assert reponse.status_code == 200
    assert reponse.json() == []
    mock_retrieve.assert_not_called()
    mock_decomposition_client.assert_not_called()
    mock_embedding_client.assert_not_called()
    mock_jugement_client.assert_not_called()
    assert "hors périmètre" in caplog.text


@patch("app.api_regles.regles.JugementClient")
@patch("app.api_regles.regles.EmbeddingClient")
@patch("app.api_regles.regles.DecompositionClient")
@patch("app.api_regles.regles.retrieve")
@patch("app.api_regles.regles.GuardrailClient")
def test_dense_echec_construction_guardrail_fail_open(
    mock_guardrail_client,
    mock_retrieve,
    mock_decomposition_client,
    mock_embedding_client,
    mock_jugement_client,
    client,
    jeu_de_regles,
    caplog,
):
    """Une panne du guardrail à la construction (ex. secret Azure manquant,
    comme le bug staging du 2026-09-10 sur DecompositionClient) ne bloque
    jamais la recherche : fail-open, la question est considérée dans le
    périmètre et le reste du pipeline se déroule normalement — la preuve
    recherchée est que la recherche aboutit (200), pas qu'elle échoue.
    DecompositionClient/EmbeddingClient/JugementClient sont mockés pour que
    seule la panne du guardrail soit sous test."""
    mock_guardrail_client.side_effect = RuntimeError("AZURE_MODEL_GPT_MINI manquant")
    mock_retrieve.return_value = [(1, 0.9)]
    mock_jugement_client.return_value.juger.return_value = [1]

    with caplog.at_level("WARNING", logger="app.api_regles.regles"):
        reponse = client.post(
            "/regles/dense",
            json={"question": "Question de test"},
            headers=_entetes(),
        )

    assert reponse.status_code == 200
    assert [item["regle"]["numero"] for item in reponse.json()] == [1]
    assert "guardrail" in caplog.text.lower()
```

- [ ] **Step 2 : Lancer les tests, vérifier qu'ils échouent**

Nécessite `qualicheck-postgres` démarré et `POSTGRES_TEST_DB` migrée.

Run: `uv run pytest tests/integration/api_regles/test_regles_dense.py -v`
Expected: `ImportError`/`AttributeError` sur `GuardrailClient` (pas encore importé dans `app/api_regles/regles.py`), ou échecs des nouveaux tests.

- [ ] **Step 3 : Modifier l'import**

Dans `app/api_regles/regles.py`, remplacer :

```python
from app.retrieval.decomposition import DecompositionClient
from app.retrieval.jugement import JugementClient
from app.retrieval.retrieval import retrieve
```

par :

```python
from app.retrieval.decomposition import DecompositionClient
from app.retrieval.guardrail import GuardrailClient
from app.retrieval.jugement import JugementClient
from app.retrieval.retrieval import retrieve
```

- [ ] **Step 4 : Modifier la docstring et le corps de `chercher_regles_dense`**

Remplacer :

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
    top_n = load_manifest()["rag_acceptance"]["top_n"]

    logger.info("Recherche dense par %s : « %s »", client_nom, requete.question)

    try:
```

par :

```python
    """
    Un guardrail LLM classe d'abord la question dans/hors périmètre
    Opquast (sans candidat) ; hors périmètre, retour immédiat sans
    appeler le reste. Dans le périmètre : décompose la question,
    vectorise, interroge pgvector, fusionne, puis un second jugement LLM
    filtre les candidats réellement pertinents (liste vide si aucun —
    refus explicite). Voir app/retrieval/guardrail.py::GuardrailClient,
    app/retrieval/retrieval.py::retrieve() et
    app/retrieval/jugement.py::JugementClient.

    Chaque appel dans le périmètre a un coût réel (LLM décomposition +
    embedding + LLM jugement, en plus du guardrail) — jeton Bearer
    requis, contrairement aux autres lectures de ce router. Le score de
    similarité (1 - distance cosinus) reste renvoyé pour chaque règle
    citée, à titre informatif — ce n'est plus le critère de pertinence.
    """
    logger.info("Recherche dense par %s : « %s »", client_nom, requete.question)

    try:
        guardrail_client = GuardrailClient()
        dans_le_perimetre = guardrail_client.est_dans_le_perimetre(requete.question)
    except Exception as e:
        logger.warning("Recherche dense — échec du guardrail (%s), fail-open", e)
        dans_le_perimetre = True

    if not dans_le_perimetre:
        logger.info(
            "Recherche dense par %s — question hors périmètre (guardrail), refus direct",
            client_nom,
        )
        return []

    top_n = load_manifest()["rag_acceptance"]["top_n"]

    try:
```

Note : le `try/except` du guardrail est **distinct** de celui qui suit
(`retrieve()`) et **fail-open** (`dans_le_perimetre = True`) plutôt que de
lever un `503` — une panne du guardrail ne doit jamais empêcher une
recherche par ailleurs valide, ni provoquer un refus silencieux. Le
`try/except` existant autour de `retrieve()` continue de lever un `503`
sur ses propres pannes (comportement inchangé).

- [ ] **Step 5 : Lancer les tests, vérifier qu'ils passent**

Run: `uv run pytest tests/integration/api_regles/test_regles_dense.py -v`
Expected: PASS (10 tests : 8 existants adaptés/inchangés + 2 nouveaux)

- [ ] **Step 6 : Lancer la suite complète**

Run: `uv run pytest tests/unit tests/integration -q`
Expected: tous les tests passent, aucune régression ailleurs.

- [ ] **Step 7 : Lint**

Run: `uv run ruff check app/api_regles/regles.py tests/integration/api_regles/test_regles_dense.py`
Expected: `All checks passed!`

- [ ] **Step 8 : Commit**

```bash
git add app/api_regles/regles.py tests/integration/api_regles/test_regles_dense.py
git commit -m "feat: guardrail de perimetre en premier maillon de POST /regles/dense"
```

---

### Task 2 : Alléger le prompt de jugement

**Files:**
- Modify: `app/retrieval/prompts/juger_pertinence.md`

**Interfaces:** aucune (contenu texte seul, aucun test automatisé dessus).

- [ ] **Step 1 : Remplacer le contenu du prompt**

Remplacer l'intégralité de `app/retrieval/prompts/juger_pertinence.md` par :

```markdown
Tu es un module de filtrage pour un moteur de question-réponse qui
s'appuie sur un référentiel de 245 règles de qualité web (Opquast).
Chaque règle décrit une vérification technique précise à faire sur un
site web (ex. « chaque image a une alternative textuelle », « au moins
deux moyens de contact sont proposés »).

La question posée a déjà été confirmée comme portant sur le périmètre
Opquast (un guardrail en amont a écarté les questions hors sujet). Une
recherche sémantique a ensuite sélectionné les règles ci-dessous comme
candidates possibles — la recherche sémantique retourne toujours des
candidats, même quand aucun ne répond réellement à la question précise
posée. Ne présume jamais qu'une règle candidate est pertinente
simplement parce qu'elle t'a été proposée.

Ta tâche : parmi les règles candidates ci-dessous, indique lesquelles
répondent réellement, précisément, à la question posée.

Une règle ne répond réellement que si elle décrit la vérification
technique que la question demande — pas si elle porte seulement sur un
thème ou un vocabulaire voisin (ex. un mot en commun comme « handicap »
ou « accessibilité » sans que la vérification décrite corresponde à la
question).

En cas de doute, réponds par une liste vide — c'est le comportement
attendu et correct quand aucune règle candidate ne répond précisément,
même si le sujet général est pertinent.

## Question posée

{question}

## Règles candidates

{candidats}

Réponds uniquement avec un objet JSON de la forme
{"numeros_pertinents": [12, 45]} (ou {"numeros_pertinents": []} si
aucune règle candidate ne répond réellement), sans aucun texte avant ou
après.
```

- [ ] **Step 2 : Vérifier que la suite de tests reste verte**

Run: `uv run pytest tests/unit tests/integration -q`
Expected: tous les tests passent (aucun test n'assert sur le contenu
littéral de ce prompt — changement de contenu texte seul).

- [ ] **Step 3 : Commit**

```bash
git add app/retrieval/prompts/juger_pertinence.md
git commit -m "docs: allege le prompt de jugement (guardrail porte desormais le perimetre)"
```

---

### Task 3 : Exécuter la mesure réelle et décider pour `is_acceptable()` — étape manuelle

**Pas de code produit par le Step 1-3 de cette tâche ; Step 4 conditionnel produit du code.**

- [ ] **Step 1 : Prérequis**

`.env` avec les secrets Azure présents ; `POSTGRES_DB` migrée avec les 245
règles enrichies et leurs embeddings à jour (`make embed-rules` si
nécessaire) ; API démarrée dans un terminal dédié (`make api-regles`).

- [ ] **Step 2 : Confirmer le coût avec David avant de lancer**

Coût réel estimé ~0,01-0,02 € (décomposition + embedding + jugement pour
chaque cas dans le périmètre, guardrail pour les 114 cas) — redemander
confirmation explicite au moment de l'exécuter.

- [ ] **Step 3 : Lancer l'acceptance réelle**

Run: `make api-regles-dense-acceptance`
Expected: rapport écrit dans `docs/eval/`, taux par famille affiché
dans les logs, en particulier `sans_reponse`.

- [ ] **Step 4 : Décision conditionnelle sur `is_acceptable()`**

Lire le taux mesuré de `sans_reponse` :

- **Si `sans_reponse` atteint 90%** (le seuil garde-fou des autres
  familles, `taux_reussite_minimum` du manifeste) : retirer son
  exclusion dans `app/ingestion/rag_acceptance.py::is_acceptable()`.
  Remplacer :

  ```python
  def is_acceptable(taux_par_famille: dict[str, dict], seuil: float) -> bool:
      """Le jeu est acceptable si chaque famille à cible normale atteint le seuil.

      La famille "sans_reponse" est exclue — pas faute de mécanisme
      (le Temps 2 en a construit un, jugement LLM sur les candidats
      retournés), mais parce que sa mesure réelle (~40-55% selon le
      modèle, cf. docs/eval/mesure_guardrail_perimetre_2026-09-11_214327.md
      et les runs précédents) a révélé une limite structurelle : présenter
      des candidats au LLM crée un biais de sélection qui l'empêche de
      répondre "aucun" de façon fiable. Le vrai correctif mesuré est un
      guardrail *sans* candidats, au niveau agent (100% sur sans_reponse
      isolément) — hors périmètre d'api_regles. Bloquer ce seuil ici
      signalerait à tort un problème de retrieval, alors que le retrieval
      et le jugement font leur travail ; c'est l'architecture qui manque
      une étape en amont.
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

      Depuis l'intégration du guardrail de périmètre en premier maillon
      d'api_regles (2026-09-13), "sans_reponse" est mesurée au même titre
      que les autres familles : le guardrail (sans candidats, mesuré
      isolément à 100%) porte désormais le refus, plus le jugement seul
      (limité par le biais de sélection, cf. mémoire assistant
      refus_architecture_trois_decisions).
      """
      for stats in taux_par_famille.values():
          if stats["taux"] < seuil:
              return False
      return True
  ```

  Puis mettre à jour les tests unitaires correspondants dans
  `tests/unit/ingestion/test_rag_acceptance.py` (fonction
  `test_is_acceptable_ignore_sans_reponse_meme_a_zero`, existante) pour
  refléter que `sans_reponse` compte désormais comme les autres
  familles — même changement de test que celui déjà fait le 2026-09-11
  pour le Temps 2 seul (`git log -p --follow -- app/ingestion/rag_acceptance.py`
  pour retrouver ce diff comme référence si besoin), puis relancer
  `uv run pytest tests/unit -q`.

- **Si `sans_reponse` reste sous 90%** : ne pas toucher à
  `is_acceptable()` — documenter le taux mesuré comme amélioration
  partielle (guardrail + jugement combinés) sans franchir le seuil,
  garder l'exclusion actuelle.

Dans les deux cas :

- [ ] **Step 5 : Tracer dans CHANGELOG.md**

Ajouter une entrée `## [date] — Claude Code` résumant : l'intégration du
guardrail, le prompt de jugement allégé, le coût réel observé, le taux
mesuré de `sans_reponse` et la décision prise sur `is_acceptable()`.

- [ ] **Step 6 : Mettre à jour TODO.md, Kanboard et la mémoire assistant**

`TODO.md` : fermer la ligne « Guardrail de périmètre au niveau agent »
(elle devient « intégré dans `api_regles` », plus « hors périmètre agent »
si le résultat confirme l'intégration). Kanboard : commenter la carte #19
avec le résultat et la déplacer en Done, sans la fermer. Mémoire assistant `refus_architecture_trois_decisions` :
mettre à jour la conclusion architecturale (le guardrail vit dans
`api_regles`, pas dans une future couche agent — corrigé par rapport à
la version précédente de cette mémoire).

---

## Self-Review (déjà appliqué en rédigeant ce plan)

- **Couverture de la spec** : guardrail en tout premier (avant `top_n`),
  hors périmètre → `[]` immédiat sans appeler le reste (Task 1) ; prompt
  de jugement allégé (Task 2) ; validation par remesure réelle (Task 3).
  Écart assumé par rapport au texte littéral de la spec : la construction
  de `GuardrailClient` est englobée dans un `try/except` fail-open (la
  spec supposait à tort qu'aucun enveloppement n'était nécessaire — la
  raison technique exacte est documentée dans « Contexte technique » et
  dans le commentaire du code lui-même).
- **Cohérence des types** : `GuardrailClient.est_dans_le_perimetre(question: str) -> bool`
  utilisé identiquement dans le code (Task 1) et dans les mocks de test
  (`mock_guardrail_client.return_value.est_dans_le_perimetre.return_value`).
- **Pas de placeholder** : le code complet de chaque remplacement est
  donné intégralement, y compris le contenu exact du nouveau prompt
  (Task 2) et les deux versions de `is_acceptable()` (Task 3, branché
  sur le résultat réel de la mesure — les deux branches sont écrites en
  entier, pas de `# TODO selon le résultat`).
