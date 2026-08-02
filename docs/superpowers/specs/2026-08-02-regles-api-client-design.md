---
title: "Design — Client Vue.js de revue du référentiel (regles_api_client)"
subtitle: "Étage présentation US0 : revue humaine des règles enrichies et gestion de la clé API"
author: "David LEGRAND"
date: "Août 2026"
lang: fr-FR
---

## Contexte

`app/api_regles` expose le référentiel Opquast enrichi et une boucle de revue
humaine (`PATCH /regles/{numero}`), documentée dans
`docs/superpowers/specs/2026-07-26-api-fastapi-regles-design.md`. Cette API
n'a aujourd'hui aucun client réel : la revue se fait via `/docs` (Swagger) ou
`curl`.

Le maquettage US0 (`conception/maquettes/US0/`) a déjà produit les écrans
statiques HTML/CSS de cet outil de revue :

- `ecran-revue-regles.html` — liste filtrable + panneau de détail/annotation
- `ecran-revue-regles-etats.html` — les 3 états du même écran (liste vide,
  annotation réussie, échec)
- `ecran-cle-api.html` — gestion de la clé API (aucune clé / clé enregistrée)

Ce chantier construit le **premier client réel** de `api_regles` : un client
Vue.js qui transpose ces maquettes en écrans fonctionnels, sans élargir le
périmètre au-delà de ce que le maquettage a déjà couvert.

## Place dans l'architecture

```text
clients/
  regles_api_client/   ◄── CETTE SPEC (US0 : revue + clé API)
  (autres clients à venir : US2 question libre, etc. — hors périmètre ici)
        │  HTTP (GET, PATCH)
        ▼
app/api_regles/        (existant, non modifié)
```

`regles_api_client` appelle `api_regles` directement, sans étage applicatif
intermédiaire — même écart assumé au 3-tiers strict que celui déjà documenté
et justifié dans la spec de `api_regles` (§ « Écart assumé au 3-tiers
strict ») : cet écran de revue est explicitement la raison pour laquelle le
CORS de `api_regles` autorise `http://localhost:5173`.

`clients/` accueillera d'autres clients par la suite (un dossier par client,
convention actée dans le skill `clients_api`). Aucun code partagé entre
clients n'est anticipé ici — YAGNI, ce sera tranché quand un deuxième client
existera réellement.

## Décisions actées

| Décision | Choix retenu | Justification |
| --- | --- | --- |
| Périmètre | US0 uniquement (revue + clé API) | US2 (question libre) a sa propre maquette et son propre client futur ; les mélanger anticiperait une conception non encore actée pour ce client |
| Outillage | Vite + Vue 3 | Standard actuel Vue.js, CORS déjà anticipé sur le port 5173 par `api_regles` |
| Langage | JavaScript (pas TypeScript) | Cohérent avec YAGNI pour un client à 2 écrans ; pas de contrat de types déjà partagé à faire respecter |
| État applicatif | Composables Vue (`ref`/`reactive`), pas Pinia | Un store centralisé n'apporte rien pour 2 écrans sans état partagé à distance |
| Stockage clé API | `localStorage` | Persistance entre sessions — évite de resaisir la clé à chaque visite, acceptable pour un outil admin sur poste de confiance |
| Routage | `vue-router`, 2 routes (`/revue`, `/cle-api`) | Redirection explicite si clé absente/invalide au moment d'annoter ; URL distincte plus standard qu'un simple `ref` de bascule |
| CSS | Sass (SCSS), un partial par composant | Convention actée dans le skill `clients_api`. Les custom properties CSS des maquettes (tokens `--color-*`, etc.) sont conservées telles quelles — Sass n'organise que les fichiers (`@use`/`@forward`), il ne réinvente pas le système de tokens |
| Tests unitaires | Vitest, sur composables/services uniquement | Pas de test de rendu de composant (`@vue/test-utils`) dans cette première itération — la fidélité visuelle aux maquettes reste vérifiée à l'œil, comme pour les maquettes elles-mêmes |
| Tests d'acceptance | Gherkin en documentation dans cette spec + jsonl exécutable rejoué par un test Vitest classique | Aligné sur la convention déjà en place (`api_regles`, RAG) : « aucun outillage BDD n'est installé dans le projet ; les scénarios Gherkin documentent la spec, ils ne sont pas exécutés par un framework dédié » |
| README | Un `README.md` à la racine du client | Ajouté au skill `clients_api` comme règle générale, pas seulement pour ce client |
| Validation métier | Miroir côté client de `app/api_regles/schemas.py` (ex. `review_note` obligatoire si `a_revoir`) | UX seulement — le serveur reste la seule source de vérité, la validation client ne fait qu'éviter un aller-retour réseau évitable |

