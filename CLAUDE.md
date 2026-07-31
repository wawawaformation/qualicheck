# QualiCheck

Règles projet spécifiques à QualiCheck.

Ce fichier est volontairement court pour limiter les tokens. Le détail est dispatché dans `docs/agent/`.

## Sources d'instructions

- Point d'entree documentation : `docs/README.md`
- Contexte projet : `docs/agent/01_contexte_projet.md`
- Règles d'exécution : `docs/agent/02_regles_execution.md`
- Références d'implémentation : `docs/agent/03_references_impl.md`
- Contexte actif compact : `docs/agent/04_contexte_actif.md`
- Conventions `app/` : `app/CLAUDE.md`
- Conventions `scripts/` : `scripts/CLAUDE.md`

## Règles non négociables

- Méthode : spec -> validation -> implémentation.
- Changelog : toute réalisation est tracée dans `CHANGELOG.md`.
- Tests destructeurs : utiliser `POSTGRES_TEST_DB`, jamais `POSTGRES_DB`.
- Pipeline LLM : retry 3 tentatives avec backoff.
- Coût : éviter les ré-ingestions complètes non nécessaires.
- Périmètre certification : ne pas élargir au-delà de ce qui valide les
  compétences visées (`conception/referentiel_competences.md`,
  `conception/certif_deroule.md`) — temps de certification restreint,
  proposer plus large est un risque, pas un service.
- Fichiers temporaires : jamais dans `/tmp` système ni un scratchpad hors
  projet — toujours dans `./tmp/` à la racine de QualiCheck (déjà
  gitignoré). Détail : `docs/agent/02_regles_execution.md`.

## Priorités d'exécution

1. Lire la spec concernée dans `conception/`.
2. Implémenter uniquement le périmètre demandé (pas d'anticipation).
3. Vérifier (tests ciblés, lint, comportement).
4. Tracer dans `CHANGELOG.md`.

## Ordre d'exécution courant

1. `scripts/migration.py`
2. `scripts/ingestion.py`

Le reste (audit, dialogue, question libre) continue d'évoluer par specs incrémentales.
