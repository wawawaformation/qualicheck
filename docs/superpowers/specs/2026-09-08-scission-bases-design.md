# Conception — scission en deux bases (référentiel / audit)

> Spec d'incrément. Décision et justification :
> `jury/decisions/2026-09-08-deux-bases-referentiel-audit.md`.
> À valider avant implémentation.
>
> Date : 2026-09-08

## 1. Problème

Le référentiel Opquast et les données d'audit partagent une seule base
PostgreSQL. Quatre conséquences observables, détaillées dans la décision :
la frontière entre étages est une convention et non une contrainte ; la
sauvegarde est à l'échelle de la base et non du domaine ; le périmètre RGPD
est une liste de tables à maintenir ; deux régimes de licence cohabitent
dans le même magasin.

La fenêtre pour corriger est ouverte **maintenant** et se refermera au
premier audit réel.

## 2. État actuel (vérifié le 2026-09-08)

| Élément | État |
| --- | --- |
| Tables référentiel | `theme`, `regle`, `objectif`, `phase`, `tag`, `objectif_regle`, `phase_regle`, `regle_tag` — 245 règles réelles, vecteurs calculés |
| Tables métier | `audit`, `page`, `audit_page`, `audit_regle`, `constat`, `utilisateur` — **0 ligne sur les six** |
| Bookkeeping | `etat_donnees` (provenance du dernier export/import) |
| FK traversantes | **2** : `audit_regle.regle_id → regle.id`, `constat.regle_id → regle.id` |
| PK concernées | `audit_regle (audit_id, regle_id)`, `constat (audit_id, page_id, regle_id)` |
| Base déclarative | **une seule** (`app/models/base.py`), partagée par `referentiel.py`, `metier.py`, `etat.py` |
| Connexion | `app/db.py` — un moteur unique construit depuis `POSTGRES_DB` |
| Migrations | une chaîne, `app/migration/versions/0001` → `0012` |
| Sauvegarde | `make export_sql` : `pg_dump --data-only` de **toute** la base (hors `alembic_version`, `etat_donnees`) ; `import_sql` ne vide rien avant restauration |
| Tests de schéma | `tests/migration/test_migration.py` cible `POSTGRES_DB` et asserte **aussi** les tables métier |
| API | `GET /health`, `GET /version`, `GET /regles`, `GET /regles/{numero}`, `PATCH /regles/{numero}` |

## 3. Décisions de conception

