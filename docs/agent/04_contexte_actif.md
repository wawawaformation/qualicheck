# Contexte actif (version compacte)

Objectif: donner un contexte fiable et peu couteux en tokens.

## Ce que l'agent doit faire en premier

1. Lire `CLAUDE.md`
2. Lire `docs/agent/02_regles_execution.md`
3. Lire la spec directement concernee dans `conception/`
4. Verifier les dernieres actions dans `CHANGELOG.md`

## Regles critiques

- Workflow: spec -> validation -> implementation
- Tracabilite: toute realisation est enregistree dans `CHANGELOG.md`
- Tests destructeurs: `POSTGRES_TEST_DB` uniquement
- Appels LLM: 3 retries avec backoff
- Limiter les re-ingestions completes (cout)

## Source de verite technique

- Commandes: `Makefile`
- Pipeline: `scripts/ingestion.py` + `app/ingestion/`
- Manifest des roles/modeles: `app/ingestion/manifest.yml`

## Ce qu'il ne faut pas charger par defaut

- `docs/jury/veille/fonds/**` (documents longs)
- `docs/superpowers/**` (historique de plans)

Ces dossiers restent utiles, mais pas pour le contexte minimal quotidien.
