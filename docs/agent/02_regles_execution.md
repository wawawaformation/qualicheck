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

## Environnement local — `uv run` cassé (constaté 2026-09-08)

`uv run pytest` / `uv run ruff` échouent dans cet environnement : le
shebang des scripts de `.venv/bin/` pointe vers un ancien chemin de montage
(`/media/david/projets1/QualiCheck/.venv/bin/python`), alors que le projet
est maintenant sur `/projets/QualiCheck`. Contournement systématique tant
que le venv n'est pas régénéré : `.venv/bin/python -m pytest`,
`.venv/bin/python -m ruff check`, `.venv/bin/python scripts/....py` — pas
`uv run <commande>`. Concerne aussi les cibles `Makefile` qui appellent
`uv run` en interne (`make migration`, `make create-db-audit`, etc.) : si
une cible échoue pour cette raison, rejouer la commande sous-jacente avec
`.venv/bin/python` plutôt que d'y voir un bug de la cible elle-même. Non
corrigé volontairement le 2026-09-08 (hors du périmètre de la tâche en
cours ce jour-là) — un `uv sync`/régénération du venv réglerait
probablement le shebang, à faire quand ça vaut la peine d'interrompre le
travail en cours pour ça.

## Fichiers temporaires

Tout fichier temporaire (test de compilation, brouillon jetable, sortie
intermédiaire) s'écrit dans `./tmp/` à la racine du dépôt QualiCheck — jamais
dans `/tmp` système, ni dans un scratchpad d'agent hors du projet. `tmp/` est
déjà gitignoré et déjà utilisé ainsi (ingestion, revues, brouillons de spec).
Un test qui doit rester consultable par David (ex. un rendu PDF à valider)
n'a pas sa place dans un répertoire qui disparaît à la fin de la session.
