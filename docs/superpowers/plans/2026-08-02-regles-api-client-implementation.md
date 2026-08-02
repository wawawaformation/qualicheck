# Client Vue.js regles_api_client Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construire `clients/regles_api_client/`, le premier client réel de `app/api_regles` : consultation et annotation des règles Opquast enrichies (US0), gestion de la clé API.

**Architecture:** Vite + Vue 3 (Composition API, `<script setup>`), état local via composables (`useRegles`, `useCleApi`), un seul point d'appel HTTP (`reglesApiService`), Sass pour l'organisation du CSS porté depuis les maquettes, `vue-router` pour les 2 écrans.

**Tech Stack:** Vue 3.5, vue-router 4.6, Vite 6.4, Vitest 3.2 + jsdom 26, Sass 1.98 (versions verrouillées pour compatibilité Node 18 — l'environnement de développement tourne sous Node 18.19.1).

## Global Constraints

- Spec de référence : `docs/superpowers/specs/2026-08-02-regles-api-client-design.md`. Toute divergence avec ce document doit être signalée, pas silencieusement appliquée.
- Périmètre : US0 uniquement (revue des règles + gestion de la clé API). Pas de code pour US2 (question libre).
- JavaScript uniquement — aucun fichier `.ts`.
- Pas de Pinia : état applicatif via composables (`ref`/`reactive`/`computed`).
- La clé API n'est jamais une variable d'environnement ni un secret commité : uniquement saisie utilisateur, stockée en `localStorage`.
- CSS en Sass (partials), mais les custom properties CSS des maquettes (`--color-*`, etc.) restent inchangées — Sass n'organise que les fichiers, il ne réinvente pas les tokens.
- Aucun test de rendu de composant (`@vue/test-utils`) dans ce chantier.
- Aucun framework BDD exécutable (Cucumber.js, `vitest-cucumber`) : les scénarios Gherkin de la spec restent de la documentation, l'exécutable est le jsonl rejoué par un test Vitest classique — même convention que `tests/acceptance/api_regles_acceptance.jsonl`.
- `GET /regles` ne supporte que les filtres `outil` et `review_status` côté serveur (`app/api_regles/regles.py`) : la recherche texte, le filtre par thème et le filtre par phase de la maquette sont donc appliqués **côté client**, sur les 245 règles chargées en une fois (pas de pagination serveur).
- Filtres `outil`/`review_status` : eux aussi appliqués côté client dans ce chantier (une seule requête `GET /regles` au montage, tout le filtrage ensuite en mémoire) — plus simple que de mélanger filtrage serveur et client, cohérent avec l'absence de pagination du corpus.
- Chaque client du dossier `clients/` a son propre `README.md` (règle actée dans le skill `clients_api`).

---

## Task 1: Scaffolding du projet Vite + Vue 3

**Files:**
- Create: `clients/regles_api_client/package.json`
- Create: `clients/regles_api_client/vite.config.js`
- Create: `clients/regles_api_client/index.html`
- Create: `clients/regles_api_client/.env.example`
- Create: `clients/regles_api_client/.env.test`
- Create: `clients/regles_api_client/.gitignore`
- Create: `clients/regles_api_client/src/main.js`
- Create: `clients/regles_api_client/src/App.vue`
- Create: `clients/regles_api_client/README.md`

**Interfaces:**
- Produces: un projet Vite démarrable (`npm run dev`), buildable (`npm run build`), testable (`npm run test`). Aucune interface JS consommée par les tâches suivantes — elles remplaceront `App.vue` et `main.js` (Task 6).

- [ ] **Step 1: Créer `package.json`**

```json
{
  "name": "regles-api-client",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "vue": "^3.5.40",
    "vue-router": "^4.6.4"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2.4",
    "jsdom": "^26.0.0",
    "sass": "1.98.0",
    "vite": "^6.4.3",
    "vitest": "^3.2.7"
  }
}
```

- [ ] **Step 2: Créer `vite.config.js`**

```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.test.js'],
  },
})
```

- [ ] **Step 3: Créer `index.html`**

```html
<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8" />
    <title>QualiCheck — Revue du référentiel</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

- [ ] **Step 4: Créer `.env.example` et `.env.test`**

`.env.example` :

```dotenv
VITE_API_REGLES_URL=http://localhost:8880
```

`.env.test` (lu automatiquement par Vitest en mode `test`, permet à `src/config.js` — Task 2 — de résoudre une URL sans dépendre d'un `.env` local) :

```dotenv
VITE_API_REGLES_URL=http://localhost:8880
```

- [ ] **Step 5: Créer `.gitignore`**

```text
node_modules/
dist/
.env
```

- [ ] **Step 6: Créer `src/main.js` et `src/App.vue` (placeholders, remplacés à la Task 6)**

`src/main.js` :

```js
import { createApp } from 'vue'
import App from './App.vue'

createApp(App).mount('#app')
```

`src/App.vue` :

```vue
<template>
  <p>regles_api_client</p>
</template>
```

- [ ] **Step 7: Créer `README.md` (squelette, complété à la Task 11)**

```markdown
# regles_api_client

Client Vue.js de revue humaine du référentiel Opquast enrichi (US0).

Documentation complète : voir Task 11 de
`docs/superpowers/plans/2026-08-02-regles-api-client-implementation.md`.
```

- [ ] **Step 8: Installer les dépendances et vérifier le serveur de dev**

Run: `cd clients/regles_api_client && npm install && npm run dev -- --port 5173 &`
Puis : `sleep 2 && curl -s http://localhost:5173 | grep -q 'regles_api_client\|<div id="app">' && echo OK`
Expected: `OK` affiché, puis arrêter le serveur (`kill %1` ou `Ctrl+C` si lancé au premier plan).

- [ ] **Step 9: Vérifier le build**

Run: `cd clients/regles_api_client && npm run build`
Expected: `dist/` créé sans erreur.

- [ ] **Step 10: Commit**

```bash
git add clients/regles_api_client/
git commit -m "feat(regles_api_client): scaffold Vite + Vue 3 project"
```

---

## Task 2: Service HTTP (`reglesApiService.js`) et configuration

**Files:**
- Create: `clients/regles_api_client/src/config.js`
- Create: `clients/regles_api_client/src/services/reglesApiService.js`
- Test: `clients/regles_api_client/tests/unit/reglesApiService.test.js`

**Interfaces:**
- Consumes: `import.meta.env.VITE_API_REGLES_URL` (Task 1, `.env.test`/`.env.example`)
- Produces: `API_REGLES_URL: string` (`src/config.js`) ; `listerRegles(): Promise<Array>`, `annoterRegle(numero: number, { reviewStatus, reviewNote }, cle: string): Promise<Object>`, `class ErreurAuthentification extends Error` (`src/services/reglesApiService.js`) — utilisés par `useRegles.js` (Task 4).

- [ ] **Step 1: Écrire les tests (failing) de `reglesApiService.js`**

Créer `clients/regles_api_client/tests/unit/reglesApiService.test.js` :

```js
import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  listerRegles,
  annoterRegle,
  ErreurAuthentification,
} from '../../src/services/reglesApiService.js'

describe('listerRegles', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  it('appelle GET /regles et renvoie le JSON', async () => {
    fetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [{ numero: 1 }],
    })

    const regles = await listerRegles()

    expect(fetch).toHaveBeenCalledWith('http://localhost:8880/regles')
    expect(regles).toEqual([{ numero: 1 }])
  })

  it('lève une erreur si la réponse n\'est pas ok', async () => {
    fetch.mockResolvedValue({ ok: false, status: 500, json: async () => ({}) })

    await expect(listerRegles()).rejects.toThrow()
  })
})

describe('annoterRegle', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  it('envoie un PATCH avec le header Authorization', async () => {
    fetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ numero: 28, review_status: 'a_revoir' }),
    })

    const resultat = await annoterRegle(
      28,
      { reviewStatus: 'a_revoir', reviewNote: 'une note' },
      'ma-cle'
    )

    expect(fetch).toHaveBeenCalledWith('http://localhost:8880/regles/28', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ma-cle',
      },
      body: JSON.stringify({ review_status: 'a_revoir', review_note: 'une note' }),
    })
    expect(resultat).toEqual({ numero: 28, review_status: 'a_revoir' })
  })

  it('lève ErreurAuthentification sur 401', async () => {
    fetch.mockResolvedValue({ ok: false, status: 401, json: async () => ({}) })

    await expect(
      annoterRegle(28, { reviewStatus: 'a_revoir', reviewNote: 'x' }, 'mauvaise-cle')
    ).rejects.toBeInstanceOf(ErreurAuthentification)
  })

  it('lève une erreur classique avec le detail du corps sur 422', async () => {
    fetch.mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({ detail: 'review_note est obligatoire' }),
    })

    await expect(
      annoterRegle(28, { reviewStatus: 'a_revoir', reviewNote: '' }, 'ma-cle')
    ).rejects.toThrow('review_note est obligatoire')
  })
})
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `cd clients/regles_api_client && npm run test -- reglesApiService`
Expected: échec — `src/config.js` et `src/services/reglesApiService.js` n'existent pas encore.

- [ ] **Step 3: Créer `src/config.js`**

```js
export const API_REGLES_URL = import.meta.env.VITE_API_REGLES_URL
```

- [ ] **Step 4: Créer `src/services/reglesApiService.js`**

```js
import { API_REGLES_URL } from '../config.js'

export class ErreurAuthentification extends Error {}

export async function listerRegles() {
  const reponse = await fetch(`${API_REGLES_URL}/regles`)
  if (!reponse.ok) {
    throw new Error(`Échec du chargement des règles (${reponse.status})`)
  }
  return reponse.json()
}

export async function annoterRegle(numero, { reviewStatus, reviewNote }, cle) {
  const reponse = await fetch(`${API_REGLES_URL}/regles/${numero}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${cle}`,
    },
    body: JSON.stringify({ review_status: reviewStatus, review_note: reviewNote ?? null }),
  })

  if (reponse.status === 401) {
    throw new ErreurAuthentification('Clé API absente ou invalide')
  }
  if (!reponse.ok) {
    const corps = await reponse.json().catch(() => ({}))
    throw new Error(corps.detail ?? `Échec de l'annotation (${reponse.status})`)
  }
  return reponse.json()
}
```

- [ ] **Step 5: Lancer les tests, vérifier qu'ils passent**

Run: `cd clients/regles_api_client && npm run test -- reglesApiService`
Expected: `PASS` — 5 tests verts.

- [ ] **Step 6: Commit**

```bash
git add clients/regles_api_client/src/config.js clients/regles_api_client/src/services/ clients/regles_api_client/tests/unit/reglesApiService.test.js
git commit -m "feat(regles_api_client): add reglesApiService HTTP layer"
```

---

## Task 3: Composable `useCleApi.js`

**Files:**
- Create: `clients/regles_api_client/src/composables/useCleApi.js`
- Test: `clients/regles_api_client/tests/unit/useCleApi.test.js`

**Interfaces:**
- Produces: `useCleApi(): { cle: Ref<string|null>, hasKey: ComputedRef<boolean>, setKey(valeur: string): void, clearKey(): void }` — utilisé par `useRegles.js` (Task 4), `App.vue` et `CleApi.vue` (Task 6, Task 9).

**Note d'implémentation** : `cle` est un `ref` défini au **niveau du module** (hors de la fonction `useCleApi`), pas recréé à chaque appel — sinon deux composants qui appellent `useCleApi()` séparément (l'entête et l'écran clé API, par exemple) ne partageraient pas la même valeur réactive, et l'entête ne se mettrait pas à jour après un enregistrement fait depuis l'écran clé API.

- [ ] **Step 1: Écrire les tests (failing)**

Créer `clients/regles_api_client/tests/unit/useCleApi.test.js` :

```js
import { describe, it, expect, beforeEach, vi } from 'vitest'

