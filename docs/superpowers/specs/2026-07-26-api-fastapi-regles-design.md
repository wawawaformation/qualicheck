---
title: "Design — API données du référentiel enrichi"
subtitle: "Étage données : accès HTTP aux règles Opquast et boucle de revue humaine"
author: "David LEGRAND"
date: "Juillet 2026"
lang: fr-FR
---

## Contexte

Le pipeline d'ingestion est terminé et exécuté pour de vrai : 245 règles
Opquast enrichies, vectorisées et indexées (`make embed-rules`, 2026-07-26).
Toute consultation ou correction de ces données passe aujourd'hui par `psql`
ou par les scripts d'ingestion.

Ce chantier ouvre une **API HTTP sur ces données**, réclamée par
`TODO_PIPELINE_INGESTION.md` (« API FastAPI pour communiquer avec la BDD »).
Elle sert deux besoins :

- permettre à un client de lire le référentiel enrichi sans credentials
  PostgreSQL ;
- outiller la **boucle de revue humaine** déjà en place : un référent Opquast
  annote les règles mal classées, un développeur lance ensuite
  `make enrich-again` qui rappelle le LLM en tenant compte de ces annotations.

Cette boucle existe et a déjà servi (11 règles corrigées le 2026-07-26 pour
0,1610 €), mais son amorce se faisait à la main en SQL. L'API la remplace par
un contrat explicite et testé.

**Deux gestes distincts, deux acteurs, deux moments** — c'est le principe
structurant de cette spec :

| Geste | Acteur | Outil | Coût |
| --- | --- | --- | --- |
| Annoter une règle mal classée | Référent Opquast | `PATCH` sur l'API | Nul |
| Corriger la classification | Développeur | `make enrich-again` (CLI) | Appel LLM payant |

L'API **n'appelle jamais de LLM** et ne recalcule jamais d'embedding.

## Place dans l'architecture

Le projet s'organise en trois étages. Cette spec ne livre qu'un composant de
l'étage données.

```text
Étage présentation
  Interface Vue.js
        │
        ├──────────────────────────► écrans d'audit et de dialogue
        │                                        │
        └──► écran de revue des enrichissements  │
                     │                           │
                     │                           ▼
                     │              Étage applicatif  (à venir, spec dédiée)
                     │                app/api_business/   — US1, US2
                     │                       │  HTTP
                     ▼                       ▼
        Étage données
          app/api_data/     ◄── CETTE SPEC
          app/db.py · app/models/ · app/migration/ · app/ingestion/
                     │
                     ▼
             PostgreSQL / pgvector
```

Conséquences directes sur le design :

- **`app/api_business/` ne parlera pas à PostgreSQL** : il consommera
  `app/api_data/` en HTTP. `app/db.py` reste réservé à l'étage données.
- **`config.py` et `auth.py` sont internes à `api_data/`**, pas des briques
  partagées : l'étage applicatif aura son propre manifeste, son propre port et
  son propre jeu de tokens.
- **L'écran de revue des enrichissements appelle `api_data` directement.**
  C'est un **écart assumé** au 3-tiers strict, détaillé juste en dessous. C'est
  pour cet écran que le CORS est configuré ici.
- Le préfixe `api_` commun aux deux paquets les regroupe côte à côte dans
  l'arborescence, ce qui rend l'étage lisible dans le chemin d'import.

### Écart assumé au 3-tiers strict

En 3-tiers strict, la présentation ne parle jamais à l'étage données : elle
passe par l'applicatif. La raison d'être de cette règle est de **centraliser
les règles métier** pour que l'interface ne puisse pas les contourner.

L'écart se défend ici parce que `api_data` **n'est pas un CRUD passe-plat** :
elle porte elle-même ses invariants.

| Un CRUD passe-plat ferait | `api_data` fait |
| --- | --- |
| Écrit `review_status = "a_revoir"` sans note | **Refuse en `422`** : sans note, `enrich_again` rappellerait le LLM sans consigne |
| Écrit la note telle quelle | **Refuse** si elle contient `#` ou des fences — protection anti-injection de prompt |
| Accepte le `reviewed_at` envoyé par le client | **L'horodate lui-même** |
| Laisse modifier `review_note` seule | **Traite les 3 colonnes comme un bloc** |

Les règles sont donc **à l'endroit où on écrit**. S'il fallait passer par un
étage au-dessus pour qu'elles s'appliquent, sauter cet étage les contournerait
— et l'accès direct serait alors une faille. Ce n'est pas le cas.

