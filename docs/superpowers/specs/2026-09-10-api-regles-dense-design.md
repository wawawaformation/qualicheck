# POST /regles/dense — RAG sémantique exposé en HTTP

2026-09-10 · carte Kanboard #14

## Contexte

`app/retrieval/` (`decomposition.py`, `retrieval.py`, construit le
2026-09-09) n'est aujourd'hui appelable que depuis un script
(`scripts/check_rag_acceptance.py`, `scripts/rag_dense_acceptance.py`) —
aucun utilisateur réel ne peut poser une question au RAG. Vision du futur
agent US2 (David, 2026-09-09) : 3 façons de chercher une règle —
`GET /regles?q=` (mots-clés/syntaxe exacte, réel), `GET /regles/{numero}`
(lookup direct, réel), et ce nouvel endpoint (sémantique).

## Révision d'une contrainte déjà documentée

`IDEA.md` (2026-07-26) anticipait ce endpoint et posait une contrainte :
l'étage données (`app/api_regles/`) ne devait faire « aucun appel LLM,
aucun recalcul d'embedding » — un futur `app/api_business/` porterait
l'appel LLM, `app/api_regles/` n'exposant qu'un endpoint « vecteur déjà
calculé ».

**Révisé le 2026-09-10** (David) : le RAG complet (décomposition +
embedding + pgvector) rejoint `app/api_regles/`, pas de découpage entre
deux services pour cette fonctionnalité. Argument : les trois façons de
chercher une règle (mots-clés, numéro, sémantique) sont conceptuellement
la même chose — des modes de *lecture* du référentiel — peu importe la
complexité interne de chacune. Ce que la contrainte d'origine protégeait
réellement (l'étage données ne touche que PostgreSQL, l'étage applicatif
ne touche jamais PostgreSQL directement) reste intact : c'est la
sous-clause spécifique « aucun appel LLM » qui est levée, pas la
séparation données/applicatif elle-même.

Conséquence pratique : `app/api_regles/` a désormais besoin des secrets
Azure (`AZURE_AI_ENDPOINT`, `AZURE_AI_API_KEY`, `AZURE_MODEL_GPT_MINI`,
`AZURE_MODEL_TEXT_EMBEDDING_SMALL`) dans son environnement de
déploiement — jusqu'ici seul `POSTGRES_*` était nécessaire.

## Contrat de l'endpoint

```text
POST /regles/dense
Authorization: Bearer <jeton>
Content-Type: application/json

{"question": "Sur mobile, faut-il des boutons assez grands ?"}
```

Réponse : `200 OK`, `list[RegleRead]` — même schéma que `GET /regles` et
`GET /regles/{numero}`. Taille variable (union dédoublonnée des
sous-questions, pas de plafond — cohérent avec `retrieve()`).

**Pourquoi POST, pas GET** : rompt la convention GET du reste du router
(`GET /regles?q=`), mais un appel qui déclenche des coûts LLM réels et
transporte du texte libre (accents, longueur variable) est mieux modélisé
en POST avec un corps JSON qu'en query param — décision de David
(2026-09-10). Le `?q=` existant n'est pas révisé rétroactivement, hors
périmètre de cette carte.

**Pourquoi jeton Bearer requis** (contrairement à `GET /regles`/
`GET /regles/{numero}`, ouverts) : chaque appel a un coût réel (LLM +
embedding), contrairement aux lectures SQL gratuites qui justifiaient
l'ouverture sans jeton (`jury/decisions/2026-07-26-lecture-ouverte-api-regles.md`
— cette décision ne portait que sur la licence CC BY-SA du contenu, pas
sur un accès qui engage un coût). Réutilise `require_bearer()`
(`app/api_regles/auth.py`) tel quel.

**Pourquoi pas de paramètre `top_n`** : réutilise
`app/ingestion/manifest.yml` → `rag_acceptance.top_n` (15 aujourd'hui,
déjà mesuré) plutôt que de laisser un appelant choisir une valeur non
mesurée.

## Composants

### `app/api_regles/regles.py`

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

    requete_orm = (
        session.query(Regle, Theme.theme)
        .filter(Theme.id == Regle.theme_id, Regle.numero.in_(numeros))
    )
    resultats = _charger_regles(session, requete_orm)
    # Réordonne selon l'ordre de pertinence de retrieve() — la requête SQL
    # IN (...) ne garantit aucun ordre.
    position = {numero: i for i, numero in enumerate(numeros)}
    return sorted(resultats, key=lambda r: position[r.numero])
```

**Gestion d'erreur** : `decomposer()` est déjà fail-open en interne (ne
lève jamais). Un échec d'`embed_batch()` (3 tentatives épuisées) ou de la
requête pgvector remonte en 503 — même logique que la sonde `/health`
pour une base injoignable, pas une 500 générique.

**Nouveau schéma** (`app/api_regles/schemas.py`) :

```python
class RegleDenseQuery(BaseModel):
    """Question en langage naturel pour la recherche sémantique."""

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

**`app/api_regles/manifest.yml`** : nouvelle clé `validation.question_max_length`
(même section que `review_note_max_length`), lue par
`app/api_regles/config.py` (`QUESTION_MAX_LENGTH`). Valeur proposée : 500
caractères — largement au-dessus des questions du jeu d'acceptance (la
plus longue fait ~150 caractères), empêche un payload abusif sans gêner
un usage normal.

**`main.py`** : `allow_methods=["GET", "PATCH"]` devient
`["GET", "PATCH", "POST"]` (CORS).

## Tests

- **Unitaires** (`tests/unit/api_regles/test_regles_dense.py`) :
  `retrieve()` mocké (`app.api_regles.regles.retrieve`) — vérifie le
  contrat HTTP (200 + corps, 401 sans jeton, 503 si `retrieve()` lève,
  422 si `question` vide/trop longue), sans jamais appeler de vrai LLM.
- **Acceptance manuelle, hors CI** : nouveau
  `scripts/check_api_regles_dense_acceptance.py` + cible
  `make api-regles-dense-acceptance`. Réutilise
  `tests/acceptance/rag_acceptance.jsonl` (99 cas existants, aucune
  duplication) mais interroge `POST /regles/dense` en HTTP réel (API
  démarrée via `make api-regles`) plutôt que d'appeler `retrieve()` en
  process — vérifie que le contrat HTTP bout-en-bout produit le même
  résultat que l'appel direct. Réutilise `evaluate_case`/
  `compute_taux_par_famille`/`is_acceptable`
  (`app.ingestion.rag_acceptance`) : les numéros retournés viennent du
  champ `numero` de chaque `RegleRead` de la réponse JSON. **Reste
  volontairement hors du jeu automatique** `api_regles_acceptance.jsonl`
  (rejoué par `cd-staging.yml` à chaque déploiement) — coût réel à
  chaque exécution, même logique que `make rag-acceptance` déjà hors CI.

## Hors périmètre

- Paramètre `top_n` client-choisi.
- Rate-limiting (mitigation du risque de coût au-delà du jeton Bearer).
- Réviser `GET /regles?q=` en POST (remarque de David, pas dans le
  périmètre de cette carte).
- Ajouter les cas dense au jeu d'acceptance automatique de CD.
