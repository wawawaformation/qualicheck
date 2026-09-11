# Mécanisme de refus du retrieval — Temps 1 (mesure) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Faire remonter le score de similarité jusqu'au contrat HTTP de `/regles/dense`, étoffer le jeu de cas `sans_reponse`, et produire une mesure comparant les scores des cas `sans_reponse` vs des cas `PASS` — pour trancher, à l'issue de ce plan, si un seuil relatif est calibrable ou s'il faut basculer sur un jugement LLM (Temps 2, hors périmètre de ce plan).

**Architecture:** `query_top_n_numeros()` retourne désormais `(numéro, score)` au lieu de `numéro` seul ; `retrieve()` propage ces tuples en gardant le meilleur score par numéro en cas de doublon entre sous-questions ; le contrat HTTP de `/regles/dense` expose ce score (`RegleAvecScore`). Un nouveau script (`scripts/mesure_scores_refus.py`) rejoue le jeu d'acceptance et produit un rapport comparant les distributions de score entre cas `sans_reponse` et cas `PASS`.

**Tech Stack:** Python, SQLAlchemy/pgvector, FastAPI/Pydantic, pytest.

## Global Constraints

- Retry LLM : 3 tentatives avec backoff (déjà en place dans `DecompositionClient`/`EmbeddingClient`, aucun nouvel appel LLM introduit par ce plan).
- Aucune constante métier en dur : rien de nouveau à ajouter à `manifest.yml` dans ce plan (le seuil de refus est un chantier du Temps 2, pas ici).
- Tests destructeurs : `POSTGRES_TEST_DB` uniquement, jamais `POSTGRES_DB`.
- Fichiers temporaires : `./tmp/` à la racine du dépôt, jamais `/tmp` système.
- Traçage : `CHANGELOG.md` à la fin de ce plan, format `## [date] — [outil]`.

---

## Contexte technique (déjà vérifié dans le code)

- `query_top_n_numeros()` vit dans `app/ingestion/rag_acceptance.py:24-32`, réutilisée par import dans `app/retrieval/retrieval.py`, `scripts/rag_dense_acceptance.py` — jamais dupliquée.
- `evaluate_case()` (`rag_acceptance.py:35-60`) garde sa signature actuelle (`numeros_retournes: list[int]`) — **ce plan ne la modifie pas**. Le changement de règle sur `sans_reponse` (PASS si `retrieve()` retourne `[]`) appartient au Temps 2 : tant que le mécanisme de refus n'existe pas, `retrieve()` ne retourne jamais `[]`, donc rien ne casse ici, et un changement de règle maintenant serait prématuré (rien à mesurer).
- Aucun test unitaire n'existe aujourd'hui pour `query_top_n_numeros()`, `check_rag_acceptance.py`, `rag_dense_acceptance.py` ou `check_api_regles_dense_acceptance.py` — le fichier `tests/unit/ingestion/test_rag_acceptance.py` le documente explicitement (« nécessitent une base réellement vectorisée, validées par exécution réelle via `make rag-acceptance` »). Ce plan suit la même convention : pas de test unitaire artificiel pour ces fonctions couplées à pgvector/LLM, vérification par exécution réelle.
- `retrieve()` (`app/retrieval/retrieval.py`), lui, a des tests unitaires réels (`tests/unit/retrieval/test_retrieval.py`) car ses dépendances (session, clients) sont déjà mockées — ce plan les met à jour.

## Décision explicite : ordre de la liste retournée par `retrieve()`

