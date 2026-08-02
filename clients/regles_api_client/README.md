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

Aucun `.env` : l'URL de `app/api_regles` est une valeur unique dans
`src/apiServer.js`, à modifier à la main selon l'environnement (`npm run
dev` en local contre `http://localhost:8880`, URL de préprod avant un
`npm run build` de déploiement).

Aucun secret dans ce fichier : la clé API se saisit dans l'application
(écran « Clé API ») et reste stockée dans le `localStorage` du navigateur.

## Lancement

1. Vérifier que `src/apiServer.js` pointe vers l'API voulue.
2. Démarrer l'API données dans un autre terminal, à la racine du projet :
   `make api-regles`
3. Démarrer ce client : `npm run dev`
4. Ouvrir `http://localhost:5173`

## Tests

```bash
npm run test
```

Unitaires (composables, service HTTP, aucun rendu de composant) et
acceptance (`tests/acceptance/`, cas décrits en Gherkin dans la spec de
conception, exécutés via un jeu de données jsonl — pas de framework BDD).