S'ajoute une **surface volontairement réduite**, indépendante de la précédente
propriété : pas de `POST` (les règles viennent d'Opquast via l'ingestion), pas
de `DELETE`, un `PATCH` limité à 3 colonnes sur 20, et `id`, `embedding`,
`strategie_score` jamais exposés. Même avec le token, on ne peut pas abîmer les
données enrichies.

Faire transiter cet écran par `api_business` n'ajouterait donc qu'un relais
recopiant requête et réponse : du code de plus, de la latence de plus, et un
endroit de plus à mettre à jour à chaque champ ajouté.

**Contrepartie, à ne pas perdre de vue** : si le navigateur appelle `api_data`,
alors `api_data` doit être joignable depuis Internet en production — voir
« Risques documentés ».

## Vue d'ensemble

```text
Client (écran de revue Vue.js, curl)
        │  HTTP
        ▼
app/api_data/main.py ─── /docs, /redoc, /openapi.json  (générés par FastAPI)
        │           └── /health                        (sonde + SELECT 1)
        │
        ├── app/api_data/config.py ──► app/api_data/manifest.yml  (config)
        │                         └──► .env                       (secrets)
        │
        ├── CORSMiddleware   (origines depuis le manifeste)
        │
        └── router app/api_data/regles.py
              ├── GET   /regles            libre    filtres ?outil= ?review_status=
              ├── GET   /regles/{numero}   libre
              └── PATCH /regles/{numero}   Bearer   écrit review_status/review_note/reviewed_at
                          │
                          ▼
                    app/db.py (get_session)
                          │
                          ▼
                    PostgreSQL / table regle
                          │
                          ▼
              make enrich-again  (plus tard, par un développeur)
```

## Décisions actées

| Décision | Choix retenu | Justification |
| --- | --- | --- |
| Périmètre | Les 3 endpoints `regles` + `/health` + `/docs` | US1/US2 relèvent de l'étage applicatif, non conçu ; tout endpoint pour elles serait spéculatif |
| Nommage des paquets | `app/api_data/` ici, `app/api_business/` plus tard | L'étage doit se lire dans le chemin. Aucun fichier existant déplacé — regrouper physiquement l'étage données (`app/data/{ingestion,models,api}/`) imposerait de reprendre tous les imports des 5 scripts, des tests et des migrations Alembic |
| Sémantique du `PATCH` | Écrit **uniquement** les 3 colonnes de revue | Le référent annote, il ne réécrit pas l'enrichissement. Évite les questions de provenance (`prompt_version`, `llm_model`) et de re-vectorisation |
| `strategie_source = 'admin'` | **Non utilisée** | `review_status IS NOT NULL` exprime déjà « un humain est intervenu ». Deux colonnes pour le même fait pourraient diverger — même raisonnement que le refus d'une version de prompt dans `app/ingestion/manifest.yml`, redondante avec `regle.prompt_version` |
| Colonne `reviewed_by` | **Non créée** | Un seul token partagé, aucun besoin de tracer l'auteur. `FASTAPI_API_ID` du `.env` reste donc **volontairement inutilisé** |
| « Revue complétée » | `review_status = 'valide'` fait foi | `enrich_again` ignore `valide`, la valeur persiste donc. Ambiguïté résiduelle assumée : une règle corrigée retombe à `NULL`, donc « à relire à nouveau » — ce qui est correct, la donnée a changé depuis la revue |
| Pagination | Aucune | Corpus figé à 245 règles, ~500 kB de charge utile mesurés. Une pagination compliquerait chaque client sans bénéfice |
| Filtrage | Côté serveur, deux critères à valeurs fermées | Le client doit avoir le moins de travail possible, sans usine à gaz côté serveur |
| Accès base | Nouveau `app/db.py`, **5 scripts inchangés** | `build_engine()` est dupliqué dans 5 points d'entrée. Les migrer serait un refactoring testable seulement en les exécutant, dont certains appellent le LLM (payant). Dette signalée, pas traitée ici |
| Configuration | `app/api_data/manifest.yml` + un unique `app/api_data/config.py` | Aucune valeur de configuration éparpillée en `os.getenv()` dans le code. Même frontière que celle actée pour `KIMI_PRICE_*` (spec E §6) : les secrets dans `.env`, les données de référence dans un manifeste versionné qui offre un historique gratuit via git |
| Port d'écoute | `8880`, dans le manifeste uniquement | `FASTAPI_URL_DEV` est retiré de `.env` : l'URL de développement se déduit du port (`http://localhost:{port}`). `FASTAPI_URL_PROD` y reste, elle n'est pas déductible |
| Préfixe des routes | `/regles`, pas la racine | La racine porte `/health` et `/docs` ; un futur endpoint de recherche a besoin de ce cloisonnement |
| Point d'entrée | Cible `make api-data`, **aucun fichier dans `scripts/`** | Uvicorn s'attache à un module (`app.api_data.main:app`), pas à un script CLI. Exception assumée à la convention de `scripts/CLAUDE.md`, qui gagnerait sinon un fichier ne faisant qu'appeler uvicorn. Le suffixe de la cible laisse la place à `make api-business` |
| Conteneurisation | Pas de service ajouté à `docker-compose.yml` | Le compose ne gère que PostgreSQL ; les scripts tournent déjà sur l'hôte via `uv`. Conteneuriser relève du déploiement production, hors périmètre |

