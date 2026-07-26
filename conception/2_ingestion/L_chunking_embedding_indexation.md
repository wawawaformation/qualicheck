# Chantier — Chunking, embedding, indexation (Étapes 5-7)

> Spec d'incrément. Fait suite au chantier `enrich_again` (Étapes 1-4
> stabilisées) et au constat que `regle.embedding` (`vector(384)`) est
> resté `NULL` sur les 245 lignes depuis le début du projet — jamais
> implémenté. Brainstorming mené sans précipitation à la demande explicite
> de David, un point à la fois. À valider avant implémentation.
>
> Date : 2026-07-26

## 1. Problème

Les Étapes 5 (chunking), 6 (embedding) et 7 (indexation) du pipeline
d'ingestion (`conception/2_ingestion/ingestion.md` §Étapes 5-7) n'ont
jamais été implémentées. Conséquence directe : `regle.embedding` est
`NULL` sur les 245 lignes réelles déjà en base — aucune recherche
sémantique (US2, question libre) n'est possible aujourd'hui.

Deux problèmes identifiés en creusant le sujet aujourd'hui :

- Le modèle initialement visé (All MiniLM L12 v2 via Infomaniak) est
  disqualifié : `max_token_input=128`, incompatible avec la décision actée
  "1 règle = 1 chunk" (mesuré sur les 245 règles réelles : ~319 tokens en
  moyenne, jusqu'à ~952 pour la règle 164).
- La dimension du vecteur initialement prévue (`vector(384)`, hérité du
  choix MiniLM) tronquerait significativement l'information d'un chunk
  aussi riche — `text-embedding-3-small` a une dimension **native** de
  1536, et rien ne justifie de la tronquer sur un corpus de 245 lignes
  (coût de stockage/calcul négligeable dans les deux cas).

Ce chantier documente la solution retenue (Azure, dimension native) et
l'architecture des trois étapes, y compris la migration de schéma qui en
découle.

## 2. État actuel (vérifié)

- `regle.embedding` : colonne `vector(384)` (migration 0001), jamais
  écrite par aucun code — **aucune donnée réelle à préserver**, c'est le
  moment le moins cher possible pour corriger la dimension.
- Index HNSW existant : `regle_embedding_idx`
  (`CREATE INDEX regle_embedding_idx ON regle USING hnsw (embedding vector_cosine_ops)`,
  migration 0001) — lié à la dimension de la colonne, doit être recréé si
  la dimension change.
- `app/ingestion/schema.py` : `EnrichedRule` n'a pas de champ `embedding`.
- `app/ingestion/stockage.py` : `upsert_rule()` ne touche pas à la colonne
  `embedding`.
- `app/ingestion/manifest.yml` : un seul rôle (`enrichissement`), pas de
  rôle `embedding`.
- `.env` : `AZURE_MODEL_TEXT_EMBEDDING_SMALL=text-embedding-3-small` déjà
  présent (déploiement Azure vérifié : `GenerallyAvailable`, 8191 tokens
  de contexte, 125k TPM/750 RPM, hors service 02/2028).
- Aucun module `app/ingestion/chunking.py` ni `app/ingestion/embedding.py`
  n'existe.

## 3. Décisions de conception

| Point | Décision |
| --- | --- |
| Contenu du chunk | `intitulé + contexte + solution + controle + guide_analyse + tags + phases` — `contexte` inclus (absent sur ~la moitié des règles, omis proprement si `NULL`), conformément à l'intention notée au chantier 1 |
| Format du chunk | Structuré avec labels (`Intitulé : ...\nContexte : ...\nSolution : ...\nControle : ...\nGuide d'analyse : ...\nTags : ...\nPhases : ...`) — aide la qualité sémantique de l'embedding, coût négligeable en tokens |
| "1 règle = 1 chunk" | Non négociable — pas de découpage sémantique, pas de chevauchement. **Référence** : déjà décidé et justifié dans `conception/2_ingestion/ingestion.md` §Étape 5 — "la granularité métier de la règle correspond exactement à la granularité de recherche RAG souhaitée pour l'audit". Une règle Opquast (intitulé, solution, controle, guide_analyse) forme un tout actionnable : solution et controle n'ont de sens que lus ensemble pour une même règle, et un futur agent d'audit (US1/US2) a besoin de la règle complète pour appliquer ou expliquer un contrôle — retrouver un fragment isolé (ex. juste le `controle`, sans le `guide_analyse` associé) serait inexploitable. Ce principe tient même avec un chunk plus riche qu'à l'origine (ajout de `contexte`) : la taille du texte a changé, pas l'unité métier qu'il représente |
| Modèle d'embedding (solution actuelle) | Azure `text-embedding-3-small` (`AZURE_MODEL_TEXT_EMBEDDING_SMALL`, déjà dans `.env`) |
| **Dimension du vecteur** | **1536, native — pas de troncature.** `dimensions=384` rejeté : sur un chunk riche (jusqu'à ~950 tokens), tronquer perd significativement plus d'information relative qu'un texte court dans la même dimension ; le corpus (245 lignes) est trop petit pour que le coût de stockage/calcul justifie une troncature. `dimensions=1536` passé explicitement à l'appel (natif, mais explicite plutôt qu'implicite) |
| **Migration de schéma** | `regle.embedding` : `vector(384)` → `vector(1536)`. Faite **maintenant**, pas différée : aucune donnée réelle n'existe encore sur cette colonne (`NULL` partout), c'est le moment le moins cher possible. Index HNSW (`regle_embedding_idx`) supprimé puis recréé après le changement de type (lié à la dimension) |
| Cible future Infomaniak (hors périmètre ici) | Modèle exact non tranché dans ce chantier (MiniLM disqualifié, BGE Multilingual Gemma2 à évaluer plus tard) ; ré-vectorisation complète prévue au bascule, potentiellement aussi une nouvelle migration de dimension selon le modèle retenu — sujet explicitement reporté |
| Orchestration | Module partagé `app/ingestion/embedding.py` (logique d'appel API), utilisé par deux points d'entrée : `scripts/ingestion.py` (Étape 6, future ré-ingestion complète) et un nouveau script indépendant `scripts/embed_rules.py` (backfill, sur le modèle d'`enrich_again.py`) |
| Périmètre du backfill | `scripts/embed_rules.py` recalcule l'embedding de **toutes** les règles à chaque exécution (pas seulement celles à `NULL`) — plus simple, coût négligeable, pas de suivi d'un état "à jour" à maintenir |
| Batch processing | Lots de 50 règles par appel API (5 appels pour 245 lignes) — cohérent avec le débit Azure (125k TPM/750 RPM) et avec le découpage déjà utilisé ailleurs dans le projet (lots ~49 pour l'audit multi-agent) |
| Retry | Réutilise tel quel le décorateur `@retry` déjà en place (3 tentatives, backoff exponentiel 2/4/8s, `tenacity`) — appliqué au niveau du lot (une panne ne retente que son propre lot de 50, pas les 245) |
| Re-embedding automatique | **Non** — aucun déclenchement automatique depuis `upsert_rule()`/`enrich_again()` pour l'instant. Un recalcul après modification de contenu reste un geste manuel (relancer `scripts/embed_rules.py`) — cohérent avec le reste du pipeline. Risque assumé : embeddings temporairement désynchronisés du contenu si on oublie de relancer |
| `manifest.yml` | Nouveau rôle `embedding` : `modele: text-embedding-3-small`, `env_var: AZURE_MODEL_TEXT_EMBEDDING_SMALL`, prix en **euros** (comme le rôle `enrichissement`) — tarif public (~0,02 $/M tokens) converti en euros par **estimation** (pas de facture Azure réelle disponible, ce sera le premier usage réel de ce modèle), à corriger dès qu'une vraie facture existe |
| Indexation (Étape 7) | Pas de nouveau code dédié au-delà de la migration — `upsert_rule()` écrit la colonne `embedding` au même titre que les autres champs |

## 4. Modifications

### 4.1 Migration `0011_widen_embedding_dimension.py` (nouveau)

```python
def upgrade() -> None:
    op.execute("DROP INDEX regle_embedding_idx")
    op.execute("ALTER TABLE regle ALTER COLUMN embedding TYPE vector(1536)")
    op.execute("CREATE INDEX regle_embedding_idx ON regle USING hnsw (embedding vector_cosine_ops)")


def downgrade() -> None:
    op.execute("DROP INDEX regle_embedding_idx")
    op.execute("ALTER TABLE regle ALTER COLUMN embedding TYPE vector(384)")
    op.execute("CREATE INDEX regle_embedding_idx ON regle USING hnsw (embedding vector_cosine_ops)")
```

Aucune donnée à migrer (`embedding` est `NULL` sur les 245 lignes) —
changement de type direct, pas de conversion de valeurs existantes.

### 4.2 `app/models/referentiel.py`

`Regle.embedding` : `Vector(384)` → `Vector(1536)`.

### 4.3 `app/ingestion/manifest.yml`

Nouveau rôle, à la suite de `enrichissement` :

```yaml
embedding:
  modele: text-embedding-3-small
  env_var: AZURE_MODEL_TEXT_EMBEDDING_SMALL
  # Prix (€ pour 1M tokens d'entrée) — tarif public Azure/OpenAI (~0,02 $/M
  # tokens) converti en euros par estimation, aucune facture Azure réelle
  # disponible pour l'instant (premier usage réel de ce modèle). À corriger
  # dès qu'une vraie facture existe — même logique que le rôle enrichissement.
  prix_entree_par_million: 0.0184
```

### 4.4 `app/ingestion/chunking.py` (nouveau)

- `build_chunk_text(rule) -> str` : assemble le texte structuré avec labels
  à partir des champs d'un objet portant `intitule`, `contexte`, `solution`,
  `controle`, `guide_analyse`, `tags`, `phases` (compatible `EnrichedRule`
  et reconstruction depuis `Regle`). Omet la ligne `Contexte :` si `contexte`
  est `None`.

### 4.5 `app/ingestion/embedding.py` (nouveau)

- Client dédié (sur le modèle de `LLMClient`) : lit `manifest.yml` (rôle
  `embedding`) et l'endpoint/clé Azure déjà utilisés (`AZURE_AI_ENDPOINT`,
  `AZURE_AI_API_KEY`).
- `embed_batch(texts: list[str]) -> list[list[float]]` : appelle l'API
  Azure embeddings (`dimensions=1536`, passé explicitement) sur un lot
  (jusqu'à 50 textes), retry 3 tentatives/backoff exponentiel, accumule le
  total de tokens consommés pour le log de coût.

### 4.6 `app/ingestion/schema.py`

`EnrichedRule` : ajout `embedding: list[float] | None = None`.

### 4.7 `app/ingestion/stockage.py`

`upsert_rule()` : écrit `regle.embedding = enriched_rule.embedding` quand
non `None` (ne touche pas à la colonne sinon, cohérent avec le reste des
champs optionnels de provenance).

### 4.8 `scripts/embed_rules.py` (nouveau)

Point d'entrée CLI, sur le modèle de `scripts/enrich_again.py` : charge
toutes les règles depuis la BDD, construit leur chunk (`chunking.py`),
calcule les embeddings par lots de 50 (`embedding.py`), écrit le résultat
(`upsert_rule()`), logge le coût total (même format que les autres scripts).
Pas de `--dry-run` ni de confirmation interactive — à trancher en plan si
jugé utile, sur le modèle des scripts précédents.

### 4.9 `scripts/ingestion.py`

Étape 6 ajoutée après l'enrichissement (Étape 3), avant le stockage
(Étape 4) : chaque `EnrichedRule` reçoit son `embedding` calculé avant
l'appel à `store_rules()`.

## 5. Validation

1. Migration 0011 : up/down testé, `regle.embedding` en `vector(1536)`
   après `upgrade`, retour à `vector(384)` après `downgrade`, index HNSW
   présent dans les deux cas.
2. `build_chunk_text()` : un test unitaire par cas (avec/sans `contexte`),
   vérifie la présence des labels et l'omission propre de `contexte` si
   absent.
3. `embed_batch()` : test unitaire avec mock de l'appel Azure (pas de
   réseau réel dans les tests), vérifie le regroupement en lots de 50,
   `dimensions=1536` passé explicitement, et le retry.
4. `upsert_rule()` : test d'intégration (contre `qualicheck_test`, jamais
   `qualicheck`) vérifiant qu'un `embedding` de 1536 flottants survit à un
   cycle store → load.
5. `pytest`/`ruff` verts.
6. **Aucun appel réel à l'API Azure embeddings dans le cadre de ce
   chantier** — validation par tests avec mocks uniquement. Le premier
   calcul réel (`scripts/embed_rules.py` sur les 245 lignes) reste une
   décision et une action de David, hors périmètre de l'implémentation.

## 6. Hors périmètre (YAGNI)

- **Migration vers Infomaniak** (modèle exact, compatibilité `dimensions`,
  migration de schéma potentielle supplémentaire) — reporté explicitement,
  sujet distinct.
- **Re-embedding automatique** sur modification de contenu — geste manuel
  pour l'instant (cf. §3).
- **US2 (question libre, recherche sémantique)** — consommation de
  l'index HNSW par un agent de dialogue, non conçue à ce stade.
- **`--dry-run` / confirmation interactive sur `scripts/embed_rules.py`** —
  à trancher en plan si jugé utile, pas de décision de principe ici.
