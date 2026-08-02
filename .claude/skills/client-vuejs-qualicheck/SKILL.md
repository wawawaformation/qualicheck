---
name: client-vuejs-qualicheck
description: Use when building or modifying a Vue.js client in QualiCheck's clients/ directory (regles_api_client, or future US1/US2 clients) — covers composable state sharing, Vue watch() pitfalls, CSS override strategy, toolchain version pinning, and headless-browser verification without Playwright
---

# Client Vue.js QualiCheck

Motifs concrets et pièges réellement rencontrés en construisant
`clients/regles_api_client/` (2026-08-02) — pas des conventions générales
(celles-là sont dans le skill global `clients_api`), mais des choses qui ont
coûté un aller-retour de correction sur CE projet et qui se reproduiront sur
les prochains clients (US1, US2).

## Composable à état partagé (pattern "singleton composable")

Pour un état vraiment global (clé API, message toast) : le `ref` vit **hors**
de la fonction exportée, pas dedans.

```js
// ❌ chaque appel de useCleApi() recrée un état indépendant — deux
// composants qui l'appellent séparément ne partagent rien
export function useCleApi() {
  const cle = ref(localStorage.getItem('cle'))
  return { cle }
}

// ✅ un seul état, partagé par tous les appelants
const cle = ref(localStorage.getItem('cle'))
export function useCleApi() {
  return { cle }
}
```

Le composant qui **affiche** un état partagé (ex. un toast) doit être monté
**une seule fois, à la racine** (`App.vue`, jamais dans le `<main>` d'un
écran particulier) — sinon sa largeur suit celle de cet écran et il ne
survit pas à une navigation (le composant se démonte).

## Piège Vue : `watch()` sur une valeur qui peut se répéter

`watch(ref, cb)` ne réagit qu'à un **changement** de valeur, pas à
l'événement métier lui-même. Si une action réussie répétée met la même ref
à la même valeur deux fois de suite (ex. deux annotations réussies mettent
`dernierResultat` à `'succes'` deux fois), le deuxième succès ne déclenche
rien.

**Fix : la fonction d'action renvoie explicitement son résultat**, l'appelant
réagit directement au retour, jamais à un watch sur un état qui peut se
répéter.

```js
// ❌ un deuxième succès de suite ne redéclenche rien
async function annoter(...) { dernierResultat.value = 'succes' }
watch(dernierResultat, (v) => { if (v === 'succes') afficherToast(...) })

// ✅ fiable à chaque appel
async function annoter(...) { dernierResultat.value = 'succes'; return 'succes' }
const resultat = await annoter(...)
if (resultat === 'succes') afficherToast(...)
```

## Redirection avec contexte à restaurer

Pattern pour "rediriger vers un écran prérequis (ex. saisie de clé API) puis
revenir exactement où on était" : le contexte (numéro de règle...) passe par
la **query string** (`?retour=X`), jamais par un état en mémoire qui serait
perdu au démontage du composant. Si un message doit survivre à cette
navigation, le déclencher via l'état global partagé (composable
singleton) plutôt que par un paramètre d'URL ad hoc — il survit
naturellement puisque le composant qui l'affiche ne se démonte jamais.