## Modules

### `app/api_data/manifest.yml` (nouveau)

Source de vérité de la configuration non secrète de cette API, sur le modèle de
`app/ingestion/manifest.yml`.

```yaml
# Configuration courante de l'API données. Aucun secret ici : voir .env.

api:
  title: "QualiCheck — API données"
  description: "Accès au référentiel Opquast enrichi et boucle de revue humaine"
  # Version du contrat d'API, distincte de la version du paquet Python de
  # pyproject.toml : elle évolue avec les endpoints, pas avec les dépendances.
  version: "0.1.0"
  port: 8880

cors:
  # Origines autorisées à appeler l'API depuis un navigateur.
  allowed_origins:
    - http://localhost:5173

validation:
  # Longueur maximale d'une review_note : borne le coût en tokens du prochain
  # enrich_again autant que la surface d'injection de prompt.
  review_note_max_length: 2000
```

Les origines de développement et de production peuvent y cohabiter : une
origine qui n'existe pas encore ne peut de toute façon appeler personne.

### `app/api_data/config.py` (nouveau)

Charge le manifeste **une seule fois** au chargement du module, sur le motif de
`load_manifest()` (`app/ingestion/llm_client.py`), et lit le seul secret dont
l'API a besoin (`FASTAPI_API_KEY`).

**Règle explicite** : aucun autre module de `app/api_data/` ne fait
`os.getenv()` ni ne lit de YAML. Un lecteur qui se demande « d'où vient cette
valeur ? » n'a qu'un fichier à ouvrir, et une valeur de configuration ne peut
pas se retrouver dupliquée à deux endroits du code.

### `app/db.py` (nouveau)

```python
def build_engine() -> Engine            # lit POSTGRES_* depuis .env
def get_session() -> Iterator[Session]  # dépendance FastAPI, ferme la session
```

`get_session()` est un générateur : FastAPI ouvre la session avant la requête
et la ferme après, y compris en cas d'exception. Le moteur est créé une seule
fois au chargement du module, pas à chaque requête — un pool de connexions
recréé par requête annulerait tout l'intérêt du pool.

Ce module lit les variables `POSTGRES_*` directement, sans passer par
`config.py` : ce sont des secrets de connexion, et `app/db.py` appartient à
l'étage données dans son ensemble (partagé avec `ingestion/`), pas à l'API. La
règle « un seul point de lecture » porte sur la configuration de l'API, pas sur
les identifiants de base de données, dont `.env` est déjà la source de vérité
unique pour tout le projet.

### `app/api_data/main.py` (nouveau)

Crée l'objet ASGI, monte le middleware CORS, monte le router `regles`, expose
`/health`.

- `title`, `description` et `version` sont passés à `FastAPI(...)` depuis
  `config.py` : ce sont eux qui alimentent `/docs`.
- `version` ne vient pas de `pyproject.toml` : le projet n'est pas installé
  comme paquet, `importlib.metadata.version()` lève `PackageNotFoundError`
  (vérifié). Elle vit dans le manifeste, où elle désigne de toute façon autre
  chose — la version du contrat d'API, pas celle du paquet Python.

### `app/api_data/auth.py` (nouveau)

```python
security = HTTPBearer(auto_error=False)

def require_bearer(credentials = Depends(security)) -> None
```

Trois points d'implémentation qui ne vont pas de soi :

- **`auto_error=False`** : le comportement par défaut de `HTTPBearer` renvoie
  un `403` quand le header est absent. On lève l'exception soi-même pour tenir
  le `401` dans les deux cas (header absent, token faux).
- **`secrets.compare_digest`** et non `==` : une comparaison naïve s'arrête au
  premier caractère différent, ce qui laisse fuiter la longueur du préfixe
  correct par le temps de réponse. Bibliothèque standard, aucune dépendance.
- **Fail-fast au démarrage** : si `FASTAPI_API_KEY` est absente ou vide,
  l'application refuse de démarrer. Sans ce garde-fou, un `.env` mal configuré
  donnerait une clé attendue vide et le `PATCH` deviendrait ouvert.

