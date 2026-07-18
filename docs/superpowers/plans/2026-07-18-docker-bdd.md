# Docker + BDD — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal :** Poser l'infrastructure Docker (PostgreSQL + pgvector) et les fichiers de configuration de base du projet (`.gitignore`, `.env`, `.env.example`).

**Architecture :** Un seul service Docker (`postgres`) exposé sur le port `8832`, sur un réseau bridge nommé `qualicheck`. Les migrations et scripts Python tournent sur l'hôte et se connectent via ce port. Pas de conteneur éphémère pour les scripts.

**Tech Stack :** Docker, docker-compose v2, image `pgvector/pgvector:pg17`

## Global Constraints

- Tous les services QualiCheck sont exposés sur des ports `88xx` — PostgreSQL : `8832`
- Réseau bridge nommé `qualicheck` partagé entre tous les futurs services
- Un seul fichier `.env` à la racine, jamais versionné
- `.env.example` versionné, valeurs vides
- Image PostgreSQL : `pgvector/pgvector:pg17` (pgvector intégré, pas d'installation manuelle)
- Phase : feature (avant dev et main)

---

### Task 1 : `.gitignore` et `.env.example`

**Files :**
- Créer : `.gitignore`
- Créer : `.env.example`

**Interfaces :**
- Produit : fichiers de configuration versionnés, `.env` protégé du versionnement

- [ ] **Étape 1 : Créer `.gitignore`**

Contenu exact :

```gitignore
# Secrets — jamais versionnés
.env

# Python
__pycache__/
*.pyc
*.pyo
.venv/

# Logs d'exécution des scripts
logs/*.log

# Éditeurs
.idea/
.vscode/
*.swp
*.swo
```

- [ ] **Étape 2 : Créer `.env.example`**

Contenu exact (valeurs vides — pas de secret) :

```dotenv
# Connexion PostgreSQL
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_HOST=
POSTGRES_PORT=
```

- [ ] **Étape 3 : Vérifier que `.gitignore` protège bien `.env`**

Créer temporairement un fichier `.env` vide à la racine, puis :

```bash
git check-ignore -v .env
```

Résultat attendu : `.gitignore:2:.env    .env`

Supprimer le fichier `.env` temporaire après vérification.

- [ ] **Étape 4 : Commit**

```bash
git add .gitignore .env.example
git commit -m "chore: add .gitignore and .env.example

- Protège .env du versionnement
- Exclut __pycache__, .venv, logs/, fichiers éditeur
- .env.example documente les variables attendues (valeurs vides)"
```

---

### Task 2 : `.env` local

**Files :**
- Créer : `.env` (non versionné)

**Interfaces :**
- Consomme : `.env.example` (structure de référence)
- Produit : variables d'environnement disponibles pour docker-compose et les scripts Python

- [ ] **Étape 1 : Créer `.env` à la racine**

Contenu exact :

```dotenv
# Connexion PostgreSQL
POSTGRES_USER=qualicheck
POSTGRES_PASSWORD=qc_dev_s3cur3!
POSTGRES_DB=qualicheck
POSTGRES_HOST=localhost
POSTGRES_PORT=8832
```

- [ ] **Étape 2 : Vérifier que git ne le voit pas**

```bash
git status
```

Résultat attendu : `.env` n'apparaît pas dans les fichiers non suivis.

---

### Task 3 : `docker-compose.yml`

**Files :**
- Créer : `docker-compose.yml`

**Interfaces :**
- Consomme : `.env` (variables `POSTGRES_*`)
- Produit : service `postgres` accessible sur `localhost:8832`, réseau `qualicheck`, volume `postgres_data`

- [ ] **Étape 1 : Créer `docker-compose.yml`**

Contenu exact :

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "8832:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - qualicheck
    restart: unless-stopped

volumes:
  postgres_data:

networks:
  qualicheck:
    driver: bridge
```

- [ ] **Étape 2 : Démarrer le service**

```bash
docker compose up -d
```

Résultat attendu : le conteneur démarre sans erreur.

```bash
docker compose ps
```

Résultat attendu : `postgres` avec status `running`.

- [ ] **Étape 3 : Vérifier la connexion PostgreSQL**

```bash
docker compose exec postgres psql -U qualicheck -d qualicheck -c "SELECT version();"
```

Résultat attendu : une ligne contenant `PostgreSQL 17` et `pgvector`.

- [ ] **Étape 4 : Vérifier que pgvector est disponible**

```bash
docker compose exec postgres psql -U qualicheck -d qualicheck -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"
```

Résultat attendu : une ligne avec `name = vector` — l'extension est disponible (pas encore activée, c'est le rôle de la migration Alembic).

- [ ] **Étape 5 : Vérifier la persistance du volume**

```bash
docker compose down
docker compose up -d
docker compose exec postgres psql -U qualicheck -d qualicheck -c "SELECT 1;"
```

Résultat attendu : la connexion fonctionne après redémarrage — les données sont persistées.

- [ ] **Étape 6 : Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add docker-compose with postgres + pgvector

- Image pgvector/pgvector:pg17 (pgvector intégré)
- Port 8832:5432, réseau bridge qualicheck
- Volume postgres_data pour la persistance
- Variables d'env lues depuis .env"
```
