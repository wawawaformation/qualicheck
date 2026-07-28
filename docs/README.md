# Documentation map

Ce fichier est la porte d'entree de la documentation.

## Contexte actif pour agent

Lecture minimale recommandee (ordre):

1. `CLAUDE.md`
2. `docs/agent/04_contexte_actif.md`
3. `docs/agent/02_regles_execution.md`
4. `docs/agent/03_references_impl.md`
5. `CHANGELOG.md`

## Source de verite par sujet

- Vision produit: `conception/conception.md`
- Schema et migrations: `conception/1_BDD/bdd.md`
- Ingestion (spec): `conception/2_ingestion/ingestion.md`
- Historique d'implementation: `CHANGELOG.md`
- Commandes projet: `Makefile` et `docs/developpement/commandes.md`
- CI: `docs/developpement/ci.md`
- Déploiement staging: `docs/developpement/deploiement_staging.md`
- Créer une clé API (`/regles`): `docs/developpement/creation_cle_api_regles.md`

## Documents utiles mais non prioritaires en contexte agent

- `docs/problemes_rencontres/` : analyses detaillees apres incidents
- `docs/jury/` : livrables et preuves de certification
- `docs/superpowers/` : plans/specs de session, historique de travail

## Archives de veille

- `docs/jury/veille/fonds/` contient des sources longues.
- A ne pas charger par defaut dans le contexte agent general.
- A ouvrir seulement si la tache porte explicitement sur la veille C6.
