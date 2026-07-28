# Règles d’exécution agent sur QualiCheck

## Validation et pédagogie

- Travailler par étapes vérifiables.
- Priorité explicite sur QualiCheck : la validation à chaque étape prime sur le défaut plus autonome de `~/.claude/CLAUDE.md` — s'arrêter et faire valider même quand ce n'est pas strictement bloquant.
- Expliquer les décisions importantes et les compromis.
- Conserver une logique simple, explicite, lisible.

## Changelog obligatoire

Toute réalisation doit être tracée dans CHANGELOG.md.

Format attendu :

`## [date] — [outil]`

`- [Ce qui a été fait] — voir [fichier(s) concerné(s)]`

## Base de données de test

Pour tout test d’intégration destructeur : utiliser POSTGRES_TEST_DB.

Ne pas cibler POSTGRES_DB pour des opérations qui effacent/modifient massivement les données locales.

Exception volontaire : `tests/migration/` cible `POSTGRES_DB` (lecture seule, vérifie le vrai schéma de dev) — ne pas y toucher. En CI, `POSTGRES_TEST_DB` réutilise `POSTGRES_DB` (base de service éphémère à chaque run) : ne pas reproduire cette égalité en local, ça recrée le risque de l'incident du 2026-07-25 (245 règles réelles effacées par un test d'intégration).

## Organisation du code

- scripts/ : points d’entrée uniquement
- app/ : logique métier
- conception/ : source de vérité fonctionnelle

## Branches

Travail au fil de l'eau directement sur `dev`, pas de découpage par sujet.
