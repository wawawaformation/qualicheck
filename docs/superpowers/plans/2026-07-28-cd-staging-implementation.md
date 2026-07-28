# CD Staging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Créer le workflow GitHub Actions `cd-staging.yml` qui déploie `app/api_regles/` sur le serveur personnel de David (cloclo) au merge d'une PR vers la branche `staging`, plus le runbook des étapes manuelles que David doit exécuter lui-même sur son infrastructure.

**Architecture:** Un seul job GitHub Actions, déclenché par un push sur `staging`, exécuté sur un runner self-hosted enregistré sur cloclo : checkout → écriture d'un `.env` depuis les secrets de l'environnement GitHub `staging` → migrations Alembic → `docker compose up -d --build` → rejeu de la suite d'acceptance existante (`make api-regles-acceptance`) comme garde-fou.

**Tech Stack:** GitHub Actions (runner self-hosted), Docker Compose, Alembic (`scripts/migration.py`), `uv`, Make.

## Global Constraints

- Un seul workflow, pas un fichier par service (`api_regles`/`api_audit`/`api_business` partagent la même stack Docker, la même base, les mêmes migrations)
- Runner self-hosted sur cloclo (connexion sortante uniquement), jamais de SSH entrant
- Déclencheur : `push` sur la branche `staging` (survient au merge d'une PR)
- Pas de rollback automatique si l'acceptance échoue après déploiement
- Réutiliser les commandes `make` existantes (`make migration`, `make up`, `make api-regles-acceptance`) plutôt que de dupliquer les commandes brutes dans le YAML
- Aucune action sur l'infrastructure personnelle de David (cloclo, sa box, son DNS/Caddy) exécutée par l'agent — tout ce qui touche à ces éléments est documenté dans un runbook, exécuté par David lui-même
- CORS (`app/api_regles/manifest.yml`) reste inchangé — Élie et le formateur utilisent un client HTTP direct (curl/Bruno/Postman), pas un navigateur. Ne pas ajouter `regles.qualicheck.koabana.fr` aux origines CORS, ce n'est pas un oubli
- Spec source : `docs/superpowers/specs/2026-07-28-cd-staging-design.md`

---

## Task 1: Créer la branche `staging`

**Files:**

- Aucun fichier — opération git pure

**Interfaces:**

- Produces: la branche `staging` sur `origin`, point de départ identique à `feature` au moment de la création — déclencheur du workflow créé en Task 2

- [ ] **Step 1: Vérifier l'état de la branche feature locale**

Run: `git -C /media/david/projets/QualiCheck status`

Expected: `On branch feature`, `nothing to commit, working tree clean` (si des modifications non commitées existent, s'arrêter et les traiter avant de continuer — ne pas créer `staging` sur un état incertain)

- [ ] **Step 2: Créer la branche staging depuis feature**

Run:

```bash
git -C /media/david/projets/QualiCheck fetch origin
git -C /media/david/projets/QualiCheck checkout feature
git -C /media/david/projets/QualiCheck merge --ff-only origin/feature
git -C /media/david/projets/QualiCheck checkout -b staging
```

- [ ] **Step 3: Pousser la branche staging**

Run: `git -C /media/david/projets/QualiCheck push -u origin staging`

- [ ] **Step 4: Vérifier que la branche existe côté origin**

Run: `git -C /media/david/projets/QualiCheck ls-remote --heads origin staging`

Expected: une ligne avec un hash de commit suivi de `refs/heads/staging`

- [ ] **Step 5: Revenir sur feature pour la suite du travail**

Run: `git -C /media/david/projets/QualiCheck checkout feature`

---

## Task 2: Écrire le workflow `cd-staging.yml`

**Files:**

- Create: `.github/workflows/cd-staging.yml`
- Modify: `docs/developpement/ci.md`
- Modify: `Makefile` (nouvelle cible `up-db`, découverte nécessaire lors du premier run réel — Postgres doit tourner avant les migrations sur un environnement neuf)

**Interfaces:**

- Consumes: `make migration` (Makefile, existant), `make up` (Makefile, existant), `make api-regles-acceptance` (Makefile, existant), `make up-db` (Makefile, nouveau dans cette tâche) — aucune modification des cibles existantes
- Consumes: secrets de l'environnement GitHub `staging` (créé manuellement, voir Task 3) : `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `FASTAPI_API_KEY`, `FASTAPI_API_KEY_ELIE`, `FASTAPI_API_KEY_DAVID`, `FASTAPI_API_KEY_FORMATEUR`
- Produces: le fichier `.github/workflows/cd-staging.yml`, déclenché par un push sur `staging`

- [ ] **Step 1: Écrire le fichier de workflow**

Créer `/media/david/projets/QualiCheck/.github/workflows/cd-staging.yml` :

```yaml
name: CD — Staging

on:
  push:
    branches:
      - staging

concurrency:
  group: staging-deploy
  cancel-in-progress: false

jobs:
  deploy:
    runs-on: [self-hosted, cloclo]
    environment: staging
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Écrire .env depuis les secrets de l'environnement staging
        run: |
          cat > .env << 'EOF'
          POSTGRES_USER=${{ secrets.POSTGRES_USER }}
          POSTGRES_PASSWORD=${{ secrets.POSTGRES_PASSWORD }}
          POSTGRES_DB=${{ secrets.POSTGRES_DB }}
          POSTGRES_HOST=localhost
          POSTGRES_PORT=8832
          FASTAPI_API_KEY=${{ secrets.FASTAPI_API_KEY }}
          FASTAPI_API_KEY_ELIE=${{ secrets.FASTAPI_API_KEY_ELIE }}
          FASTAPI_API_KEY_DAVID=${{ secrets.FASTAPI_API_KEY_DAVID }}
          FASTAPI_API_KEY_FORMATEUR=${{ secrets.FASTAPI_API_KEY_FORMATEUR }}
          COMPOSE_FILE=docker-compose.yml:/srv/docker/qualicheck-staging-override/docker-compose.override.yml
          EOF

      - name: Installer uv et les dépendances (migrations + acceptance)
        run: uv sync

      - name: Démarrer Postgres et attendre qu'il accepte les connexions
        env:
          POSTGRES_USER: ${{ secrets.POSTGRES_USER }}
        run: |
          make up-db
          until docker compose exec -T postgres pg_isready -U "$POSTGRES_USER"; do
            sleep 1
          done

      - name: Appliquer les migrations Alembic
        run: make migration

      - name: Construire et (re)démarrer les conteneurs modifiés
        run: make up

      - name: Attendre que l'API réponde
        run: |
          until curl -sf http://localhost:8880/health; do
            sleep 1
          done

      - name: Rejouer la suite d'acceptance (garde-fou post-déploiement)
        run: make api-regles-acceptance
```

- [ ] **Step 2: Valider la syntaxe YAML**

Run:

```bash
cd /media/david/projets/QualiCheck && python3 -c "import yaml; yaml.safe_load(open('.github/workflows/cd-staging.yml'))" && echo "YAML valide"
```

Expected: `YAML valide` affiché, aucune exception

- [ ] **Step 3: Mettre à jour docs/developpement/ci.md**

Le fichier affirme actuellement (dernière ligne) que les branches `dev`/`staging` « n'existent pas encore » et que le workflow dédié n'est « pas encore écrit » — devenu faux après ce plan. Remplacer le dernier paragraphe.

Ancien texte à remplacer :

```text
- `tests/migration/` (et un futur `tests/acceptance/`) sont volontairement exclus de ce workflow — scope de tests plus léger pour une branche de travail. Réservés à un futur workflow dédié `dev`/`staging` (pas encore écrit, ces branches n'existent pas encore) avec une suite plus complète avant promotion.
```

Nouveau texte :

```text
- `tests/migration/` (et `tests/acceptance/`) sont volontairement exclus de ce workflow — scope de tests plus léger pour une branche de travail.
- `.github/workflows/cd-staging.yml` — déclenché sur push sur `staging` (survient au merge d'une PR `feature → staging`). Tourne sur un runner self-hosted enregistré sur le serveur personnel de David (cloclo) : migrations Alembic (`make migration`), déploiement (`make up`), puis rejeu de la suite d'acceptance existante (`make api-regles-acceptance`) comme garde-fou sur l'instance réellement déployée. Pas de rollback automatique en cas d'échec de l'acceptance — voir `docs/superpowers/specs/2026-07-28-cd-staging-design.md` pour la justification complète et le runbook des prérequis manuels (`docs/developpement/deploiement_staging.md`).
```

- [ ] **Step 4: Commit**

```bash
cd /media/david/projets/QualiCheck
git add .github/workflows/cd-staging.yml docs/developpement/ci.md
git commit -m "$(cat <<'EOF'
feat: add cd-staging.yml deploy workflow

Un seul job sur runner self-hosted (cloclo), déclenché au push sur
staging (merge de PR) : migrations, docker compose up -d --build, puis
rejeu de la suite d'acceptance existante comme garde-fou. Détail et
justification : docs/superpowers/specs/2026-07-28-cd-staging-design.md

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Écrire le runbook des prérequis manuels

**Files:**

- Create: `docs/developpement/deploiement_staging.md`
- Modify: `docs/README.md` (si ce fichier référence déjà `docs/developpement/`, y ajouter ce nouveau document — sinon, passer cette sous-étape)

**Interfaces:**

- Consumes: rien de nouveau côté code — documente les 7 prérequis restants de la spec (la branche `staging`, item 4 de la spec, est déjà couverte par la Task 1)
- Produces: un document autonome que David suit lui-même, hors de portée de l'agent

- [ ] **Step 1: Écrire le runbook**

Créer `/media/david/projets/QualiCheck/docs/developpement/deploiement_staging.md` avec exactement ce contenu (le fence extérieur utilise 4 backticks pour englober les blocs de code imbriqués sans les fermer prématurément — ne pas copier ces 4 backticks dans le fichier réel, seulement le contenu entre eux) :

````markdown
# Déploiement staging — prérequis manuels sur cloclo

Étapes à exécuter toi-même sur cloclo (ou dans l'interface GitHub/Infomaniak)
avant que `.github/workflows/cd-staging.yml` puisse déployer avec succès.
Détail et justification des choix : `docs/superpowers/specs/2026-07-28-cd-staging-design.md`.

## 1. Prérequis logiciels sur cloclo

Docker déjà en place. Vérifier/installer `uv` :

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 2. Runner GitHub Actions self-hosted

Dans le repo GitHub : **Settings → Actions → Runners → New self-hosted runner**,
choisir Linux x64. GitHub affiche un jeton d'enregistrement unique et généré
à la volée (expire rapidement, ne pas le réutiliser d'une fois sur l'autre) —
suivre les commandes affichées à l'écran, de la forme :

```bash
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64.tar.gz -L <URL fournie par GitHub>
tar xzf ./actions-runner-linux-x64.tar.gz
./config.sh --url https://github.com/wawawaformation/qualicheck --token <TOKEN fourni par GitHub> --labels cloclo
```

Puis l'installer comme service systemd, pour qu'il survive aux redémarrages :

```bash
sudo ./svc.sh install
sudo ./svc.sh start
```

Vérifier que l'utilisateur système qui exécute le runner appartient au
groupe `docker` (sinon `docker compose` échouera par permission refusée) :

```bash
groups $(whoami) | grep docker || sudo usermod -aG docker $(whoami)
```

(déconnexion/reconnexion nécessaire après `usermod` pour que le groupe
s'applique)

## 3. Environnement GitHub `staging` et ses secrets

Dans le repo GitHub : **Settings → Environments → New environment**, nommer
`staging`. Puis, dans cet environnement, ajouter les secrets suivants :

| Secret | Valeur |
| --- | --- |
| `POSTGRES_USER` | à choisir, dédié à staging |
| `POSTGRES_PASSWORD` | à choisir, dédié à staging |
| `POSTGRES_DB` | à choisir, dédié à staging |
| `FASTAPI_API_KEY` | valeur de `FASTAPI_API_KEY` dans `.env` local |
| `FASTAPI_API_KEY_ELIE` | valeur de `FASTAPI_API_KEY_ELIE` dans `.env` local |
| `FASTAPI_API_KEY_DAVID` | valeur de `FASTAPI_API_KEY_DAVID` dans `.env` local |
| `FASTAPI_API_KEY_FORMATEUR` | valeur de `FASTAPI_API_KEY_FORMATEUR` dans `.env` local |

Les 4 jetons Bearer sont à copier tels quels depuis le `.env` local (générés
le 2026-07-28, jamais distribués) — pas besoin d'en générer de nouveaux pour
staging.

## 4. Bootstrap de la base Postgres de staging

Une fois seulement, avant le premier déploiement automatisé. Sur ta machine
locale :

```bash
cd /media/david/projets/QualiCheck
make export_sql
```

Note le nom du fichier généré dans `backups/` (ex. `backups/20260728_120000.sql`),
transfère-le sur cloclo (`scp` ou équivalent), puis sur cloclo :

```bash
cd <chemin du repo sur cloclo>
docker compose up -d postgres
make migration
make import_sql FILE=<chemin du fichier transféré>
```

## 5. DNS chez Infomaniak

Ajouter un enregistrement A pour `regles.qualicheck.koabana.fr` pointant vers
l'IP publique fixe de cloclo, dans le panneau DNS Infomaniak de `koabana.fr`.

## 6. Rejoindre le réseau cloudnet

Caddy sur cloclo proxie ses cibles par nom de conteneur sur le réseau Docker
externe `cloudnet` (déjà en place, partagé avec d'autres services), pas via
`localhost`.

**Pas dans le dossier du dépôt** : `actions/checkout` nettoie les fichiers
non suivis (`git clean -ffdx`) avant chaque déploiement — un fichier posé
directement là serait supprimé au run suivant. Créer plutôt un dossier
stable à part :

```bash
mkdir -p /srv/docker/qualicheck-staging-override
cat > /srv/docker/qualicheck-staging-override/docker-compose.override.yml << 'EOF'
services:
  api-regles:
    networks:
      - cloudnet

networks:
  cloudnet:
    external: true
EOF
```

Ce fichier n'est jamais commité dans le dépôt (n'existe donc pas en local
pour David, qui n'a pas `cloudnet`). Le `.env` écrit par le workflow (Task 2)
contient déjà `COMPOSE_FILE=docker-compose.yml:/srv/docker/qualicheck-staging-override/docker-compose.override.yml`,
qui indique à `docker compose` d'aller le fusionner depuis cet emplacement —
aucune option de ligne de commande à ajouter, `make up` fonctionne sans
modification.

## 7. Configuration Caddy sur cloclo

Ajouter au `Caddyfile` de cloclo (à adapter à ta configuration existante) :

```caddyfile
regles.qualicheck.koabana.fr {
    reverse_proxy api-regles:8880
}
```

Puis recharger Caddy (`caddy reload` ou équivalent selon ton installation).

## Vérification finale

1. Merger une PR `feature → staging` (même triviale) et observer le run
   GitHub Actions de bout en bout.
2. `curl https://regles.qualicheck.koabana.fr/health` depuis un réseau
   différent de celui de cloclo.
3. Sur cloclo : `tail -f logs/api_regles.log` après un déploiement, vérifier
   le message de démarrage listant les 4 clients.
````

- [ ] **Step 2: Vérifier si docs/README.md référence docs/developpement/**

Run: `grep -n "developpement" /media/david/projets/QualiCheck/docs/README.md`

Si une liste de fichiers de `docs/developpement/` y apparaît déjà (`commandes.md`, `ci.md`), ajouter une ligne pour `deploiement_staging.md` au même endroit, même format. Si `docs/developpement/` n'y est pas listé du tout, ne rien changer (rester dans le périmètre de cette tâche).

- [ ] **Step 3: Commit**

```bash
cd /media/david/projets/QualiCheck
git add docs/developpement/deploiement_staging.md docs/README.md
git commit -m "$(cat <<'EOF'
docs: add staging deployment runbook

Étapes manuelles pour David sur cloclo : runner self-hosted, environnement
GitHub staging + secrets, bootstrap de la base staging, DNS/Caddy — hors
de portée de l'agent, qui n'agit pas sur l'infrastructure personnelle.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

(si `docs/README.md` n'a pas été modifié à l'étape précédente, ne pas
l'ajouter au commit)

---

## Task 4: Tracer dans CHANGELOG.md

**Files:**

- Modify: `CHANGELOG.md`

**Interfaces:**

- Consumes: rien
- Produces: rien consommé par du code — trace uniquement

- [ ] **Step 1: Lire le début de CHANGELOG.md pour trouver la dernière entrée du jour**

Run: `head -15 /media/david/projets/QualiCheck/CHANGELOG.md`

- [ ] **Step 2: Ajouter une entrée en tête de la section du jour**

Si une section `## 2026-07-28 — Claude Code` existe déjà en tête du fichier, ajouter la ligne suivante juste après son titre. Sinon, créer la section en tête de fichier (après le bloc d'explication du format).

```text
- **CD staging** (`docs/superpowers/specs/2026-07-28-cd-staging-design.md`, `docs/superpowers/plans/2026-07-28-cd-staging-implementation.md`) : `.github/workflows/cd-staging.yml` (runner self-hosted sur cloclo, déclenché au merge d'une PR vers `staging`) — migrations, `docker compose up -d --build`, rejeu de la suite d'acceptance existante comme garde-fou. Runbook des prérequis manuels : `docs/developpement/deploiement_staging.md`. **Non exécuté pour de vrai** à ce stade — dépend des prérequis manuels (runner, secrets, DNS, Caddy, bootstrap de la base staging) non encore réalisés
```

- [ ] **Step 3: Commit**

```bash
cd /media/david/projets/QualiCheck
git add CHANGELOG.md
git commit -m "$(cat <<'EOF'
docs: log cd-staging workflow in CHANGELOG

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Note finale (pas une tâche)

Ce plan produit du code et de la documentation vérifiables (YAML valide, branche poussée, docs cohérentes) mais **pas** un déploiement réel : le workflow ne peut s'exécuter avec succès qu'une fois les 7 prérequis manuels du Task 3 réalisés par David sur cloclo et dans les interfaces GitHub/Infomaniak. Rien dans ce plan ne doit être présenté comme « staging est en ligne » tant que la vérification finale du runbook n'a pas été faite pour de vrai.