`retrieve()` garde son ordre actuel (« première apparition » à travers l'union des sous-questions), **pas** un tri par score décroissant. Seul le score associé à un numéro déjà vu est mis à jour s'il est meilleur. Un tri par score serait un changement de comportement produit non discuté en brainstorming (seule la question du score *gardé* en cas de doublon a été tranchée, pas l'ordre de la liste) — à confirmer avec toi si ce n'est pas ce que tu attends, sinon ce point n'est plus soulevé après ce plan.

---

### Task 1: `query_top_n_numeros()` retourne aussi le score de similarité

**Files:**
- Modify: `app/ingestion/rag_acceptance.py:24-32`

**Interfaces:**
- Produces: `query_top_n_numeros(session: Session, vector: list[float], top_n: int) -> list[tuple[int, float]]` — remplace l'ancien retour `list[int]`. Score = similarité cosinus (`1 - cosine_distance`), 1 = identique, 0 = aucun rapport.

- [ ] **Step 1: Modifier la fonction**

```python
def query_top_n_numeros(session: Session, vector: list[float], top_n: int) -> list[tuple[int, float]]:
    """Retourne les (numéro, score) des top_n règles les plus proches du vecteur.

    Score de similarité cosinus (1 - distance) : 1 = identique, 0 = aucun
    rapport. Ordonné par similarité décroissante (le plus proche en premier).
    """
    resultats = (
        session.query(Regle.numero, Regle.embedding.cosine_distance(vector))
        .order_by(Regle.embedding.cosine_distance(vector))
        .limit(top_n)
        .all()
    )
    return [(numero, 1 - distance) for numero, distance in resultats]
```

- [ ] **Step 2: Vérifier par lecture qu'aucun autre appelant direct n'existe**

Run: `grep -rn "query_top_n_numeros" /projets/QualiCheck --include="*.py"`
Expected: seulement `app/ingestion/rag_acceptance.py` (définition), `app/retrieval/retrieval.py`, `scripts/rag_dense_acceptance.py` — les deux derniers seront corrigés aux tasks 2 et 4.

- [ ] **Step 3: Commit**

```bash
git add app/ingestion/rag_acceptance.py
git commit -m "feat: query_top_n_numeros retourne le score de similarite"
```

---

### Task 2: `retrieve()` retourne `(numéro, score)`, meilleur score gardé en cas de doublon

**Files:**
- Modify: `app/retrieval/retrieval.py`
- Test: `tests/unit/retrieval/test_retrieval.py`

**Interfaces:**
- Consumes: `query_top_n_numeros(session, vector, top_n) -> list[tuple[int, float]]` (Task 1).
- Produces: `retrieve(session, question, top_n, decomposition_client, embedding_client) -> list[tuple[int, float]]`.

- [ ] **Step 1: Réécrire les tests existants pour la nouvelle signature (ils doivent échouer)**

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
        mock_query.side_effect = [
            [(1, 0.9), (2, 0.5), (3, 0.3)],
            [(3, 0.6), (4, 0.4), (5, 0.2)],
        ]
        session = MagicMock()

        resultat = retrieve(
            session=session,
            question="question originale multi-sujets",
            top_n=15,
            decomposition_client=decomposition_client,
            embedding_client=embedding_client,
        )

        assert resultat == [(1, 0.9), (2, 0.5), (3, 0.6), (4, 0.4), (5, 0.2)]

    @patch("app.retrieval.retrieval.query_top_n_numeros")
    def test_retrieve_garde_le_meilleur_score_en_cas_de_doublon(self, mock_query):
        """Le numéro 3 apparaît dans les deux sous-questions : le score gardé est le plus haut (0.6), pas le premier trouvé (0.3)."""
        decomposition_client = MagicMock()
        decomposition_client.decomposer.return_value = ["sous-question A", "sous-question B"]
        embedding_client = MagicMock()
        embedding_client.embed_batch.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_query.side_effect = [
            [(3, 0.3)],
            [(3, 0.6)],
        ]
        session = MagicMock()

        resultat = retrieve(
            session=session,
            question="question",
            top_n=15,
            decomposition_client=decomposition_client,
            embedding_client=embedding_client,
        )

        assert resultat == [(3, 0.6)]

    @patch("app.retrieval.retrieval.query_top_n_numeros")
    def test_retrieve_mono_sujet_une_seule_recherche(self, mock_query):
        """Une seule sous-question déclenche une seule recherche pgvector."""
        decomposition_client = MagicMock()
        decomposition_client.decomposer.return_value = ["question mono-sujet"]
        embedding_client = MagicMock()
        embedding_client.embed_batch.return_value = [[0.5, 0.6]]
        mock_query.return_value = [(10, 0.9), (20, 0.5), (30, 0.2)]
        session = MagicMock()

        resultat = retrieve(
            session=session,
            question="question mono-sujet",
            top_n=15,
            decomposition_client=decomposition_client,
            embedding_client=embedding_client,
        )

        assert resultat == [(10, 0.9), (20, 0.5), (30, 0.2)]
        assert mock_query.call_count == 1
        embedding_client.embed_batch.assert_called_once_with(["question mono-sujet"])
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `uv run pytest tests/unit/retrieval/test_retrieval.py -v`
Expected: FAIL — `retrieve()` retourne encore `list[int]`, les assertions sur des tuples ne correspondent pas.

- [ ] **Step 3: Modifier `retrieve()`**

```python
"""
Orchestration du retrieval : décomposition, embedding, recherche pgvector,
union. Voir docs/superpowers/specs/2026-09-09-retrieval-decomposition-multi-sujets-design.md
et docs/superpowers/specs/2026-09-11-retrieval-refus-design.md.
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
) -> list[tuple[int, float]]:
    """Retrouve les (numéro, score) de règle pertinents pour une question.

    Décompose la question en 1..N sous-questions, vectorise toutes les
    sous-questions en un seul appel embed_batch, interroge pgvector
    (top_n) une fois par sous-question, puis fusionne par union simple
    dédoublonnée (ordre de première apparition). En cas de doublon entre
    sous-questions, le score gardé est le meilleur (le plus similaire),
    pas celui de la première apparition. Pas de plafond après fusion : la
    taille du résultat varie selon le nombre de sous-questions.
    """
    sous_questions = decomposition_client.decomposer(question)
    vectors = embedding_client.embed_batch(sous_questions)

    ordre: list[int] = []
    meilleurs_scores: dict[int, float] = {}
    for vector in vectors:
        for numero, score in query_top_n_numeros(session, vector, top_n):
            if numero not in meilleurs_scores:
                ordre.append(numero)
                meilleurs_scores[numero] = score
            elif score > meilleurs_scores[numero]:
                meilleurs_scores[numero] = score

    return [(numero, meilleurs_scores[numero]) for numero in ordre]
```

- [ ] **Step 4: Lancer les tests, vérifier qu'ils passent**

Run: `uv run pytest tests/unit/retrieval/test_retrieval.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add app/retrieval/retrieval.py tests/unit/retrieval/test_retrieval.py
git commit -m "feat: retrieve() propage le score de similarite, meilleur score garde sur doublon"
```

---

### Task 3: Adapter `scripts/check_rag_acceptance.py` à la nouvelle signature

**Files:**
- Modify: `scripts/check_rag_acceptance.py:76-90`

**Interfaces:**
- Consumes: `retrieve(...) -> list[tuple[int, float]]` (Task 2). `evaluate_case(case, numeros_retournes: list[int])` — signature inchangée.

- [ ] **Step 1: Extraire les numéros avant `evaluate_case`**

Remplacer (lignes 76-90) :

```python
            for case in cases:
                numeros_retournes = retrieve(
                    session=session,
                    question=case["question"],
                    top_n=top_n,
                    decomposition_client=decomposition_client,
                    embedding_client=embedding_client,
                )
                evaluation = evaluate_case(case, numeros_retournes)
```

par :

```python
            for case in cases:
                resultat = retrieve(
                    session=session,
                    question=case["question"],
                    top_n=top_n,
                    decomposition_client=decomposition_client,
                    embedding_client=embedding_client,
                )
                numeros_retournes = [numero for numero, _ in resultat]
                evaluation = evaluate_case(case, numeros_retournes)
```

(le reste de la boucle — logs, `progress_logger.info(...)` — référence déjà `numeros_retournes`, inchangé)

- [ ] **Step 2: Vérifier par lecture qu'aucune autre ligne du fichier ne référence l'ancien type de retour**

Run: `grep -n "retrieve(" scripts/check_rag_acceptance.py`
Expected: un seul appel, celui modifié à l'étape 1.

- [ ] **Step 3: Commit**

```bash
git add scripts/check_rag_acceptance.py
git commit -m "fix: check_rag_acceptance extrait les numeros des tuples (numero,score)"
```

---

### Task 4: Adapter `scripts/rag_dense_acceptance.py` à la nouvelle signature

**Files:**
- Modify: `scripts/rag_dense_acceptance.py:78-80`

**Interfaces:**
- Consumes: `query_top_n_numeros(session, vector, top_n_max) -> list[tuple[int, float]]` (Task 1).

- [ ] **Step 1: Extraire les numéros directement à la source**

Ce script ne se sert jamais du score (seulement de la présence d'un numéro dans le top-N tronqué). Remplacer (lignes 78-80) :

```python
    numeros_max_par_sous_question = [
        query_top_n_numeros(session, vector, top_n_max) for vector in vectors
    ]
```

par :

```python
    numeros_max_par_sous_question = [
        [numero for numero, _ in query_top_n_numeros(session, vector, top_n_max)]
        for vector in vectors
    ]
```

Le reste de la fonction (`resultats[top_n] = numeros`, boucle de troncature `numeros_max[:top_n]`) reste inchangé : `numeros_max_par_sous_question` est toujours `list[list[int]]` en sortie de cette étape.

- [ ] **Step 2: Commit**

```bash
git add scripts/rag_dense_acceptance.py
git commit -m "fix: rag_dense_acceptance extrait les numeros des tuples (numero,score)"
```

---

### Task 5: Contrat HTTP `/regles/dense` expose le score (`RegleAvecScore`)

**Files:**
- Modify: `app/api_regles/schemas.py` (ajout après `RegleRead`, ligne 120)
- Modify: `app/api_regles/regles.py:257-299`
- Test: `tests/integration/api_regles/test_regles_dense.py`

**Interfaces:**
- Consumes: `retrieve(...) -> list[tuple[int, float]]` (Task 2).
- Produces: `RegleAvecScore` (Pydantic, `app/api_regles/schemas.py`) — `{regle: RegleRead, score: float}`. Endpoint `POST /regles/dense` → `response_model=list[RegleAvecScore]`.

- [ ] **Step 1: Réécrire les tests d'intégration pour le nouveau contrat (ils doivent échouer)**

Dans `tests/integration/api_regles/test_regles_dense.py`, remplacer les 3 lignes qui référencent l'ancien format `mock_retrieve.return_value` et l'assertion associée :

```python
@patch("app.api_regles.regles.EmbeddingClient")
@patch("app.api_regles.regles.DecompositionClient")
@patch("app.api_regles.regles.retrieve")
def test_dense_retourne_les_regles_dans_l_ordre_de_pertinence(
    mock_retrieve, mock_decomposition_client, mock_embedding_client, client, jeu_de_regles
):
    """La réponse suit l'ordre de retrieve(), pas l'ordre numéro, et embarque le score."""
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

Et dans `test_dense_journalise_la_question_et_le_client` :

```python
    mock_retrieve.return_value = [(1, 0.9)]
```

(seule cette ligne change dans ce test, le reste est inchangé)

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `uv run pytest tests/integration/api_regles/test_regles_dense.py -v`
Expected: FAIL sur `test_dense_retourne_les_regles_dans_l_ordre_de_pertinence` (le corps ne contient pas de clé `regle`/`score` avec le code actuel) et sur `test_dense_journalise_la_question_et_le_client` (erreur de construction : `retrieve()` mocké retourne `[(1, 0.9)]`, mais le code appelle encore `Regle.numero.in_(numeros)` avec `numeros = [(1, 0.9)]`, ce qui ne matchera aucune règle).

- [ ] **Step 3: Ajouter `RegleAvecScore` dans `app/api_regles/schemas.py`**

Juste après la classe `RegleRead` (après la ligne 119, avant `class RegleDenseQuery`) :

```python
class RegleAvecScore(BaseModel):
    """Règle retournée par la recherche sémantique, avec son score de similarité.

    Score de similarité cosinus (1 - distance) : 1 = identique, 0 = aucun
    rapport. Voir app/retrieval/retrieval.py::retrieve().
    """

    regle: RegleRead
    score: float
```

- [ ] **Step 4: Adapter l'endpoint dans `app/api_regles/regles.py`**

Modifier l'import (ligne 13-19) :

```python
from app.api_regles.schemas import (
    OutilFiltre,
    RegleAvecScore,
    RegleDenseQuery,
    ReglePatch,
    RegleRead,
    ReviewStatusFiltre,
)
```

Remplacer la fonction `chercher_regles_dense` (lignes 257-299) :

```python
@router.post("/dense", response_model=list[RegleAvecScore])
def chercher_regles_dense(
    requete: RegleDenseQuery,
    session: Session = Depends(get_session_referentiel),
    client_nom: str = Depends(require_bearer),
) -> list[RegleAvecScore]:
    """
    Recherche sémantique : décompose la question, vectorise, interroge
    pgvector, fusionne. Voir app/retrieval/retrieval.py::retrieve().

    Chaque appel a un coût réel (LLM + embedding) — jeton Bearer requis,
    contrairement aux autres lectures de ce router. Le score de similarité
    (1 - distance cosinus) est renvoyé pour chaque règle.
    """
    top_n = load_manifest()["rag_acceptance"]["top_n"]

    logger.info("Recherche dense par %s : « %s »", client_nom, requete.question)

    try:
        decomposition_client = DecompositionClient()
        embedding_client = EmbeddingClient()
        resultat = retrieve(
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

- [ ] **Step 5: Lancer les tests, vérifier qu'ils passent**

Run: `uv run pytest tests/integration/api_regles/test_regles_dense.py -v`
Expected: PASS (6 tests) — nécessite `qualicheck-postgres` démarré et `POSTGRES_TEST_DB` migrée (`make migration-test`), comme documenté en tête du fichier de test.

- [ ] **Step 6: Commit**

```bash
git add app/api_regles/schemas.py app/api_regles/regles.py tests/integration/api_regles/test_regles_dense.py
git commit -m "feat: /regles/dense expose le score de similarite (RegleAvecScore)"
```

---

### Task 6: Adapter `scripts/check_api_regles_dense_acceptance.py` au nouveau contrat JSON

**Files:**
- Modify: `scripts/check_api_regles_dense_acceptance.py:52`

**Interfaces:**
- Consumes: réponse HTTP `list[RegleAvecScore]` (Task 5) — chaque élément est désormais `{"regle": {...}, "score": ...}` au lieu de la règle à plat.

- [ ] **Step 1: Adapter l'extraction des numéros**

Remplacer (ligne 52) :

```python
    numeros_retournes = [regle["numero"] for regle in reponse.json()]
```

par :

```python
    numeros_retournes = [item["regle"]["numero"] for item in reponse.json()]
```

- [ ] **Step 2: Commit**

```bash
git add scripts/check_api_regles_dense_acceptance.py
git commit -m "fix: check_api_regles_dense_acceptance lit le nouveau contrat {regle,score}"
```

---

### Task 7: Étoffer la famille `sans_reponse` (5 → 20 cas)

**Files:**
- Modify: `tests/acceptance/rag_acceptance.jsonl` (après la ligne 49)

**Interfaces:** aucune (données seulement).

- [ ] **Step 1: Validation utilisateur des 15 cas candidats avant ajout**

Candidats (3 catégories, 5 chacune), sources : catégorie 3 construite à partir du contenu réel de `opquast.com` (fondamentaux du projet, modèle VPTCS, offre de formation) plutôt que devinée :

*Hors-domaine total :*
1. « Quelle est la meilleure recette de tarte aux pommes ? »
2. « Comment planifier un voyage en Europe pas cher ? »
3. « Quel est le palmarès de la dernière Coupe du monde de football ? »
4. « Comment entretenir un jardin potager en hiver ? »
5. « Quelle est la différence entre un chat et un chien comme animal de compagnie ? »

*Domaine proche mais hors périmètre Opquast :*
6. « Quel est le meilleur CMS pour un petit site vitrine ? »
7. « Comment structurer une équipe de développement web en méthode Scrum ? »
8. « Quels indicateurs suivre pour mesurer le trafic d'un site e-commerce ? »
9. « Combien coûte un audit RGPD complet pour une PME ? »
10. « Comment rédiger un cahier des charges pour un projet web ? »

*Vocabulaire Opquast détourné / écosystème (hors des 245 règles) :*
11. « Qu'est-ce que le modèle VPTCS et quelles sont ses cinq composantes ? »
12. « Qui a créé le modèle VPTCS et en quelle année ? »
13. « Quelle est la différence entre UX et UI selon le modèle VPTCS ? »
14. « Combien coûte la formation Référent Qualité Numérique chez Opquast ? »
15. « Quelles sont les conditions pour devenir formateur Opquast ? »

**Ne pas passer à l'étape 2 sans confirmation explicite de David sur cette liste** (ajustement, retrait ou remplacement possible).

- [ ] **Step 2: Ajouter les cas validés au fichier JSONL**

Insérer après la ligne 49 (dernier cas `sans_reponse` existant), une ligne JSON par cas validé, même format que les cas existants :

```json
{"question": "Quelle est la meilleure recette de tarte aux pommes ?", "famille": "sans_reponse", "numeros_regle_attendus": []}
```

(répéter pour chacun des cas validés à l'étape 1, dans l'ordre)

- [ ] **Step 3: Vérifier le fichier**

Run: `uv run python -c "
import json
with open('tests/acceptance/rag_acceptance.jsonl') as f:
    cas = [json.loads(l) for l in f if l.strip()]
sans_reponse = [c for c in cas if c['famille'] == 'sans_reponse']
print(f'{len(cas)} cas au total, {len(sans_reponse)} sans_reponse')
assert all(c['numeros_regle_attendus'] == [] for c in sans_reponse)
"`
Expected: `114 cas au total, 20 sans_reponse` (99 existants + le nombre de cas validés à l'étape 1, jusqu'à 15)

- [ ] **Step 4: Commit**

```bash
git add tests/acceptance/rag_acceptance.jsonl
git commit -m "test: etoffe la famille sans_reponse (5 a 20 cas, 3 categories)"
```

---

### Task 8: Fonction pure de calcul des métriques (top-1, écart top-1/top-15)

**Files:**
- Modify: `app/ingestion/rag_acceptance.py` (nouvelle fonction, après `query_top_n_numeros`)
- Test: `tests/unit/ingestion/test_rag_acceptance.py`

**Interfaces:**
- Consumes: `list[tuple[int, float]]` (sortie de `retrieve()`, Task 2).
- Produces: `metriques_scores(candidats: list[tuple[int, float]]) -> dict` — `{"top1": float, "top15": float, "ecart": float}`.

- [ ] **Step 1: Écrire les tests (ils doivent échouer)**

Ajouter à la fin de `tests/unit/ingestion/test_rag_acceptance.py` :

```python
from app.ingestion.rag_acceptance import metriques_scores


def test_metriques_scores_top1_et_top15():
    """top1 = meilleur score, top15 = score du 15e candidat une fois trié."""
    candidats = [(i, 1.0 - i * 0.05) for i in range(20)]  # scores de 1.0 à 0.05

    resultat = metriques_scores(candidats)

    assert resultat["top1"] == 1.0
    assert resultat["top15"] == round(1.0 - 14 * 0.05, 10)
    assert resultat["ecart"] == round(resultat["top1"] - resultat["top15"], 10)


def test_metriques_scores_ignore_l_ordre_d_entree():
    """Le tri se fait par score, indépendamment de l'ordre de la liste passée."""
    candidats = [(1, 0.2), (2, 0.9), (3, 0.5)]

    resultat = metriques_scores(candidats)

    assert resultat["top1"] == 0.9


def test_metriques_scores_moins_de_15_candidats():
    """Avec moins de 15 candidats, top15 retombe sur le dernier (le plus faible)."""
    candidats = [(1, 0.8), (2, 0.3)]

    resultat = metriques_scores(candidats)

    assert resultat["top15"] == 0.3
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -k metriques_scores -v`
Expected: FAIL avec `ImportError` (`metriques_scores` n'existe pas encore)

- [ ] **Step 3: Implémenter la fonction**

Ajouter dans `app/ingestion/rag_acceptance.py`, juste après `query_top_n_numeros` :

```python
def metriques_scores(candidats: list[tuple[int, float]]) -> dict:
    """Calcule top1 (meilleur score) et top15 (15e meilleur, ou le dernier si moins de 15).

    Trie localement par score décroissant, indépendamment de l'ordre de la
    liste passée (retrieve() ordonne par première apparition entre
    sous-questions, pas par score).
    """
    tries = sorted(candidats, key=lambda c: c[1], reverse=True)
    top1 = tries[0][1]
    index_top15 = min(14, len(tries) - 1)
    top15 = tries[index_top15][1]
    return {"top1": top1, "top15": top15, "ecart": top1 - top15}
```

- [ ] **Step 4: Lancer les tests, vérifier qu'ils passent**

Run: `uv run pytest tests/unit/ingestion/test_rag_acceptance.py -k metriques_scores -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add app/ingestion/rag_acceptance.py tests/unit/ingestion/test_rag_acceptance.py
git commit -m "feat: metriques_scores (top1/top15/ecart) pour la mesure du refus"
```

---

### Task 9: Script `scripts/mesure_scores_refus.py` + cible Makefile

**Files:**
- Create: `scripts/mesure_scores_refus.py`
- Modify: `Makefile` (après la cible `rag-dense-acceptance`, ligne 117)

**Interfaces:**
- Consumes: `retrieve()` (Task 2), `evaluate_case()` (inchangée), `metriques_scores()` (Task 8), `load_cases()`, `load_manifest()`.
- Pas de test unitaire dédié (même convention que `check_rag_acceptance.py`/`rag_dense_acceptance.py` : script couplé à pgvector + LLM réels, validé par exécution réelle — voir note en tête de `tests/unit/ingestion/test_rag_acceptance.py`).

- [ ] **Step 1: Écrire le script**

```python
"""Mesure les scores de similarité (top-1, écart top-1/top-15) pour trancher
si un seuil relatif sépare les cas sans_reponse des cas PASS.

Rejoue tests/acceptance/rag_acceptance.jsonl (coût réel : décomposition LLM
+ embedding), calcule metriques_scores() par cas, puis compare les
distributions entre la famille sans_reponse et les cas jugés PASS par
evaluate_case() (les autres familles). Produit un rapport Markdown
horodaté dans docs/eval/. Voir
docs/superpowers/specs/2026-09-11-retrieval-refus-design.md (Temps 1).

Volontairement hors CI, comme rag_dense_acceptance.py — lancé à la demande
via `make mesure-scores-refus`.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.embedding import EmbeddingClient  # noqa: E402
from app.ingestion.rag_acceptance import (  # noqa: E402
    evaluate_case,
    load_cases,
    metriques_scores,
)
from app.logging_config import setup_logging  # noqa: E402
from app.retrieval.decomposition import DecompositionClient  # noqa: E402
from app.retrieval.retrieval import retrieve  # noqa: E402

logger = logging.getLogger(__name__)
progress_logger = logging.getLogger("progress")

CASES_PATH = Path(__file__).resolve().parents[1] / "tests" / "acceptance" / "rag_acceptance.jsonl"
REPORT_DIR = Path(__file__).resolve().parents[1] / "docs" / "eval"

FAMILLE_SANS_REPONSE = "sans_reponse"


def get_engine():
    """Construit l'engine SQLAlchemy depuis les variables .env."""
    url = (
        f"postgresql+psycopg2://{os.environ['POSTGRES_USER']}:"
        f"{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:"
        f"{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
    )
    return create_engine(url)


def _resume(valeurs: list[float]) -> dict:
    """Min/max/moyenne d'une liste de scores, pour comparer deux groupes."""
    return {
        "min": min(valeurs),
        "max": max(valeurs),
        "moyenne": sum(valeurs) / len(valeurs),
        "n": len(valeurs),
    }


def build_report(mesures: list[dict], horodatage: datetime) -> str:
    """Compare les distributions top1/top15/ecart entre sans_reponse et PASS."""
    sans_reponse = [m for m in mesures if m["famille"] == FAMILLE_SANS_REPONSE]
    pass_cases = [
        m for m in mesures if m["famille"] != FAMILLE_SANS_REPONSE and m["verdict"] == "PASS"
    ]

    lignes = [
        f"# Mesure des scores — refus du retrieval ({horodatage.strftime('%Y-%m-%d %H:%M')})",
        "",
        f"`sans_reponse` : {len(sans_reponse)} cas — cas `PASS` (autres familles) : {len(pass_cases)} cas",
        "",
        "## Distributions par métrique",
        "",
        "| Métrique | Groupe | min | max | moyenne |",
        "|---|---|---|---|---|",
    ]
    for metrique in ("top1", "top15", "ecart"):
        for nom_groupe, groupe in (("sans_reponse", sans_reponse), ("PASS", pass_cases)):
            stats = _resume([m[metrique] for m in groupe])
            lignes.append(
                f"| {metrique} | {nom_groupe} | {stats['min']:.3f} | {stats['max']:.3f} | "
                f"{stats['moyenne']:.3f} |"
            )

    lignes.append("")
    lignes.append("## Détail par cas")
    lignes.append("")
    lignes.append("| Famille | Verdict | top1 | top15 | écart | Question |")
    lignes.append("|---|---|---|---|---|---|")
    for m in mesures:
        lignes.append(
            f"| {m['famille']} | {m['verdict']} | {m['top1']:.3f} | {m['top15']:.3f} | "
            f"{m['ecart']:.3f} | {m['question']} |"
        )

    return "\n".join(lignes) + "\n"


def main() -> None:
    setup_logging()
    load_dotenv()

    engine = get_engine()
    cases = load_cases(CASES_PATH)
    embedding_client = EmbeddingClient()
    decomposition_client = DecompositionClient()

    logger.info("=== mesure_scores_refus : démarrage ===")
    progress_logger.info("=== mesure_scores_refus : démarrage ===")

    mesures = []
    with Session(engine) as session:
        for case in cases:
            resultat = retrieve(
                session=session,
                question=case["question"],
                top_n=15,
                decomposition_client=decomposition_client,
                embedding_client=embedding_client,
            )
            numeros = [numero for numero, _ in resultat]
            evaluation = evaluate_case(case, numeros)
            metriques = metriques_scores(resultat)
            mesures.append(
                {
                    "question": case["question"],
                    "famille": case["famille"],
                    "verdict": evaluation["verdict"],
                    **metriques,
                }
            )
            progress_logger.info(
                f"mesure_scores_refus — « {case['question']} » [{case['famille']}] "
                f"{evaluation['verdict']} — top1={metriques['top1']:.3f} "
                f"top15={metriques['top15']:.3f}"
            )

    horodatage = datetime.now()
    rapport = build_report(mesures, horodatage)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"mesure_scores_refus_{horodatage.strftime('%Y-%m-%d_%H%M%S')}.md"
    report_path.write_text(rapport, encoding="utf-8")

    logger.info(f"=== mesure_scores_refus : rapport écrit dans {report_path} ===")
    progress_logger.info(f"=== mesure_scores_refus : rapport écrit dans {report_path} ===")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Ajouter la cible Makefile**

Dans `Makefile`, juste après la cible `rag-dense-acceptance` (ligne 117) :

```makefile

## Mesure les scores (top-1, écart top-1/top-15) : sans_reponse vs cas PASS,
## pour trancher si un seuil relatif est calibrable (Temps 1 du chantier refus)
mesure-scores-refus:
	uv run python scripts/mesure_scores_refus.py
```

Et ajouter `mesure-scores-refus` à la liste `.PHONY` en tête du fichier (ligne 1).

- [ ] **Step 3: Vérifier que le script s'importe sans erreur (sans l'exécuter)**

Run: `uv run python -c "import ast; ast.parse(open('scripts/mesure_scores_refus.py').read())"`
Expected: aucune erreur (vérifie uniquement la syntaxe, sans appeler l'API Azure)

- [ ] **Step 4: Commit**

```bash
git add scripts/mesure_scores_refus.py Makefile
git commit -m "feat: script mesure_scores_refus (make mesure-scores-refus)"
```

---

### Task 10: Exécuter la mesure réelle (coût réel, hors CI) — étape manuelle

**Pas de code produit par cette tâche** — c'est l'exécution du Temps 1 dans son ensemble, débouchant sur le point de décision du Temps 2.

- [ ] **Step 1: Prérequis**

Vérifier `.env` (secrets Azure présents), `make migration` déjà joué sur `POSTGRES_DB` (le script lit la base réelle, pas `POSTGRES_TEST_DB` — comme `rag_dense_acceptance.py`), et `make embed-rules` déjà joué (embeddings à jour).

- [ ] **Step 2: Lancer la mesure**

Run: `make mesure-scores-refus`
Expected : un fichier `docs/eval/mesure_scores_refus_<horodatage>.md` créé, coût affiché dans les logs (`progress_logger`).

- [ ] **Step 3: Lire le rapport — point de décision (Temps 2, hors périmètre de ce plan)**

Si le tableau « Distributions par métrique » montre, sur `top1` ou `top15`, un écart net entre les groupes `sans_reponse` et `PASS` (max du groupe `sans_reponse` < min du groupe `PASS`, ou marge confortable) : un seuil relatif est calibrable — le prochain chantier (nouvelle spec) l'ajoute à `manifest.yml` et l'applique dans `retrieve()`.

Sinon (chevauchement significatif sur les deux métriques) : bascule vers un client LLM de jugement (`app/retrieval/`, nouvelle spec également).

Dans les deux cas, ce choix ouvre un **nouveau cycle spec → plan** (Temps 2) — pas une suite automatique de ce plan.

- [ ] **Step 4: Tracer le résultat**

Ajouter une entrée `CHANGELOG.md` (`## [date] — Claude Code`) résumant : cas ajoutés à `sans_reponse`, score propagé jusqu'au contrat HTTP, résultat chiffré de la mesure (écart ou chevauchement), et le choix de bascule qui en découle. Mettre à jour `jury/documents_jury/working/fiche-rag-similarite-cosinus.md` (section 4.1) avec ce résultat. Cocher la sous-case correspondante dans `TODO.md` (section « Retrieval US2 »).

---

## Self-Review (déjà appliqué en rédigeant ce plan)

- **Couverture de la spec** : Temps 1 entièrement couvert (étoffement `sans_reponse`, score propagé jusqu'au contrat HTTP, script de mesure, critère de bascule lu depuis le rapport). Temps 2 volontairement laissé en point de décision (Task 10, Step 3), pas de tâche de code pour l'une ou l'autre branche — conforme à la spec.
- **Cohérence des types** : `query_top_n_numeros` (Task 1) → `retrieve()` (Task 2) → `regles.py`/`rag_dense_acceptance.py`/`check_rag_acceptance.py`/`mesure_scores_refus.py` (Tasks 3, 4, 5, 9) — tous consomment `list[tuple[int, float]]` de façon cohérente. `evaluate_case()` n'est jamais appelée qu'avec `list[int]` (extraction explicite à chaque site d'appel).
- **Pas de placeholder** : les 15 questions candidates de la Task 7 sont rédigées en entier (pas de "TODO: trouver des questions"), sourcées sur le contenu réel d'opquast.com pour la catégorie 3.