## Structure du projet

```text
clients/regles_api_client/
├── README.md
├── package.json
├── vite.config.js
├── src/
│   ├── main.js
│   ├── App.vue
│   ├── router/
│   │   └── index.js              # routes /revue, /cle-api
│   ├── views/
│   │   ├── RevueRegles.vue        # ecran-revue-regles(-etats).html
│   │   └── CleApi.vue             # ecran-cle-api.html (2 états)
│   ├── components/
│   │   ├── BarreFiltres.vue
│   │   ├── ListeRegles.vue
│   │   ├── PanneauDetailRegle.vue
│   │   └── BandeauMessage.vue
│   ├── composables/
│   │   ├── useRegles.js           # liste, filtres, sélection, chargement/erreur
│   │   └── useCleApi.js           # lecture/écriture localStorage
│   ├── services/
│   │   └── reglesApiService.js    # seul point d'appel HTTP
│   ├── apiServer.js                # API_REGLES_URL, modifié à la main (dev/prod)
│   └── styles/
│       ├── _variables.scss        # tokens portés depuis US0/style/variables.css
│       ├── _bouton.scss
│       ├── _entete.scss
│       ├── _panneau-detail-regle.scss
│       ├── ...                    # un partial par composant des maquettes
│       └── main.scss               # @use de tous les partials
└── tests/
    ├── unit/
    │   ├── reglesApiService.test.js
    │   ├── useRegles.test.js
    │   └── useCleApi.test.js
    └── acceptance/
        ├── regles_api_client_acceptance.jsonl
        └── acceptance.test.js      # charge le jsonl, rejoue chaque cas
```

## Modules

### `src/apiServer.js`

**Amendement du 2026-08-02, après la première implémentation** : ce module
remplace le `src/config.js` lu via `import.meta.env`/`.env.example` décrit
plus haut dans cette spec. Décision explicite du porteur du projet : pas de
fichier `.env` local pour ce client, `apiServer.js` est la source de vérité
unique, modifiée à la main selon l'environnement (valeur de dev en local,
URL de préprod avant un `npm run build` de déploiement).

```js
export const API_REGLES_URL = 'http://localhost:8880'
```

Aucun secret dans ce fichier : la clé API n'est jamais une variable
d'environnement du client, elle est saisie par l'utilisateur et stockée en
`localStorage` (cf. `useCleApi`). `reglesApiService.js` retire tout `/` final
de cette valeur avant de construire ses URLs (`API_REGLES_URL.replace(/\/+$/,
''`) — une valeur donnée avec un slash de fin ne doit pas produire de double
slash.

### `src/composables/useCleApi.js`

```js
export function useCleApi() {
  // hasKey, key (lecture/écriture localStorage['qualicheck_regles_api_key'])
  // setKey(valeur), clearKey()
}
```

Ne fait aucun appel réseau — un composable de stockage pur. La validité réelle
de la clé n'est connue qu'au premier `PATCH` qui l'utilise (401 si invalide).

### `src/services/reglesApiService.js`

```js
export async function listerRegles({ outil, reviewStatus } = {})
export async function annoterRegle(numero, { reviewStatus, reviewNote }, cle)
```

Centralise `fetch` vers `API_REGLES_URL`. Ne connaît pas le routeur : en cas de
`401`, il propage l'erreur (ex. `class ErreurAuthentification extends Error`)
plutôt que de rediriger lui-même — la décision de navigation reste dans la vue
appelante, pas dans un service HTTP générique.

### `src/composables/useRegles.js`

