# CD Staging Embed-Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Le pipeline CD staging relance `make embed-rules` après chaque
migration, pour que la base staging ne reste plus jamais désynchronisée
sur les embeddings par rapport au chunk vectorisé déployé.

**Architecture:** Une seule modification de fichier YAML
(`.gitea/workflows/cd-staging.yml`) : 3 nouvelles lignes dans le `.env`
généré sur l'hôte distant (secrets Azure, déjà présents sur Gitea), une
nouvelle étape `make embed-rules` entre `make migration` et
`make up-staging` dans le script SSH existant. Aucun code applicatif
touché — `embed_rules.py` et la cible Makefile `embed-rules` existent déjà
et sont inchangés.

**Tech Stack:** Gitea Actions (YAML), bash (script SSH distant).

## Global Constraints

- Spec de référence : `docs/superpowers/specs/2026-09-10-cd-staging-embed-rules-design.md`.
- Étape inconditionnelle, à chaque déploiement staging — pas de filtre
  sur les fichiers modifiés.
- Position exacte : après `make migration`, avant `make up-staging` (pas
  besoin de l'API démarrée, les données doivent être prêtes avant que
  quoi que ce soit ne les serve).
- Secrets `AZURE_AI_ENDPOINT`, `AZURE_AI_API_KEY`,
  `AZURE_MODEL_TEXT_EMBEDDING_SMALL` déjà ajoutés au dépôt Gitea
  (2026-09-10, via `tea actions secrets create`) — ce plan les
  **consomme**, ne les recrée pas.
- Pas de test automatisé possible pour ce changement (fichier de
  pipeline CI/CD, pas de code applicatif) : la vérification réelle est le
  prochain déploiement staging réel, hors du périmètre de ce plan
  (déclenché séparément par un push sur la branche `staging`).

---

## Task 1 : Ajouter les secrets Azure et l'étape embed-rules au pipeline

**Files:**
- Modify: `.gitea/workflows/cd-staging.yml`

**Interfaces:** Aucune — modification d'un seul fichier YAML, aucune
dépendance de code.

- [ ] **Step 1 : Ajouter les 3 secrets Azure au `.env` généré sur l'hôte distant**

Dans `.gitea/workflows/cd-staging.yml`, dans le bloc `cat > .env <<ENVEOF`
(step « Déployer l'API et la BDD sur l'hôte cible »), ajouter après
`FASTAPI_API_KEY_FORMATEUR=${{ secrets.FASTAPI_API_KEY_FORMATEUR }}` :

```yaml
          AZURE_AI_ENDPOINT=${{ secrets.AZURE_AI_ENDPOINT }}
          AZURE_AI_API_KEY=${{ secrets.AZURE_AI_API_KEY }}
          AZURE_MODEL_TEXT_EMBEDDING_SMALL=${{ secrets.AZURE_MODEL_TEXT_EMBEDDING_SMALL }}
```

Le bloc `ENVEOF` complet doit ressembler à :

```yaml
          cat > .env <<ENVEOF
          POSTGRES_USER=${{ secrets.POSTGRES_USER }}
          POSTGRES_PASSWORD=${{ secrets.POSTGRES_PASSWORD }}
          POSTGRES_DB=${{ secrets.POSTGRES_DB }}
          POSTGRES_HOST=localhost
          POSTGRES_PORT=8832
          FASTAPI_API_KEY=${{ secrets.FASTAPI_API_KEY }}
          FASTAPI_API_KEY_ELIE=${{ secrets.FASTAPI_API_KEY_ELIE }}
          FASTAPI_API_KEY_DAVID=${{ secrets.FASTAPI_API_KEY_DAVID }}
          FASTAPI_API_KEY_FORMATEUR=${{ secrets.FASTAPI_API_KEY_FORMATEUR }}
          AZURE_AI_ENDPOINT=${{ secrets.AZURE_AI_ENDPOINT }}
          AZURE_AI_API_KEY=${{ secrets.AZURE_AI_API_KEY }}
          AZURE_MODEL_TEXT_EMBEDDING_SMALL=${{ secrets.AZURE_MODEL_TEXT_EMBEDDING_SMALL }}
          API_REGLES_IMAGE=git.david-legrand.fr/david/qualicheck-api-regles:${{ github.sha }}
          DEPLOYED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
          COMPOSE_FILE=docker-compose.yml:/srv/docker/qualicheck-staging-override/docker-compose.override.yml
          ENVEOF
```

