# CD staging sur Gitea Actions : pipeline image + déploiement SSH

2026-08-30 · validé réellement sur `git.david-legrand.fr` (API/BDD et client Vue.js)

## Contexte

`cd-staging.yml` déploie réellement sur `cloclo` (conteneurs Docker, fichiers
servis par Caddy) — contrairement à `ci-dev.yml` (tests seuls, voir
`conception/4_ci_cd/ci_dev.md`), une erreur ici a un impact réel sur
l'environnement de staging.

Objectif du design : que build et déploiement soient conçus **comme si**
ils tournaient sur des machines distinctes, même si c'est `cloclo` des deux
côtés aujourd'hui — pour être directement réutilisable lors de la bascule
de `main` vers l'hébergement Infomaniak, et plus généralement pour pouvoir
déployer sur **n'importe quel hôte** sans reconfigurer de runner.

## Décision d'architecture

Deux jobs :

**`build`** (`runs-on: ubuntu-latest`) : construit et pousse une image
`api-regles` vers le registre de conteneurs OCI intégré à Gitea (tag = SHA
du commit, pas de tag flottant — traçabilité exacte, rollback possible vers
n'importe quel commit passé), rejoue les tests unitaires/intégration en
garde-fou, et construit le client `regles_api_client` (publié comme
artefact de workflow).

**`deploy`** (`needs: build`, `runs-on: ubuntu-latest` — **pas** un runner
attaché à un hôte précis) : se connecte en SSH à un hôte cible paramétré
par secrets (`DEPLOY_HOST`/`DEPLOY_USER`/`DEPLOY_SSH_KEY`) et y exécute
l'orchestration Docker (pull de l'image, migrations, redémarrage) ; publie
le client via l'artefact téléchargé + `scp`.

Changer d'hôte de déploiement (`cloclo` → Infomaniak, ou un autre) devient
un changement de secrets, pas une reconfiguration de pipeline.

## Architecture détaillée

### Job `build`

Postgres éphémère (mêmes raisons que `ci_dev.md`), puis :

1. Checkout, `uv sync`, migrations, tests (garde-fou avant déploiement)
2. `docker login` (secrets `REGISTRY_USER`/`REGISTRY_TOKEN`, jeton Gitea
   scope `package: écriture`)
3. `docker build --build-arg GIT_SHA=${{ github.sha }} -t
   git.david-legrand.fr/david/qualicheck-api-regles:${{ github.sha }} .`
4. `docker push` de cette image
5. Installation de Node, `npm ci && npm run build` du client
   `regles_api_client`
6. Publication du build du client comme artefact de workflow
   (`actions/upload-artifact@v3` — **pas `@v4`**, voir plus bas)

`GIT_SHA` est figé **dans l'image** au build (`ARG`/`ENV` du `Dockerfile`),
pas dans `.env` : garantit que la valeur reflète le code réellement compilé
dans cette image, exposée ensuite par l'API elle-même via `GET /version`
(`app/api_regles/main.py`) — sert à vérifier depuis un client externe qu'un
déploiement a réellement pris effet.

### Job `deploy`

1. Écrit la clé SSH dédiée au déploiement dans le runner éphémère
2. Se connecte en SSH à l'hôte cible et y exécute, à distance :
   - Clone (si absent) ou `fetch` + `reset --hard ${{ github.sha }}` d'un
     dossier de déploiement dédié (`/srv/docker/qualicheck-staging-deploy/`
     sur `cloclo`) — dossier propre géré par ce pipeline, pas de
     réutilisation de l'ancien checkout laissé par l'ex-runner GitHub
   - Écrit le `.env` (secrets Postgres/API + `API_REGLES_IMAGE` +
     `DEPLOYED_AT`, calculé au moment réel du déploiement)
   - `docker login`, `docker compose pull api-regles`
   - `make up-db`, attente Postgres, `make migration`, `make up-staging`
     (nouvelle cible Makefile, sans `--build` — ne reconstruit jamais
     localement, n'utilise que l'image tirée du registre)
   - Attente de santé de l'API, `make api-regles-acceptance`
3. Télécharge l'artefact du client (`actions/download-artifact@v3`),
   le transfère par `scp` vers un dossier temporaire sur l'hôte cible, puis
   bascule atomiquement dans `/srv/www/regles.qualicheck.koabana.fr/`

