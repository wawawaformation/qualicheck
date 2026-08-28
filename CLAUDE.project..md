# Nom du projet

Règles projet spécifiques à <projet>.

## Sources d'instuctions

- .CLAUDE/*
- */CLAUDE.md
- README.md
- */README.md
- conception/**
- TODO*.md
- IDEA.md 



## Règles non négociables

- Méthode : spec -> validation -> implémentation.
- Changelog : toute réalisation est tracée dans `CHANGELOG.md`.
- Tests destructeurs : utiliser pour les tests d'integrations '`POSTGRES_TEST_DB`, jamais `POSTGRES_DB`.
- Pipeline LLM : retry 3 tentatives avec backoff.
- Fichiers temporaires : jamais dans `/tmp` système ni un scratchpad hors
  projet — toujours dans `./tmp/` à la racine du projet

## Priorités d'exécution

1. Lire la spec concernée dans `conception/`.
2. Implémenter uniquement le périmètre demandé (pas d'anticipation).
3. Vérifier (tests ciblés, lint, comportement).
4. Tracer dans `CHANGELOG.md`.