Orchestre `reglesApiService` : liste chargée, filtres actifs, règle
sélectionnée, état `chargement`/`erreur`. Sur `annoterRegle`, si le service
lève une erreur d'authentification, expose un signal que `RevueRegles.vue`
traduit en redirection vers `/cle-api` (via `useCleApi().clearKey()` puis
`router.push('/cle-api')` — la clé stockée est prouvée invalide, la conserver
provoquerait un nouveau 401 silencieux à la prochaine tentative).

### `src/router/index.js`

Deux routes, pas de garde globale : la redirection vers `/cle-api` est un
geste explicite déclenché par `useRegles` au moment d'une écriture refusée,
pas un garde de navigation générique (`GET /regles` reste public, aucune route
n'a besoin d'être protégée en lecture).

## Écrans

### `RevueRegles.vue`

Reprend `ecran-revue-regles.html` comme template (liste + filtres + panneau de
détail), avec les 3 états de `ecran-revue-regles-etats.html` pilotés par
`useRegles` :

| État maquette | Déclencheur réel |
| --- | --- |
| Liste vide | Filtres actifs ne retournent aucune règle |
| Bandeau succès | Réponse `200` du `PATCH` |
| Bandeau échec | Erreur réseau/`500` sur le `PATCH`, ou `404`/`422` inattendus |

L'entête (`entete__nav`) affiche « Modifier ma clé API » / « Supprimer ma clé
API » si `useCleApi().hasKey`, sinon « Renseigner ma clé API » — reprise
directe de la règle déjà actée dans `conception/maquettes/CLAUDE.md`.

### `CleApi.vue`

Reprend `ecran-cle-api.html` : bascule aucune-clé / clé-enregistrée sur
`useCleApi().hasKey`. « Enregistrer/Modifier la clé » appelle `setKey()`,
« Supprimer la clé » appelle `clearKey()`. Aucun appel réseau depuis cet écran
— la validité se découvre uniquement à l'usage (`PATCH`).

## Gestion des erreurs

| Situation | Comportement client |
| --- | --- |
| Pas de clé stockée, tentative d'annotation | Redirection immédiate vers `/cle-api`, sans appel réseau (garde côté `useRegles`, évite un aller-retour inutile) |
| `PATCH` → `401` (clé stockée mais invalide/révoquée) | `clearKey()`, puis redirection vers `/cle-api` avec un message explicite |
| `PATCH` → `404` | Bandeau d'erreur générique — ne devrait pas se produire via l'UI normale (le `numero` vient de la liste chargée) |
| `PATCH` → `422` | Bandeau affichant `detail` de la réponse — ne devrait pas se produire, la validation client (miroir de `schemas.py`) bloque en amont ; filet de sécurité si les deux dérivent |
| Erreur réseau ou `500` | Bandeau d'erreur générique (« Une erreur est survenue, veuillez réessayer »), reprise du texte déjà présent dans la maquette |

## Tests / Validation

