# Fixtures pour la CI

## `referentiel_embedde.sql`

Dump `pg_dump --data-only` du référentiel Opquast déjà ingéré et embeddé
(245 règles), utilisé par `.gitea/workflows/ci-acceptance.yml` pour peupler
le Postgres éphémère du job d'acceptance sur tag, **sans refaire les appels
LLM réels** (ingestion + embedding) à chaque tag.

**Statique, pas régénéré automatiquement.** Devient périmé dès que le
référentiel change vraiment (nouvelles règles, ré-enrichissement,
ré-embedding sur `dev`/`staging`) — dans ce cas, le régénérer manuellement :

```bash
docker exec qualicheck-postgres pg_dump -U "$(grep POSTGRES_USER .env | cut -d= -f2)" \
  -d "$(grep '^POSTGRES_DB=' .env | cut -d= -f2)" --data-only \
  --exclude-table=alembic_version --exclude-table=etat_donnees \
  > tests/fixtures/referentiel_embedde.sql
```

(même commande que `make export_sql`, sortie redirigée ici au lieu de
`backups/`.) Puis committer le fichier mis à jour.

Voir `conception/4_ci_cd/strategie_tests_et_gates.md`.
