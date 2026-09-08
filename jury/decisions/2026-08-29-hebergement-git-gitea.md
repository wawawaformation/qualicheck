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

> **Précision du 2026-08-30** : la compatibilité `uses:` de Gitea Actions
> (constatée en fonctionnement réel sur `ci-dev.yml`/`cd-staging.yml`) ne
> réimplémente pas les actions tierces — elle va chercher leur code là où
> elles sont réellement hébergées, c'est-à-dire `github.com` pour la quasi-
> totalité de l'écosystème (`actions/checkout`, `astral-sh/setup-uv`,
> `actions/setup-node`, `actions/upload-artifact`...). La bascule élimine
> la dépendance à GitHub pour l'hébergement du code, de l'historique et du
> CI/CD lui-même, **mais pas** pour ces briques tierces récupérées à
> l'exécution de chaque run — un accès réseau à `github.com` reste
> nécessaire. Alternative possible (non retenue ici) : miroirer ces actions
> sur Gitea, ou n'utiliser que des actions `docker://` autonomes.

## Installation

Déployé réellement sur `cloclo`, `/srv/docker/gitea/` — configuration
initiale le 2026-08-29, finalisée le 2026-08-30. Trois services dans un seul
`docker-compose.yml` : `app` (Gitea), `db` (sa base Postgres dédiée, séparée
de celle de QualiCheck), `runner` (`act_runner`, exécuteur des Actions) :

```yaml
services:
  app:
    image: gitea/gitea:latest
    container_name: gitea
    restart: unless-stopped
    depends_on:
      - db
    environment:
      - USER_UID=1000
      - USER_GID=1000
      - GITEA__server__ROOT_URL=https://git.david-legrand.fr/
      - GITEA__server__DOMAIN=git.david-legrand.fr
      - GITEA__server__SSH_DOMAIN=git.david-legrand.fr
      - GITEA__server__SSH_PORT=2222
      - GITEA__server__SSH_LISTEN_PORT=22
      - GITEA__database__DB_TYPE=postgres
      - GITEA__database__HOST=db:5432
      - GITEA__database__NAME=gitea
      - GITEA__database__USER=gitea
      - GITEA__database__PASSWD=${GITEA_DB_PASSWORD}
      - GITEA__mailer__ENABLED=true
      - GITEA__mailer__PROTOCOL=smtp+starttls
      - GITEA__mailer__SMTP_ADDR=mail.infomaniak.com
      - GITEA__mailer__SMTP_PORT=587
      - GITEA__mailer__USER=contact@david-legrand.fr
      - GITEA__mailer__PASSWD=${GITEA_SMTP_PASSWORD}
      - GITEA__mailer__FROM=contact@david-legrand.fr
      - GITEA__service__ENABLE_NOTIFY_MAIL=true
    volumes:
      - data:/data
    ports:
      - "2222:22"
    networks:
      - cloudnet

  db:
    image: postgres:17-alpine
    container_name: gitea-db
    restart: unless-stopped
    environment:
      - POSTGRES_USER=gitea
      - POSTGRES_PASSWORD=${GITEA_DB_PASSWORD}
      - POSTGRES_DB=gitea
    volumes:
      - db-data:/var/lib/postgresql/data
    networks:
      - cloudnet

  runner:
    image: gitea/act_runner:latest
    container_name: gitea-runner
    restart: unless-stopped
    depends_on:
      - app
    environment:
      - GITEA_INSTANCE_URL=https://git.david-legrand.fr
      - GITEA_RUNNER_REGISTRATION_TOKEN=${GITEA_RUNNER_REGISTRATION_TOKEN}
      - GITEA_RUNNER_NAME=cloclo
      - GITEA_RUNNER_LABELS=ubuntu-latest:docker://docker.gitea.com/runner-images:ubuntu-latest,ubuntu-24.04:docker://docker.gitea.com/runner-images:ubuntu-24.04,ubuntu-22.04:docker://docker.gitea.com/runner-images:ubuntu-22.04,self-hosted:host,cloclo:host
    volumes:
      - runner-data:/data
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - cloudnet

volumes:
  data:
  db-data:
  runner-data:
networks:
  cloudnet:
    external: true
```

Points notables :

- Port SSH Git publié en `2222:22` — le `22` de l'hôte reste réservé à
  l'accès SSH classique à `cloclo` — d'où `SSH_PORT=2222` côté config Gitea
  pour que les URLs `git clone ssh://...` générées par l'interface soient
  correctes.
- Le runner reçoit le socket Docker (`/var/run/docker.sock`) pour builder et
  exécuter les jobs. Labels multiples déclarés : images
  `docker://docker.gitea.com/runner-images:*` pour les jobs déclarant
  `runs-on: ubuntu-latest`/`ubuntu-24.04`/`ubuntu-22.04` (compatibilité
  directe avec la syntaxe GitHub Actions), plus `self-hosted:host` et
  `cloclo:host` pour les jobs qui doivent tourner directement sur l'hôte
  (cas de `cd-staging.yml`, qui a besoin d'accéder à Docker Compose et au
  réseau `cloudnet` de `cloclo` — un exécuteur en conteneur isolé ne le
  permettrait pas).

Config Caddy (`/srv/docker/reverse-proxy/Caddyfile`), même gabarit d'en-têtes
de sécurité que les autres domaines de `cloclo` :

```caddyfile
git.david-legrand.fr {
    encode zstd gzip

    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        Referrer-Policy "strict-origin-when-cross-origin"
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
        X-XSS-Protection "1; mode=block"
        Permissions-Policy "interest-cohort=()"
    }

    reverse_proxy gitea:3000
}
```

Secrets réels (`GITEA_DB_PASSWORD`, `GITEA_SMTP_PASSWORD`,
`GITEA_RUNNER_REGISTRATION_TOKEN`) dans `/srv/docker/gitea/.env`, non
versionnés, non reproduits ici.
