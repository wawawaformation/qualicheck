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
./config.sh --url https://github.com/wawawaformation/qualicheck --token <TOKEN fourni par GitHub> --labels cloclo --work /srv/docker/qualicheck-staging
```

Puis l'installer comme service systemd, pour qu'il survive aux redémarrages :

```bash
sudo ./svc.sh install
sudo ./svc.sh start
```

Vérifier que l'utilisateur système qui exécute le runner appartient au
groupe `docker` (sinon `docker compose` échouera par permission refusée).

## 3. Environnement GitHub `staging` et ses secrets

Un environnement GitHub (Settings → Environments → `staging`), avec les
secrets suivants :

| Secret | Valeur |
| --- | --- |
| `POSTGRES_USER` | dédié à staging (`qualicheck_staging`) |
| `POSTGRES_PASSWORD` | dédié à staging (généré aléatoirement) |
| `POSTGRES_DB` | dédié à staging (`qualicheck_staging`) |
| `FASTAPI_API_KEY` | valeur de `FASTAPI_API_KEY` dans `.env` local |
| `FASTAPI_API_KEY_ELIE` | valeur de `FASTAPI_API_KEY_ELIE` dans `.env` local |
| `FASTAPI_API_KEY_DAVID` | valeur de `FASTAPI_API_KEY_DAVID` dans `.env` local |
| `FASTAPI_API_KEY_FORMATEUR` | valeur de `FASTAPI_API_KEY_FORMATEUR` dans `.env` local |

Les 4 jetons Bearer sont copiés tels quels depuis le `.env` local (générés
le 2026-07-28, jamais distribués) — pas besoin d'en générer de nouveaux pour
staging.

## 4. Bootstrap de la base Postgres de staging

Une fois seulement, avant le premier déploiement automatisé (ou juste après,
une fois `docker-compose.yml` présent via le premier checkout du workflow).
Sur ta machine locale :

```bash
cd /media/david/projets/QualiCheck
make export_sql
```

Note le nom du fichier généré dans `backups/` (ex. `backups/20260728_135208.sql`),
transfère-le sur cloclo (`scp` ou équivalent), puis sur cloclo, une fois le
dépôt checkouté par le workflow (`/srv/docker/qualicheck-staging`) :

```bash
cd /srv/docker/qualicheck-staging
make migration
make import_sql FILE=<chemin du fichier transféré>
```

## 5. DNS chez Infomaniak

Enregistrement A pour `regles.qualicheck.koabana.fr` pointant vers l'IP
publique fixe de cloclo, dans le panneau DNS Infomaniak de `koabana.fr`.

## 6. Rejoindre le réseau cloudnet

Caddy sur cloclo proxie ses cibles par nom de conteneur sur le réseau Docker
externe `cloudnet`, pas via `localhost`. `actions/checkout` nettoyant les
fichiers non suivis à chaque run, ce fichier vit dans un dossier stable **en
dehors** du dossier checkouté :

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

Le `.env` écrit par le workflow référence ce chemin via `COMPOSE_FILE` —
`make up` fonctionne sans modification.

## 7. Configuration Caddy sur cloclo

Ajouté à `reverse-proxy/Caddyfile` (même style que les autres sites) :

```caddyfile
# ============================================
# QualiCheck — API de revue du référentiel (staging)
# ============================================
regles.qualicheck.koabana.fr {
    encode zstd gzip
    reverse_proxy api-regles:8880
}
```

Puis `docker restart caddy`.

## Vérification finale

1. Merger une PR `feature → staging` (même triviale) et observer le run
   GitHub Actions de bout en bout.
2. `curl https://regles.qualicheck.koabana.fr/health` depuis un réseau
   différent de celui de cloclo.
3. Sur cloclo : `docker compose logs api-regles` / `logs/api_regles.log`
   après un déploiement, vérifier le message de démarrage listant les 4
   clients.
