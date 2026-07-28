# Client léger de revue — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> (single agent, inline) to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformer la maquette statique `conception/maquettes/ecran_revue_regles.html`
en client fonctionnel branché sur l'API réelle (`app/api_regles`), pour que le
formateur et Élie Sloïm puissent annoter les règles sans manier curl.

**Architecture:** Un seul fichier HTML/CSS/JS (`client_revue/index.html`),
servi statiquement par `python3 -m http.server 5173`. Aucun build, aucune
dépendance JS. La logique de rendu de la maquette est conservée à l'identique ;
seuls les points de contact avec les données changent (fetch réseau au lieu
du tableau `REGLES` en dur, PATCH réel au lieu d'une mutation en mémoire).

**Tech Stack:** HTML/CSS/JS vanilla (aucune dépendance), `python3 -m http.server`,
API FastAPI existante (`app/api_regles`).

## Global Constraints

- Port du client : 5173 (déjà whitelisté dans `cors.allowed_origins` de
  `app/api_regles/manifest.yml`) — ne pas changer ce port.
- URL de l'API : constante en tête du script, `http://localhost:8880` — pas
  de variable d'environnement, usage local uniquement.
- Le jeton API est envoyé uniquement au moment du PATCH (`Authorization:
  Bearer <jeton>`) ; la lecture/navigation reste possible sans jeton saisi.
- Le jeton est persisté en `localStorage` (clé `jetonApiRevue`).
- Ne pas modifier `app/api_regles/` : ce plan ne touche que le nouveau
  dossier `client_revue/`, `Makefile` et `CHANGELOG.md`.
- Pas de test automatisé JS (aucun harnais de test JS dans ce projet 100%
  Python) : chaque tâche se vérifie manuellement dans un navigateur, avec un
  résultat attendu explicite — pas de TDD classique ici, cohérent avec le
  choix YAGNI acté dans la spec (§2 de
  `docs/superpowers/specs/2026-07-28-client-revue-design.md`).

---

### Task 1: Scaffolding — copier la maquette, servir en statique

**Files:**
- Create: `client_revue/index.html` (copie exacte de `conception/maquettes/ecran_revue_regles.html`, aucune modification de contenu à cette étape)
- Modify: `Makefile` (ajout à `.PHONY` et nouvelle cible `client-revue`)

**Interfaces:**
- Produces: cible `make client-revue`, qui sert `client_revue/index.html` sur `http://localhost:5173`.

- [ ] **Step 1: Copier la maquette telle quelle**

```bash
cp conception/maquettes/ecran_revue_regles.html client_revue/index.html
```

- [ ] **Step 2: Ajouter la cible Makefile**

Dans `Makefile`, ajouter `client-revue` à la liste `.PHONY` (ligne 1), puis
ajouter cette section (à la suite de la section « API données », avant la
section « Tests ») :

```makefile
# ============================================================
# Client de revue
# ============================================================

## Sert le client léger de revue humaine sur http://localhost:5173
client-revue:
	python3 -m http.server 5173 --directory client_revue
```

- [ ] **Step 3: Vérifier manuellement**

Lancer `make client-revue`, ouvrir `http://localhost:5173` dans un
navigateur.

Résultat attendu : la page s'affiche exactement comme la maquette d'origine
— 18 règles mockées, compteur "18 / 245 règles affichées", filtres et
recherche fonctionnels. C'est la maquette inchangée, servie différemment :
aucune régression attendue à ce stade.

- [ ] **Step 4: Commit**

```bash
git add client_revue/index.html Makefile
git commit -m "feat: scaffold client_revue static server from existing mockup"
```

---

### Task 2: Charger les vraies règles depuis l'API

**Files:**
- Modify: `client_revue/index.html`

**Interfaces:**
- Consumes: `GET /regles` de l'API (`app/api_regles/regles.py:99`), réponse
  `list[RegleRead]` — champs pertinents ici : `numero`, `intitule`, `theme`,
  `contexte`, `solution`, `controle`, `strategie_analyse`, `outils` (déjà une
  liste, fournie par l'API), `strategie_justification`, `guide_analyse`,
  `tags`, `phases`, `prompt_version`, `llm_model`, `review_status`,
  `review_note`, `reviewed_at`.
- Produces: variable JS globale `let REGLES = []`, peuplée après une requête
  réseau réussie, consommée par `renderList()`/`renderDetail()` (Task 3 et 4
  s'appuient dessus).

- [ ] **Step 1: Remplacer la constante par une variable mutable vide**

Remplacer la ligne (le tableau `const REGLES = [...]` codé en dur, environ
lignes 566-584 du fichier copié) par :

```js
const API_BASE_URL = "http://localhost:8880";
let REGLES = [];
```

- [ ] **Step 2: Ajouter le chargement réseau et l'appeler au démarrage**

Remplacer l'appel final `renderList();` (fin du script) par :

```js
async function chargerRegles() {
  const reponse = await fetch(`${API_BASE_URL}/regles`);
  if (!reponse.ok) {
    document.getElementById("list").innerHTML =
      '<div class="list-empty">Impossible de charger les règles depuis l\'API — vérifier qu\'elle tourne (make api-regles).</div>';
    return;
  }
  REGLES = await reponse.json();
  renderList();
}

chargerRegles();
```

- [ ] **Step 3: Utiliser le champ `outils` fourni par l'API au lieu de le recalculer**

Remplacer les deux appels `outilsDe(r.strategie_analyse)` (dans
`renderList()` et `renderDetail()`) par `r.outils`. Supprimer la fonction
`outilsDe()`, devenue inutilisée.

Vérifier avec :

```bash
grep -n "outilsDe" client_revue/index.html
```

Résultat attendu : aucune occurrence.

- [ ] **Step 4: Vérifier manuellement**

Démarrer l'API dans un terminal (`make api-regles`), puis dans un autre
`make client-revue`, ouvrir `http://localhost:5173`.

Résultat attendu : le compteur affiche "245 / 245 règles affichées" (au lieu
de 18), les 245 règles réelles apparaissent dans la liste, les filtres par
thème/phase/outil/statut de revue fonctionnent toujours, cliquer une règle
affiche son détail complet.

- [ ] **Step 5: Commit**

```bash
git add client_revue/index.html
git commit -m "feat: load real rules from GET /regles instead of mock data"
```

---

### Task 3: Champ jeton API dans la topbar, persistance localStorage

**Files:**
- Modify: `client_revue/index.html`

**Interfaces:**
- Produces: élément `#jeton-api` (input), dont la valeur est lue par Task 4
  au moment du PATCH.

- [ ] **Step 1: Ajouter le champ dans la topbar**

Dans le HTML, juste avant `<div class="licence">` (à l'intérieur de
`.topbar-head`), ajouter :

```html
<div class="jeton-wrap">
  <label for="jeton-api" style="display:block;font-size:11px;color:var(--ink-soft);margin-bottom:4px;">Jeton API (pour annoter)</label>
  <input type="password" id="jeton-api" placeholder="Coller votre jeton…" style="width:220px;padding:6px 10px;border:1px solid var(--line-strong);border-radius:var(--radius);background:var(--paper-raised);color:var(--ink);font-size:12.5px;" />
</div>
```

- [ ] **Step 2: Charger/sauvegarder la valeur en localStorage**

Ajouter, juste avant `chargerRegles();` en fin de script :

```js
const CLE_JETON = "jetonApiRevue";
const champJeton = document.getElementById("jeton-api");
champJeton.value = localStorage.getItem(CLE_JETON) || "";
champJeton.addEventListener("input", () => {
  localStorage.setItem(CLE_JETON, champJeton.value);
});
```

- [ ] **Step 3: Vérifier manuellement**

Recharger `http://localhost:5173`, saisir une valeur quelconque dans le
champ, recharger la page.

Résultat attendu : la valeur saisie est toujours présente après rechargement.
Dans les devtools du navigateur (Application → Local Storage), la clé
`jetonApiRevue` contient la valeur saisie.

- [ ] **Step 4: Commit**

```bash
git add client_revue/index.html
git commit -m "feat: add API token field with localStorage persistence"
```

---

### Task 4: Brancher l'enregistrement d'une annotation sur le vrai PATCH

**Files:**
- Modify: `client_revue/index.html`

**Interfaces:**
- Consumes: `PATCH /regles/{numero}` (`app/api_regles/regles.py:157`), corps
  attendu `{review_status: "valide"|"a_revoir"|"invalide"|null, review_note:
  string|null}` (`app/api_regles/schemas.py:124` `ReglePatch`), réponse
  `RegleRead` en cas de succès (200), `{detail: string}` en cas d'erreur
  (401/404/422).
- Consumes: `champJeton` (Task 3), `REGLES` (Task 2).

- [ ] **Step 1: Ajouter une zone d'erreur réseau générique**

Le `field-error` existant (`#note-error`) ne gère que l'erreur de validation
"note obligatoire". Ajouter, juste après lui dans `renderDetail()` (dans le
template du bloc `.annotation`, après `<div class="field-error" id="note-error">...</div>`) :

```html
<div class="field-error" id="patch-error"></div>
```

- [ ] **Step 2: Remplacer la mutation en mémoire par un appel réseau**

Dans le gestionnaire de clic de `#btn-save` (dans `renderDetail()`),
remplacer le bloc qui suit la validation de la note (à partir de
`errorEl.classList.remove("is-visible");` jusqu'à `showToast(...)`) par :

```js
    errorEl.classList.remove("is-visible");
    const erreurPatch = detail.querySelector("#patch-error");
    erreurPatch.classList.remove("is-visible");

    const corps = {
      review_status: chosen === "aucun" ? null : chosen,
      review_note: chosen === "aucun" ? null : (note || null),
    };

    let reponse;
    try {
      reponse = await fetch(`${API_BASE_URL}/regles/${r.numero}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${champJeton.value}`,
        },
        body: JSON.stringify(corps),
      });
    } catch {
      erreurPatch.textContent = "Impossible de contacter l'API — vérifier qu'elle tourne (make api-regles).";
      erreurPatch.classList.add("is-visible");
      return;
    }

    if (!reponse.ok) {
      const messages = {
        401: "Jeton invalide ou absent.",
        404: "Règle introuvable (a-t-elle été supprimée ?).",
      };
      if (messages[reponse.status]) {
        erreurPatch.textContent = messages[reponse.status];
      } else {
        const corpsErreur = await reponse.json().catch(() => ({}));
        erreurPatch.textContent = corpsErreur.detail || `Erreur ${reponse.status}.`;
      }
      erreurPatch.classList.add("is-visible");
      return;
    }

    const miseAJour = await reponse.json();
    const index = REGLES.findIndex(regle => regle.numero === miseAJour.numero);
    REGLES[index] = miseAJour;
    renderList();
    renderDetail(miseAJour);
    showToast(chosen === "aucun" ? "Annotation effacée." : "Annotation enregistrée.");
```

Le gestionnaire de clic doit devenir une fonction `async` (ajouter `async`
devant `() => {` dans `detail.querySelector("#btn-save").addEventListener("click", async () => { ... })`).

- [ ] **Step 3: Vérifier manuellement — sans jeton (401)**

Vider le champ jeton (le laisser vide), sélectionner une règle, choisir un
statut, cliquer "Enregistrer l'annotation".

Résultat attendu : message "Jeton invalide ou absent." affiché dans la zone
d'erreur sous le champ note, l'annotation n'est pas modifiée dans la liste.

- [ ] **Step 4: Vérifier manuellement — avec un jeton valide (succès)**

Récupérer la valeur de `FASTAPI_API_KEY` dans `.env`, la coller dans le
champ jeton. Sélectionner une règle, choisir un statut différent de
« Non revue » et une note, cliquer "Enregistrer l'annotation".

Résultat attendu : toast "Annotation enregistrée.", le statut change dans la
liste et dans le panneau de détail, l'horodatage "Dernière revue" se met à
jour. Recharger la page entière (`F5`) : la règle annotée apparaît toujours
avec son nouveau statut (preuve que l'écriture a bien atteint la base, pas
seulement l'état JS en mémoire).

- [ ] **Step 5: Commit**

```bash
git add client_revue/index.html
git commit -m "feat: wire annotation form to real PATCH /regles/{numero}"
```

---

### Task 5: Traçabilité — CHANGELOG

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Ajouter l'entrée**

Ajouter en tête de `CHANGELOG.md`, dans le même format que les entrées
existantes (date + auteur + liste à puces avec références de fichiers) :

```markdown
## 2026-07-28 — Claude Code

- **Client léger de revue humaine** — voir `client_revue/index.html`, `Makefile` (cible `client-revue`)
  - Reprend la maquette `conception/maquettes/ecran_revue_regles.html`, branchée sur l'API réelle (`GET /regles`, `PATCH /regles/{numero}`)
  - Champ jeton API dans la topbar, persistance `localStorage`, envoyé en `Authorization: Bearer` uniquement au PATCH
  - Usage local uniquement (`http://localhost:5173`), pas de déploiement distant — destiné au formateur et à Élie Sloïm pour la revue humaine
  - Spec : `docs/superpowers/specs/2026-07-28-client-revue-design.md`
```

- [ ] **Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: log client_revue in CHANGELOG"
```
