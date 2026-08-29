# Hébergement Git et CI/CD : Gitea plutôt que GitHub

2026-08-29 · retenu (bascule via essai non destructif, pas encore exécutée)

## Contexte

Même déclencheur que `2026-08-29-outil-pilotage-kanban.md` : vérifier la
cohérence entre le positionnement éthique affiché du projet
(`conception/conception.md` § Souveraineté numérique) et les outils
réellement utilisés. GitHub (Microsoft, États-Unis) héberge le dépôt
QualiCheck et sa CI/CD (`ci-dev.yml`, `cd-staging.yml`, un runner
auto-hébergé sur `cloclo`) depuis le début du projet — en tension directe
avec ce positionnement, plus large que le seul sujet kanban.

Contrainte que la décision précédente n'avait pas : ici, il ne s'agit pas
d'un outil neuf sans historique, mais de faire bouger une CI/CD **qui
fonctionne déjà en production** (déploiement staging réel). Le risque de
casser un pipeline opérationnel est d'un autre ordre que celui de choisir un
outil de pilotage.

## Options envisagées

**Rester sur GitHub** — pour : rien à migrer, zéro risque. Contre : contredit
le positionnement éthique affiché ; le coût de migration ne fera que croître
avec le temps (plus d'historique, plus de workflows, plus de dépendances) —
attendre n'élimine pas la question, la reporte à un moment plus coûteux.

**GitLab** — pour : alternative connue, CI intégrée. Contre : GitLab Inc.
est une société américaine (Delaware) ; GitLab.com (SaaS) est hébergé sur
GCP — ne répond pas mieux au critère de souveraineté qu'une bascule vers un
autre SaaS américain.

**Codeberg** — pour : hébergement associatif allemand à but non lucratif,
basé sur Gitea (logiciel libre), répond directement à « libre et européen »
sans aucune infrastructure à gérer. Contre : reste un tiers hébergeur (moins
de contrôle qu'un auto-hébergement complet) ; CI (Codeberg CI, Woodpecker)
distincte de Gitea Actions, à vérifier séparément si retenue plus tard.

**Gitea auto-hébergé sur `cloclo` (retenu)** — pour : souveraineté complète
(serveur déjà utilisé pour le staging QualiCheck), logiciel libre, **Gitea
Actions ~90 % compatible avec la syntaxe GitHub Actions** (mêmes clés
`on:`/`jobs:`/`steps:`, même `uses:` pour les actions tierces — vérifié dans
plusieurs sources concordantes), **registre de conteneurs OCI intégré et
activé par défaut** (remplace `ghcr.io` sans service supplémentaire —
inquiétude directement héritée d'une expérience personnelle antérieure sur un
autre projet, résolue). Expérience personnelle positive déjà vécue sur un
autre projet (Gitea + CI en `.yml`). Contre : aucun runner « hébergé »
fourni comme chez GitHub — toute exécution repose sur un runner qu'on gère
soi-même (déjà le cas pour `cd-staging.yml` via le runner `cloclo`
existant ; `ci-dev.yml`, actuellement `runs-on: ubuntu-latest`, devra
pointer vers ce même runner avec un label adapté, sous peine de rester
bloqué indéfiniment en attente sans erreur explicite). Comportement du bloc
`services:` (conteneur Postgres éphémère de `ci-dev.yml`) sous `act_runner`
non vérifié par la recherche — à valider empiriquement, le runner tournant
sur un réseau séparé de l'instance Gitea pour des raisons de sécurité.

## Décision

**Gitea auto-hébergé sur `cloclo`**, migration par **essai non destructif** :
ajout de Gitea comme second remote Git (`origin` GitHub inchangé), miroir du
dépôt, `.gitea/workflows/` testés en parallèle sur le runner `cloclo`
existant, sans toucher au pipeline GitHub actuel tant que l'essai n'est pas
validé. Bascule définitive (DNS, `git remote set-url`, invitation des
collaborateurs) uniquement après validation réelle — pas dans cette session.

Critère qui a tranché : le contre-argument « déjà sur GitHub » perd sa force
face à un chemin de migration à risque nul (essai en parallèle) — reporter
n'aurait fait qu'alourdir un futur transfert, sans réduire le risque
aujourd'hui.

## Conséquences

- `ci-dev.yml` doit être adapté (label de runner) avant de pouvoir tourner
  sous Gitea Actions — pas un simple copier-coller comme `cd-staging.yml`.
- Le comportement de `services:` (Postgres éphémère) reste à vérifier
  empiriquement lors de l'essai — point d'incertitude assumé, pas ignoré.
- Plugin Kanboard **Github Webhook Plus** (cf. décision kanban) devient sans
  objet si la bascule Git aboutit — à remplacer par l'équivalent Gitea
  (webhooks natifs vers Actions automatiques) le moment venu.
- Le registre de conteneurs Gitea répond par avance à un risque identifié
  dès le départ (dépendance à `ghcr.io`) — non applicable à QualiCheck
  aujourd'hui (déploiement par build local sur `cloclo`, jamais de push/pull
  de registre), mais utile si le modèle de déploiement évolue plus tard.
- Décision indépendante de celle sur Kanboard : chacune reste valable même
  si l'autre était révisée séparément.
