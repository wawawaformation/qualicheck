# Règles d’exécution agent sur QualiCheck

## Validation et pédagogie

- Travailler par étapes vérifiables.
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

## Organisation du code

- scripts/ : points d’entrée uniquement
- app/ : logique métier
- conception/ : source de vérité fonctionnelle

## Branches

Créer une branche par sujet au fil de l’eau. Ne pas reconstituer rétroactivement l’historique ancien.