Vérifier une précondition bloquante (ex. clé API) dès l'**intention**
exprimée (choix d'un statut qui implique une écriture), pas seulement au
clic final — sinon une saisie déjà commencée (note de revue) se perd à la
redirection.

## `scrollBehavior` du routeur

```js
createRouter({
  scrollBehavior(to, from, savedPosition) {
    return savedPosition || { top: 0 }
  },
})
```

Sans ça, changer de page garde le défilement de la page précédente.
`savedPosition` n'existe que pour précédent/suivant navigateur — le
restaurer dans ce cas précis, sinon revenir en haut.

## Épingler les versions du toolchain pour Node ancien

Avant `npm install` sur un poste à Node figé (ex. 18.x), vérifier `npm view
<paquet>@<version> engines` — un paquet peut relever son plancher Node sur
un simple patch/minor **sans** bump de version majeure (`sass@^1.98.0` a
résolu vers `1.102.0`, qui exige Node ≥20.19 ; `1.98.0` figé en dur, sans
`^`, reste sur Node ≥14). Épingler en version **exacte** les paquets à
risque, pas seulement contraindre la plage semver avec `^`.

## CSS partagé vs. correction locale à un écran

Les composants CSS partagés (boutons, bandeaux, blocs de métadonnées...)
viennent souvent d'un contexte de démo isolé et étroit
(`--container-narrow`). Réutilisés dans un écran plus large, un `max-width`
ou l'absence de contrainte de largeur crée une zone morte invisible tant que
le conteneur reste étroit, visible dès qu'il s'élargit.

- **Bug local à un écran** (le composant garde son comportement par défaut
  ailleurs) → surcharger dans le Sass de l'écran, sélecteur
  `.ecran-xxx .composant { ... }`, jamais dans le fichier du composant
  partagé.
- **Bug universel** (le défaut du composant est faux quel que soit le
  contexte, ex. un élément de bloc qui s'étire sans le vouloir) → corriger
  directement le fichier du composant partagé.
- Avant de choisir entre `justify-content` et `width: fit-content` pour une
  "zone vide dans une boîte flex" : la boîte doit-elle s'ajuster à son
  contenu, ou occuper toute la largeur avec ses items répartis ? Les deux se
  ressemblent en capture d'écran mais ne sont pas interchangeables — demander
  si le doute persiste plutôt que choisir au hasard.
- `header`/`footer` en pleine largeur : ne jamais mettre `max-width` +
  `margin-inline: auto` directement sur l'élément qui porte le `background`.
  Séparer un conteneur externe pleine largeur (fond) d'un conteneur interne
  centré (`max-width` + `margin-inline: auto`, le contenu réel).
- Toujours la **même variable** CSS pour tout ce qui doit s'aligner
  visuellement — jamais une valeur recopiée en dur depuis la maquette
  statique d'origine (`max-width: 75rem` au lieu de
  `var(--container-wide)`, 73.125rem : écart invisible à l'œil, visible aux
  DevTools).

## Déploiement same-origin (Caddy) : l'ordre des directives n'est pas l'ordre du fichier

Pour servir le front (fichiers statiques) et l'API (reverse proxy) sur le
même domaine, **ne pas** empiler `reverse_proxy @matcher ...` puis
`try_files`/`file_server` à plat — Caddy réordonne les directives selon un
ordre fixe interne, pas l'ordre écrit dans le `Caddyfile`, et `try_files`
s'exécute **avant** `reverse_proxy` dans cet ordre. Résultat observé en réel
(cloclo, 2026-08-02) : une requête vers `/regles` était réécrite en interne
vers `/index.html` par `try_files` (aucun fichier `regles`) avant que le
matcher API n'ait vu le chemin d'origine — l'API ne recevait jamais la
requête.

**Fix : des blocs `handle`**, qui s'exécutent dans l'ordre écrit et
s'excluent mutuellement (switch/case) :

```caddyfile
@api path /regles* /health /docs* /redoc /openapi.json
handle @api {
    reverse_proxy api-regles:8880
}
handle {
    root * /srv/www/mondomaine
    try_files {path} /index.html
    file_server
}
```

## Vérification visuelle sans Playwright

Ce projet n'a pas d'outil de navigateur piloté. Toute vérification passe
par `chromium --headless --disable-gpu`.

- **`--dump-dom` ne prouve rien sur le rendu calculé.** Un attribut
  `disabled` présent dans le dump ne garantit pas que le style visuel est
  correct (bouton resté en couleur pleine faute de règle `:disabled`).
  Toujours confirmer par `--screenshot`.
- Contenu async (fetch) → `--virtual-time-budget=Xms`. Piège : les timers JS
  sont aussi accélérés — un toast avec auto-dismiss à 4000ms peut disparaître
  avant la capture si le budget est ≥ 4000ms. Choisir un budget juste
  suffisant pour le fetch.
- Composant caché dans un scroll imbriqué (`overflow-y:auto` indépendant du
  scroll de la page) → une capture classique ne montre rien au-delà de la
  zone visible. Écrire un fichier HTML isolé important le **vrai CSS
  compilé** (`dist/assets/index-XXXX.css`) et reproduire juste le fragment de
  markup à vérifier, avec un `outline` de debug temporaire pour comparer des
  largeurs sans ambiguïté.
- Nettoyer les fichiers de vérification dans `./tmp/` après usage (jamais
  `/tmp` système, jamais le scratchpad de session — règle du projet).

## Redimensionnement d'une colonne au glisser

`display: flex` (pas `grid`), largeur en `ref()` appliquée via `:style` sur
l'élément à redimensionner, poignée séparée (`role="separator"`,
`cursor: col-resize`) écoutant `mousedown` sur elle-même puis
`mousemove`/`mouseup` sur `window` (pas sur la poignée — sinon le
mouvement se perd si le curseur sort de la poignée pendant le glisser).
Ajouter le support clavier (flèches gauche/droite) sur la poignée pour
l'accessibilité.

## Tests

- Composables/services testés unitairement, **aucun test de rendu de
  composant** (`@vue/test-utils`) — la fidélité visuelle se vérifie à l'œil
  sur ce projet.
- Acceptance : jsonl + Vitest classique, **jamais de framework BDD
  exécutable** (Cucumber.js, `vitest-cucumber`) — cohérent avec
  `tests/acceptance/api_regles_acceptance.jsonl` côté API.

## Messages utilisateur (toasts/bandeaux)

Un seul mécanisme pour tout le projet, pas un par écran : composable
singleton (`useToast`) exposant `message`/`type`/`afficher()`/`effacer()`,
rendu une fois dans `App.vue`. `afficher()` fait aussi
`window.scrollTo({ top: 0 })` — le message est toujours en haut de page,
donc invisible si une action précédente a fait défiler ailleurs (ex. un
scroll automatique vers un bouton de validation).
