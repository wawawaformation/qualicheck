# Changelog

Historique des réalisations sur QualiCheck. Mis à jour par tout outil agentique utilisé (Claude Code, OpenCode...) — voir `CLAUDE.md` pour la règle d'usage.

Format d'entrée, une ligne par réalisation :

```
## [date] — [outil]
- [Ce qui a été fait] — voir [fichier(s) concerné(s)]
```

---

## 2026-07-18 — OpenCode

- Initialisation du dépôt Git — voir `.git/`
- Ajout du `.gitignore` (protection `.env`, Python, logs, éditeurs) — voir `.gitignore`
- Ajout du `.env.example` (variables PostgreSQL, valeurs vides) — voir `.env.example`
- Création du `.env` local (non versionné, valeurs de dev) — voir `.env`
- Ajout du `docker-compose.yml` : service `postgres` (pgvector/pgvector:pg17, port 8832, réseau `qualicheck`, volume `postgres_data`) — voir `docker-compose.yml`
- Ajout des docs de conception de la brique Docker/BDD — voir `docs/superpowers/specs/2026-07-18-docker-bdd-design.md`, `docs/superpowers/plans/2026-07-18-docker-bdd.md`

---
