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
- Perimetre certification: ne pas elargir au-dela de ce qui valide les
  competences visees (`conception/referentiel_competences.md`,
  `conception/certif_deroule.md`)

## Source de verite technique

- Commandes: `Makefile`
- Pipeline: `scripts/ingestion.py` + `app/ingestion/`
- Config des roles/modeles: `app/ingestion/config.yml` (enrichissement, embedding), `app/retrieval/config.yml` (decomposition, jugement, guardrail, rag_acceptance)

## Chantier en cours

- Carte #45, strategie de tests : atelier de definitions avec David, suivi pas a pas dans
  `docs/strategie_tests_dialogue.md` (a lire en premier pour reprendre). Ne pas
  proposer de definition avant celle de David.

## Ce qu'il ne faut pas charger par defaut

- `docs/superpowers/**` (historique de plans)

Ce dossier reste utile, mais pas pour le contexte minimal quotidien.
