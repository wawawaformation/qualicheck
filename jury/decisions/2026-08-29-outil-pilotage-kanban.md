# Outil de pilotage agile : Kanboard

2026-08-29 · retenu

## Contexte

En travaillant sur la spec US2, un point de méthode a émergé : penser la
validation/le pilotage **pendant** la conception plutôt qu'après coup (cf.
mémoire de session, correction explicite sur C13). En vérifiant la
compétence C16 (« coordonner la réalisation technique... outils de pilotage
[kanban, burndown chart, backlog...], rituels partagés ») contre l'existant
du projet, le constat a été net : `TODO.md`/`CHANGELOG.md` font office de
backlog/journal, mais ce ne sont ni un kanban visuel, ni un outil produisant
un burndown — le critère demande explicitement ce type d'outil.

Contrainte de fond, déjà affichée dans `conception/conception.md`
(§ Souveraineté numérique) : le projet revendique une posture éthique sur la
souveraineté numérique. Un outil de pilotage choisi pour combler C16 ne
peut pas contredire ce positionnement sans le vider de son sens.

Les rituels agiles (planification, revue) sont écartés du périmètre de
cette décision — jugés difficiles à faire exister honnêtement dans un
contexte solo + assistant IA, sans tomber dans la performance artificielle.

## Options envisagées

**Notion** — pour : connecteur MCP déjà présent dans l'environnement de
développement, zéro infrastructure à monter, pilotable immédiatement. Contre :
SaaS américain non-souverain, en contradiction directe avec le positionnement
éthique déjà affiché du projet.

**Trello** — pour : simple, connu. Contre : même problème de souveraineté
que Notion, sans même le bénéfice du connecteur MCP déjà prêt.

**Planka** (auto-hébergé, libre) — pour : interface façon Trello, cohérent
avec la souveraineté visée, API REST complète (utilisateurs, projets,
tableaux, cartes, membres, commentaires, étiquettes, pièces jointes, champs
personnalisés, webhooks — vérifié dans `server/config/routes.js` du dépôt
officiel). Contre : **pas de burndown chart natif** — fonctionnalité
seulement demandée, jamais implémentée (issue GitHub #895 du dépôt
`plankanban/planka`, toujours ouverte). Aurait fallu le reconstruire à la
main via l'API pour répondre pleinement au critère C16.

**Kanboard** (auto-hébergé, libre, retenu) — pour : même cohérence de
souveraineté que Planka, mais avec un **burndown chart natif** (calculé sur
le champ complexité des tâches, cf. doc officielle et
`app/Template/analytic/burndown.php` du dépôt), une section Analytics plus
large, des relations de tâches natives (« bloque » / « est bloquée par »,
utile pour les dépendances entre tâches identifiées comme réelles), et un
plugin **AgileIndicators** (MIT, actif — dernier commit à 2 semaines de
cette décision) pour rendre visible priorité/complexité sur les cartes.
Contre : expérience mitigée d'un essai personnel il y a 1-2 ans (interface
datée, partage pénible) — nuancé par une vraie activité de maintenance
récente (versions jusqu'à juillet 2026, refontes incrémentales de
l'interface) ; à revalider avec un œil neuf plutôt que sur un souvenir
ancien.

Plugin **Backlog** (`vistree/kanboard-backlog`) envisagé pour matérialiser
un backlog en colonne dédiée — écarté : abandonné depuis 2019 (dernier
commit), risque de rupture avec la version actuelle de Kanboard sans aucune
maintenance en face. Un backlog reste modélisable nativement par une simple
colonne nommée, sans plugin.

Plugin **Github Webhook** (officiel, `kanboard/plugin-github-webhook`)
envisagé pour lier commits/PR GitHub aux cartes — écarté au profit du fork
**Github Webhook Plus** (`y9938/plugin-github-webhook-plus`, MIT, actif) :
l'officiel est archivé depuis 2020.

## Décision

**Kanboard**, auto-hébergé sur `cloclo`, sous-domaine `kanban.david-legrand.fr`
(hors domaine `qualicheck.koabana.fr` : outil personnel de pilotage, pas un
composant du produit). Plugin **AgileIndicators** activé pour
priorité/complexité. Plugin **Github Webhook Plus** envisagé une fois la
question de l'hébergement Git elle-même tranchée (cf.
`2026-08-29-hebergement-git-gitea.md`). `PLUGIN_INSTALLER=false` (défaut
sécurisé de l'image officielle depuis la v1.2.8 — Kanboard ne fait aucune
revue de code sur les plugins listés dans son annuaire officiel).

Critère qui a tranché : à cohérence de souveraineté égale entre Planka et
Kanboard, seul Kanboard répond nativement à l'exigence de burndown chart du
critère C16 — éviter de reconstruire à la main une fonctionnalité qui existe
déjà ailleurs.

## Conséquences

- Le backlog vit comme une colonne de tableau, pas un module dédié — suffit
  à répondre à l'esprit du critère sans plugin supplémentaire à maintenir.
- Priorité/complexité doivent être réellement estimées tâche par tâche pour
  que le burndown ait un sens — un champ non renseigné produit un graphe
  vide ou trompeur, pas une preuve de pilotage.
- Rituels agiles toujours hors périmètre — reste une limite assumée de C16
  pour ce projet (solo + assistant IA), pas quelque chose que l'outil seul
  peut combler.
- Décision indépendante de `2026-08-29-hebergement-git-gitea.md` : Kanboard
  reste pertinent que le dépôt Git reste sur GitHub ou bascule vers Gitea.
