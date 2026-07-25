---
title: Isolation des tests d'intégration destructeurs (base de test dédiée)
author: David LEGRAND
date: 2026-07-25
---

## 1. Problème

Le 2026-07-25, juste après la ré-ingestion réelle V5 (245 règles, 4,3210 €
de coût LLM), l'exécution de `uv run pytest tests/ -v` a effacé ces mêmes
245 règles.

Cause : `tests/integration/ingestion/test_stockage_contexte.py` et
`tests/integration/ingestion/test_stockage_provenance.py` ouvrent une
connexion Postgres construite directement à partir de `POSTGRES_HOST` /
`POSTGRES_DB` (les variables de `.env`) et appellent `clear_opquast_tables()`
en setup et en teardown. En local, ces variables pointent vers le même
conteneur (`qualicheck-postgres`) et la même base (`qualicheck`) que ceux
utilisés pour les vraies ingestions — ces deux tests traitent donc une base
de production locale comme une base jetable.

Le CI n'est pas concerné : chaque run y dispose d'un conteneur Postgres
éphémère dédié (`services.postgres` dans `ci-feature.yml`), sans donnée
réelle à perdre.

## 2. Décision

Une base Postgres séparée, sur le même conteneur qu'aujourd'hui (pas de
nouveau service Docker) : `qualicheck_test`. Les deux tests concernés s'y
connectent via une nouvelle variable d'environnement dédiée,
`POSTGRES_TEST_DB`, **jamais** via `POSTGRES_DB`.

Cette variable est **obligatoire** côté test (`os.environ["POSTGRES_TEST_DB"]`,
pas de valeur par défaut ni de repli sur `POSTGRES_DB`). Un repli silencieux
reproduirait exactement l'incident si la variable n'était pas positionnée
(nouveau poste, oubli) : la base réelle serait de nouveau utilisée sans
avertissement. L'absence de la variable doit faire échouer le test
immédiatement, avec un message explicite plutôt qu'un comportement dégradé.

## 3. Modifications

### 3.1 `.env` / `.env.example`

Nouvelle variable, à côté du bloc de connexion PostgreSQL existant :

```text
POSTGRES_TEST_DB=qualicheck_test
```

Commentaire dans `.env.example` : base séparée pour les tests d'intégration
destructeurs — ne jamais réutiliser `POSTGRES_DB`.

### 3.2 Makefile — cible `migration-test`

Nouvelle cible, sur le modèle de la cible `psql` existante (même façon de
lire `.env`) :

- Crée `qualicheck_test` si absente (requête idempotente sur `pg_database`
  via `psql`, pas de dépendance à l'outil `createdb`).
- Applique les migrations Alembic sur cette base, en surchargeant
  `POSTGRES_DB` pour l'invocation de `scripts/migration.py`. Ça fonctionne
  car `load_dotenv()` (utilisé par `app/migration/env.py`) ne réécrase
  jamais une variable déjà présente dans l'environnement du process — une
  variable positionnée en préfixe de commande shell (`POSTGRES_DB=... uv
  run ...`) prend donc le dessus sur la valeur lue dans `.env`.

```makefile
## Crée (si absente) et migre la base de test dédiée aux tests d'intégration
## destructeurs (jamais la base de dev réelle)
migration-test:
	docker exec qualicheck-postgres psql -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" -d postgres -tc \
		"SELECT 1 FROM pg_database WHERE datname = '$$(grep POSTGRES_TEST_DB .env | cut -d= -f2)'" | grep -q 1 || \
		docker exec qualicheck-postgres createdb -U "$$(grep POSTGRES_USER .env | cut -d= -f2)" "$$(grep POSTGRES_TEST_DB .env | cut -d= -f2)"
	POSTGRES_DB="$$(grep POSTGRES_TEST_DB .env | cut -d= -f2)" uv run python scripts/migration.py
```

### 3.3 Tests concernés

Dans `test_stockage_contexte.py` et `test_stockage_provenance.py`,
`_database_url()` :

```python
def _database_url():
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.environ["POSTGRES_TEST_DB"]
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"
```

Seul le nom de la variable change (`POSTGRES_DB` → `POSTGRES_TEST_DB`,
lecture obligatoire via `os.environ[...]`) — aucune autre logique de test
modifiée.

### 3.4 CI — `.github/workflows/ci-feature.yml`

Ajout dans le bloc `env` du job, même valeur que la base éphémère existante
(elle est déjà jetable, donc aucun changement de comportement CI — la
variable est ajoutée uniquement pour satisfaire l'exigence des tests) :

```yaml
env:
  POSTGRES_USER: ${{ secrets.POSTGRES_USER }}
  POSTGRES_PASSWORD: ${{ secrets.POSTGRES_PASSWORD }}
  POSTGRES_DB: ${{ secrets.POSTGRES_DB }}
  POSTGRES_TEST_DB: ${{ secrets.POSTGRES_DB }}
  POSTGRES_HOST: localhost
  POSTGRES_PORT: 5432
```

### 3.5 `CLAUDE.md` — convention à documenter

Nouvelle règle actée, dans la section stack/tests du `CLAUDE.md` racine :
tout futur test d'intégration nécessitant une vraie connexion Postgres doit
utiliser `POSTGRES_TEST_DB`, jamais `POSTGRES_DB` directement. Justification
citée : l'incident du 2026-07-25 (perte des 245 règles V5 réingérées, suite
à `pytest tests/` lancé juste après l'ingestion).

## 4. Validation

1. `make migration-test` : la base `qualicheck_test` existe et contient le
   schéma à jour (mêmes tables que `qualicheck`).
2. `uv run pytest tests/integration/ingestion/test_stockage_contexte.py
   tests/integration/ingestion/test_stockage_provenance.py -v` : passent,
   et `SELECT count(*) FROM regle` sur la base **`qualicheck`** (pas
   `qualicheck_test`) reste inchangé avant/après l'exécution.
3. Retirer `POSTGRES_TEST_DB` de l'environnement et relancer ces deux
   tests : échec explicite (`KeyError: 'POSTGRES_TEST_DB'`), pas de
   fallback silencieux sur `POSTGRES_DB`.
4. `uv run pytest tests/ -v` complet : vert.
5. CI (prochain push) : vert, sans secret supplémentaire à créer côté
   GitHub (réutilise `POSTGRES_DB`).

## 5. Hors périmètre

- Ré-ingestion réelle V5 pour reconstituer les 245 règles perdues —
  décision et déclenchement laissés à David, indépendamment de ce chantier.
- Toute automatisation de sauvegarde/restauration de la base de dev réelle
  (pg_dump périodique, etc.) — non demandé, au-delà du problème traité ici.
- Migration des autres tests d'intégration existants (aucun autre fichier
  ne touche une vraie connexion Postgres aujourd'hui — vérifié par
  recherche sur `create_engine`/`POSTGRES_HOST` dans `tests/integration/`).
