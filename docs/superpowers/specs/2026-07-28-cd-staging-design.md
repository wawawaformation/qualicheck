# CD staging — déploiement de la stack sur cloclo

2026-07-28 · brainstorming validé, en attente de relecture

## Contexte

`app/api_regles/` tourne aujourd'hui en local via `docker compose up` (voir
`docs/jury/decisions/2026-07-28-cle-valeur-multi-clients-api-regles.md` pour
l'authentification multi-clients). Objectif réel : permettre à Élie Sloïm
(fondateur Opquast) et au formateur d'utiliser le `PATCH` d'annotation de
revue depuis chez eux, sur une instance réellement déployée — pas en local
sur la machine de David.

Cible : le serveur personnel de David, **cloclo** (Docker + Caddy déjà en
place, IP publique fixe, domaine `koabana.fr` réel chez Infomaniak). Rien
n'existe encore côté CD : pas de workflow, pas de runner, pas
d'environnement `staging` déployé.

**Amendement du 2026-08-02** : cette spec a été écrite avant l'existence de
`clients/regles_api_client/` (client Vue.js réel, US0). À l'époque, l'usage
prévu était un client HTTP direct (curl, Bruno, Postman) — d'où « CORS
inchangé » dans les décisions ci-dessous. Décision prise en déployant :
**même origine** pour le front et l'API (`regles.qualicheck.koabana.fr`
sert le front Vue.js à la racine, Caddy reverse-proxie les chemins de l'API
sur ce même domaine) — la conclusion « pas de CORS à gérer » reste donc
vraie, mais pour une raison différente (same-origin, pas absence de
navigateur). Pas de conteneur Docker ajouté pour le front : Caddy sert les
fichiers statiques du build directement, cohérent avec le choix déjà acté
de ne pas ajouter de conteneur superflu. Détail : sections « Prérequis
manuels » (point 7 modifié) et workflow `cd-staging.yml` (étapes de build
ajoutées).

## Décisions actées pendant le brainstorming

- **Un seul workflow `cd-staging.yml`**, pas un fichier par service
  (`cd-staging-regles.yml` envisagé un temps, écarté) : les trois services
  de l'architecture n-tiers (`api_regles`, futurs `api_audit`/`api_business`)
  partagent la même machine, le même `docker-compose.yml`, la même base
  Postgres, donc les **mêmes migrations Alembic**. Séparer le déploiement
  par service dupliquerait ces étapes communes sans bénéfice — la séparation
  qui se justifie est applicative (déjà actée), pas celle du pipeline de
  déploiement.
- **Runner GitHub Actions self-hosted sur cloclo**, pas de SSH push depuis
  les runners cloud GitHub : connexion sortante uniquement, aucun port à
  ouvrir sur la box. Contrepartie assumée : le runner exécute n'importe quel
  workflow du repo avec les droits de cloclo — acceptable sur un repo privé
  mono-contributeur. Fourni tel quel par GitHub (binaire officiel), installé
  une fois par David directement sur cloclo (hors périmètre de cette tâche).
- **Déclencheur : push sur la branche `staging`**, qui survient au merge
  d'une PR (même en solo, pour la revue et la trace — David choisit d'ouvrir
  systématiquement une PR `dev → staging` plutôt que de pousser
  directement).
- **Rejeu de la suite d'acceptance existante après déploiement**
  (`make api-regles-acceptance`), comme garde-fou automatisé sur l'instance
  réellement déployée. Terminologie clarifiée pendant le brainstorming : ce
  n'est **pas** un « smoke test » au sens test QA exploratoire manuel — c'est
  la suite d'acceptance déjà établie dans ce projet (même patron que
  `rag_acceptance.py`), rejouée une fois de plus, après déploiement plutôt
  qu'en local.
- **Pas de rollback automatique** si l'acceptance échoue après déploiement :
  le run est marqué en échec, le code reste déployé, décision manuelle
  ensuite. Un vrai mécanisme de rollback (blue-green ou équivalent) serait
  disproportionné pour ce projet à ce stade.