| Point | Décision |
| --- | --- |
| Nombre de bases | Deux, dans **la même instance** PostgreSQL (un conteneur, un volume) |
| Base référentiel | `qualicheck` — l'existante, **inchangée quant aux données** : les 245 règles et leurs vecteurs ne bougent pas |
| Base audit | `qualicheck_audit` — nouvelle, créée vide |
| Nom asymétrique | Assumé. Renommer `qualicheck` → `qualicheck_referentiel` toucherait `.env`, `docker-compose.yml`, les secrets Actions Gitea et le déploiement staging pour un bénéfice cosmétique — dette documentée, non traitée ici |
| Référence croisée | `audit_regle.regle_numero INT` et `constat.regle_numero INT` remplacent `regle_id` — clé métier Opquast stable, déjà le langage des frontières du système (`GET /regles/{numero}`, `numero_regle_attendue`, `query_top_n_numeros()`) |
| PK décalées | `audit_regle (audit_id, regle_numero)`, `constat (audit_id, page_id, regle_numero)` |
| Intégrité des liens | Validation à la frontière API (`api_audit` vérifie l'existence du `numero` via `api_regles`), plus au niveau SGBD. Perte assumée et documentée |
| Bases déclaratives | Deux : `BaseReferentiel` et `BaseAudit`. Sans cela, l'`autogenerate` de chaque chaîne Alembic verrait les tables de l'autre domaine et proposerait de les supprimer |
| Chaînes Alembic | Deux. La chaîne existante (`app/migration/`) reste celle du **référentiel** et reçoit un `0013` qui `DROP` les six tables métier. Une chaîne neuve (`app/migration_audit/`) porte le schéma d'audit, son `0001` créant les six tables sous leur forme cible |
| Historique | Les migrations `0001`–`0012` continuent de mentionner les tables métier : c'est de l'histoire, elle ne se réécrit pas. Le `DROP` du `0013` est l'acte qui les déplace |
| Connexions | `app/db.py` expose deux constructeurs d'URL et deux moteurs, nommés par domaine. Aucun code ne doit pouvoir obtenir « la » session sans dire laquelle |
| `etat_donnees` | Reste côté référentiel — il trace les backups du référentiel |
| Sauvegarde | `export_sql`/`import_sql` deviennent explicitement référentiel (`-d qualicheck`). Le domaine audit n'a pas encore de données ni de cible de sauvegarde : à traiter avec US1, pas ici |
| Bases de test | Une par domaine. La règle existante ne change pas : aucun test destructeur ne cible une base de développement. `tests/migration/` (lecture seule) continue de viser les bases de développement |
| `pgvector` / HNSW | Restent sur la base référentiel uniquement |
| Lecture du référentiel par le métier | **Rien à construire.** `GET /regles` renvoie déjà les 245 règles en un appel, sans pagination (corpus figé, choix acté), avec les filtres `outil` et `review_status` ; `GET /regles/{numero}` pour une règle précise. Contrat : `https://regles.qualicheck.koabana.fr/docs` |
| `GET /dense` | **Hors périmètre.** Seule capacité manquante ; désignée par la décision, construite avec son consommateur (US2) |
| `api_audit` | **Hors périmètre.** Cette spec crée sa base et son schéma, pas son service — à concevoir avec US1 |

## 4. Modifications

### 4.1 `app/models/base.py`

Deux bases déclaratives au lieu d'une :

```python
class BaseReferentiel(DeclarativeBase):
    """Schéma de la base du référentiel Opquast."""


class BaseAudit(DeclarativeBase):
    """Schéma de la base des données d'audit."""
```

`referentiel.py` et `etat.py` héritent de `BaseReferentiel` ; `metier.py`
de `BaseAudit`.

### 4.2 `app/models/metier.py`

- `AuditRegle.regle_id` → `regle_numero = Column(Integer, nullable=False)`,
  sans `ForeignKey` ; PK `(audit_id, regle_numero)`.
- `Constat.regle_id` → `regle_numero` idem ; PK
  `(audit_id, page_id, regle_numero)`.
- Les FK **internes** au domaine (`audit.utilisateur_id`,
  `audit_page.audit_id`, `audit_page.page_id`, `constat.audit_id`,
  `constat.page_id`) sont conservées telles quelles.

### 4.3 `app/db.py`

Deux URL, deux moteurs, deux dépendances FastAPI — nommage explicite par
domaine (`get_session_referentiel`, `get_session_audit`), pas de session
« par défaut ». Deux nouvelles variables d'environnement,
`POSTGRES_DB_AUDIT` et `POSTGRES_TEST_DB_AUDIT`, ajoutées à `.env.example`.

### 4.4 Migration référentiel `0013_drop_tables_metier.py` (nouveau)

`DROP` des six tables métier dans l'ordre inverse des dépendances
(`constat`, `audit_regle`, `audit_page`, `page`, `audit`, `utilisateur`).
`downgrade()` les recrée sous leur forme **d'origine** (avec `regle_id` et
les FK) — c'est bien la réciproque de cette migration, pas la forme cible.

### 4.5 Chaîne `app/migration_audit/` (nouveau)

`alembic.ini`, `env.py` (`target_metadata = BaseAudit.metadata`,
connexion sur `POSTGRES_DB_AUDIT`), `versions/0001_schema_audit.py` créant
les six tables sous leur forme cible, avec les index existants
(`ix_constat_audit_id`, `ix_audit_regle_audit_id`).

### 4.6 `scripts/migration.py` et `Makefile`

- Le point d'entrée accepte le domaine visé ; `make migration` migre les
  deux, `make migration-referentiel` / `make migration-audit` ciblent l'un.
- `export_sql` / `import_sql` : `-d` explicitement sur la base référentiel.

### 4.7 Création de la base d'audit

L'image `pgvector/pgvector:pg17` ne crée qu'une base (`POSTGRES_DB`). Le
mécanisme habituel — un script monté dans
`/docker-entrypoint-initdb.d/` — ne s'exécute **que sur un volume vierge**,
donc pas sur l'installation existante ni après un simple `make up`.

