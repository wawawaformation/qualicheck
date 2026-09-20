# Références à consulter avant implémentation

## Sources de vérité

Pour chaque donnée ci-dessous, un seul endroit fait foi. Ne pas la
recopier ou la déduire ailleurs — la relire à la source à chaque fois
qu'elle compte pour une décision.

| Donnée | Source de vérité | Piège |
|---|---|---|
| Prix/modèle LLM à utiliser au prochain run (enrichissement, embedding) | `app/ingestion/config.yml` | — |
| Seuils du jeu d'acceptance RAG (`top_n`, `taux_reussite_minimum`) | `app/retrieval/config.yml` (section `rag_acceptance`) | — |
| Rôles LLM du retrieval (decomposition, jugement, guardrail) | `app/retrieval/config.yml` | — |
| Version de prompt active, à écrire au prochain enrichissement | Frontmatter de `app/ingestion/prompts/enrich_rule.md` | — |
| Version de prompt ayant produit une règle donnée (déjà en base) | Colonne `regle.prompt_version` | `config.yml` et le frontmatter du prompt ne le savent pas — un `enrich_again` partiel peut mélanger les versions règle par règle |
| Modèle LLM ayant produit une règle donnée | Colonne `regle.llm_model` | — |
| Schéma de données réellement en place | Migrations Alembic (`app/migration/versions/`) | `conception/1_BDD/MLD_qualicheck.md` et le dictionnaire de données décrivent la **cible**, pas forcément l'état réel courant (convention `X_reel` vs cible, ex. `docs/schemas/`) |
| Dernière opération d'export/import de backup | Table `etat_donnees` | — |
| Décisions d'architecture actées et leur justification | `jury/decisions/*.md` | — |
| Avancement détaillé du pipeline d'ingestion (étapes 1-7) | `TODO_PIPELINE_INGESTION.md` | Non dupliqué dans `TODO.md` (transverse) |
| Historique des réalisations (ce qui a été fait, quand) | `CHANGELOG.md` | Ne décrit que le passé, pas les décisions à venir (`TODO.md`) |
| Variables d'environnement/secrets réels | `.env` (non versionné) | `.env.example` documente les clés attendues, pas les valeurs réelles |
| Configuration de l'API données (port, origines CORS, titre, version du contrat) | `app/api_regles/config.yml` | — |
| Jetons Bearer des écritures de l'API données (un par client nommé) | `app/api_regles/config.yml` (section `clients`) + `.env` (une variable par client) | — |
| Configuration de l'API business (port 8882, `POST /questions`) | `app/agent_us2/config.yml` (section `api_business`) | l'API business est le futur étage partagé US1/US2 (`conception/3_autre_us/en_commun.md`) — les routes `/questions/...` existent, `/audits/...` viendra avec US1 |
| URL/port des APIs selon l'environnement (dev/preprod) | `.env` (`API_REGLES_URL_DEV`, `API_REGLES_URL_PREPROD`, `API_BUSINESS_URL_DEV`, `API_BUSINESS_URL_PREPROD`) | `API_BUSINESS_URL_DEV` = `http://localhost:8882` ; l'agent US2 lit l'URL des règles via `API_REGLES_URL_DEV` (nom déclaré dans `app/agent_us2/config.yml`) |

## Spécifications principales

- conception/conception.md
- conception/1_BDD/bdd.md
- conception/1_BDD/MLD_qualicheck.md
- conception/1_BDD/A_dictionnaire_donnees_qualicheck.xlsx
- conception/2_us0/ingestion/ingestion.md
- conception/2_us0/enrichissement/E_provenance_manifeste.md
- conception/2_us0/api_regles/api_regles.md

## Exécution et commandes

- Makefile
- docs/developpement/commandes.md
- docs/developpement/ci.md

## Conventions locales

- app/CLAUDE.md
- scripts/CLAUDE.md

## Livrables certification (au moment de documenter)

- conception/referentiel_competences.md
- conception/certif_deroule.md