- **CORS inchangé** : Élie et le formateur utiliseront un client HTTP direct
  (curl, Bruno, Postman), pas un navigateur — CORS ne s'applique pas. Même le
  testeur intégré à `/docs` reste same-origin.

## Architecture

```text
dev ── PR vers staging ── merge ── push sur staging
                                           │
                                           ▼
                         cd-staging.yml (runner self-hosted, cloclo)
                                           │
     checkout → écrit .env depuis les secrets → démarre Postgres → migrations → docker compose up -d --build
                                           │
                                           ▼
                    rejeu de make api-regles-acceptance (garde-fou, données réelles)
```

Un seul job, séquentiel, entièrement exécuté sur cloclo (le runner y tourne
déjà — pas de SSH ni de copie de fichiers depuis GitHub).

Diagramme de déploiement complet (machines, réseaux, flux) :
`conception/annexes/K_deploiement_staging.drawio`.

## Workflow (`.github/workflows/cd-staging.yml`)

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

      - name: Installer uv et les dépendances (pour les migrations et l'acceptance)
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

Notes sur ce squelette :

- `POSTGRES_HOST=localhost` / `POSTGRES_PORT=8832` : ce sont les migrations et
  le script d'acceptance qui tournent nativement sur cloclo (via `uv run`,
  hors conteneur), donc via le port publié par le service `postgres` — pas le
  port interne du réseau Docker (`5432`, réservé au conteneur `api-regles`,
  déjà configuré en dur dans `docker-compose.yml`).
- `docker compose up -d --build` sans argument ne reconstruit/relance que les
  services dont l'image ou la configuration a changé — Postgres (et sa
  donnée) n'est pas touché si seul le code d'`api_regles` a changé.
- **Attente sur `/health` avant l'acceptance** — même cause que pour
  Postgres : `make up` rend la main dès que le conteneur est *démarré*, pas
  forcément prêt à accepter des connexions (uvicorn met un instant à se
  lancer après un rebuild). Découvert sur le premier run réel : l'acceptance
  échouait en `Connection reset by peer` juste après un déploiement, alors
  que l'API répondait déjà quelques secondes plus tard en vérifiant à la
  main.
- **`make up-db` (nouvelle cible Makefile) démarre Postgres seul, avant les
  migrations** — découvert lors du premier run réel : sur une machine où la
  stack n'a jamais tourné, les migrations échouaient (`connection refused`,
  Postgres pas encore démarré). `docker compose up -d --build` seul ne
  suffisait pas puisqu'il n'intervient qu'après les migrations dans ce
  squelette. La boucle `until ... pg_isready` attend que Postgres accepte
  vraiment les connexions (le conteneur peut être « démarré » sans être
  encore prêt) avant de continuer.
- Label `cloclo` sur `runs-on` : à donner au runner lors de son installation
  (`config.sh --labels cloclo`), pour un ciblage explicite plutôt qu'un
  `self-hosted` générique.
- Contrairement à un runner cloud GitHub (VM neuve à chaque run), un runner
  self-hosted réutilise le même répertoire de travail d'un run à l'autre.
  `actions/checkout` nettoie par défaut les fichiers non suivis (équivalent
  `git clean -ffdx`) avant de checkouter — le `.env` de l'étape suivante ne
  peut donc pas être un résidu d'un run précédent. **Même raison pour
  laquelle `docker-compose.override.yml` (réseau `cloudnet`, voir prérequis
  8) ne peut pas vivre dans ce dossier checkouté** : il serait supprimé au
  run suivant. Il vit dans un dossier stable à part
  (`/srv/docker/qualicheck-staging-override/`), et `COMPOSE_FILE` (dans le
  `.env` ci-dessus) dit à `docker compose` d'aller le chercher là — sans
  toucher à `make up` ni au Makefile.