**Un seul mécanisme, pas deux** : une cible `make create-db-audit`
idempotente, qui teste la présence de la base dans `pg_database` avant de
la créer (`CREATE DATABASE ... IF NOT EXISTS` n'existe pas en PostgreSQL).
Elle fonctionne aussi bien sur un volume existant que neuf, ce qui évite
d'avoir à maintenir un script d'init en parallèle. `docker-compose.yml`
n'est donc pas modifié.

### 4.8 `tests/migration/`

Scindé en deux fichiers : les assertions référentiel restent sur la base
référentiel ; les assertions métier (`TABLES_ATTENDUES` amputée,
`test_colonnes_not_null_audit`, `test_pk_composite_audit_page`,
`test_index_btree_constat_audit_id`, `test_index_btree_audit_regle_audit_id`)
passent sur la base d'audit. `test_pk_composite_constat` change d'attendu :
`(audit_id, page_id, regle_numero)`.

### 4.9 CI et staging

`ci-dev.yml` fournit aujourd'hui une base de service unique. Il devra en
déclarer une seconde (ou créer la base d'audit dans une étape préalable), et
`cd-staging.yml` de même — les secrets Actions gagnent
`POSTGRES_DB_AUDIT`. À vérifier réellement sur un run, la compatibilité du
bloc `services:` sous `act_runner` étant un point déjà identifié comme
sensible.

### 4.10 Documents de conception — source de vérité durable

Cette spec vit dans `docs/superpowers/specs/`, que
`docs/agent/04_contexte_actif.md` classe en « historique de plans, à ne pas
charger par défaut ». Elle est donc le **compte rendu de conception de ce
chantier**, pas la référence permanente. Sans les mises à jour ci-dessous, on
recrée exactement la dérive spec/réel corrigée le 2026-09-08 sur
`conception.md` : la source de vérité référencée continuerait de décrire une
seule base.

- **`conception/1_BDD/bdd.md`** — désigné par `docs/README.md` comme source de
  vérité « schéma et migrations ». Trois affirmations à corriger : couvrir
  « l'intégralité du schéma » en un seul modèle (§ Contexte) ; « la première
  migration crée le schéma complet » (§ Choix technique) ; l'ordre
  d'exécution à un seul `scripts/migration.py` (§ Déclenchement). À réécrire
  pour décrire deux bases, deux chaînes, et la frontière HTTP.
- **`conception/1_BDD/MLD_qualicheck.md`** — indiquer, par table, la base
  d'accueil ; mettre à jour la table des cardinalités (les deux relations
  traversantes ne sont plus des relations du même modèle) ; refléter
  `regle_numero`.
- **`conception/annexes/B_MCD_qualicheck.drawio`** — matérialiser la
  frontière entre les deux bases. À traiter avec les deux points de notation
  déjà ouverts dans `TODO.md` (association ternaire de `constat`, colonnes
  absentes), pour un seul passage sur le schéma plutôt que trois.
- **`docs/rgpd/registre_traitements.md`** — le périmètre des données
  personnelles devient une base, c'est l'un des quatre critères qui motivent
  la décision : il doit s'y lire.

## 5. Validation

Chaque étape est vérifiable indépendamment.

1. `make create-db-audit` deux fois de suite : idempotent, pas d'erreur.
2. Migration référentiel `0013` : `upgrade` puis `downgrade` puis `upgrade`
   — les six tables disparaissent, réapparaissent sous leur forme d'origine,
   redisparaissent. **Les 245 règles et leurs vecteurs sont intacts après
   chaque étape** (comptage + `embedding IS NOT NULL` sur 245).
3. Chaîne audit `0001` : `upgrade`/`downgrade` sur la base d'audit ; les six
   tables existent avec les bonnes PK et les deux index ; **aucune FK vers
   `regle`** (vérification explicite sur `pg_constraint`).
4. Isolation prouvée, et pas seulement affirmée : depuis une connexion à
   `qualicheck_audit`, un `SELECT` sur `regle` **échoue** ; une jointure
   `constat` × `regle` est impossible.
5. `make export_sql` : le dump produit ne contient **aucune** table métier.
6. `tests/migration/` scindé : les deux fichiers passent contre leur base.
7. `pytest` et `ruff` verts ; l'API `api_regles` répond toujours sur ses cinq
   routes (`/health` inclus).
8. Un run CI réel vert avant de considérer l'étape 4.9 faite.
9. **Anti-dérive** : relire `conception/1_BDD/bdd.md`,
   `MLD_qualicheck.md` et `docs/rgpd/registre_traitements.md` en cherchant
   « une seule base », « schéma complet » et `regle_id` — aucune occurrence
   ne doit subsister qui décrive le présent. Le chantier n'est pas fini tant
   que la source de vérité référencée par `docs/README.md` décrit l'ancienne
   architecture.

## 6. Hors périmètre (YAGNI)

- **`GET /dense`** — désigné par la décision, construit avec son consommateur
  (US2). Seule capacité que l'API n'expose pas encore : la lecture du
  référentiel est déjà couverte par `GET /regles` en un appel.
- **`app/api_audit`** — service à concevoir avec la spec US1.
- **Deux instances PostgreSQL** (au lieu de deux bases dans une instance) —
  évolution naturelle si le besoin apparaît, rendue peu coûteuse par cette
  scission logique.
- **Renommage de `qualicheck` en `qualicheck_referentiel`** — dette assumée.
- **Sauvegarde du domaine audit** — pas de données à sauvegarder aujourd'hui.
- **Validation applicative du `regle_numero`** — appartient à `api_audit`,
  qui n'existe pas encore.