Aucun outil autre que `ssh`/`scp` n'est requis sur le runner lui-même —
tout ce dont dépendent les commandes de déploiement (`docker`, `make`,
`uv`, `curl`) doit exister sur l'hôte **cible**, pas sur le runner. C'est
déjà le cas sur `cloclo`, hérité de l'ancien runner GitHub natif.

## Composants

- `.gitea/workflows/cd-staging.yml` : les deux jobs décrits ci-dessus.
- `Makefile` : cible `up-staging` (`docker compose up -d`, sans `--build`).
- `Dockerfile` : `ARG GIT_SHA` figé en `ENV` dans l'image.
- `app/api_regles/config.py`/`main.py` : `GET /version` (commit + date de
  déploiement).
- `docker-compose.override.yml` (sur `cloclo`, hors dépôt,
  `/srv/docker/qualicheck-staging-override/`) : `image: ${API_REGLES_IMAGE}`
  sur le service `api-regles`.
- Paire de clés SSH dédiée au déploiement (distincte des clés
  personnelles), clé publique dans les `authorized_keys` de l'hôte cible.
- Secrets Actions Gitea : `REGISTRY_USER`, `REGISTRY_TOKEN` (registre
  d'images), `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY` (déploiement
  SSH), en plus des secrets `POSTGRES_*`/`FASTAPI_API_KEY*` déjà en place.

## Gestion des erreurs

- `docker push` échoue → `deploy` ne démarre pas (`needs: build`).
- `docker compose pull` échoue → arrêt avant toute migration ou
  redémarrage de conteneur.
- Connexion SSH échoue → `deploy` échoue avant toute action sur l'hôte ;
  `set -e` dans le script distant interrompt aussi la suite au premier
  échec (pas de migration lancée sur un pull raté, par exemple).
- Le garde-fou d'acceptance (rejeu post-déploiement) reste inchangé,
  indépendamment de l'origine de l'image.

## Incidents rencontrés en mise au point

Détail complet (cause, reproduction, correction) dans
`docs/problemes_rencontres/deploiement/1_ssh_deploy_gitea.md` :

1. Script distant tronqué silencieusement (`docker compose exec` sans
   `< /dev/null` consommait le stdin du script SSH), job marqué réussi à
   tort.
2. `uv` introuvable en session SSH non-interactive (`PATH` non hérité,
   `~/.bashrc` non sourcé).
3. Secrets `POSTGRES_*`/`FASTAPI_API_KEY*` désynchronisés de la base réelle
   de staging (récupérés depuis l'ancien `.env` du runner GitHub, seule
   source encore disponible).
4. `actions/upload-artifact@v4`/`download-artifact@v4` non supportés sous
   Gitea Actions (`GHESNotSupportedError`) — verrouillé sur `@v3`.

## Hors périmètre

- Bascule effective de `main`/Infomaniak sur ce même modèle : pas traitée
  ici, seulement préparée (le pipeline sera transposable tel quel).
- **Politique de rétention des images du registre / espace disque sur
  `cloclo`** : la partition racine (`/dev/sdb2`, 55 Go) est à 90 % pleine,
  presque entièrement à cause de Docker (~48 Go). `/srv` (`/dev/sdb5`) a
  110 Go libres. Plan retenu (pas encore exécuté, volontairement reporté
  après une sauvegarde complète de `cloclo`) : bind mount
  `/srv/docker-data` → `/var/lib/docker`, sans repartitionnement ni
  changement de `daemon.json` — voir `TODO.md`.
- **Séparation des déploiements par service** : dès qu'un second service
  applicatif construit arrivera (ex. `api_business` pour US1/US2), il
  faudra éviter qu'un push touchant uniquement ce service ne redéploie
  `api-regles` inutilement (et inversement) — filtre `on: push: paths:`
  par fichier de workflow dédié, pas fait tant qu'aucun second service
  réel n'existe (un filtre sans cible concrète serait spéculatif). Le
  socle actuel (image nommée `qualicheck-api-regles`, `docker compose pull
  api-regles` déjà ciblé sur ce seul service) est déjà pensé pour permettre
  cette séparation le moment venu.
