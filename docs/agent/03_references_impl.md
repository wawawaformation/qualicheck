# Références à consulter avant implémentation

## Sources de vérité

Pour chaque donnée ci-dessous, un seul endroit fait foi. Ne pas la
recopier ou la déduire ailleurs — la relire à la source à chaque fois
qu'elle compte pour une décision.

| Donnée | Source de vérité | Piège |
|---|---|---|
| Prix/modèle LLM à utiliser au prochain run (enrichissement, embedding) | `app/ingestion/manifest.yml` | — |
| Seuils du jeu d'acceptance RAG (`top_n`, `taux_reussite_minimum`) | `app/ingestion/manifest.yml` (section `rag_acceptance`) | — |
| Version de prompt active, à écrire au prochain enrichissement | Frontmatter de `app/ingestion/prompts/enrich_rule.md` | — |
| Version de prompt ayant produit une règle donnée (déjà en base) | Colonne `regle.prompt_version` | `manifest.yml` et le frontmatter du prompt ne le savent pas — un `enrich_again` partiel peut mélanger les versions règle par règle |
| Modèle LLM ayant produit une règle donnée | Colonne `regle.llm_model` | — |
| Schéma de données réellement en place | Migrations Alembic (`app/migration/versions/`) | `conception/MLD_qualicheck.md` et le dictionnaire de données décrivent la **cible**, pas forcément l'état réel courant (convention `X_reel` vs cible, ex. `docs/schemas/`) |
| Dernière opération d'export/import de backup | Table `etat_donnees` | — |
| Décisions d'architecture actées et leur justification | `docs/jury/decisions/*.md` | — |
| Avancement détaillé du pipeline d'ingestion (étapes 1-7) | `TODO_PIPELINE_INGESTION.md` | Non dupliqué dans `TODO.md` (transverse) |
| Historique des réalisations (ce qui a été fait, quand) | `CHANGELOG.md` | Ne décrit que le passé, pas les décisions à venir (`TODO.md`) |
| Variables d'environnement/secrets réels | `.env` (non versionné) | `.env.example` documente les clés attendues, pas les valeurs réelles |
| Configuration de l'API données (port, origines CORS, titre, version du contrat) | `app/api_regles/manifest.yml` | — |
| Token Bearer des écritures de l'API données | `.env` (`FASTAPI_API_KEY`) | `FASTAPI_API_ID` existe mais n'est volontairement pas utilisé |

## Spécifications principales

- conception/conception.md
- conception/1_BDD/bdd.md
- conception/2_ingestion/ingestion.md
- conception/MLD_qualicheck.md
- conception/A_dictionnaire_donnees_qualicheck.xlsx

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
