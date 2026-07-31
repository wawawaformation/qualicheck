---
title: "API données du référentiel — QualiCheck"
subtitle: "Étage données : accès HTTP aux règles Opquast et boucle de revue humaine"
author: "David LEGRAND"
date: "Juillet 2026"
lang: fr-FR
toc: true
toc-depth: 2
---

\newpage

## Contexte et objectif

Le pipeline d'ingestion (`2_ingestion/`) est terminé et exécuté pour de vrai :
245 règles Opquast enrichies, vectorisées et indexées. Jusqu'ici, toute
consultation ou correction de ces données passait par `psql` ou par les
scripts d'ingestion eux-mêmes.

`app/api_regles/` ouvre une **API HTTP** sur ces données. Elle sert deux
besoins :

- permettre à un client de lire le référentiel enrichi sans identifiants
  PostgreSQL ;
- outiller la **boucle de revue humaine** (`3_enrichissement/G_revue_manuelle.md`) :
  un référent Opquast annote les règles mal classées, un développeur lance
  ensuite `make enrich-again` qui rappelle le LLM en tenant compte de ces
  annotations.

**Deux gestes distincts, deux acteurs, deux moments** :

| Geste | Acteur | Outil | Coût |
| --- | --- | --- | --- |
| Annoter une règle mal classée | Référent Opquast | `PATCH` sur l'API | Nul |
| Corriger la classification | Développeur | `make enrich-again` (CLI) | Appel LLM payant |

L'API **n'appelle jamais de LLM** et ne recalcule jamais d'embedding.

## Place dans l'architecture

Le projet s'organise en trois étages ; cette brique ne livre que l'étage
données.

```text
Étage présentation (Vue.js) ── écrans d'audit/dialogue (US1/US2, à concevoir)
        │                  └── écran de revue des enrichissements
        │                              │ (appel direct, écart assumé — voir ci-dessous)
        ▼                              ▼
Étage applicatif — app/api_business/ (à concevoir, US1/US2)
        │ HTTP
        ▼
Étage données
  app/api_regles/  ◄── CETTE BRIQUE
  app/db.py · app/models/ · app/migration/ · app/ingestion/
        │
        ▼
  PostgreSQL / pgvector
```

**Écart assumé au 3-tiers strict** : l'écran de revue des enrichissements
appelle `api_regles` directement, sans passer par un futur `api_business`. Se
défend parce que `api_regles` n'est pas un CRUD passe-plat — elle porte
elle-même ses invariants (note obligatoire sur un marquage `a_revoir`,
`reviewed_at` toujours serveur, 3 colonnes de revue traitées comme un bloc).
Contrepartie assumée : `api_regles` doit être joignable depuis Internet en
production (cf. `docs/jury/decisions/2026-07-26-lecture-ouverte-api-regles.md`).

`app/api_business/` (à venir) consommera `api_regles` en HTTP, jamais
PostgreSQL directement — `app/db.py` reste réservé à l'étage données.

## Décisions clés

| Décision | Choix retenu | Justification |
| --- | --- | --- |
| Périmètre | 3 endpoints `regles` + `/health` + `/docs` | US1/US2 non conçues ; tout endpoint pour elles serait spéculatif |
| Sémantique du `PATCH` | Écrit **uniquement** `review_status`/`review_note`/`reviewed_at` | Le référent annote, il ne réécrit pas l'enrichissement (pas de provenance/re-vectorisation à trancher) |
| `reviewed_at` | Horodaté par le serveur, jamais accepté du client | Un client ne peut ni le falsifier ni l'oublier |
| Utilisateurs/rôles en base | Aucun — un jeton par client nommé (`manifest.yml`) | Aucune US ne demande une table `utilisateur` pour ce besoin ; cf. `docs/jury/decisions/2026-07-28-cle-valeur-multi-clients-api-regles.md` |
| Lecture (`GET`) | Aucune authentification | Référentiel Opquast sous CC BY-SA 4.0 (partage à l'identique) — fermer la lecture travaillerait contre la licence. Décision actée : `docs/jury/decisions/2026-07-26-lecture-ouverte-api-regles.md` |
| Attribution CC BY-SA sur les `GET` | **Obligatoire, pas une politesse** | La base reproduit littéralement le contenu Opquast : chaque réponse `GET` en diffuse une reproduction/adaptation. CC BY-SA 4.0 impose crédit + lien de licence sur toute diffusion, que l'enrichissement pris isolément soit ou non une œuvre dérivée au sens strict (question de droit non tranchée par le projet — la conclusion pratique n'en dépend pas) |
| Périmètre de l'ouverture | **Limitée au référentiel Opquast** — pas un principe général du projet | L'ouverture (lecture libre + CC BY-SA) suit le contenu, pas l'étage : elle vaut pour `regle`/`theme`/`objectif`/`phase`/`tag`, qui sont la donnée Opquast elle-même. Tout ce qui touche `utilisateur`/`audit`/`page`/`constat` (données personnelles et données d'audit, futur `app/api_audit/`) sera **fermé** — authentification requise, aucune obligation de licence ne s'y applique. Cf. `docs/rgpd/registre_traitements.md` (le volet audit reste hors du registre RGPD tant qu'il n'est pas peuplé, mais sera un traitement de données personnelles à part entière une fois actif) |
| Écriture (`PATCH`) | `Authorization: Bearer <token>`, un jeton par client nommé | Traçabilité de la revue sans table `utilisateur` |
| Pagination / tri paramétrable | Aucun | Corpus figé à 245 règles (~500 kB de charge utile mesurés) |
| Configuration | `app/api_regles/manifest.yml` + `.env` pour les secrets | Même frontière que `app/ingestion/manifest.yml` : données de référence versionnées vs secrets |