- [ ] **Step 2 : Ajouter l'étape `make embed-rules` après `make migration`**

Toujours dans le même bloc SSH, remplacer :

```yaml
          make migration
          make up-staging
```

par :

```yaml
          make migration
          make embed-rules
          make up-staging
```

- [ ] **Step 3 : Valider la syntaxe YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('.gitea/workflows/cd-staging.yml'))" && echo OK`
Expected: `OK` (aucune exception de parsing)

- [ ] **Step 4 : Relire le fichier complet une fois modifié**

Vérifier à l'œil que le bloc SSH (steps « Déployer l'API et la BDD sur
l'hôte cible ») contient bien, dans cet ordre : `make up-db` → attente
`pg_isready` → `make migration` → `make embed-rules` → `make up-staging`
→ attente `/health` → `make api-regles-acceptance`. Aucune autre ligne du
fichier ne doit avoir changé (diff minimal : 3 lignes de secrets + 1
ligne `make embed-rules`).

- [ ] **Step 5 : Commit**

```bash
git add .gitea/workflows/cd-staging.yml
git commit -m "feat: relance make embed-rules apres migration en CD staging"
```

---

## Task 2 : Tracer dans CHANGELOG.md et TODO.md

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `TODO.md`

**Interfaces:** Aucune.

- [ ] **Step 1 : Ajouter une entrée CHANGELOG.md**

Ajouter en tête de `CHANGELOG.md`, dans l'entrée du jour (2026-09-10) :

```markdown
- **CD staging relance l'embedding après migration** —
  `.gitea/workflows/cd-staging.yml` exécute désormais `make embed-rules`
  entre `make migration` et `make up-staging`, à chaque déploiement.
  Résout le point de vigilance noté le 2026-09-09 (staging restait
  désynchronisée sur les embeddings après l'ajout de `theme`/`objectifs`
  au chunk). Secrets Azure ajoutés au dépôt Gitea
  (`AZURE_AI_ENDPOINT`, `AZURE_AI_API_KEY`,
  `AZURE_MODEL_TEXT_EMBEDDING_SMALL`). Spec :
  `docs/superpowers/specs/2026-09-10-cd-staging-embed-rules-design.md`.
```

- [ ] **Step 2 : Clore le point de vigilance dans TODO.md**

Repérer la ligne « **Point de vigilance avant la prochaine synchro
staging** » (section Retrieval US2) et la remplacer par :

```markdown
  - [x] **Point de vigilance staging résolu** (2026-09-10) —
    `.gitea/workflows/cd-staging.yml` relance `make embed-rules` après
    chaque migration : la base staging ne peut plus rester
    désynchronisée sur les embeddings par rapport au chunk vectorisé
    déployé. Détail :
    `docs/superpowers/specs/2026-09-10-cd-staging-embed-rules-design.md`.
```

- [ ] **Step 3 : Commit**

```bash
git add CHANGELOG.md TODO.md
git commit -m "docs: trace la resolution du point de vigilance embeddings staging"
```

---

## Self-Review (déjà appliqué en rédigeant ce plan)

- **Couverture de la spec** : position de l'étape (Task 1 Step 2), 3
  secrets consommés (Task 1 Step 1, déjà créés sur Gitea hors de ce
  plan), traçabilité (Task 2). Le point « conséquences » de la spec sur
  `export_sql`/accumulation de backups est documenté comme hors périmètre
  dans la spec elle-même — aucune tâche n'y correspond, volontairement.
- **Pas de placeholder** : les deux blocs YAML des Steps 1-2 de la Task 1
  sont le texte exact à écrire, pas une description.
- **Vérification réelle** : ce plan ne peut pas être « testé » comme du
  code applicatif — sa vérification est le prochain push réel vers
  `staging`, explicitement noté comme hors périmètre des tâches
  elles-mêmes (déclenché par l'utilisateur, pas par ce plan).