- **`logs/.gitkeep` (nouveau fichier tracké) — même cause, autre symptôme**
  découvert sur le premier run réel : `logs/` n'est suivi par git nulle part
  (seul `logs/*.log` est dans `.gitignore`), donc `git clean -ffdx`
  supprimait le dossier entier à chaque run. Le conteneur `api-regles`
  (aucun `USER` dans le `Dockerfile`, tourne en `root`) le recréait ensuite
  en `root` au `make up` suivant — un `chown` manuel par David ne tenait
  donc jamais d'un run à l'autre. Un fichier tracké (même vide) dans `logs/`
  empêche `git clean` de supprimer le dossier lui-même.

## Secrets — environnement GitHub `staging`

Un environnement GitHub (Settings → Environments → `staging`), pas les
secrets du repo déjà utilisés par `ci-dev.yml` pour sa base éphémère —
évite toute collision de nom avec des valeurs différentes.

| Secret | Valeur |
| --- | --- |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Dédiées à staging, distinctes de la base locale |
| `FASTAPI_API_KEY` | Jeton `dev`, déjà généré localement |
| `FASTAPI_API_KEY_ELIE` | Jeton `elie-sloim`, déjà généré localement, jamais distribué |
| `FASTAPI_API_KEY_DAVID` | Jeton `david-legrand`, déjà généré localement |
| `FASTAPI_API_KEY_FORMATEUR` | Jeton `formateur`, déjà généré localement |

Les 4 jetons Bearer sont réutilisés tels quels (générés le 2026-07-28, jamais
distribués à ce jour) plutôt que régénérés spécifiquement pour staging.

## Prérequis manuels (hors périmètre de l'implémentation, faits par David sur cloclo)

Aucune de ces étapes n'est automatisée par ce spec ni par l'implémentation
qui en découlera — commandes exactes fournies au moment de l'implémentation,
exécutées par David lui-même sur cloclo.

1. Docker + `uv` installés sur cloclo (Docker déjà confirmé présent)
2. Runner GitHub Actions self-hosted installé et enregistré comme service
   systemd sur cloclo, label `cloclo` — l'utilisateur système qui l'exécute
   doit appartenir au groupe `docker` (sinon `docker compose up` échoue par
   permission refusée)
3. Environnement GitHub `staging` créé avec les secrets ci-dessus
4. Branche `staging` créée (depuis `dev`)
5. Base Postgres de staging bootstrappée une fois : `scripts/migration.py`
   puis restauration d'un dump réel (`make export_sql` en local → transfert
   → `make import_sql` sur cloclo) — pas de ré-ingestion complète (gratuit,
   données identiques à la base locale au moment du dump)
6. Enregistrement DNS A chez Infomaniak pour `regles.qualicheck.koabana.fr`
   → IP publique de cloclo
7. **Configuration Caddy sur cloclo** (amendée le 2026-08-02 : même origine
   front + API, plus un reverse proxy pur) — fichiers statiques du client
   Vue.js à la racine, chemins de l'API reverse-proxiés vers
   `api-regles:8880` sur le réseau Docker externe `cloudnet` (déjà en place
   sur cloclo, partagé avec d'autres services — Caddy y proxie ses cibles
   par nom de conteneur, pas par `localhost`) :

   Remplace le bloc existant du `Caddyfile` (`reverse-proxy/Caddyfile` sur
   cloclo), qui ne faisait qu'un reverse proxy simple sans en-têtes de
   sécurité — aligné ici sur le style des autres domaines publics du même
   `Caddyfile` (ex. `demo-dev.koabana.fr`) :

   ```caddyfile
   regles.qualicheck.koabana.fr {
       encode zstd gzip

       header {
           Strict-Transport-Security "max-age=31536000; includeSubDomains"
           Referrer-Policy "strict-origin-when-cross-origin"
           X-Frame-Options "SAMEORIGIN"
           X-Content-Type-Options "nosniff"
           X-XSS-Protection "1; mode=block"
           Permissions-Policy "interest-cohort=()"
       }

       @api path /regles* /health /docs* /redoc /openapi.json
       reverse_proxy @api api-regles:8880

       root * /srv/www/regles.qualicheck.koabana.fr
       try_files {path} /index.html
       file_server
   }
   ```

   Le répertoire `/srv/www/regles.qualicheck.koabana.fr/` doit exister et
   être accessible en écriture par l'utilisateur du runner GitHub Actions
   (qui y copie le build à chaque déploiement — voir `cd-staging.yml`).
   `try_files {path} /index.html` : nécessaire pour le SPA (`vue-router`
   en mode `createWebHistory`) — une route interne comme `/cle-api`
   n'existe pas en tant que fichier, Caddy doit retomber sur `index.html`
   pour que Vue Router la gère côté client.
