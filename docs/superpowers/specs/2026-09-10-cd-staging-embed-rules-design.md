# CD staging : ré-embedding automatique après migration

2026-09-10 · retenu

## Contexte

`TODO.md` note depuis le 2026-09-09 un point de vigilance :
`.gitea/workflows/cd-staging.yml` applique les migrations Alembic
(`make migration`) à chaque déploiement staging, mais ne relance jamais
l'ingestion ni l'embedding. Le chunk vectorisé a changé deux fois depuis
(`theme`/`objectifs` ajoutés le 2026-09-09) sans que staging ne soit
jamais synchronisé — la base staging garde des embeddings calculés sur
l'ancien chunk tant que personne ne relance `make embed-rules`
manuellement là-bas.

Déclenché en préparant le push de `dev` vers `staging` (75 commits
d'écart) : le nouvel endpoint `POST /regles/dense` serait déployé et
fonctionnel, mais tournerait sur des vecteurs périmés.

## Décision

Ajouter `make embed-rules` au script de déploiement distant (bloc SSH de
`cd-staging.yml`), juste après `make migration` et avant `make
up-staging` — `embed_rules.py` parle directement à Postgres (psycopg2),
n'a pas besoin de l'API démarrée, et les nouvelles règles doivent être en
base avant que quoi que ce soit ne les serve.

**Inconditionnel, à chaque déploiement** — pas de filtre sur les fichiers
modifiés (ex. déclencher seulement si `app/ingestion/chunking.py` a
changé). Cohérent avec la philosophie déjà actée du projet pour
`embed-rules` (« recalcule tout, coût négligeable » — 0,0023 € mesuré le
2026-09-09 pour 245 règles) : un filtre conditionnel ajouterait de la
complexité (path filter Gitea Actions, ou diff git dans le script) pour
économiser quelques centimes et ~15-20 secondes par déploiement.

## Options envisagées

**Rattrapage manuel ponctuel** (se connecter à l'hôte staging et lancer
`make embed-rules` à la main une fois) — écarté : résout l'écart actuel
mais pas le suivant. Le point de vigilance de `TODO.md` se reproduirait à
chaque futur changement de chunk.

**Étape conditionnelle** (ne relancer l'embedding que si des fichiers
d'ingestion ont changé dans le commit) — écarté : plus robuste en théorie
contre un chunk qui change souvent, mais complexité disproportionnée pour
un coût de quelques centimes et 245 règles. Le projet a déjà tranché ce
type d'arbitrage dans le même sens pour `embed-rules` lui-même (recalcule
toujours tout, jamais un sous-ensemble).

**Étape inconditionnelle à chaque déploiement (retenu)** — pour : simple,
supprime la classe entière de bug (staging jamais désynchronisé sur les
embeddings), cohérent avec l'existant. Contre : ~15-20s et quelques
centimes ajoutés à chaque déploiement staging, même quand rien n'a changé
côté chunking — jugé négligeable.

## Conséquences

**Nouveaux secrets Gitea requis** : `AZURE_AI_ENDPOINT`,
`AZURE_AI_API_KEY`, `AZURE_MODEL_TEXT_EMBEDDING_SMALL` — jusqu'ici le
`.env` généré sur l'hôte distant ne portait que les secrets
Postgres/FastAPI, `embed_rules.py` (rôle `embedding` du manifeste) en a
besoin. Seuls ces trois-là : le rôle `enrichissement`
(`AZURE_MODEL_KIMI`) n'est pas utilisé par `embed_rules.py`.
**Fait (2026-09-10)** : ajoutés au dépôt via `tea actions secrets create`
(secrets repo simples, pas de scoping par environnement dans cette
installation Gitea — confirmé par `tea actions secrets list`), mêmes
valeurs que le `.env` local, jamais affichées en clair.

**`export_sql` s'exécute aussi** (chaîné dans la cible Makefile
`embed-rules`) — écrit un nouveau dump dans `$DEPLOY_DIR/backups/` à
chaque déploiement, sur l'hôte distant. Comportement déjà existant de la
cible, pas un effet de bord nouveau introduit ici ; accumulation de
fichiers sur le disque distant non traitée par cette carte (hors
périmètre — le dossier `backups/` n'a jamais eu de politique de purge,
ni en local ni ailleurs).

**Si `AZURE_AI_ENDPOINT`/`AZURE_AI_API_KEY` sont absents ou invalides au
moment du déploiement** : `make embed-rules` échoue (l'API Azure renverra
une erreur d'authentification), le déploiement s'arrête avant
`make up-staging` (`set -e` déjà en tête du script SSH) — pas de
déploiement partiel avec une API tournant sur du code neuf mais sans
tentative de ré-embedding masquée.