La fonction s'appelle `require_bearer`, pas `require_admin` : c'est une garde
d'écriture, pas un rôle.

### `app/api_data/schemas.py` (nouveau)

Deux modèles Pydantic et deux énumérations.

`OutilFiltre` : `statique`, `playwright`, `vision`, `manuel`.

`ReviewStatusFiltre` : `valide`, `a_revoir`, `invalide`, `aucun`
(`aucun` signifie `review_status IS NULL`).

`RegleRead` — **19 champs** :

```text
numero · intitule · theme · contexte · solution · controle
strategie_analyse · outils[] · strategie_justification · strategie_source
guide_analyse · objectifs[] · tags[] · phases[]
prompt_version · llm_model
review_status · review_note · reviewed_at
```

`theme` est le **libellé** issu de la table `theme` (colonne `theme`), pas son
identifiant — aucun client de cette API n'a besoin des clés techniques.

`outils[]` est un **champ dérivé** de `strategie_analyse`, calculé côté
serveur : `"statique&playwright"` devient `["statique", "playwright"]`, dans
l'ordre d'apparition. Le client affiche ses filtres et ses badges sans
réimplémenter la grammaire `+` (PUIS) et `&` (ET) — cette logique métier reste
à un seul endroit. `strategie_analyse` reste exposé brut, car la distinction
`+`/`&` porte du sens que la liste aplatie perd.

Champs volontairement exclus :

| Champ | Raison de l'exclusion |
| --- | --- |
| `id` | Le `numero` est la clé publique et il est `UNIQUE` |
| `embedding` | 1536 flottants inutiles à tout client de cette API |
| `strategie_score` | Vide sur les 245 règles, alimenté par la feedback loop post-MVP |
| `created_at`, `updated_at` | Aucun usage identifié dans la boucle de revue |

`ReglePatch` — corps du `PATCH` :

```text
review_status : valide | a_revoir | invalide | null   (obligatoire)
review_note   : texte                                 (conditionnel)
```

`reviewed_at` **n'est pas dans le corps** : le serveur l'horodate. Un client ne
peut donc ni le falsifier ni l'oublier.

Trois règles de validation, chacune avec sa raison d'être :

1. **`review_note` obligatoire si `review_status` vaut `a_revoir` ou
   `invalide`.** C'est cette note que `enrich_again` injecte dans le prompt.
   Sans elle, le LLM serait rappelé sans consigne — un appel payant pour rien.
2. **`review_status: null` efface les 3 colonnes.** Annuler un marquage posé
   par erreur sans repasser par `psql` ; un marquage erroné oublié coûterait un
   appel LLM au prochain `enrich-again`. Une `review_note` transmise en même
   temps qu'un `review_status: null` est **refusée en `422`** : le geste est
   contradictoire, mieux vaut le dire que d'ignorer silencieusement la note.
3. **Les 3 colonnes bougent comme un bloc.** Le `PATCH` remplace l'annotation
   entière, il ne modifie pas les champs un par un — contrat plus simple à
   tenir et à tester.

Validation anti-injection de prompt sur `review_note`, détaillée en section
« Sécurité ».

### `app/api_data/regles.py` (nouveau)

Le router. Ne contient que la traduction « requête → session → réponse ».

**Chargement des collections — 4 requêtes groupées, quel que soit le nombre de
règles.** `app/models/` ne déclare **aucun `relationship()`** : les
associations (`objectif_regle`, `phase_regle`, `regle_tag`) sont des tables
nues. `selectinload()` est donc hors de portée sans modifier les modèles, ce
que ce chantier ne fait pas — `app/models/` est partagé avec le pipeline
d'ingestion, dont une ré-exécution coûte de l'argent.

À la place, quatre requêtes en lot, assemblées en Python :

| Requête | Contenu |
| --- | --- |
| 1 | Les règles, `theme` obtenu par une jointure simple (relation 1:N, aucun risque de N+1) |
| 2 | `regle_id` → `tag` pour toutes les règles retenues |
| 3 | `regle_id` → `phase` pour toutes les règles retenues |
| 4 | `regle_id` → `objectif` pour toutes les règles retenues |

Les trois dernières sont regroupées en dictionnaires `{regle_id: [libellés]}`
avant construction des réponses. Le motif naïf — une requête par collection et
par règle, comme le fait `enrich_again.load_rules_to_review()` — produirait 736
requêtes sur 245 règles.

### `pyproject.toml`

Dépendances à ajouter :

| Paquet | Groupe | Rôle |
| --- | --- | --- |
| `fastapi` | principal | Le framework |
| `uvicorn[standard]` | principal | Serveur ASGI |
| `httpx` | `dev` | Requis par `TestClient` de Starlette |