// vi.resetModules() + import dynamique : useCleApi garde son état au niveau
// du module (voir Task 3), donc chaque test a besoin d'une instance fraîche
// du module pour ne pas hériter de l'état laissé par le test précédent.
describe('useCleApi', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.resetModules()
  })

  it('hasKey est faux sans clé enregistrée', async () => {
    const { useCleApi } = await import('../../src/composables/useCleApi.js')
    const { hasKey } = useCleApi()
    expect(hasKey.value).toBe(false)
  })

  it('setKey enregistre la clé en localStorage et met hasKey à jour', async () => {
    const { useCleApi } = await import('../../src/composables/useCleApi.js')
    const { hasKey, cle, setKey } = useCleApi()

    setKey('ma-cle-secrete')

    expect(hasKey.value).toBe(true)
    expect(cle.value).toBe('ma-cle-secrete')
    expect(localStorage.getItem('qualicheck_regles_api_key')).toBe('ma-cle-secrete')
  })

  it('clearKey supprime la clé', async () => {
    const { useCleApi } = await import('../../src/composables/useCleApi.js')
    const { hasKey, setKey, clearKey } = useCleApi()

    setKey('ma-cle-secrete')
    clearKey()

    expect(hasKey.value).toBe(false)
    expect(localStorage.getItem('qualicheck_regles_api_key')).toBeNull()
  })

  it('une clé déjà en localStorage au chargement du module est reprise', async () => {
    localStorage.setItem('qualicheck_regles_api_key', 'cle-existante')
    const { useCleApi } = await import('../../src/composables/useCleApi.js')
    const { hasKey, cle } = useCleApi()

    expect(hasKey.value).toBe(true)
    expect(cle.value).toBe('cle-existante')
  })
})
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `cd clients/regles_api_client && npm run test -- useCleApi`
Expected: échec — le fichier n'existe pas.

- [ ] **Step 3: Créer `src/composables/useCleApi.js`**

```js
import { ref, computed } from 'vue'

const STORAGE_KEY = 'qualicheck_regles_api_key'

const cle = ref(localStorage.getItem(STORAGE_KEY))

export function useCleApi() {
  const hasKey = computed(() => cle.value !== null && cle.value !== '')

  function setKey(valeur) {
    localStorage.setItem(STORAGE_KEY, valeur)
    cle.value = valeur
  }

  function clearKey() {
    localStorage.removeItem(STORAGE_KEY)
    cle.value = null
  }

  return { cle, hasKey, setKey, clearKey }
}
```

- [ ] **Step 4: Lancer les tests, vérifier qu'ils passent**

Run: `cd clients/regles_api_client && npm run test -- useCleApi`
Expected: `PASS` — 4 tests verts.

- [ ] **Step 5: Commit**

```bash
git add clients/regles_api_client/src/composables/useCleApi.js clients/regles_api_client/tests/unit/useCleApi.test.js
git commit -m "feat(regles_api_client): add useCleApi composable"
```

---

## Task 4: Composable `useRegles.js`

**Files:**
- Create: `clients/regles_api_client/src/composables/useRegles.js`
- Test: `clients/regles_api_client/tests/unit/useRegles.test.js`

**Interfaces:**
- Consumes: `listerRegles`, `annoterRegle`, `ErreurAuthentification` (Task 2) ; `useCleApi` (Task 3)
- Produces: `useRegles(): { reglesBrutes, chargement, erreurChargement, recherche, filtreTheme, filtrePhase, filtreOutil, filtreReviewStatus, themesDisponibles, phasesDisponibles, reglesFiltrees, regleSelectionneeNumero, regleSelectionnee, dernierResultat, erreurAnnotation, redirectionCleApi, charger, selectionner, annoter }` — tous des `Ref`/`ComputedRef` sauf `charger()`, `selectionner(numero)`, `annoter(numero, patch)` qui sont des fonctions. Utilisé par `RevueRegles.vue` (Task 8).

- [ ] **Step 1: Écrire les tests (failing)**

Créer `clients/regles_api_client/tests/unit/useRegles.test.js` :

