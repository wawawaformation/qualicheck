# Client léger de revue — design

> Date : 2026-07-28

## 1. Problème

L'annotation de revue humaine (`review_status`/`review_note`) sur les règles
enrichies est aujourd'hui possible via l'API (`PATCH /regles/{numero}`,
`app/api_regles/regles.py`), mais uniquement en HTTP brut (curl, Postman...).
Le besoin réel : faire relire et annoter le référentiel par le formateur et
par Élie Sloïm (fondateur Opquast) — deux tiers externes, chacun avec son
propre jeton (voir
`docs/jury/decisions/2026-07-28-cle-valeur-multi-clients-api-regles.md`) —
sans leur demander de manier curl.

Une maquette interactive existe déjà :
`conception/maquettes/ecran_revue_regles.html`. Elle a toute la logique UI
nécessaire (liste filtrable/recherchable, panneau de détail, formulaire
d'annotation avec validation de la note obligatoire, toast de confirmation)
mais fonctionne sur un tableau `REGLES` codé en dur — 18 règles illustratives,
pas d'appel réseau. Ce design décrit comment la transformer en client
fonctionnel branché sur la vraie API.

## 2. Principe directeur

**Client statique minimal, aucun toolchain nouveau.** Le projet est
entièrement Python ; ajouter Node/npm/un bundler pour un client de quelques
centaines de lignes JS serait disproportionné. Un seul fichier HTML
(HTML+CSS+JS inline, comme la maquette actuelle), servi par
`python3 -m http.server`.

**Usage local, pas de déploiement distant pour l'instant.** Le formateur et
Élie Sloïm ne sont pas le jury de certification (`certif_deroule.md`) — cet
outil ne fait pas partie du périmètre de certification. Le déploiement en
staging, s'il devient nécessaire, sera une itération ultérieure, faite à la
main.

**On répare la maquette, on ne la réécrit pas.** Toute la logique de rendu
(liste, détail, filtres, segmented control, validation de note, toast) reste
inchangée. Seuls les points de contact avec les données changent : la
source des règles (fetch au lieu du tableau en dur) et la persistance de
l'annotation (PATCH réseau au lieu d'une mutation en mémoire).

## 3. Décisions

| Point | Décision |
| --- | --- |
| Emplacement | Nouveau dossier `client_revue/` à la racine, `index.html` unique — repris de la maquette, pas dans `app/` (pas du code FastAPI) |
| Service | Cible Makefile `client-revue` → `python3 -m http.server 5173 --directory client_revue` |
| Port | 5173 — déjà whitelisté dans `cors.allowed_origins` (`app/api_regles/manifest.yml`), aucune modification de config nécessaire |
| URL de l'API | Constante en tête du script JS, `http://localhost:8880` — pas de variable d'environnement, usage local uniquement |
| Chargement des règles | `GET /regles` sans filtre, une fois au chargement de la page (lecture ouverte, pas d'auth) — remplace le tableau `REGLES` |
| Champ `outils` | Utiliser `regle.outils` (déjà fourni en liste par l'API) — supprimer `outilsDe()` qui le recalculait depuis `strategie_analyse` |
| Authentification | Champ "Jeton API" dans la topbar, toujours visible (pas d'écran de login séparé) — navigation/lecture possibles sans rien saisir |
| Persistance du jeton | `localStorage` — lu au chargement, écrit à chaque saisie |
| Écriture d'une annotation | `PATCH /regles/{numero}` avec `Authorization: Bearer <jeton>`, corps `{review_status, review_note}` — validation de note obligatoire déjà présente côté client (maquette), inchangée |
| Erreurs PATCH | Affichées dans la zone `field-error` déjà existante : 401 → jeton invalide/absent ; 404 → règle introuvable ; 422 → message renvoyé par l'API ; erreur réseau → API non démarrée |
| Après succès (200) | Règle mise à jour dans le tableau local, toast existant affiché — pas d'avance automatique vers la règle suivante |

## 4. Hors périmètre (YAGNI)

- Déploiement distant (staging) — confirmé non nécessaire, le jury ne s'en sert pas.
- Traçabilité « qui a annoté quoi » côté client — l'API résout déjà un nom de
  client (`require_bearer`) mais ne l'expose pas ; hors périmètre de cette
  brique (à instruire séparément si le besoin devient réel, comme déjà noté
  dans la décision d'auth du 2026-07-28).
- Pagination — 245 règles chargées en une fois, comme le fait déjà l'API
  (`lister_regles`, sans pagination).
- Navigation automatique vers la règle suivante après annotation.
- Build tool / framework JS (Vite, React...) — un fichier HTML statique suffit.
- Gestion multi-environnement (dev/staging/prod) de l'URL de l'API — une
  seule constante, usage local.

## 5. Validation

1. `make client-revue` sert `client_revue/index.html` sur `http://localhost:5173`.
2. Avec `make api-regles` démarré, la page charge les 245 règles réelles au
   chargement (plus de tableau `REGLES` en dur).
3. Filtrage/recherche/sélection : comportement inchangé par rapport à la
   maquette (mêmes tests visuels manuels).
4. Sans jeton saisi : la lecture/navigation fonctionne, le PATCH échoue avec
   le message 401 attendu dans `field-error`.
5. Avec un jeton valide (`FASTAPI_API_KEY` de dev) : le PATCH réussit, la
   règle annotée reste visible avec son nouveau statut après rechargement de
   la page (relit `GET /regles`, qui reflète l'écriture en base).
6. Rechargement de la page : le jeton saisi précédemment est toujours présent
   dans le champ (persistance `localStorage`).
