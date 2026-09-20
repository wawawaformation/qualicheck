# Règles d’exécution agent sur QualiCheck

## Validation et pédagogie

- Travailler par étapes vérifiables.
- Priorité explicite sur QualiCheck : la validation à chaque étape prime sur le défaut plus autonome de `~/.claude/CLAUDE.md` — s'arrêter et faire valider même quand ce n'est pas strictement bloquant.
- Expliquer les décisions importantes et les compromis.
- Conserver une logique simple, explicite, lisible.

## Aborder une carte (increment)

Séquence à suivre pour toute carte Kanboard / increment, quel que soit
l'outil agentique utilisé (Claude Code, OpenCode...) — ne pas sauter
d'étape, ne pas implémenter avant la fin de la séquence :

1. Réflexion, tracée dans le dossier de l'increment concerné (ex.
   `conception/.../increments/<epic>/`).
2. Se poser les bonnes questions — lever les ambiguïtés avant d'écrire
   quoi que ce soit (voir `CLAUDE.md` racine, section « Avant toute
   implémentation »).
3. Créer la fiche `.md` (user story, mesure, questions ouvertes).
4. Diviser en sous-tâches si besoin.
5. Écrire les scénarios Gherkin quand il y a lieu — ne pas sauter cette
   étape.
6. Créer ou enrichir le(s) schéma(s) `.drawio` (voir le skill
   `schemas-drawio`).
7. Une fois la conception réalisée (fiche `.md` + visuel), les joindre
   en pièce jointe sur la carte Kanboard correspondante (export du
   schéma, ex. PNG/SVG, en plus du `.drawio` source versionné dans
   `conception/`).
8. Cycle spec / plan d'implémentation au besoin.
9. Écrire les tests (unitaires puis intégration) — avant le code, jamais
   après.
10. Implémenter seulement une fois les 9 points précédents faits.

Début de séquence : dès le premier acte concret sur une carte, la passer en
colonne **En cours** (`column_id: 3`), renseigner sa **date de début** et
**lancer le chrono** (chrono d'une sous-tâche ; s'il n'y en a pas, en créer une
ou renseigner `time_spent` sur la carte). Le temps réel de chaque carte nourrit
la mesure du projet (écart estimé/réel) : sans lui, l'écart n'est pas mesurable.
Ne pas attendre que l'utilisateur le demande.

Fin de séquence : arrêter le chrono et vérifier que `time_spent` est renseigné,
puis, une fois la carte terminée, ajouter un commentaire de
clôture puis la déplacer en colonne **Done** (`column_id: 4`) et la
**laisser active** — ne jamais la fermer (`closeTask`), sinon elle disparaît
du board.

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

## Environnement local — `uv run` (shebang cassé, corrigé le 2026-09-09)

Incident résolu : `uv run pytest` / `uv run ruff` échouaient (shebang de
`.venv/bin/` pointant vers un ancien chemin de montage,
`/media/david/projets1/QualiCheck/.venv/bin/python`, depuis que le projet a
déménagé sur `/projets/QualiCheck`). Corrigé par régénération complète du
venv (`rm -rf .venv && uv sync` — un `uv sync` seul sur un venv déjà
"checked" ne suffit pas, il ne réécrit pas les shebangs existants).
`uv run <commande>` fonctionne à nouveau normalement. Si le symptôme
revient après un déplacement de dépôt, rejouer la même procédure plutôt que
réintroduire le contournement `.venv/bin/python -m ...`.

## Fichiers temporaires

Tout fichier temporaire (test de compilation, brouillon jetable, sortie
intermédiaire) s'écrit dans `./tmp/` à la racine du dépôt QualiCheck — jamais
dans `/tmp` système, ni dans un scratchpad d'agent hors du projet. `tmp/` est
déjà gitignoré et déjà utilisé ainsi (ingestion, revues, brouillons de spec).
Un test qui doit rester consultable par David (ex. un rendu PDF à valider)
n'a pas sa place dans un répertoire qui disparaît à la fin de la session.