`httpx` est déjà présent dans `uv.lock` (0.28.1), tiré transitivement par
`langchain-core` et `openai` — le coût d'installation est nul. Il est malgré
tout déclaré : la suite de tests en dépend **directement**, et un retrait
futur de `langchain-openai` casserait les tests sans raison apparente.

### `.env` et `.env.example`

Aucune variable ajoutée — **une variable retirée** :

```dotenv
# Conservées
FASTAPI_API_KEY=...        # secret : token Bearer du PATCH
FASTAPI_URL_PROD=...       # non déductible (autre hôte, autre schéma)
FASTAPI_API_ID=...         # volontairement inutilisé (pas de reviewed_by)

# Retirée : l'URL de développement se déduit du port du manifeste
# FASTAPI_URL_DEV=http://localhost:8800
```

`.env` ne conserve donc que des secrets et une valeur non déductible. Tout le
reste vit dans le manifeste.

### `Makefile`

```make
API_DATA_PORT = $(shell grep 'port:' app/api_data/manifest.yml | tr -d ' ' | cut -d: -f2)

api-data:
	uv run uvicorn app.api_data.main:app --reload --port $(API_DATA_PORT)
```

Le port est lu dans le manifeste, seule source de vérité — le `Makefile`
extrait déjà des valeurs par `grep` pour les cibles `psql`, `export_sql` et
`import_sql`, le motif est donc déjà en place dans le projet.

### `docs/agent/03_references_impl.md`

Deux lignes à ajouter au tableau des sources de vérité, pour qu'un agent qui
cherche une valeur de configuration de l'API sache où regarder :

| Donnée | Source de vérité |
| --- | --- |
| Configuration de l'API données (port, origines CORS, titre, version du contrat) | `app/api_data/manifest.yml` |
| Token Bearer du `PATCH` | `.env` (`FASTAPI_API_KEY`) |

## Contrats d'API

### `GET /regles`

| Aspect | Valeur |
| --- | --- |
| Authentification | Aucune |
| Réponse | `200`, liste de `RegleRead` triée par `numero` |
| Sans paramètre | Les 245 règles |
| `?outil=` | Répétable, ∈ `statique · playwright · vision · manuel` |
| `?review_status=` | Répétable, ∈ `valide · a_revoir · invalide · aucun` |
| Combinaison | **OU** à l'intérieur d'un critère, **ET** entre les deux critères |
| Valeur hors énumération | `422`, produit par Pydantic avant toute requête SQL |

`?outil=playwright` signifie « la stratégie **contient** playwright », pas
« la stratégie **égale** playwright ». La distinction est massive sur les
données réelles : 62 règles sont `playwright` pur, mais 85 contiennent
playwright via les valeurs composites. De même 93 contre 124 pour `statique`.
Seul `manuel` n'est jamais composite (44 règles).

Répartition réelle des 12 valeurs de `strategie_analyse` en base :

| Valeur | Nombre |
| --- | --- |
| `statique` | 93 |
| `playwright` | 62 |
| `manuel` | 44 |
| `vision+statique` | 12 |
| `playwright+vision` | 8 |
| `playwright+statique` | 8 |
| `vision` | 6 |
| `statique&playwright` | 5 |
| `statique+vision` | 4 |
| `statique+playwright` | 1 |
| `vision+playwright` | 1 |
| `vision&statique` | 1 |

### `GET /regles/{numero}`

`200` avec la règle · `404` si le numéro n'existe pas · `422` si `{numero}`
n'est pas un entier. Aucune authentification.

### `PATCH /regles/{numero}`

| Aspect | Valeur |
| --- | --- |
| Authentification | `Authorization: Bearer <FASTAPI_API_KEY>` |
| Corps | `ReglePatch` |
| Réponse | `200` avec la règle mise à jour |
| Erreurs | `401` header absent ou token faux · `404` numéro inconnu · `422` corps invalide |

La réponse renvoie la règle complète afin que le client voie l'état résultant
sans refaire un `GET`.

### `GET /health`

Vérifie la base par un `SELECT 1`. Une sonde qui se contenterait de répondre
« je suis vivant » déclarerait l'API en bonne santé alors qu'elle serait
incapable de servir la moindre règle — le seul travail de cette API étant de
lire la base, la sonde doit le refléter. Coût négligeable, aucune donnée
exposée.

| Situation | Réponse |
| --- | --- |
| Base joignable | `200` — `{"status": "ok", "base": "ok", "version": "..."}` |
| Base injoignable | `503` — `{"status": "degraded", "base": "injoignable"}` |