```js
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useRegles } from '../../src/composables/useRegles.js'
import { ErreurAuthentification } from '../../src/services/reglesApiService.js'

vi.mock('../../src/services/reglesApiService.js', async () => {
  const actual = await vi.importActual('../../src/services/reglesApiService.js')
  return {
    ...actual,
    listerRegles: vi.fn(),
    annoterRegle: vi.fn(),
  }
})
vi.mock('../../src/composables/useCleApi.js', () => ({
  useCleApi: vi.fn(),
}))

import { listerRegles, annoterRegle } from '../../src/services/reglesApiService.js'
import { useCleApi } from '../../src/composables/useCleApi.js'

const REGLE_28 = {
  numero: 28,
  intitule: 'Le formulaire de contact confirme la bonne soumission des données',
  theme: 'Formulaires',
  outils: ['statique', 'playwright'],
  phases: ['Développement'],
  review_status: null,
  review_note: null,
}
const REGLE_65 = {
  numero: 65,
  intitule: 'Les liens ne sont pas soulignés en dehors du texte courant',
  theme: 'Liens',
  outils: ['vision'],
  phases: ['Conception'],
  review_status: 'valide',
  review_note: null,
}

describe('useRegles — chargement et filtrage', () => {
  beforeEach(() => {
    listerRegles.mockResolvedValue([REGLE_28, REGLE_65])
  })

  it('charger() remplit reglesBrutes', async () => {
    const { reglesBrutes, charger } = useRegles()
    await charger()
    expect(reglesBrutes.value).toEqual([REGLE_28, REGLE_65])
  })

  it('reglesFiltrees applique la recherche texte', async () => {
    const { reglesFiltrees, recherche, charger } = useRegles()
    await charger()
    recherche.value = 'formulaire'
    expect(reglesFiltrees.value).toEqual([REGLE_28])
  })

  it('reglesFiltrees applique le filtre outil en OU', async () => {
    const { reglesFiltrees, filtreOutil, charger } = useRegles()
    await charger()
    filtreOutil.value = ['vision']
    expect(reglesFiltrees.value).toEqual([REGLE_65])
  })

  it('reglesFiltrees applique le filtre revue, "aucun" = review_status null', async () => {
    const { reglesFiltrees, filtreReviewStatus, charger } = useRegles()
    await charger()
    filtreReviewStatus.value = ['aucun']
    expect(reglesFiltrees.value).toEqual([REGLE_28])
  })

  it('themesDisponibles liste les thèmes uniques triés', async () => {
    const { themesDisponibles, charger } = useRegles()
    await charger()
    expect(themesDisponibles.value).toEqual(['Formulaires', 'Liens'])
  })
})

describe('useRegles — annotation', () => {
  it('sans clé API, redirige sans appeler le service', async () => {
    useCleApi.mockReturnValue({ hasKey: { value: false }, cle: { value: null }, clearKey: vi.fn() })
    const { annoter, redirectionCleApi } = useRegles()

    await annoter(28, { reviewStatus: 'a_revoir', reviewNote: 'x' })

    expect(annoterRegle).not.toHaveBeenCalled()
    expect(redirectionCleApi.value).toBe(true)
  })

  it('avec une clé valide, met à jour reglesBrutes et dernierResultat', async () => {
    useCleApi.mockReturnValue({ hasKey: { value: true }, cle: { value: 'ma-cle' }, clearKey: vi.fn() })
    listerRegles.mockResolvedValue([REGLE_28])
    annoterRegle.mockResolvedValue({ ...REGLE_28, review_status: 'a_revoir', review_note: 'x' })

    const { charger, reglesBrutes, dernierResultat, annoter } = useRegles()
    await charger()
    await annoter(28, { reviewStatus: 'a_revoir', reviewNote: 'x' })

    expect(dernierResultat.value).toBe('succes')
    expect(reglesBrutes.value[0].review_status).toBe('a_revoir')
  })

  it('sur ErreurAuthentification, efface la clé et redirige', async () => {
    const clearKey = vi.fn()
    useCleApi.mockReturnValue({ hasKey: { value: true }, cle: { value: 'cle-perimee' }, clearKey })
    annoterRegle.mockRejectedValue(new ErreurAuthentification('invalide'))

    const { annoter, redirectionCleApi } = useRegles()
    await annoter(28, { reviewStatus: 'a_revoir', reviewNote: 'x' })

    expect(clearKey).toHaveBeenCalled()
    expect(redirectionCleApi.value).toBe(true)
  })

  it('sur erreur serveur, expose dernierResultat=erreur avec le message', async () => {
    useCleApi.mockReturnValue({ hasKey: { value: true }, cle: { value: 'ma-cle' }, clearKey: vi.fn() })
    annoterRegle.mockRejectedValue(new Error('Échec de l\'annotation (500)'))

    const { annoter, dernierResultat, erreurAnnotation } = useRegles()
    await annoter(28, { reviewStatus: 'a_revoir', reviewNote: 'x' })

    expect(dernierResultat.value).toBe('erreur')
    expect(erreurAnnotation.value).toBe('Échec de l\'annotation (500)')
  })
})
```

- [ ] **Step 2: Lancer les tests, vérifier qu'ils échouent**

Run: `cd clients/regles_api_client && npm run test -- useRegles`
Expected: échec — le fichier n'existe pas.

- [ ] **Step 3: Créer `src/composables/useRegles.js`**

```js
import { ref, computed } from 'vue'
import { listerRegles, annoterRegle, ErreurAuthentification } from '../services/reglesApiService.js'
import { useCleApi } from './useCleApi.js'

export function useRegles() {
  const reglesBrutes = ref([])
  const chargement = ref(false)
  const erreurChargement = ref(null)

  const recherche = ref('')
  const filtreTheme = ref([])
  const filtrePhase = ref([])
  const filtreOutil = ref([])
  const filtreReviewStatus = ref([])

  const regleSelectionneeNumero = ref(null)
  const dernierResultat = ref(null)
  const erreurAnnotation = ref(null)
  const redirectionCleApi = ref(false)

  const themesDisponibles = computed(() =>
    [...new Set(reglesBrutes.value.map((r) => r.theme))].sort()
  )
  const phasesDisponibles = computed(() =>
    [...new Set(reglesBrutes.value.flatMap((r) => r.phases))].sort()
  )

  const reglesFiltrees = computed(() =>
    reglesBrutes.value.filter((regle) => {
      const texte = recherche.value.trim().toLowerCase()
      const matchRecherche = texte === '' || regle.intitule.toLowerCase().includes(texte)
      const matchTheme = filtreTheme.value.length === 0 || filtreTheme.value.includes(regle.theme)
      const matchPhase =
        filtrePhase.value.length === 0 || filtrePhase.value.some((p) => regle.phases.includes(p))
      const matchOutil =
        filtreOutil.value.length === 0 || filtreOutil.value.some((o) => regle.outils.includes(o))
      const matchStatut =
        filtreReviewStatus.value.length === 0 ||
        filtreReviewStatus.value.some((statut) =>
          statut === 'aucun' ? regle.review_status === null : regle.review_status === statut
        )
      return matchRecherche && matchTheme && matchPhase && matchOutil && matchStatut
    })
  )

  const regleSelectionnee = computed(
    () => reglesBrutes.value.find((r) => r.numero === regleSelectionneeNumero.value) ?? null
  )

  async function charger() {
    chargement.value = true
    erreurChargement.value = null
    try {
      reglesBrutes.value = await listerRegles()
    } catch (e) {
      erreurChargement.value = e.message
    } finally {
      chargement.value = false
    }
  }

  function selectionner(numero) {
    regleSelectionneeNumero.value = numero
    dernierResultat.value = null
    erreurAnnotation.value = null
  }

  async function annoter(numero, patch) {
    const { hasKey, cle, clearKey } = useCleApi()
    if (!hasKey.value) {
      redirectionCleApi.value = true
      return
    }
    try {
      const regleMiseAJour = await annoterRegle(numero, patch, cle.value)
      const index = reglesBrutes.value.findIndex((r) => r.numero === numero)
      if (index !== -1) reglesBrutes.value[index] = regleMiseAJour
      dernierResultat.value = 'succes'
      erreurAnnotation.value = null
    } catch (e) {
      if (e instanceof ErreurAuthentification) {
        clearKey()
        redirectionCleApi.value = true
        return
      }
      dernierResultat.value = 'erreur'
      erreurAnnotation.value = e.message
    }
  }

  return {
    reglesBrutes,
    chargement,
    erreurChargement,
    recherche,
    filtreTheme,
    filtrePhase,
    filtreOutil,
    filtreReviewStatus,
    themesDisponibles,
    phasesDisponibles,
    reglesFiltrees,
    regleSelectionneeNumero,
    regleSelectionnee,
    dernierResultat,
    erreurAnnotation,
    redirectionCleApi,
    charger,
    selectionner,
    annoter,
  }
}
```