## Contrats d'API

### `GET /regles`

Aucune authentification. Réponse `200`, liste de règles triée par `numero`.

- `?outil=` (répétable) — `statique · playwright · vision · manuel`. Un
  outil "contient" la stratégie composite (`?outil=playwright` inclut
  `playwright+statique`), il ne teste pas l'égalité stricte.
- `?review_status=` (répétable) — `valide · a_revoir · aucun`
  (`aucun` = `review_status IS NULL`).
- Combinaison : **OU** à l'intérieur d'un critère, **ET** entre les deux.
- Valeur hors énumération → `422` avant toute requête SQL (liste blanche
  Pydantic).

### `GET /regles/{numero}`

`200` avec la règle · `404` si le numéro n'existe pas · `422` si `{numero}`
n'est pas un entier. Aucune authentification.

### `PATCH /regles/{numero}`

Jeton Bearer requis. Corps : `review_status` (obligatoire) + `review_note`
(obligatoire si `a_revoir`). Réponse `200` avec la règle mise à
jour complète. `review_status: null` efface les 3 colonnes (annule un
marquage). Erreurs : `401` (jeton absent/invalide) · `404` (numéro inconnu) ·
`422` (corps invalide, ex. note manquante).

### `GET /health`

`SELECT 1` sur la base — pas un simple "je suis vivant". `200` si la base
répond, `503` sinon. Hors du router `regles`, sans authentification.

### Documentation générée

`/docs` (Swagger), `/redoc`, `/openapi.json` — générés par FastAPI depuis les
schémas Pydantic, sans code dédié. L'attribution CC BY-SA 4.0 (nom + URL de
licence + citation Opquast) y apparaît via `license_info`, obligation de la
licence et non simple politesse : chaque `GET /regles`/`GET /regles/{numero}`
diffuse du contenu Opquast reproduit tel quel, ce qui déclenche l'obligation
de partage à l'identique (crédit + lien de licence) — pas seulement une
mention en page d'accueil, mais une exigence qui suit **chaque réponse**
distribuant ce contenu.

## Sécurité

- **Injection SQL** : hors de portée par construction — SQLAlchemy émet des
  requêtes préparées, et les deux filtres passent par des `Enum` Pydantic
  (liste blanche).
- **Injection de prompt** : `review_note` est réinjectée telle quelle dans le
  prompt du prochain `enrich_again`. Trois règles de validation Pydantic :
  longueur ≤ 2000 caractères (manifeste), aucune ligne ne commence par `#`,
  aucune séquence de trois barres inversées — ce sont les délimiteurs du
  prompt d'enrichissement. Rejet en `422`, sans nettoyage silencieux.
- **CORS** : liste explicite d'origines (jamais `["*"]"`), `allow_credentials=False`
  (authentification par header, pas par cookie — hors périmètre CSRF par
  cookie).
- **Comparaison du jeton** : `secrets.compare_digest`, pas `==` (évite une
  fuite de timing sur le préfixe correct). `401` (pas `403`) dans tous les cas
  d'échec d'authentification — il n'y a pas d'identité, seulement un secret
  partagé.

## Hors périmètre (YAGNI)

| Hors périmètre | Raison |
| --- | --- |
| `app/api_business/` | US1/US2 non conçues — spec dédiée à venir |
| Recherche sémantique (pgvector) | Relève d'US2, brique déjà validée (`make rag-acceptance`) |
| Modification du contenu enrichi par l'API | Le référent annote, seul le LLM (`enrich_again`) corrige |
| Utilisateurs/rôles en base | Un jeton par client nommé suffit à l'usage réel |
| Pagination, tri paramétrable | Corpus figé à 245 règles |
| Limitation de débit | Aucune exposition publique à ce stade |
| Conteneurisation / déploiement prod | Chantier de déploiement distinct |

## Pour aller plus loin

Détail exhaustif (schémas Pydantic champ par champ, plan de tests
unitaires/intégration, scénarios Gherkin, données réelles de répartition des
245 règles par stratégie) : `docs/superpowers/specs/2026-07-26-api-fastapi-regles-design.md`
et `docs/superpowers/plans/2026-07-26-api-regles-implementation.md`.