Sans authentification, et **hors du router** `regles` : c'est une route
d'infrastructure, pas une ressource métier.

### Documentation générée

FastAPI produit trois routes à partir des schémas Pydantic, sans code à
écrire :

| Route | Contenu |
| --- | --- |
| `/docs` | Swagger UI — interface interactive, bouton « Authorize » pour le Bearer |
| `/redoc` | ReDoc — même contenu, présentation en lecture continue |
| `/openapi.json` | Schéma OpenAPI brut, consommable par un générateur de client |

`RegleRead` et `ReglePatch` **sont** la documentation : un champ ajouté au
schéma apparaît dans Swagger sans action manuelle, la doc ne peut donc pas
dériver du code.

`/docs` reste accessible sans authentification. Ce n'est pas une fuite — les
`GET` sont déjà ouverts et le token n'apparaît nulle part — mais l'existence
du `PATCH` y est visible.

## Sécurité

### Injection SQL

L'ORM SQLAlchemy émet des **requêtes préparées** : la requête et les valeurs
partent séparément vers PostgreSQL, une valeur ne peut donc jamais être
interprétée comme du code SQL. C'est le mécanisme de `PDO::prepare()` avec
placeholders, côté Python.

Deux règles explicites pour cette API :

- les deux filtres passent par des `Enum` Pydantic — **liste blanche par
  construction**, une valeur inattendue est rejetée en `422` avant toute
  requête ;
- **aucun `text()` avec f-string.** Si du SQL doit un jour s'écrire à la main,
  ce sera `text()` avec paramètres nommés (`:terme`). Rappel : les noms de
  colonnes et de tables ne peuvent pas être paramétrés par le driver — un tri
  ou un filtre sur champ dynamique venant du client devrait être validé contre
  une liste blanche.

### Injection de prompt

`review_note` est réinjecté dans le prompt d'enrichissement par
`enrich_again` : la note est insérée **brute** dans une section
`## Contexte de revue humaine`, juste avant l'instruction finale
(`app/ingestion/llm_client.py`). Le prompt délimite ses sections par `##` et
`###`, ses exemples par des blocs de code JSON. Une note malveillante pourrait
donc simuler une nouvelle section ou un faux exemple.

Trois règles ciblées, en validateur Pydantic sur `review_note` :

| Règle | Raison |
| --- | --- |
| Longueur ≤ `validation.review_note_max_length` du manifeste (2000) | Borne le coût en tokens du prochain `enrich_again` autant que l'espace d'attaque |
| Aucune ligne ne commence par `#` | C'est ainsi que le prompt délimite ses sections |
| Aucune occurrence de trois barres inversées consécutives | C'est ainsi que le prompt délimite ses exemples JSON |

Rejet en `422` avec message explicite, **sans nettoyage silencieux** : le
référent corrige sa note. On s'arrête volontairement là — traquer des
tournures du type « ignore les instructions précédentes » est une liste noire
perdante, et la protection réelle reste la frontière de confiance : seul un
porteur du token écrit ce champ.

**Risque accepté et documenté** : si le token fuite, un tiers peut piloter le
prompt du prochain `enrich-again` et dépenser de l'argent.

### CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOWED_ORIGINS,  # manifeste, jamais ["*"]
    allow_methods=["GET", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=False,
)
```

| Réglage | Pourquoi pas le défaut habituel |
| --- | --- |
| Liste explicite, pas `["*"]` | Avec `"*"`, n'importe quel site peut faire lire le corpus enrichi par le navigateur d'un visiteur. Et `"*"` est interdit par la spécification CORS dès que `allow_credentials=True` |
| `allow_methods` limité | Déclarer `["*"]` annoncerait des verbes qui n'existent pas ; la réponse préflight doit dire la vérité |
| `allow_headers` explicites | `Authorization` **doit** y figurer, sinon le préflight du `PATCH` échoue — l'erreur la plus fréquente sur ce sujet |
| `allow_credentials=False` | L'authentification passe par un header, pas par un cookie : la classe entière des attaques CSRF par cookie ne s'applique pas |

**Point à ne pas confondre** : CORS est une protection **du navigateur**, pas
du serveur. Elle empêche le JavaScript d'un site tiers de lire les réponses ;
elle n'empêche rien à `curl`, à un script Python ou à Postman, qui
n'implémentent aucune politique d'origine.

### Autres garde-fous

- Le token n'est **jamais journalisé**, même tronqué.
- `401` et non `403` : `401` signifie « aucune identité valide fournie »,
  `403` « identité connue, droits insuffisants ». Ici il n'y a pas d'identité,
  seulement un secret partagé.
- `reviewed_at` écrit par le serveur, jamais accepté du client.

## Tests / Validation

Ordre TDD du projet : unitaire, puis intégration, puis acceptance.

### Tests unitaires

Dans `tests/unit/api_data/`. Aucune base, aucun serveur.

`test_schemas.py` — validation de `ReglePatch` :

| Cas | Attendu |
| --- | --- |
| `a_revoir` sans `review_note` | Rejet |
| `review_note` de plus de 2000 caractères | Rejet |
| `review_note` avec une ligne débutant par `#` | Rejet |
| `review_note` contenant trois barres inversées | Rejet |
| `review_note` en français riche — accents, apostrophes, guillemets, tirets cadratins | **Accepté** |
| `review_status` hors énumération | Rejet |
| `review_status: null` seul | Accepté |
| `review_status: null` accompagné d'une note | Rejet |