- [ ] **Step 4: Lancer les tests, vérifier qu'ils passent**

Run: `cd clients/regles_api_client && npm run test -- useRegles`
Expected: `PASS` — 8 tests verts.

- [ ] **Step 5: Commit**

```bash
git add clients/regles_api_client/src/composables/useRegles.js clients/regles_api_client/tests/unit/useRegles.test.js
git commit -m "feat(regles_api_client): add useRegles composable with client-side filtering"
```

---

## Task 5: Port des styles des maquettes en Sass

**Files:**
- Create: `clients/regles_api_client/src/styles/_variables.scss`
- Create: `clients/regles_api_client/src/styles/_base.scss`
- Create: `clients/regles_api_client/src/styles/_bootstrap-icons.scss`
- Create: `clients/regles_api_client/src/styles/_entete.scss`
- Create: `clients/regles_api_client/src/styles/_pied-de-page.scss`
- Create: `clients/regles_api_client/src/styles/_bouton.scss`
- Create: `clients/regles_api_client/src/styles/_champ-texte.scss`
- Create: `clients/regles_api_client/src/styles/_chip-filtre.scss`
- Create: `clients/regles_api_client/src/styles/_barre-filtres.scss`
- Create: `clients/regles_api_client/src/styles/_badge-statut.scss`
- Create: `clients/regles_api_client/src/styles/_tag-outil.scss`
- Create: `clients/regles_api_client/src/styles/_ligne-regle.scss`
- Create: `clients/regles_api_client/src/styles/_segmented-statut.scss`
- Create: `clients/regles_api_client/src/styles/_bloc-provenance.scss`
- Create: `clients/regles_api_client/src/styles/_panneau-detail-regle.scss`
- Create: `clients/regles_api_client/src/styles/_bandeau-message.scss`
- Create: `clients/regles_api_client/src/styles/_ecran-revue-regles.scss`
- Create: `clients/regles_api_client/src/styles/_ecran-cle-api.scss`
- Create: `clients/regles_api_client/src/styles/main.scss`
- Create: `clients/regles_api_client/src/styles/fonts/` (copie de `conception/maquettes/US0/style/fonts/`)
- Modify: `clients/regles_api_client/src/main.js` (import de `./styles/main.scss`)

**Interfaces:**
- Produces: classes CSS globales disponibles dans tous les composants (`entete`, `pied-de-page`, `bouton`, `champ-texte`, `chip-filtre`, `barre-filtres`, `badge-statut`, `tag-outil`, `ligne-regle`, `segmented-statut`, `bloc-provenance`, `panneau-detail-regle`, `bandeau-message`, `ecran-revue-regles*`, `ecran-cle-api*`, icônes `bi bi-*`). Consommé par les composants (Task 7) et vues (Task 8, 9).