8. **`docker-compose.override.yml` créé une fois sur cloclo**, dans un
   dossier stable en dehors du dépôt
   (`/srv/docker/qualicheck-staging-override/`) — jamais dans le dossier
   checkouté par le workflow, qui serait nettoyé (fichiers non suivis
   supprimés) au run suivant par `actions/checkout`. Fait rejoindre
   `cloudnet` au service `api-regles`, en plus de son réseau interne — sans
   quoi Caddy ne peut pas l'atteindre par son nom. Référencé depuis le
   `.env` du workflow via `COMPOSE_FILE`, jamais commité dans le dépôt
   (n'existe donc pas en local pour David, qui n'a pas `cloudnet`) :

   ```yaml
   services:
     api-regles:
       networks:
         - cloudnet

   networks:
     cloudnet:
       external: true
   ```

## Gestion des erreurs

- **Migration en échec** : le job s'arrête avant tout redéploiement
  (fail-fast, convention déjà en place dans le projet) — staging reste sur
  la version précédente, saine.
- **Build/déploiement en échec** : run rouge sur GitHub ; l'ancien conteneur
  reste généralement debout (Docker Compose ne coupe pas l'ancien avant que
  le nouveau soit prêt).
- **Acceptance en échec après déploiement réussi** : run marqué en échec,
  code déjà en place, décision manuelle ensuite (pas de rollback auto).
- **cloclo/runner injoignable au moment du merge** : le job attend qu'un
  runner se connecte, aucun traitement spécial nécessaire.
- **Deux merges rapprochés sur `staging`** : `concurrency: staging-deploy`
  empêche deux déploiements simultanés sur cloclo — le second attend que le
  premier se termine.

## Plan de vérification

1. Une fois les 8 prérequis manuels faits : petit changement sur `dev` →
   PR vers `staging` → merge → observer le run GitHub Actions de bout en
   bout (chaque étape verte).
2. Vérifier `https://regles.qualicheck.koabana.fr/health` réellement depuis
   l'extérieur du réseau local (pas depuis cloclo lui-même).
3. Vérifier que `logs/api_regles.log` se met à jour sur cloclo après le
   déploiement (message de démarrage avec les 4 clients déclarés).
4. Vérifier `https://regles.qualicheck.koabana.fr/` (racine, sans chemin) :
   le client Vue.js doit s'afficher, la liste des règles doit se charger
   sans erreur CORS dans la console (confirmerait le same-origin).
5. Vérifier qu'une route interne du client (ex.
   `https://regles.qualicheck.koabana.fr/mentions-legales` collée
   directement dans la barre d'adresse, pas juste cliquée depuis
   l'application) s'affiche correctement — confirme que le fallback
   `try_files {path} /index.html` fonctionne pour `vue-router`.

## Hors périmètre (explicitement)

- Rollback automatique / déploiement blue-green
- CD pour `api_audit`/`api_business` (n'existent pas encore)
- Protection de l'environnement GitHub `staging` (reviewers requis) —
  disproportionné en solo, à reconsidérer si d'autres contributeurs
  arrivent
- Rotation ou expiration des jetons Bearer (déjà noté comme provisoire dans
  `docs/jury/decisions/2026-07-28-cle-valeur-multi-clients-api-regles.md`)
