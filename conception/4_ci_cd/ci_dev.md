# CI Dev sur Gitea Actions : validation continue à chaque push

2026-08-30 · validé réellement sur `git.david-legrand.fr`

## Contexte

`ci-dev.yml` est le garde-fou qui tourne sur toute branche poussée hors
`main`/`staging` (en pratique : `dev`). Son rôle : garantir qu'aucun code
qui casse le lint, les migrations ou les tests n'atteint `staging` — c'est
sur cette hypothèse que s'appuie `cd-staging.yml`, qui ne rejoue pas les
tests unitaires/intégration lui-même (voir `conception/4_ci_cd/cd_staging.md`).

Premier workflow porté de GitHub Actions vers Gitea Actions dans le cadre de
l'essai non destructif (`jury/decisions/2026-08-29-hebergement-git-gitea.md`).

## Architecture

Un seul job `ci`, `runs-on: ubuntu-latest` (résolu par le runner `cloclo` en
mode conteneur docker, image `docker.gitea.com/runner-images:ubuntu-latest`
— pas d'exécution directe sur l'hôte physique).

**Service éphémère** : `postgres` (`pgvector/pgvector:pg17`), une base
jetable par run, jamais la base réelle.

**Étapes** : checkout, installation de `uv`, lint (`ruff check`),
application des migrations Alembic, tests unitaires + intégration.

## Point technique validé empiriquement

`POSTGRES_HOST` vaut `postgres` (le nom du service), **pas** `localhost`.

Sur un runner GitHub-hébergé, le job tourne directement sur la VM et le
service `postgres` a son port mappé sur `localhost`. Sur Gitea Actions avec
le label `ubuntu-latest` (résolu en `docker://...`), le job tourne **dans
un conteneur**, et le service `postgres` est un conteneur voisin sur le
même réseau — joignable par son nom de service, pas par `localhost`. Erreur
constatée avant correction : `Connection refused` sur `localhost:5432`.

## Déclencheur

```yaml
on:
  push:
    branches-ignore:
      - main
      - staging
```

`main` et `staging` sont explicitement exclus : `main` n'a volontairement
aucun pipeline (réservé à la bascule de production Infomaniak, voir
`docs/developpement/ci.md`), `staging` est couvert par `cd-staging.yml`.

## Hors périmètre

- `rag-acceptance` (coût réel par appel LLM) : volontairement hors CI,
  lancé manuellement.
- Rejeu des tests unitaires/intégration dans `cd-staging.yml` : non fait,
  ce fichier est censé garantir qu'ils ont déjà passé sur `dev` avant le
  merge vers `staging` — hypothèse qui suppose un merge propre (fast-forward
  ou sans changement additionnel), pas garantie à 100 % en cas de conflit
  résolu manuellement.