**16 des 18 fichiers sont des copies verbatim** (seule l'extension change, le contenu CSS ne nécessite aucune syntaxe Sass) : les custom properties (`--color-*`) n'ont pas besoin de `@use`/variables Sass. `_ecran-revue-regles.scss` et `_ecran-cle-api.scss` sont **un assemblage**, pas une copie : dans les maquettes, ces règles vivaient en `<style>` inline dans chaque fichier HTML (`ecran-revue-regles.html`, `ecran-revue-regles-etats.html`, `ecran-cle-api.html`), pas dans `US0/style/`.

- [ ] **Step 1: Copier les 15 fichiers CSS réutilisables tels quels**

Run:

```bash
cd /media/david/projets1/QualiCheck
mkdir -p clients/regles_api_client/src/styles/fonts
cp conception/maquettes/US0/style/fonts/* clients/regles_api_client/src/styles/fonts/
for f in variables base bootstrap-icons entete pied-de-page bouton champ-texte \
         chip-filtre barre-filtres badge-statut tag-outil ligne-regle \
         segmented-statut bloc-provenance panneau-detail-regle bandeau-message; do
  cp "conception/maquettes/US0/style/$f.css" "clients/regles_api_client/src/styles/_$f.scss"
done
```

Expected: 16 fichiers `_*.scss` créés dans `clients/regles_api_client/src/styles/`, dossier `fonts/` avec 3 fichiers copiés.

- [ ] **Step 2: Créer `_ecran-revue-regles.scss` (assemblage des styles inline de `ecran-revue-regles.html` et `ecran-revue-regles-etats.html`)**

```scss
.ecran-revue-regles {
  max-width: 75rem;
  margin-inline: auto;
  padding-block: 2rem;
}
.ecran-revue-regles__entete {
  margin-bottom: 1.5rem;
}
.ecran-revue-regles__titre {
  font: var(--title-section-font);
  color: var(--color-text);
  margin: 0;
}
.ecran-revue-regles__sous-titre {
  font: var(--text-font);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0.375rem 0 0;
}
.ecran-revue-regles__corps {
  display: grid;
  grid-template-columns: minmax(20rem, 26rem) 1fr;
  gap: 0;
  margin-top: 1rem;
  border: 1px solid var(--color-surface);
  border-radius: var(--radius-default);
  min-height: 34rem;
}
.ecran-revue-regles__liste {
  border-right: 1px solid var(--color-surface);
  max-height: 40rem;
  overflow-y: auto;
}
.ecran-revue-regles__liste-vide {
  padding: 2.5rem 1.5rem;
  text-align: center;
  font: var(--text-font);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}
.ecran-revue-regles__detail {
  padding: 1.75rem 2rem;
  max-height: 40rem;
  overflow-y: auto;
}
.ecran-revue-regles__detail-placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 2.5rem;
  font: var(--text-font);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}
.panneau-detail-regle__annotation {
  margin-top: 1.625rem;
  padding-top: 1.125rem;
  border-top: 1px solid var(--color-surface);
}
.panneau-detail-regle__annotation h3 {
  font-size: 0.8125rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
  margin: 0 0 0.875rem;
}
.panneau-detail-regle__annotation .champ-texte {
  margin-top: 1rem;
}
.panneau-detail-regle__pied {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 1.25rem;
  flex-wrap: wrap;
}
.panneau-detail-regle__horodatage {
  font: var(--text-font);
  font-size: 0.8125rem;
  color: var(--color-text-secondary);
}
```

- [ ] **Step 3: Créer `_ecran-cle-api.scss` (assemblage du style inline de `ecran-cle-api.html`)**

```scss
.ecran-cle-api {
  max-width: var(--container-narrow);
  margin-inline: auto;
  padding-block: 2rem;
  display: flex;
  flex-direction: column;
  gap: 4rem;
}
.ecran-cle-api__titre {
  font: var(--title-section-font);
  color: var(--color-text);
  margin: 0;
}
.ecran-cle-api__sous-titre {
  font: var(--text-font);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0.375rem 0 0;
}
.ecran-cle-api__statut {
  font: var(--text-font);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin: 0;
}
.ecran-cle-api__actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}
```

- [ ] **Step 4: Créer `main.scss`**

```scss
@use 'variables';
@use 'bootstrap-icons';
@use 'base';
@use 'entete';
@use 'pied-de-page';
@use 'bouton';
@use 'champ-texte';
@use 'chip-filtre';
@use 'barre-filtres';
@use 'badge-statut';
@use 'tag-outil';
@use 'ligne-regle';
@use 'segmented-statut';
@use 'bloc-provenance';
@use 'panneau-detail-regle';
@use 'bandeau-message';
@use 'ecran-revue-regles';
@use 'ecran-cle-api';
```

- [ ] **Step 5: Importer les styles dans `main.js`**

Modifier `clients/regles_api_client/src/main.js` :

```js
import { createApp } from 'vue'
import App from './App.vue'
import './styles/main.scss'

createApp(App).mount('#app')
```

- [ ] **Step 6: Vérifier que le build compile le Sass et produit les tokens attendus**

Run: `cd clients/regles_api_client && npm run build && grep -q -- "--color-text" dist/assets/*.css && echo OK`
Expected: `OK` — la variable `--color-text` de `_variables.scss` est bien présente dans le CSS compilé.

- [ ] **Step 7: Commit**

```bash
git add clients/regles_api_client/src/styles/ clients/regles_api_client/src/main.js
git commit -m "feat(regles_api_client): port maquette CSS to Sass partials"
```

---

## Task 6: Routeur et coquille `App.vue`

**Files:**
- Create: `clients/regles_api_client/src/router/index.js`
- Create: `clients/regles_api_client/src/views/RevueRegles.vue` (placeholder, remplacé Task 8)
- Create: `clients/regles_api_client/src/views/CleApi.vue` (placeholder, remplacé Task 9)
- Modify: `clients/regles_api_client/src/App.vue`
- Modify: `clients/regles_api_client/src/main.js`

**Interfaces:**
- Consumes: `useCleApi` (Task 3)
- Produces: `router` (export par défaut de `src/router/index.js`), monté dans `main.js`. Routes `revue` (`/revue`) et `cle-api` (`/cle-api`), `/` redirige vers `/revue`.

- [ ] **Step 1: Créer les vues placeholder**

`clients/regles_api_client/src/views/RevueRegles.vue` :

```vue
<template>
  <main class="ecran-revue-regles">
    <p>Écran de revue des règles (à venir — Task 8)</p>
  </main>
</template>
```

`clients/regles_api_client/src/views/CleApi.vue` :

```vue
<template>
  <main class="ecran-cle-api">
    <p>Écran de gestion de la clé API (à venir — Task 9)</p>
  </main>
</template>
```

- [ ] **Step 2: Créer `src/router/index.js`**

```js
import { createRouter, createWebHistory } from 'vue-router'
import RevueRegles from '../views/RevueRegles.vue'
import CleApi from '../views/CleApi.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/revue' },
    { path: '/revue', name: 'revue', component: RevueRegles },
    { path: '/cle-api', name: 'cle-api', component: CleApi },
  ],
})

export default router
```

- [ ] **Step 3: Réécrire `App.vue`**

```vue
<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useCleApi } from './composables/useCleApi.js'

const route = useRoute()
const { hasKey } = useCleApi()

const liensNav = computed(() => {
  if (hasKey.value) {
    return [{ texte: 'Modifier ma clé API', actif: false }, { texte: 'Supprimer ma clé API', actif: false }]
  }
  return [{ texte: 'Renseigner ma clé API', actif: route.name === 'cle-api' }]
})
</script>

<template>
  <header class="entete">
    <router-link class="entete__logo" to="/revue">
      <span class="entete__logo-icone"><i class="bi bi-check-lg"></i></span>
      QualiCheck
    </router-link>
    <nav class="entete__nav">
      <router-link
        v-for="lien in liensNav"
        :key="lien.texte"
        to="/cle-api"
        :aria-current="lien.actif ? 'page' : undefined"
      >
        {{ lien.texte }}
      </router-link>
    </nav>
  </header>

  <router-view />

  <footer class="pied-de-page">
    <div class="pied-de-page__haut">
      <div>
        <a class="pied-de-page__logo" href="#">
          <i class="bi bi-check-lg"></i> QualiCheck
        </a>
        <p class="pied-de-page__tagline">Assistant d'aide à l'audit qualité web basé sur les règles Opquast</p>
      </div>
      <nav class="pied-de-page__nav">
        <a href="#"><i class="bi bi-book"></i> Le projet</a>
        <a href="#"><i class="bi bi-bank"></i> Mentions légales</a>
        <a href="#"><i class="bi bi-shield-lock"></i> Politique des données</a>
      </nav>
    </div>
    <div class="pied-de-page__bas">
      <p>🄯 Copyleft 2026, vous trouverez le projet sur <a href="#">GitHub</a></p>
      <p class="pied-de-page__mention">QualiCheck n'est pas un outil officiel Opquast et ne remplace pas l'expertise d'un auditeur</p>
    </div>
  </footer>
</template>
```

- [ ] **Step 4: Brancher le routeur dans `main.js`**

```js
import { createApp } from 'vue'
import App from './App.vue'
import router from './router/index.js'
import './styles/main.scss'

createApp(App).use(router).mount('#app')
```

- [ ] **Step 5: Vérification manuelle**

Run: `cd clients/regles_api_client && npm run dev`
Ouvrir `http://localhost:5173` : redirige vers `/revue`, affiche le placeholder, l'entête montre "Renseigner ma clé API". Cliquer le lien : navigue vers `/cle-api`, affiche son placeholder. Arrêter le serveur.

- [ ] **Step 6: Commit**

```bash
git add clients/regles_api_client/src/router/ clients/regles_api_client/src/views/ clients/regles_api_client/src/App.vue clients/regles_api_client/src/main.js
git commit -m "feat(regles_api_client): wire vue-router and App shell"
```

---

## Task 7: Composants de présentation

**Files:**
- Create: `clients/regles_api_client/src/utils/statutRevue.js`
- Create: `clients/regles_api_client/src/components/BandeauMessage.vue`
- Create: `clients/regles_api_client/src/components/BarreFiltres.vue`
- Create: `clients/regles_api_client/src/components/ListeRegles.vue`
- Create: `clients/regles_api_client/src/components/PanneauDetailRegle.vue`

**Interfaces:**
- Produces:
  - `libelleStatut(reviewStatus: string|null): { classe: string, texte: string }`
  - `BandeauMessage` — props `type: 'succes'|'erreur'`, `message: string`
  - `BarreFiltres` — props `themesDisponibles: string[]`, `phasesDisponibles: string[]`, `compteAffiche: number`, `compteTotal: number` ; v-model `recherche`, `filtreTheme`, `filtrePhase`, `filtreOutil`, `filtreReviewStatus`
  - `ListeRegles` — props `regles: Array`, `selectionneeNumero: number|null` ; emits `selectionner(numero: number)`
  - `PanneauDetailRegle` — props `regle: Object` (une `RegleRead` du schéma `app/api_regles/schemas.py`) ; emits `annoter({ reviewStatus: string|null, reviewNote: string|null })`
- Consommé par `RevueRegles.vue` (Task 8).

- [ ] **Step 1: Créer `src/utils/statutRevue.js`**

```js
const LIBELLES = {
  null: { classe: 'badge-statut--neutre', texte: 'Non revue' },
  a_revoir: { classe: 'badge-statut--danger', texte: 'À revoir' },
  valide: { classe: 'badge-statut--succes', texte: 'Validée' },
}

export function libelleStatut(reviewStatus) {
  return LIBELLES[reviewStatus] ?? LIBELLES[null]
}
```

- [ ] **Step 2: Créer `src/components/BandeauMessage.vue`**

```vue
<script setup>
defineProps({
  type: { type: String, required: true },
  message: { type: String, required: true },
})
</script>

<template>
  <div class="bandeau-message" :class="`bandeau-message--${type}`" :role="type === 'erreur' ? 'alert' : 'status'">
    <i class="bi" :class="type === 'erreur' ? 'bi-exclamation-circle' : 'bi-check-circle'"></i>
    {{ message }}
  </div>
</template>
```

- [ ] **Step 3: Créer `src/components/BarreFiltres.vue`**

```vue
<script setup>
defineProps({
  themesDisponibles: { type: Array, default: () => [] },
  phasesDisponibles: { type: Array, default: () => [] },
  compteAffiche: { type: Number, required: true },
  compteTotal: { type: Number, required: true },
})

const recherche = defineModel('recherche', { default: '' })
const filtreTheme = defineModel('filtreTheme', { default: () => [] })
const filtrePhase = defineModel('filtrePhase', { default: () => [] })
const filtreOutil = defineModel('filtreOutil', { default: () => [] })
const filtreReviewStatus = defineModel('filtreReviewStatus', { default: () => [] })

const OUTILS = [
  { valeur: 'statique', libelle: 'Statique' },
  { valeur: 'playwright', libelle: 'Playwright' },
  { valeur: 'vision', libelle: 'Vision' },
  { valeur: 'manuel', libelle: 'Manuel' },
]
const STATUTS = [
  { valeur: 'aucun', libelle: 'Non revue' },
  { valeur: 'a_revoir', libelle: 'À revoir' },
  { valeur: 'valide', libelle: 'Validée' },
]
</script>

<template>
  <div class="barre-filtres">
    <div class="barre-filtres__ligne-recherche">
      <div class="barre-filtres__recherche">
        <label for="recherche" class="visually-hidden">Rechercher dans l'intitulé des règles</label>
        <input type="search" id="recherche" v-model="recherche" placeholder="Rechercher dans l'intitulé…" />
      </div>
      <p class="barre-filtres__compte"><strong>{{ compteAffiche }}</strong> / {{ compteTotal }} règles affichées</p>
    </div>

    <details class="barre-filtres__filtres">
      <summary>Filtres <i class="bi bi-chevron-down"></i></summary>
      <div class="barre-filtres__groupes">
        <fieldset class="barre-filtres__groupe">
          <legend class="visually-hidden">Thème</legend>
          <span class="barre-filtres__groupe-titre" aria-hidden="true">Thème</span>
          <div class="barre-filtres__groupe-ligne">
            <label class="chip-filtre" v-for="theme in themesDisponibles" :key="theme">
              <input type="checkbox" :value="theme" v-model="filtreTheme" />{{ theme }}
            </label>
          </div>
        </fieldset>

        <fieldset class="barre-filtres__groupe">
          <legend class="visually-hidden">Phase</legend>
          <span class="barre-filtres__groupe-titre" aria-hidden="true">Phase</span>
          <div class="barre-filtres__groupe-ligne">
            <label class="chip-filtre" v-for="phase in phasesDisponibles" :key="phase">
              <input type="checkbox" :value="phase" v-model="filtrePhase" />{{ phase }}
            </label>
          </div>
        </fieldset>

        <fieldset class="barre-filtres__groupe">
          <legend class="visually-hidden">Outil</legend>
          <span class="barre-filtres__groupe-titre" aria-hidden="true">Outil</span>
          <div class="barre-filtres__groupe-ligne">
            <label class="chip-filtre" v-for="outil in OUTILS" :key="outil.valeur">
              <input type="checkbox" :value="outil.valeur" v-model="filtreOutil" />{{ outil.libelle }}
            </label>
          </div>
        </fieldset>

        <fieldset class="barre-filtres__groupe">
          <legend class="visually-hidden">Revue</legend>
          <span class="barre-filtres__groupe-titre" aria-hidden="true">Revue</span>
          <div class="barre-filtres__groupe-ligne">
            <label class="chip-filtre" v-for="statut in STATUTS" :key="statut.valeur">
              <input type="checkbox" :value="statut.valeur" v-model="filtreReviewStatus" />{{ statut.libelle }}
            </label>
          </div>
        </fieldset>
      </div>
    </details>
  </div>
</template>
```

- [ ] **Step 4: Créer `src/components/ListeRegles.vue`**

```vue
<script setup>
import { libelleStatut } from '../utils/statutRevue.js'

defineProps({
  regles: { type: Array, required: true },
  selectionneeNumero: { type: Number, default: null },
})
const emit = defineEmits(['selectionner'])
</script>

<template>
  <nav class="ecran-revue-regles__liste" aria-label="Liste des règles">
    <p v-if="regles.length === 0" class="ecran-revue-regles__liste-vide">
      Aucune règle ne correspond aux filtres sélectionnés.
    </p>
    <ul v-else class="liste-regles">
      <li v-for="regle in regles" :key="regle.numero">
        <button
          class="ligne-regle"
          type="button"
          :aria-current="regle.numero === selectionneeNumero ? 'true' : undefined"
          @click="emit('selectionner', regle.numero)"
        >
          <span class="ligne-regle__numero">n°{{ regle.numero }}</span>
          <span>
            <p class="ligne-regle__intitule">{{ regle.intitule }}</p>
            <span class="ligne-regle__outils">
              <span class="tag-outil" v-for="outil in regle.outils" :key="outil">{{ outil }}</span>
            </span>
          </span>
          <span class="badge-statut" :class="libelleStatut(regle.review_status).classe">
            {{ libelleStatut(regle.review_status).texte }}
          </span>
        </button>
      </li>
    </ul>
  </nav>
</template>
```

- [ ] **Step 5: Créer `src/components/PanneauDetailRegle.vue`**

```vue
<script setup>
import { ref, computed, watch } from 'vue'
import { libelleStatut } from '../utils/statutRevue.js'

const props = defineProps({
  regle: { type: Object, required: true },
})
const emit = defineEmits(['annoter'])

const statutForm = ref(props.regle.review_status ?? 'aucun')
const noteForm = ref(props.regle.review_note ?? '')

watch(
  () => props.regle.numero,
  () => {
    statutForm.value = props.regle.review_status ?? 'aucun'
    noteForm.value = props.regle.review_note ?? ''
  }
)

watch(statutForm, (valeur) => {
  if (valeur === 'aucun') noteForm.value = ''
})

const peutEnregistrer = computed(
  () => statutForm.value !== 'a_revoir' || noteForm.value.trim() !== ''
)

const badge = computed(() => libelleStatut(props.regle.review_status))

const horodatage = computed(() => {
  if (!props.regle.reviewed_at) return 'Jamais revue'
  const date = new Date(props.regle.reviewed_at)
  return `Dernière revue : ${date.toLocaleDateString('fr-FR')} ${date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}`
})

function enregistrer() {
  if (statutForm.value === 'aucun') {
    emit('annoter', { reviewStatus: null, reviewNote: null })
  } else {
    emit('annoter', { reviewStatus: statutForm.value, reviewNote: noteForm.value })
  }
}
</script>

<template>
  <article class="panneau-detail-regle">
    <p class="panneau-detail-regle__eyebrow">Règle n°{{ regle.numero }} · {{ regle.theme }}</p>
    <div class="panneau-detail-regle__entete">
      <h2 class="panneau-detail-regle__titre">{{ regle.intitule }}</h2>
      <span class="badge-statut" :class="badge.classe">{{ badge.texte }}</span>
    </div>
    <div class="panneau-detail-regle__meta">
      <span class="tag-outil" v-for="outil in regle.outils" :key="outil">{{ outil }}</span>
      <span class="tag-meta" v-for="tag in regle.tags" :key="tag">{{ tag }}</span>
      <span class="tag-meta" v-for="phase in regle.phases" :key="phase">{{ phase }}</span>
    </div>

    <section class="panneau-detail-regle__section">
      <h3>Contexte</h3>
      <p>{{ regle.contexte ?? 'Non renseigné.' }}</p>
    </section>
    <section class="panneau-detail-regle__section">
      <h3>Solution</h3>
      <p>{{ regle.solution }}</p>
    </section>
    <section class="panneau-detail-regle__section">
      <h3>Contrôle</h3>
      <p>{{ regle.controle }}</p>
    </section>
    <section class="panneau-detail-regle__section">
      <h3>Guide d'analyse</h3>
      <p>{{ regle.guide_analyse }}</p>
      <p v-if="regle.strategie_justification" class="panneau-detail-regle__justification">
        <strong>Justification —</strong> {{ regle.strategie_justification }}
      </p>
    </section>

    <dl class="bloc-provenance">
      <div class="bloc-provenance__item"><dt>Stratégie</dt><dd>{{ regle.strategie_analyse }}</dd></div>
      <div class="bloc-provenance__item"><dt>Version du prompt</dt><dd>{{ regle.prompt_version ?? '—' }}</dd></div>
      <div class="bloc-provenance__item"><dt>Modèle</dt><dd>{{ regle.llm_model ?? '—' }}</dd></div>
    </dl>

    <div class="panneau-detail-regle__annotation">
      <h3>Annotation de revue</h3>
      <fieldset class="segmented-statut">
        <legend>Statut de revue</legend>
        <label class="segmented-statut__option segmented-statut__option--neutre">
          <input type="radio" name="review_status" value="aucun" v-model="statutForm" />
          Non revue
        </label>
        <label class="segmented-statut__option segmented-statut__option--danger">
          <input type="radio" name="review_status" value="a_revoir" v-model="statutForm" />
          À revoir
        </label>
        <label class="segmented-statut__option segmented-statut__option--succes">
          <input type="radio" name="review_status" value="valide" v-model="statutForm" />
          Validée
        </label>
      </fieldset>

      <div class="champ-texte" v-if="statutForm !== 'aucun'">
        <label for="review-note">
          Note de revue
          <span v-if="statutForm === 'a_revoir'" style="color: var(--color-danger-background)"> — obligatoire</span>
        </label>
        <textarea id="review-note" rows="3" v-model="noteForm"></textarea>
        <p class="champ-texte__aide">
          Cette note est réinjectée telle quelle dans le prompt lors du prochain <code>make enrich-again</code>.
        </p>
      </div>

      <div class="panneau-detail-regle__pied">
        <span class="panneau-detail-regle__horodatage">{{ horodatage }}</span>
        <button class="bouton bouton--plein" type="button" :disabled="!peutEnregistrer" @click="enregistrer">
          Enregistrer l'annotation
        </button>
      </div>
    </div>
  </article>
</template>
```

- [ ] **Step 6: Vérifier que tout compile**

Run: `cd clients/regles_api_client && npm run build`
Expected: build sans erreur (les composants ne sont pas encore montés nulle part, mais Vite/Vue valident la syntaxe des SFC au build).

- [ ] **Step 7: Commit**

```bash
git add clients/regles_api_client/src/utils/ clients/regles_api_client/src/components/
git commit -m "feat(regles_api_client): add presentational components for the revue screen"
```

---

## Task 8: Écran `RevueRegles.vue` (réel)

**Files:**
- Modify: `clients/regles_api_client/src/views/RevueRegles.vue` (remplace le placeholder de la Task 6)

**Interfaces:**
- Consumes: `useRegles` (Task 4), `BarreFiltres`, `ListeRegles`, `PanneauDetailRegle`, `BandeauMessage` (Task 7)

- [ ] **Step 1: Réécrire `src/views/RevueRegles.vue`**

```vue
<script setup>
import { onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useRegles } from '../composables/useRegles.js'
import BarreFiltres from '../components/BarreFiltres.vue'
import ListeRegles from '../components/ListeRegles.vue'
import PanneauDetailRegle from '../components/PanneauDetailRegle.vue'
import BandeauMessage from '../components/BandeauMessage.vue'

const router = useRouter()
const {
  reglesBrutes,
  reglesFiltrees,
  erreurChargement,
  recherche,
  filtreTheme,
  filtrePhase,
  filtreOutil,
  filtreReviewStatus,
  themesDisponibles,
  phasesDisponibles,
  regleSelectionneeNumero,
  regleSelectionnee,
  dernierResultat,
  erreurAnnotation,
  redirectionCleApi,
  charger,
  selectionner,
  annoter,
} = useRegles()

onMounted(charger)

watch(redirectionCleApi, (doitRediriger) => {
  if (doitRediriger) router.push('/cle-api')
})
</script>

<template>
  <main class="ecran-revue-regles">
    <div class="ecran-revue-regles__entete">
      <h1 class="ecran-revue-regles__titre">Revue du référentiel</h1>
      <p class="ecran-revue-regles__sous-titre">Classification des règles Opquast par l'agent d'enrichissement</p>
    </div>

    <p v-if="erreurChargement" class="ecran-revue-regles__liste-vide">{{ erreurChargement }}</p>

    <template v-else>
      <BarreFiltres
        v-model:recherche="recherche"
        v-model:filtre-theme="filtreTheme"
        v-model:filtre-phase="filtrePhase"
        v-model:filtre-outil="filtreOutil"
        v-model:filtre-review-status="filtreReviewStatus"
        :themes-disponibles="themesDisponibles"
        :phases-disponibles="phasesDisponibles"
        :compte-affiche="reglesFiltrees.length"
        :compte-total="reglesBrutes.length"
      />

      <div class="ecran-revue-regles__corps">
        <ListeRegles
          :regles="reglesFiltrees"
          :selectionnee-numero="regleSelectionneeNumero"
          @selectionner="selectionner"
        />

        <div class="ecran-revue-regles__detail">
          <template v-if="regleSelectionnee">
            <BandeauMessage v-if="dernierResultat === 'succes'" type="succes" message="Annotation enregistrée." />
            <BandeauMessage
              v-else-if="dernierResultat === 'erreur'"
              type="erreur"
              :message="erreurAnnotation ?? 'Une erreur est survenue, veuillez réessayer.'"
            />
            <PanneauDetailRegle
              :regle="regleSelectionnee"
              @annoter="(patch) => annoter(regleSelectionnee.numero, patch)"
            />
          </template>
          <p v-else class="ecran-revue-regles__detail-placeholder">
            Sélectionnez une règle dans la liste pour l'examiner et l'annoter.
          </p>
        </div>
      </div>
    </template>
  </main>
</template>
```

- [ ] **Step 2: Vérification manuelle de bout en bout**

Prérequis : `make api-regles` démarré dans un autre terminal (à la racine du projet), une base avec des règles ingérées.

Run: `cd clients/regles_api_client && npm run dev`

Vérifier dans le navigateur (`http://localhost:5173/revue`) :
- la liste des règles se charge (pas d'erreur CORS dans la console) ;
- cocher un filtre qui n'a aucune correspondance affiche le message de liste vide ;
- sélectionner une règle affiche le panneau de détail ;
- sans clé API enregistrée, cliquer "Enregistrer l'annotation" redirige immédiatement vers `/cle-api` sans requête réseau visible dans l'onglet Réseau du navigateur ;
- avec une clé valide enregistrée (voir Task 9), annoter réellement une règle affiche le bandeau de succès, puis `curl http://localhost:8880/regles/{numero}` (dans un terminal) confirme que `review_status`/`review_note`/`reviewed_at` sont bien écrits en base.

Arrêter le serveur.

- [ ] **Step 3: Commit**

```bash
git add clients/regles_api_client/src/views/RevueRegles.vue
git commit -m "feat(regles_api_client): assemble the real RevueRegles screen"
```

---

## Task 9: Écran `CleApi.vue` (réel)

**Files:**
- Modify: `clients/regles_api_client/src/views/CleApi.vue` (remplace le placeholder de la Task 6)

**Interfaces:**
- Consumes: `useCleApi` (Task 3)

- [ ] **Step 1: Réécrire `src/views/CleApi.vue`**

```vue
<script setup>
import { ref } from 'vue'
import { useCleApi } from '../composables/useCleApi.js'

const { hasKey, setKey, clearKey } = useCleApi()
const saisie = ref('')
const enModification = ref(false)

function commencerModification() {
  enModification.value = true
  saisie.value = ''
}

function enregistrer() {
  if (saisie.value.trim() === '') return
  setKey(saisie.value.trim())
  saisie.value = ''
  enModification.value = false
}
</script>

<template>
  <main class="ecran-cle-api">
    <div>
      <h1 class="ecran-cle-api__titre">Clé API</h1>
      <p class="ecran-cle-api__sous-titre">Nécessaire pour modifier les règles du référentiel.</p>
    </div>

    <template v-if="!hasKey || enModification">
      <div class="champ-texte">
        <label for="cle-api">Votre clé API</label>
        <input type="password" id="cle-api" v-model="saisie" placeholder="Collez votre clé ici" />
        <p class="champ-texte__aide">
          Cette clé vous a été fournie par l'équipe QualiCheck. Elle n'est nécessaire que pour
          enregistrer des annotations sur les règles.
        </p>
      </div>
      <div class="ecran-cle-api__actions">
        <button class="bouton bouton--plein" type="button" @click="enregistrer">
          {{ hasKey ? 'Enregistrer la nouvelle clé' : 'Enregistrer la clé' }}
        </button>
      </div>
    </template>

    <template v-else>
      <p class="ecran-cle-api__statut">Une clé API est enregistrée sur cet appareil.</p>
      <dl class="bloc-provenance">
        <div class="bloc-provenance__item"><dt>Clé API</dt><dd>••••••••••••••••••••••••••••••••</dd></div>
      </dl>
      <div class="ecran-cle-api__actions">
        <button class="bouton bouton--contour" type="button" @click="commencerModification">Modifier la clé</button>
        <button class="bouton bouton--neutre" type="button" @click="clearKey">Supprimer la clé</button>
      </div>
    </template>
  </main>
</template>
```

- [ ] **Step 2: Vérification manuelle**

Run: `cd clients/regles_api_client && npm run dev`

Sur `http://localhost:5173/cle-api` : saisir une clé et l'enregistrer bascule l'écran sur l'état "clé enregistrée" et l'entête de l'application passe de "Renseigner ma clé API" à "Modifier ma clé API" / "Supprimer ma clé API" ; "Modifier la clé" revient au formulaire ; "Supprimer la clé" revient à l'état initial. Arrêter le serveur.

- [ ] **Step 3: Commit**

```bash
git add clients/regles_api_client/src/views/CleApi.vue
git commit -m "feat(regles_api_client): assemble the real CleApi screen"
```

---

## Task 10: Tests d'acceptance (Gherkin documentation + jsonl exécutable)

**Files:**
- Create: `clients/regles_api_client/tests/acceptance/regles_api_client_acceptance.jsonl`
- Create: `clients/regles_api_client/tests/acceptance/acceptance.test.js`

**Interfaces:**
- Consumes: `useRegles` (Task 4), `useCleApi` (Task 3) — modules réels, seul `fetch` est simulé (cohérent avec la spec : « il n'y a pas de base de données côté client »).

Les scénarios Gherkin correspondants sont déjà écrits dans
`docs/superpowers/specs/2026-08-02-regles-api-client-design.md` (section
« Scénarios d'acceptance ») — ce ne sont pas des fichiers `.feature`
exécutés, seulement de la documentation. Le jsonl ci-dessous couvre les 4
scénarios de la fonctionnalité « Revue humaine des règles enrichies ».

- [ ] **Step 1: Créer le jsonl**

```json
{"scenario": "annotation reussie", "a_cle": true, "reponse_patch_statut": 200, "reponse_patch_corps": {"numero": 28, "intitule": "x", "theme": "Formulaires", "contexte": null, "solution": "s", "controle": "c", "strategie_analyse": "statique", "outils": ["statique"], "strategie_justification": null, "strategie_source": "llm", "guide_analyse": "g", "objectifs": [], "tags": [], "phases": [], "prompt_version": 1, "llm_model": "kimi", "review_status": "a_revoir", "review_note": "Note de test", "reviewed_at": "2026-08-02T10:00:00"}, "resultat_attendu": "succes"}
{"scenario": "tentative sans cle API enregistree", "a_cle": false, "resultat_attendu": "redirection_cle_api"}
{"scenario": "cle API revoquee par le serveur", "a_cle": true, "reponse_patch_statut": 401, "resultat_attendu": "redirection_cle_api"}
{"scenario": "erreur serveur pendant l'annotation", "a_cle": true, "reponse_patch_statut": 500, "resultat_attendu": "erreur"}
```

- [ ] **Step 2: Écrire le test (failing avant que le fichier jsonl ne soit lu correctement — vérifie surtout le câblage, pas une logique nouvelle)**

```js
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const ICI = dirname(fileURLToPath(import.meta.url))
const CAS = readFileSync(join(ICI, 'regles_api_client_acceptance.jsonl'), 'utf-8')
  .trim()
  .split('\n')
  .map((ligne) => JSON.parse(ligne))

describe('acceptance — boucle de revue (regles_api_client_acceptance.jsonl)', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.resetModules()
    vi.unstubAllGlobals()
  })

  it.each(CAS)('$scenario', async (cas) => {
    const { useCleApi } = await import('../../src/composables/useCleApi.js')
    const { useRegles } = await import('../../src/composables/useRegles.js')

    if (cas.a_cle) {
      useCleApi().setKey('cle-de-test')
    }

    vi.stubGlobal(
      'fetch',
      vi.fn(async (_url, options) => {
        if (options?.method === 'PATCH') {
          return {
            ok: cas.reponse_patch_statut === 200,
            status: cas.reponse_patch_statut,
            json: async () => cas.reponse_patch_corps ?? { detail: 'Erreur serveur' },
          }
        }
        return { ok: true, status: 200, json: async () => [] }
      })
    )

    const { annoter, dernierResultat, redirectionCleApi } = useRegles()
    await annoter(28, { reviewStatus: 'a_revoir', reviewNote: 'Note de test' })

    if (cas.resultat_attendu === 'redirection_cle_api') {
      expect(redirectionCleApi.value).toBe(true)
    } else {
      expect(dernierResultat.value).toBe(cas.resultat_attendu)
    }
  })
})
```

- [ ] **Step 3: Lancer les tests, vérifier qu'ils passent**

Run: `cd clients/regles_api_client && npm run test -- acceptance`
Expected: `PASS` — 4 cas verts (un par ligne du jsonl).

- [ ] **Step 4: Lancer toute la suite**

Run: `cd clients/regles_api_client && npm run test`
Expected: tous les tests (unitaires + acceptance) passent.

- [ ] **Step 5: Commit**

```bash
git add clients/regles_api_client/tests/acceptance/
git commit -m "test(regles_api_client): add acceptance suite backed by jsonl cases"
```

---

## Task 11: README, Makefile et CHANGELOG

**Files:**
- Modify: `clients/regles_api_client/README.md`
- Modify: `Makefile` (racine du projet)
- Modify: `CHANGELOG.md` (racine du projet)

- [ ] **Step 1: Finaliser `README.md`**

```markdown
# regles_api_client

Client Vue.js de revue humaine du référentiel Opquast enrichi (US0) :
consultation et annotation des règles classées par l'agent d'enrichissement,
gestion de la clé API nécessaire pour écrire une annotation.

Consomme `app/api_regles` en HTTP. Ne couvre que US0 — voir
`docs/superpowers/specs/2026-08-02-regles-api-client-design.md` pour le
détail et le périmètre.

## Installation

```
npm install
```

## Configuration

Copier `.env.example` vers `.env` et ajuster si besoin :

```
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

```
npm run test
```

Unitaires (composables, service HTTP, aucun rendu de composant) et
acceptance (`tests/acceptance/`, cas décrits en Gherkin dans la spec de
conception, exécutés via un jeu de données jsonl — pas de framework BDD).
```

- [ ] **Step 2: Ajouter les cibles au `Makefile`**

Ajouter `regles-api-client regles-api-client-install regles-api-client-test` à la ligne `.PHONY` en tête de fichier, puis insérer cette section après la cible `api-regles-acceptance` (avant `# Tests`) :

```make
# ============================================================
# Clients
# ============================================================

## Installe les dépendances npm du client de revue des règles
regles-api-client-install:
	cd clients/regles_api_client && npm install

## Démarre le serveur de développement du client de revue des règles
## (Vite, http://localhost:5173) — nécessite make api-regles démarré à part
regles-api-client:
	cd clients/regles_api_client && npm run dev

## Lance les tests (unitaires + acceptance) du client de revue des règles
regles-api-client-test:
	cd clients/regles_api_client && npm run test
```

- [ ] **Step 3: Vérifier les nouvelles cibles**

Run: `cd /media/david/projets1/QualiCheck && make regles-api-client-test`
Expected: la suite Vitest complète s'exécute et passe.

- [ ] **Step 4: Ajouter l'entrée CHANGELOG**

Ouvrir `CHANGELOG.md`, repérer le dernier en-tête `## YYYY-MM-DD — Claude Code (Part N)` et insérer une nouvelle entrée juste avant, avec `N+1` et la date réelle du jour de l'implémentation :

```markdown
## [date du jour] — Claude Code (Part [N+1])

- **`clients/regles_api_client/` : premier client réel de `app/api_regles`**,
  construit depuis la spec `docs/superpowers/specs/2026-08-02-regles-api-client-design.md`
  et le plan `docs/superpowers/plans/2026-08-02-regles-api-client-implementation.md` —
  Vite + Vue 3 + JavaScript, composables (`useRegles`, `useCleApi`) sans
  Pinia, CSS des maquettes US0 porté en Sass, `vue-router` (2 écrans),
  filtrage recherche/thème/phase appliqué côté client (non supporté par
  `GET /regles`)
- **Tests** : unitaires Vitest sur les composables et le service HTTP
  (aucun rendu de composant), acceptance par jsonl rejoué en Vitest
  classique (`tests/acceptance/regles_api_client_acceptance.jsonl`) — même
  convention que `tests/acceptance/api_regles_acceptance.jsonl`, les
  scénarios Gherkin de la spec restent de la documentation
- **`Makefile`** : cibles `regles-api-client`, `regles-api-client-install`,
  `regles-api-client-test`
```

- [ ] **Step 5: Commit**

```bash
git add clients/regles_api_client/README.md Makefile CHANGELOG.md
git commit -m "docs(regles_api_client): add README, Makefile targets and changelog entry"
```