La cinquième ligne est le test qui compte le plus : une regex trop stricte
casserait les notes rédigées en français, régression qu'on ne verrait qu'en
production.

Le même fichier couvre le champ dérivé `outils[]` — un fichier de test par
module testé : `"statique&playwright"` donne `["statique", "playwright"]`,
`"vision+statique"` donne `["vision", "statique"]`, `"manuel"` donne
`["manuel"]`.

`test_auth.py` — token correct passe · token faux donne `401` · header absent
donne `401` · `FASTAPI_API_KEY` vide ou absente empêche le démarrage.

`test_config.py` — les valeurs du manifeste sont exposées (port, longueur max,
origines CORS) et un secret vide est refusé.

### Tests d'intégration

Dans `tests/integration/api_data/test_regles.py`, sur **`POSTGRES_TEST_DB`**,
en suivant le motif déjà en place dans
`tests/integration/ingestion/test_stockage_embedding.py` (fonction
`_database_url()` locale, fixture `session`, `clear_opquast_tables`).

**Isolation structurelle** : la session de test est injectée dans
l'application via `app.dependency_overrides[get_session]`. L'API sous test ne
peut alors **physiquement pas** ouvrir de connexion vers `POSTGRES_DB` — la
garantie ne dépend pas d'une variable d'environnement correctement
positionnée. Précaution directement issue de l'incident du 2026-07-25.

Jeu de 4 règles en fixture : une `statique`, une `playwright`, une composite
`statique&playwright`, une marquée `a_revoir`.

| Test | Vérifie |
| --- | --- |
| `GET /regles` | `200`, les 4 règles, triées par `numero` |
| `GET /regles?outil=playwright` | Inclut la composite — preuve du « contient » et non de l'égalité |
| `GET /regles?review_status=aucun` | Exclut la règle marquée |
| `GET /regles?outil=valeurinvalide` | `422` |
| `GET /regles/{numero}` inconnu | `404` |
| `PATCH` sans header, puis avec mauvais token | `401` dans les deux cas |
| `PATCH` valide | `200`, **et relecture en base** : les 3 colonnes écrites, `reviewed_at` non nul |
| `PATCH review_status: null` | Les 3 colonnes repassées à `NULL` |
| `PATCH` numéro inconnu | `404` |
| `GET /health` | `200`, puis `503` en surchargeant `get_session` par une session qui échoue |

### Critères de validation du chantier

1. `make api-data` démarre le serveur sur le port `8880` lu dans le manifeste,
   et `/docs` affiche les 3 endpoints ainsi que le bouton « Authorize ».
2. `GET /regles` renvoie 245 règles sur la vraie base de développement.
3. `GET /regles?outil=playwright` en renvoie 85, `?outil=manuel` en renvoie 44.
4. Un `PATCH` réel marque une règle, et
   `uv run python scripts/enrich_again.py --dry-run` la sélectionne — la boucle
   est bouclée sans dépenser d'argent.
5. `pytest tests/unit/api_data tests/integration/api_data` passe intégralement.
6. `ruff check app/api_data app/db.py tests/unit/api_data tests/integration/api_data`
   ne remonte rien.

## Scénarios d'acceptance

Écrits en Gherkin comme critères de validation lisibles, **sans `pytest-bdd`**
— même choix que la suite d'acceptance RAG : l'exécution reste en pytest.