Ordre TDD du projet : unitaire, puis acceptance (pas de couche intégration
distincte ici — il n'y a pas de base de données côté client).

### Tests unitaires (Vitest)

Aucun rendu de composant. `fetch` mocké pour `reglesApiService` ;
`localStorage` réel (disponible en environnement `jsdom` de Vitest) pour
`useCleApi`.

| Fichier | Couvre |
| --- | --- |
| `reglesApiService.test.js` | Construction des requêtes (URL, méthode, header `Authorization`), levée de `ErreurAuthentification` sur `401`, propagation des autres erreurs HTTP |
| `useCleApi.test.js` | `hasKey` reflète `localStorage` ; `setKey`/`clearKey` écrivent et suppriment la bonne clé |
| `useRegles.test.js` | Filtrage combiné outil/statut (miroir des règles serveur : OU dans un critère, ET entre critères) ; passage en état d'erreur/succès selon la réponse du service mocké |

### Tests d'acceptance

Scénarios Gherkin ci-dessous : documentation de spec, non exécutés par un
framework dédié — même convention que `api_regles` et le RAG (aucun outillage
BDD installé dans le projet).

```gherkin
Fonctionnalité: Revue humaine des règles enrichies

  En tant que référent Opquast
  Je veux consulter et annoter les règles mal classées
  Afin que l'agent d'enrichissement en tienne compte au prochain enrich-again

  Scénario: consultation de la liste sans clé API
    Étant donné un client sans clé API enregistrée
    Quand la liste des règles se charge
    Alors les règles s'affichent sans qu'aucune clé n'ait été demandée

  Scénario: tentative d'annotation sans clé API
    Étant donné un client sans clé API enregistrée
    Quand le référent tente d'enregistrer une annotation
    Alors il est redirigé vers l'écran de clé API sans appel réseau

  Scénario: annotation réussie
    Étant donné une clé API valide enregistrée
    Quand le référent enregistre une annotation "à revoir" avec une note
    Alors la règle affiche le bandeau de succès et la note enregistrée

  Scénario: clé API révoquée pendant l'usage
    Étant donné une clé API enregistrée mais invalide côté serveur
    Quand le référent tente d'enregistrer une annotation
    Alors la clé est effacée localement et l'écran de clé API s'affiche

  Fonctionnalité: Gestion de la clé API

  En tant que référent Opquast
  Je veux renseigner, modifier ou supprimer ma clé API
  Afin de pouvoir annoter les règles à tout moment sans compte utilisateur

  Scénario: enregistrement d'une première clé
    Étant donné aucune clé API enregistrée
    Quand le référent saisit une clé et l'enregistre
    Alors la navigation propose désormais "Modifier"/"Supprimer" au lieu de "Renseigner"

  Scénario: suppression de la clé
    Étant donné une clé API enregistrée
    Quand le référent la supprime
    Alors la navigation revient à "Renseigner ma clé API"
```

Le jsonl exécutable (`tests/acceptance/regles_api_client_acceptance.jsonl`)
porte les cas concrets rejoués par `acceptance.test.js` — un cas par ligne,
même forme que `tests/acceptance/api_regles_acceptance.jsonl` :

```json
{"scenario": "annotation réussie", "numero": 28, "review_status": "a_revoir", "review_note": "...", "resultat_attendu": "succes"}
{"scenario": "annotation sans clé", "a_clé": false, "resultat_attendu": "redirection_cle_api"}
```

`acceptance.test.js` mocke `fetch` (même mécanisme que les tests unitaires de
`reglesApiService`) — pas d'instance réelle de `api_regles` ni de
`POSTGRES_TEST_DB` : cohérent avec l'absence de couche intégration pour ce
client, énoncée en tête de cette section. Le jsonl décrit donc des réponses
HTTP simulées, pas des règles réelles en base.

### Critères de validation du chantier

1. `npm run dev` démarre le client sur `http://localhost:5173`, `api_regles`
   tournant sur `8880` (`make api-regles`) répond sans erreur CORS.
2. Les 3 états de `ecran-revue-regles-etats.html` sont atteignables réellement
   (pas seulement maquettés) : liste vide par filtrage, succès, échec.
3. Une annotation réelle sur une règle de `POSTGRES_TEST_DB` est visible via
   `GET /regles/{numero}` après coup.
4. Sans clé API stockée, toute tentative d'annotation redirige vers
   `/cle-api`, sans requête réseau observable.
5. `npm run test` (Vitest, unitaires + acceptance) passe intégralement.
6. Le README permet à quelqu'un n'ayant jamais vu le projet de lancer le
   client en suivant seulement ses instructions.

## Scope et limites (hors périmètre — YAGNI)

| Hors périmètre | Raison |
| --- | --- |
| Client US2 (question libre) | Maquette distincte, client futur distinct |
| Redimensionnement de la colonne de liste au glisser | Documenté comme exigence future dans `conception/maquettes/CLAUDE.md`, pas simulé — nécessite un vrai comportement JS que les maquettes s'interdisent, à faire ici mais dans une itération dédiée si demandée explicitement |
| Tests de rendu de composant (`@vue/test-utils`) | Décision actée : la fidélité visuelle reste vérifiée à l'œil pour cette première itération |
| Framework BDD exécutable (Cucumber.js, `vitest-cucumber`) | Aucun outillage BDD n'est installé dans le projet ; écart non justifié ici |
| Pinia / state manager dédié | Aucun état partagé entre écrans éloignés à ce stade |
| Authentification par compte utilisateur | Le token seul identifie le client côté serveur (`app/api_regles/auth.py`) ; pas de champ nom d'utilisateur |
| Déploiement / conteneurisation du client | Relève d'un chantier de déploiement distinct |
