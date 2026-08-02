# regles_api_client

Client Vue.js de revue humaine du référentiel Opquast enrichi (US0) :
consultation et annotation des règles classées par l'agent d'enrichissement,
gestion de la clé API nécessaire pour écrire une annotation.

Consomme `app/api_regles` en HTTP. Ne couvre que US0 — voir
`docs/superpowers/specs/2026-08-02-regles-api-client-design.md` pour le
détail et le périmètre.

## Installation

```bash
npm install
```

## Configuration

Copier `.env.example` vers `.env` et ajuster si besoin :

```dotenv
VITE_API_REGLES_URL=http://localhost:8880
```

Aucun secret ici : la clé API se saisit dans l'application (écran « Clé
API ») et reste stockée dans le `localStorage` du navigateur — jamais dans
une variable d'environnement.

## Lancement

1. Démarrer l'API données dans un autre terminal, à la racine du projet :
   `make api-regles`
2. Démarrer ce client : `npm run dev`
3. Ouvrir `http://localhost:5173`

## Tests

```bash
npm run test
```

Unitaires (composables, service HTTP, aucun rendu de composant) et
acceptance (`tests/acceptance/`, cas décrits en Gherkin dans la spec de
conception, exécutés via un jeu de données jsonl — pas de framework BDD).