```gherkin
Fonctionnalité: Boucle de revue humaine des enrichissements

  Scénario: un référent consulte les règles jamais relues
    Étant donné 245 règles enrichies en base
    Quand un client appelle GET /regles?review_status=aucun
    Alors la réponse contient les règles dont review_status est NULL
    Et aucune authentification n'a été nécessaire

  Scénario: un référent marque une règle à corriger
    Étant donné une règle 124 classée "statique" sans annotation
    Quand le référent envoie un PATCH avec un token valide,
      review_status="a_revoir" et une note explicative
    Alors la règle porte l'annotation et reviewed_at est horodaté
    Et make enrich-again la sélectionnera au prochain passage

  Scénario: une annotation sans note est refusée
    Quand le référent envoie un PATCH review_status="a_revoir" sans note
    Alors la réponse est 422
    Et la règle n'est pas modifiée en base

  Scénario: une écriture sans token est refusée
    Quand un client envoie un PATCH sans header Authorization
    Alors la réponse est 401
    Et la règle n'est pas modifiée en base

  Scénario: un référent annule un marquage posé par erreur
    Étant donné une règle marquée a_revoir
    Quand le référent envoie un PATCH review_status=null
    Alors les trois colonnes de revue repassent à NULL
    Et make enrich-again ne la sélectionnera plus
```

## Gestion des erreurs

Format de réponse d'erreur : celui de FastAPI par défaut,
`{"detail": "..."}`. Aucun format personnalisé — le standard est déjà
documenté dans `/docs` et compris de tous les clients générés.

| Code | Situation |
| --- | --- |
| `401` | Header `Authorization` absent, ou token invalide |
| `404` | Numéro de règle inexistant |
| `422` | Corps ou paramètre de requête invalide (Pydantic) |
| `503` | Base injoignable, sur `/health` uniquement |

Une erreur de base de données pendant un `GET` ou un `PATCH` remonte en `500`
par le comportement par défaut de FastAPI, avec la trace dans les logs. Aucun
traitement spécifique : c'est un défaut d'infrastructure, pas un cas
fonctionnel à modéliser.

## Scope et limites (hors périmètre — YAGNI)

Ne sont **pas** dans ce chantier, et pourquoi :

| Hors périmètre | Raison |
| --- | --- |
| `app/api_business/` — API de l'étage applicatif | US1 et US2 ne sont pas conçues. Elles feront l'objet d'une spec dédiée et consommeront celle-ci en HTTP |
| Recherche sémantique (`pgvector`) | Relève d'US2. La brique existe déjà et est validée par `make rag-acceptance` |
| Modification du contenu enrichi par l'API | Le référent annote, le LLM corrige. Éviterait sinon de trancher la provenance (`prompt_version`, `llm_model`) et la re-vectorisation |
| Utilisateurs et rôles en base | Aucune US ne le demande ; un token partagé suffit à l'usage réel |
| Pagination, tri paramétrable | Corpus figé de 245 règles |
| Limitation de débit | Aucune exposition publique à ce stade |
| Conteneurisation et déploiement production | `FASTAPI_URL_PROD` existe mais le déploiement est un chantier distinct |
| Migration des 5 scripts vers `app/db.py` | Refactoring de points d'entrée dont certains coûtent de l'argent à exécuter |
| Regroupement physique de l'étage données | `app/data/{ingestion,models,api}/` imposerait de reprendre tous les imports existants |

## Risques documentés

**Lecture ouverte et déploiement production.** En développement local, des
`GET` sans authentification sont sans conséquence. Mais `FASTAPI_URL_PROD`
pointe vers un domaine public : exposée telle quelle, l'API laisserait
n'importe qui télécharger **l'intégralité du corpus enrichi** — les
`guide_analyse` et `strategie_analyse` qui ont coûté environ 4 € d'appels LLM
et constituent la valeur ajoutée du projet, sur un référentiel dont l'usage
est accordé par Élie Sloïm.

Ce risque est la contrepartie directe de l'écart au 3-tiers strict : c'est
parce que le navigateur appelle `api_data` que `api_data` doit être joignable
depuis Internet.

**La réponse prévue est le passage en 3-tiers strict**, une fois
`app/api_business/` conçue : l'écran de revue passerait par l'étage applicatif,
`api_data` resterait sur le réseau privé, et le risque disparaîtrait par
construction plutôt que par un réglage. À trancher **avant** tout déploiement,
hors périmètre de cette spec. Deux autres réponses restent possibles à ce
moment-là — exiger le Bearer sur les `GET` également, ou assumer la publication
du référentiel enrichi — mais elles ferment ou ouvrent une porte que le
3-tiers strict rend simplement inutile.

**Champ `contexte` vide.** Constat fait en préparant cette spec : `contexte`
est `NULL` sur les 245 règles, alors que le correctif de code existe
(migration 0006 et correction du round-trip du 2026-07-26). Aucune ingestion
réelle ne l'a alimenté depuis. L'API l'exposera donc systématiquement vide.
Sans impact sur ce chantier, mais à traiter à part — une entrée est à ajouter
dans `TODO.md`.
