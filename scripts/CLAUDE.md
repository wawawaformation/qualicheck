# scripts/

Uniquement les points d'entrée, à plat. Aucune logique métier ici, aucun sous-dossier — l'orchestration appelle les modules situés dans `app/`.

## Fichiers

- **`migration.py`** : déclenche la montée de version Alembic. Logique et configuration dans `app/migration/`. Détail : `conception/1_BDD/bdd.md`.
- **`ingestion.py`** : orchestre les 7 étapes du pipeline d'ingestion en séquence (acquisition → agrégation → enrichissement → stockage → chunking → embedding → indexation), applique le principe fail-fast, écrit les logs. Modules dans `app/ingestion/`. Détail : `conception/2_us0/ingestion/ingestion.md`.
- **`enrich_again.py`** : réécriture ciblée des règles marquées `review_status = a_revoir`/`invalide`, en tenant compte de `review_note` (`--dry-run` pour prévisualiser sans appeler le LLM). Logique dans `app/ingestion/enrich_again.py`.
- **`creer_cle_api_regles.py`** : automatise la procédure manuelle de `docs/developpement/creation_cle_api_regles.md` (nouveau client autorisé au PATCH de `/regles`, dev + staging). Outil d'ops, pas de logique métier applicative — tient exceptionnellement sa logique en propre plutôt que dans `app/`. Modifie 4 fichiers et crée un vrai secret GitHub dans l'environnement `staging` (aucune simulation).

- **`embed_rules.py`** : recalcule et stocke les embeddings des règles déjà en base (`make embed-rules`), sans repasser par l'enrichissement. Modules dans `app/ingestion/`.
- **`create_db_audit.py`** : crée et migre la base du domaine audit (utilisé par la CI). Modules dans `app/migration/`.
- **`agent_cli.py`** : pose une question à l'agent US2 en ligne de commande et affiche la réponse et ses métriques. Logique dans `app/agent_us2/`.
- **`clear_opquast_tables.py`** : vide les tables du référentiel Opquast sur `POSTGRES_DB` (aucune confirmation). **Plus de cible `make`** depuis le 2026-09-20 : un seul appel efface les 245 règles enrichies. Sort de ce dossier ou est supprimé (décision en attente, voir `docs/scripts_reorganisation.md`).

## Ce qui n'est plus ici

Réorganisation du 2026-09-20 (carte Kanboard #44), détail dans `docs/scripts_reorganisation.md` :

- **Vérifications d'acceptance** (appels réels) : `tests/acceptance/`, à côté de leurs jeux de données.
- **Campagnes de mesure** : `tests/mesures/`. Elles contiennent de la logique, ce que ce dossier n'accepte pas.
- Trois scripts périmés, supprimés (ils écrivaient dans `POSTGRES_DB`).

Les cibles `make` gardent les mêmes noms : seuls les chemins ont changé.

## Changelog

Toute modification d'un point d'entrée ou de ses modules de support (`app/migration/`, `app/ingestion/`) est déclarée dans `CHANGELOG.md` à la racine — voir `CLAUDE.md` racine pour le format.
