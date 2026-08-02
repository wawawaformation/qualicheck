# Changelog

Historique des réalisations sur QualiCheck. Mis à jour par tout outil agentique utilisé (Claude Code, OpenCode...) — voir `CLAUDE.md` pour la règle d'usage.

Format d'entrée, une ligne par réalisation :

```text
## [date] — [outil]
- [Ce qui a été fait] — voir [fichier(s) concerné(s)]
```

## 2026-08-02 — Claude Code (Part 22)

- **Retour automatique à la règle après renseignement de la clé API**
  (`regles_api_client`) : la redirection vers `/cle-api` porte désormais
  `?retour=<numero>` (numéro de la règle qu'on tentait d'annoter),
  `CleApi.vue` la relit et renvoie vers `/revue?regle=<numero>` une fois la
  clé enregistrée, `RevueRegles.vue` restaure la sélection au montage.
  Vérifié : `/revue?regle=28` sélectionne réellement la règle 28
  (`aria-current`, panneau de détail correspondant)

## 2026-08-02 — Claude Code (Part 21)

- **Politique des données : mention de Langfuse ajoutée** (section
  « Évolution prévue ») — décision déjà actée (`TODO.md`) que Langfuse
  monitorera les appels LLM d'US1/US2, mais pas d'ingestion ni d'US0.
  Question de l'anonymisation des données tracées explicitement non
  tranchée, signalée comme telle plutôt que supposée

## 2026-08-02 — Claude Code (Part 20)

- **Politique des données corrigée** (`clients/contenus_partages/politique-des-donnees.md`
  et `PolitiqueDonnees.vue`) : le constat « aucune création de compte » est
  scopé explicitement à US0 (seule fonctionnalité disponible). Ajout d'une
  section « Évolution prévue » : US1 (audit) et US2 (question libre)
  nécessiteront un compte utilisateur et une gestion dédiée des données
  personnelles — précision du porteur du projet, pas encore conçue en détail

## 2026-08-02 — Claude Code (Part 19)

- **Pages de pied de page implémentées dans `regles_api_client`** : les 3
  liens `href="#"` ("Le projet", "Mentions légales", "Politique des
  données") deviennent 3 routes réelles (`LeProjet.vue`,
  `MentionsLegales.vue`, `PolitiqueDonnees.vue`), contenu repris de
  `clients/contenus_partages/*.md`. Nouveau partial Sass `_page-contenu.scss`
  (conteneur étroit, titres, paragraphes — réutilise les tokens existants,
  aucun style de lien dédié nécessaire, `a { color: var(--color-accent) }`
  s'applique déjà globalement). Vérifié par rendu réel (Chromium headless) :
  les 3 titres s'affichent, style cohérent avec le reste du client

## 2026-08-02 — Claude Code (Part 18)

- **`regles_api_client` : config par `.env` remplacée par `src/apiServer.js`**
  — décision explicite du porteur du projet, après la Part 17. Plus de
  `.env`/`.env.example`/`.env.test`/`src/config.js` : `apiServer.js` exporte
  une unique constante `API_REGLES_URL`, modifiée à la main selon
  l'environnement (dev local, URL de préprod avant un build de
  déploiement) — pas de bascule automatique par mode Vite
- **Bug corrigé en même temps** : `reglesApiService.js` construisait
  `${API_REGLES_URL}/regles` sans neutraliser un éventuel `/` final, ce qui
  produisait une URL à double slash. Ajout d'un `.replace(/\/+$/, '')`
- **Tests corrigés** : `reglesApiService.test.js` codait en dur
  `http://localhost:8880`, cassé dès qu'`apiServer.js` contient une autre
  valeur (ex. l'URL de préprod). Les tests lisent maintenant
  `API_REGLES_URL` au lieu de deviner sa valeur
- **Spec et plan amendés** (pas réécrits) : note d'amendement datée dans
  chacun des deux documents, pointant vers ce changement, sans effacer le
  compte-rendu de ce qui a été exécuté à l'origine

## 2026-08-02 — Claude Code (Part 17)

- **`clients/regles_api_client/` implémenté** (11 tâches TDD du plan
  `docs/superpowers/plans/2026-08-02-regles-api-client-implementation.md`) :
  premier client réel de `app/api_regles`, Vite + Vue 3 + JavaScript,
  composables `useRegles`/`useCleApi` (pas de Pinia), CSS des maquettes US0
  porté en Sass, `vue-router` (`/revue`, `/cle-api`), filtrage
  recherche/thème/phase appliqué côté client (non supporté par
  `GET /regles`). Vérifié manuellement contre l'API réelle (245/245 règles
  chargées, rendu conforme aux maquettes)
- **Tests** : 22 tests Vitest verts (`reglesApiService`, `useCleApi`,
  `useRegles`, acceptance par jsonl `tests/acceptance/regles_api_client_acceptance.jsonl`)
- **2 bugs trouvés et corrigés pendant l'implémentation** :
  - `sass: "^1.98.0"` résolvait vers `1.102.0`, qui exige Node ≥20.19 alors
    que ce poste tourne sous Node 18.19.1 — sass avait relevé son plancher
    Node sans bump de version majeure. Épinglé en version exacte (`1.98.0`),
    corrigé aussi dans le plan
  - Bouton "Modifier la clé" (écran clé API) : première version effaçait la
    clé directement au lieu de rouvrir le formulaire de saisie — corrigé
    avant tout test manuel, via un état local `enModification` distinct de
    `hasKey`
- **`Makefile`** : cibles `regles-api-client`, `regles-api-client-install`,
  `regles-api-client-test`

## 2026-08-02 — Claude Code (Part 16)

- **Nouveau skill `clients_api`** (hors dépôt QualiCheck, `~/.claude/skills/`) :
  conventions générales pour tout futur client API (Vue.js par défaut,
  maquettes comme référence, services HTTP centralisés, composants
  réutilisables). Complété en cours de session : **CSS en Sass** et
  **README obligatoire par client**
- **Spec de conception `regles_api_client`**
  (`docs/superpowers/specs/2026-08-02-regles-api-client-design.md`) :
  premier client Vue.js réel de `app/api_regles`, périmètre US0 uniquement
  (revue des règles + gestion de la clé API). Décisions actées : Vite +
  Vue 3 + JavaScript (pas TypeScript), composables (`useRegles`,
  `useCleApi`) sans Pinia, clé API en `localStorage`, `vue-router` (2
  écrans), CSS en Sass en conservant les custom properties des maquettes,
  tests Vitest sur la logique uniquement (pas de rendu de composant),
  scénarios d'acceptance en Gherkin (documentation) + jsonl exécutable —
  même convention que `api_regles` et le RAG (aucun outillage BDD
  installé dans le projet)
- **Plan d'implémentation `regles_api_client`**
  (`docs/superpowers/plans/2026-08-02-regles-api-client-implementation.md`) :
  11 tâches TDD. Versions du toolchain verrouillées pour compatibilité
  Node 18.19.1 (Vite 6.4, Vitest 3.2, sass 1.98, jsdom 26, vue-router 4.6 —
  les dernières majeures exigent Node 20+). Écart découvert en rédigeant
  le plan : `GET /regles` ne supporte que les filtres `outil` et
  `review_status` côté serveur, donc la recherche texte, le filtre thème
  et le filtre phase de la maquette sont appliqués côté client sur les 245
  règles déjà chargées (pas de pagination serveur)
- **Implémentation mise en pause** à la demande explicite, avant la Task 1
  du plan — spec et plan restent la référence pour la reprendre
- **Pages de contenu partagées** (`clients/contenus_partages/le-projet.md`,
  `mentions-legales.md`, `politique-des-donnees.md`) : les liens
  "Le projet"/"Mentions légales"/"Politique des données" du pied de page
  étaient des `href="#"` sur tous les écrans maquettés. Vérifié hors
  périmètre des compétences certifiées
  (`conception/referentiel_competences.md`, `conception/certif_deroule.md`)
  mais nécessaires car `regles_api_client` sera réellement partagé (pas
  seulement démontré au jury). Contenu en Markdown (pas de maquette HTML
  dédiée), destiné à être rendu par les futurs clients Vue.js. Adresse
  postale de l'éditeur volontairement remplacée par une formule "sur
  demande" dans `mentions-legales.md` — éviter une exposition permanente
  dans l'historique Git d'un dépôt public. Page "Contact" (US1/US2)
  différée, pas encore d'écran ni de besoin identifié à ce stade

## 2026-08-02 — Claude Code (Part 15)

- **US0 (revue du référentiel) : 3 nouveaux écrans/états, brainstormés puis
  maquettés** (aucune spec écrite en amont — validations successives par
  questions ciblées, cohérent avec le mode de travail léger déjà en place
  pour le maquettage) :
  - `ecran-revue-regles-etats.html` : liste vide après filtrage (0/245),
    confirmation d'enregistrement (`bandeau-message--succes`), échec
    d'enregistrement (`bandeau-message--erreur`) — panneau détail isolé
    sans redupliquer la liste pour les 2 derniers états. `bandeau-message.css`
    copié dans `US0/style/` (jusqu'ici seulement dans `US2/style/`)
  - `ecran-cle-api.html` : 2 états (aucune clé / clé enregistrée), champ
    unique — le jeton suffit à l'identification côté serveur
    (`app/api_regles/auth.py`), pas de champ nom d'utilisateur
- **Nav de l'entête (US0)** : les 3 liens habituels (Mes audits/Question
  libre/Règles Opquast) remplacés par la gestion de la clé API
  ("Renseigner ma clé API" / "Modifier ma clé API" + "Supprimer ma clé
  API" selon l'état) sur les 3 écrans US0 — l'écran de revue n'a jamais eu
  de lien de menu qui lui corresponde réellement (aucun des 3 ne mène à cet
  écran), la clé API a rempli ce vide
- **`aria-current="page"` retiré du lien "Règles Opquast"** sur les écrans
  US0 : ce lien mène au référentiel officiel externe (opquast.com), pas à
  l'écran de revue interne — le marquer actif était trompeur
- **Icône avatar (`entete__avatar`) retirée des 3 écrans US0** — pas de
  notion de compte utilisateur sur ces écrans d'administration
- **Pied de page (US0)** : liens "Accueil"/"Préparer un audit" (destinés à
  l'utilisateur final) retirés de `pied-de-page__nav` sur les 3 écrans —
  hors contexte pour une zone d'administration
- **2 bugs CSS trouvés et corrigés en construisant `ecran-cle-api.html`**,
  répercutés dans les 3 copies du design system
  (`directives/composants/CSS/`, `US0/style/`, `US2/style/`) :
  - `.bouton--neutre` sans `background: transparent` → fond gris par
    défaut du navigateur, texte illisible ("Supprimer la clé")
  - Écart entre les 2 rangées du pied de page trop important (4rem cumulés
    entre `__haut` et `__bas`) — resserré à 1rem cumulé
    (`padding-bottom`/`padding-top` explicites au lieu de `padding-block`
    symétrique, pour ne pas toucher l'espacement extérieur)
- **Nouvelle règle actée dans `conception/maquettes/CLAUDE.md`** : aucun
  JavaScript dans les maquettes — tout comportement interactif repéré
  pendant le maquettage (redimensionnement, redirection selon état...) est
  documenté comme exigence pour l'implémentation Vue.js réelle, pas simulé
  ici. Exigences notées sous US0 : colonne de liste redimensionnable,
  gestion de la clé API (stockage client — localStorage/sessionStorage —
  non tranché, à décider lors de l'implémentation)

## 2026-08-02 — Claude Code (Part 14)

- **Solde de crédit remis dans les 2 écrans US2** (`ecran-question-libre.html`,
  `ecran-question-libre-garde-fous.html`) — retiré un peu vite lors d'une
  itération précédente ; ré-affiché via `.indicateur-credit` existant ("8
  questions restantes" / variant `--faible` "0 question restante" sur
  l'écran garde-fous)
- **Barre de saisie (`zone-saisie-question`) rendue réellement opaque** —
  son fond utilisait `--color-surface` (#070707), quasi indiscernable de
  `--color-background` (#0b0b0e), ce qui la faisait paraître transparente.
  Nouveau token `--color-surface-opaque` (#000000, noir plein garanti)
  ajouté dans `variables.css`, utilisé par la barre de saisie plutôt qu'une
  valeur hex brute
- Les deux copies (`composants/CSS/` et `US2/style/`) mises à jour en
  parallèle, comme convenu depuis la scission des dossiers

## 2026-08-02 — Claude Code (Part 13)

- **US2 (question libre) : diagrammes UML** — `conception/5_us2_question_libre/cas_utilisation_us2.drawio`
  (cas d'utilisation : vérification authentification/crédit en `«include»`,
  soumission de page en `«extend»`, vider la session en acteur direct) et
  `diagramme_activite_us2.drawio` (2 couloirs Utilisateur/Système, boucle de
  re-vérification du crédit à chaque nouvelle question, bandeau d'erreur
  après 3 échecs techniques du RAG/agent, "Terminer la session" redirige
  explicitement vers "Mes audits" après une étape optionnelle de sauvegarde)
- **Écran assemblé US2** — `conception/maquettes/US2/ecran-question-libre.html` :
  5 composants (zone-soumission-page en modale CSS pure, zone-saisie-question
  en pilule avec bouton "+" intégré, carte-regle-citee, fil-dialogue)
  assemblés selon les conventions ChatGPT/Claude web (messages agent sans
  bulle + avatar, bulle discrète pour l'utilisateur), historique borné
  (`max-height` + défilement interne, jamais de contenu sous la barre de
  saisie), horodatage et pouce haut/bas par réponse, exemple à 2 règles
  citées dans une même réponse
- **Écran garde-fous** — `conception/maquettes/US2/ecran-question-libre-garde-fous.html` :
  copie illustrant crédit épuisé / échec technique (nouveau variant
  `bandeau-message--avertissement`), question hors sujet, gros mots, idées
  suicidaires (réponse redirigeant vers le 3114/15/112, volontairement sans
  pouce ni règle citée)
- **Réorganisation des dossiers de maquette** — les écrans assemblés déménagés
  de `composants/` (réservé aux briques réutilisables) vers
  `conception/maquettes/US2/`, avec son propre `style/` autonome (copie des
  CSS et polices nécessaires, découplée de `composants/CSS/`)
- **`--container-wide` élargi à 1170px** (`variables.css`, dupliqué dans
  `US2/style/variables.css`) pour l'en-tête et le pied-de-page
- **Pied de page aligné sur `accueil_a_revoir.png`** — séparateurs verticaux
  (logo/tagline ↔ nav, copyright ↔ mention légale), icônes de nav en violet
  accent, lien "Politique des données" ajouté
- **RGPD** — section "Traitements anticipés, non actifs — US2" ajoutée à
  `docs/rgpd/registre_traitements.md` (même logique que le volet audit US1 :
  rien de réel à traiter tant qu'US2 n'a pas de spec), suivi dans `TODO.md`
- **Audit UX** (nouveau skill `ui-ux-pro-max`) sur les 2 écrans US2 : cibles
  tactiles sous 44px, absence de media queries, focus clavier peu visible
  sur la modale CSS-only, transitions `:hover` manquantes — acceptés en
  l'état, périmètre maquettage desktop-first, aucun correctif appliqué

## 2026-07-31 — Claude Code (Part 12)

- **9 nouveaux composants de maquette** pour l'écran de revue du référentiel,
  construits en confrontant `ecran_revue_regles_a_nettement _ameliorer.html`
  (ancienne référence, hors design system) au design system actuel :
  `badge-statut` (3 états, `invalide` exclu), `chip-filtre`, `barre-filtres`,
  `tag-outil`, `ligne-regle`, `segmented-statut`, `bloc-provenance`,
  `panneau-detail-regle`, `bandeau-message`. Egalement `formulaire.html`
  (types de champ) complété d'une bande de succès en tete et d'un lien vers
  les CGU
- **Corrections d'accessibilité concrètes** (priorité Opquast) :
  - `--color-accent-bouton` ajouté à `variables.css` : le texte blanc sur
    bouton plein n'atteignait que 3.36:1 (sous le seuil AA 4.5:1) avec
    `--color-accent` seul
  - `champ-texte__aide` (messages d'erreur/succès) utilisait
    `--color-danger-text`/`--color-success-text` — pensés pour du texte sur
    fond colore (badge), pas sur le fond de page sombre (1.68:1/2.33:1,
    illisibles). Corrigé en `--color-danger-background`/`--color-success-background`
    (7.64:1/10.63:1)
  - Focus clavier visible généralisé dans `base.css` (`summary` inclus),
    `.visually-hidden` ajouté pour les `<legend>`/`<label>` masqués sans
    perdre la sémantique
  - Bug de rendu découvert : un `<legend>` se place toujours sur sa propre
    ligne dans un fieldset flex sous Chromium 150, jamais traité comme un
    item flex — contourné par un `<span>` visuel a cote du `<legend>`
    masqué (accessibilité conservée)
- **`barre-filtres`** : recherche pleine largeur, panneau de filtres
  repliable (`<details>`, ferme par defaut), groupe Theme (14 valeurs) en 2
  lignes de 8/6 plutôt qu'un défilement (loi de Miller), tous les groupes
  alignés sur la même structure titre/chips, sélection en vert
- **`entete`** : lien "Question libre" (US2) ajouté, bascule thème
  clair/sombre retirée (hors périmètre pour l'instant), état de page active
  illustré (`aria-current`)
- **`bouton`** : effet de survol en négatif (fond/texte inversés) sur le
  bouton plein, bordure épaissie à 2px
- **`formulaire`** : bouton d'envoi grisé (CSS `:has()`, sans JS) tant que
  la case CGU n'est pas cochée

## 2026-07-31 — Claude Code (Part 11)

- **Vocabulaire `review_status` simplifié : retrait de `invalide`** — décelé
  en confrontant les maquettes (`conception/maquettes/`) à l'API réelle
  (`https://regles.qualicheck.koabana.fr/regles`) : `invalide` (classification
  franchement fausse) était visuellement et fonctionnellement indiscernable
  de `a_revoir` (à corriger), les deux finissant dans la même file de
  réécriture ciblée. Vocabulaire réduit à `valide`/`a_revoir`, sans perte de
  comportement — `enrich_again` sélectionne déjà par exclusion
  (`review_status IS NOT NULL AND != 'valide'`), pas par énumération.
  Répercuté sur `app/api_regles/schemas.py` (énums `ReviewStatus` et
  `ReviewStatusFiltre`, message de validation), `app/ingestion/enrich_again.py`
  (docstring), `Makefile` (commentaire de la cible `enrich-again`),
  `conception/4_api_regles/api_regles.md`, `conception/1_BDD/MLD_qualicheck.md`,
  `conception/3_enrichissement/G_revue_manuelle.md` (§3, §4.1, §5 + addendum
  §6 documentant la décision) et `conception/3_enrichissement/J_chantier_enrich_again.md`.
  Deux tests devenus obsolètes supprimés (`test_note_obligatoire_pour_invalide`,
  `test_load_rules_to_review_includes_invalide_status`), trois docstrings de
  test mis à jour. 134/134 tests unitaires + intégration passent, `ruff check`
  propre. Non touché volontairement : `ecran_revue_regles_a_nettement _ameliorer.html`,
  déjà marqué "à reprendre entièrement" dans `conception/maquettes/CLAUDE.md`
  — corriger son vocabulaire aurait été un effort perdu avant sa refonte
- **Ajout du lien de nav "Question libre" (US2)** dans le composant `entete`
  (`conception/maquettes/directives/composants/entete.html`) — la maquette
  n'exposait que "Mes audits", oubliant l'US2 (question libre, RAG sémantique)
- **Principe de page active illustré dans `entete`** — `aria-current="page"`
  sur le lien courant + style associé (`CSS/entete.css`), démontré sur
  "Mes audits"
- **4 nouveaux composants de maquette** construits depuis
  `Etape2 Sélection des pages.pdf` : `stepper`, `ligne-page`,
  `panneau-selection`, `navigation-etapes` — mêmes conventions que la session
  précédente (CSS externalisé, assets locaux, `:hover`). `bouton.css` complété
  de deux modificateurs (`--petit`, `--neutre`)
- **`composants/formulaire.html` créé** : formulaire imaginé illustrant les
  types de champ courants (texte, email avec erreur, mot de passe avec
  succès, select, textarea, radio, interrupteur, case à cocher) sur la base
  du design system existant. Mentions "(obligatoire)"/"(optionnel)" en toutes
  lettres partout (plus d'astérisque)
- **Restructuration `composants/`** : tous les CSS (dont `variables.css`)
  regroupés dans `composants/CSS/`, Bootstrap Icons et la police Inter
  rapatriés en fichiers locaux (plus de dépendance CDN)

- **Montage « Livret 0 » abandonné, fusionné dans E1** — réponse reçue de la
  référente certification (Helena) : 5 livrables au total, pas 6 ; si le
  même projet sert aux 5, le contexte se présente une seule fois, en tête
  du premier livrable. `docs/jury/documents_jury/commun/` supprimé
  (`explication_projet.md`, `Livret0.pdf`). Le contexte (condensé :
  présentation du projet + tableau des 3 US, sans l'annexe personas, pour
  préserver le budget de pages) ouvre désormais `epreuvres/E1/E1.md`
  directement (§ « Présentation du projet »), avec une phrase indiquant que
  les livrets suivants n'y reviendront pas. `docs/jury/documents_jury/README.md`
  et `TODO.md` mis à jour en conséquence. E1 passe de 3 à 4 pages, toujours
  dans le budget 2-5 p.

## 2026-07-29 — Claude Code (Part 9)

- **Tirets cadratins retirés du Livret 0 et du livret E1** (demande
  explicite : style de prose ne doit pas "sonner IA"). Titres et sous-titres
  reformulés avec des deux-points ou des virgules ; phrases restructurées
  plutôt que ponctuées d'incises systématiques. Pied de page et couverture
  du template (`working/config/jury-livret.tex`) corrigés de la même façon
- **Devise « Garbage in, garbage out » déplacée : uniquement sur E1**, pas
  sur les 6 livrets. Mécanisme `\devise` rendu optionnel (vide par défaut) ;
  bug découvert au passage : le YAML `header-includes:` d'un `.md` ne se
  combine pas de façon fiable avec `--include-in-header` sur Pandoc 3.1.3
  (la valeur du document disparaissait silencieusement). Contournement :
  un second fichier `--include-in-header` propre à E1
  (`epreuvres/E1/devise.tex`), les fichiers `-H` multiples se concaténant
  correctement entre eux. Documenté dans `docs/jury/documents_jury/README.md`

## 2026-07-29 — Claude Code (Part 8)

- **Livret E1 rédigé** (`docs/jury/documents_jury/epreuvres/E1/E1.md`) : C1 à
  C5, introduction (renvoi Livret 0, mention LLM + revue humaine, note sur
  l'enrichissement du périmètre à US1/US2), synthèse des critères de
  performance (tableau + renvoi `docs/jury/E1_bloc1_criteres_performance.xlsx`).
  3 pages, dans le budget 2-5 p. d'E1 (`conception/certif_deroule.md`)
- **Débordement du code inline corrigé** (`working/config/jury-livret.tex`) :
  les chemins longs (`docs/jury/decisions/...`) sortaient de la marge —
  `seqsplit` + `\ttfamily` sur `\texttt` autorise la coupure en fin de ligne.
  Même bug probable dans `~/.config/pandoc/styles/conception.tex`/`formation.tex`
  (non corrigé, hors périmètre de cette session)
- **Devise « Garbage in, garbage out » ajoutée en page de garde** (les 6
  livrets, template commun)

## 2026-07-29 — Claude Code (Part 7)

- **Branche par défaut GitHub changée `main` → `dev`** (`gh repo edit
  --default-branch dev`) : `main` avait ~288 commits de retard sur `dev`
  (rien n'est déployé en production, cf. `README.md` §Branches) — quiconque
  ouvrait le dépôt sans préciser de branche (jury de certification compris)
  atterrissait sur un squelette figé au setup Docker/BDD initial, sans rien
  du pipeline d'ingestion ni d'`api_regles`. `README.md` mis à jour en
  conséquence. Aucun workflow CI ne dépend du réglage de branche par défaut
  (vérifié)

## 2026-07-29 — Claude Code (Part 6)

- **`conception/annexes/J_personas_qualicheck.png` exporté** (CLI `drawio
  --export`, à la demande explicite de David — schéma déjà relu) — ajouté en
  Annexe A du Livret 0 (`docs/jury/documents_jury/commun/explication_projet.md`),
  référencé depuis le texte (« Détail complet des deux profils : Annexe A »)
- **Contenu du Livret 0 relu et corrigé** : Opquast est une entreprise, pas
  une organisation
- **Piège Pandoc documenté** (`docs/jury/documents_jury/README.md`) : les
  chemins d'image dans ces livrets sont relatifs à la racine du dépôt
  (répertoire de lancement de `pandoc`), pas au dossier du fichier `.md`

## 2026-07-29 — Claude Code (Part 5)

- **Structure `docs/jury/documents_jury/` amorcée** — livrets à remettre au
  jury (Livret 0 + E1 à E5), distincte du reste de `docs/jury/` qui pointe
  vers les preuves sans les recopier (`README.md` dédié)
  - `working/config/jury-livret.tex` : template Pandoc/XeLaTeX (identité
    visuelle de `~/.config/pandoc/styles/conception.tex`), page de garde
    unique — `\maketitle` redéfini, construite depuis le Front Matter
  - `commun/explication_projet.md` = **Livret 0** : présentation du projet
    (~2 pages), document **autonome**, remis une seule fois — pas concaténé
    dans les 5 livrets d'épreuve. Décision alignée sur
    `conception/certif_deroule.md` (*« 5 livrables... le contexte n'est
    présenté qu'une fois »*) et sur le budget de pages serré d'E1/E5 (2 à 5 p.)
  - `epreuvres/E{1..5}/` : un dossier par épreuve, s'y référence en une
    phrase plutôt que de le recopier
  - Build validé par compilation réelle (`./tmp/jury_livret_test/`) :
    Livret 0 seul (2 pages, cover + contenu) et un livret d'épreuve seul
    (cover + sommaire + corps) — commandes documentées dans
    `docs/jury/documents_jury/README.md`
- **Règle « fichiers temporaires dans `./tmp/` du projet »** formalisée —
  `CLAUDE.md`, `docs/agent/02_regles_execution.md` : jamais `/tmp` système ni
  un scratchpad d'agent hors projet

## 2026-07-29 — Claude Code (Part 4)

- **Dette de documentation E1 (C2/C3) résolue** — `conception/2_ingestion/ingestion.md` :
  - §« Choix de nettoyage : rejet, jamais correction silencieuse » (Étape 2) :
    validation Pydantic de `RuleAggregation` documentée (champs texte non
    vides, `objectifs`/`phases` non vides, `tags` volontairement non validé
    car seul champ optionnel) — critère C3 (« choix de nettoyage/homogénéisation »)
  - §« Requêtes SQL d'extraction — choix de sélection, jointures et
    optimisation » (Étape 4) : documentation de `load_enriched_rules_from_db()`
    (sélection, jointures via tables d'association, absence volontaire de
    batching pour un usage administratif ponctuel sur 245 lignes), mis en
    contraste avec `app/api_regles/regles.py::_libelles_par_regle()` qui fait
    le choix inverse (requêtes groupées) pour un contexte HTTP public —
    critère C2 (« documentation des choix de sélection/jointures » et
    « documentation des optimisations »)
  - `docs/jury/E1_bloc1_criteres_performance.xlsx` mis à jour en conséquence
    (3 critères passés de Non à Oui), commentaire C5 aligné sur
    `conception/4_api_regles/api_regles.md` (nouvelle source de vérité)

## 2026-07-29 — Claude Code (Part 3)

- **Réorganisation de `conception/` selon la numérotation par sujet, abandonnée
  depuis `1_BDD`/`2_ingestion`** — `3_enrichissement/` (créé mais resté vide)
  reçoit désormais `E_provenance_manifeste.md`, `F_chantier2_prompt_v4.md`,
  `G_revue_manuelle.md`, `H_chantier_prompt_v5.md`, `J_chantier_enrich_again.md`,
  `K_chantier_prompt_v6.md`, déplacés depuis `2_ingestion/` où ils s'étaient
  accumulés faute de dossier dédié. Nouveau `4_api_regles/api_regles.md` —
  condensé depuis `docs/superpowers/specs/2026-07-26-api-fastapi-regles-design.md`,
  seule spec qui documentait jusqu'ici `api_regles` (C5), dans un dossier
  explicitement qualifié d'historique de travail plutôt que de source de
  vérité
- **Deux doublons stricts éliminés au passage** (contenu identique confirmé —
  diff pour le Markdown, comparaison hors métadonnées pour les binaires) :
  `MLD_qualicheck.md` et `A_dictionnaire_donnees_qualicheck.xlsx` existaient
  chacun en deux exemplaires (`2_ingestion/` et `annexes/`), maintenus en
  parallèle faute de référence unique — conservés dans `1_BDD/` uniquement
  (schéma/BDD, pas ingestion). Même chose pour `I_feedback_loop.drawio`
  (Annexe I de `conception.md`) : copie en trop dans `2_ingestion/` supprimée,
  seule celle d'`annexes/` fait foi
- Toutes les références croisées corrigées en conséquence (`conception.md`,
  `docs/agent/03_references_impl.md`, `docs/README.md`, `docs/jury/README.md`,
  `app/CLAUDE.md`, `app/ingestion/manifest.yml`, et les fichiers déplacés
  entre eux) — les documents historiques (`docs/superpowers/`,
  `docs/problemes_rencontres/`, `docs/jury/decisions/`, les entrées passées de
  ce changelog) gardent volontairement leurs anciens chemins, en tant que
  constat d'époque, pas de référence vivante

## 2026-07-29 — Claude Code (Part 2)

- **`G_user_stories_qualicheck.drawio` réaligné** — voir
  `conception/annexes/G_user_stories_qualicheck.drawio`, `TODO.md` : la source
  décrivait encore l'ancien découpage (US1 = génération des constats, US2 =
  dialogue/validation), périmé depuis la fusion de la génération et du
  dialogue/validation dans US1 et la redéfinition d'US2 comme question libre
  sur une page (`conception.md`). Carte US1 et critère d'acceptation mis à
  jour, carte US2 réécrite. Les encarts « Scénario nominal » (US1/US2)
  retirés pour laisser plus de place aux 3 cartes user story, passées en
  pleine largeur — le détail des scénarios reste dans `conception.md`
  (§User stories). Export `.png` volontairement pas régénéré (relecture
  visuelle manuelle par David requise avant export, convention déjà actée)
- **Carte US0 complétée avec la revue humaine** (`review_status`,
  `review_note`) — absente jusqu'ici du schéma et de `conception.md`
  (§US0) alors que la fonctionnalité existe déjà (migration 0010,
  `docs/2_ingestion/G_revue_manuelle.md`, endpoint `PATCH /regles/{numero}`)
- **US0 précise l'acteur de la revue humaine** — pas seulement
  l'administrateur : un expert qualité externe désigné (ex. Élie Sloïm) peut
  aussi l'effectuer, authentifié par son propre jeton API
  (`app/api_regles/manifest.yml`). Mis à jour dans `conception.md` §US0 et
  dans le schéma G (`us0_as`)
- **`conception.md` §US2 corrigé** — « En tant qu'auditeur qualité web » ne
  correspondait pas aux deux personas réels d'US2 (l'auditeur expert *et*
  l'auditeur curieux, explicitement non certifié Opquast — cf. §Personas et
  `conception/annexes/J_personas_qualicheck.drawio`) ; reformulé en « En tant
  que professionnel du web », répercuté dans le schéma G

## 2026-07-29 — Claude Code

- **Registre des traitements RGPD et procédures de tri (C4)** — voir
  `docs/rgpd/registre_traitements.md`, décision
  `docs/jury/decisions/2026-07-29-perimetre-registre-rgpd.md` : registre
  scindé entre les traitements réellement en place (référentiel Opquast, hors
  champ RGPD ; jetons API nominatifs, seule donnée personnelle réelle) et le
  volet audit (`utilisateur`/`audit`/`constat`) anticipé dans le schéma mais
  non peuplé/non actif, réservé pour la spec US1 — raisonnement fondé sur
  l'article 30 du RGPD (registre des traitements réels, pas envisagés)

## 2026-07-28 — Claude Code

- **Script `creer_cle_api_regles.py`** — automatise la procédure de création de clé API (`docs/developpement/creation_cle_api_regles.md`) : ajoute le client dans `manifest.yml`, `.env`/`.env.example`, le workflow `cd-staging.yml`, et crée le secret GitHub dans l'environnement `staging` via `gh`. Testé sur copies des vrais fichiers ; un bug réel trouvé et corrigé (`.env` sans retour à la ligne final faisait fusionner la nouvelle ligne avec la précédente)
- **Procédure de création de clé API pour `/regles`** (dev + staging) — voir `docs/developpement/creation_cle_api_regles.md`, indexé dans `docs/README.md`
- **Branche `feature` renommée `dev`** (renommage GitHub natif, redirige automatiquement toute référence) : plus cohérent avec son rôle réel de tronc de développement principal (documenté depuis le 2026-07-26, `docs/agent/02_regles_execution.md`) plutôt qu'une branche de fonctionnalité isolée. `.github/workflows/ci-feature.yml` renommé `ci-dev.yml`, `dev` retiré de son `branches-ignore` (devient la branche couverte, pas exclue — sans ce correctif la CI aurait cessé de tourner silencieusement). Docs vivantes mises à jour (`docs/agent/02_regles_execution.md`, `docs/developpement/ci.md`, `docs/developpement/deploiement_staging.md`, `docs/superpowers/specs/2026-07-28-cd-staging-design.md`) ; specs/plans/CHANGELOG datés antérieurs volontairement laissés tels quels (enregistrements historiques, pas des références à jour). Vérifié : CI verte sur un vrai push à `dev` après le renommage
- **CD staging vérifié en conditions réelles, de bout en bout** : `https://regles.qualicheck.koabana.fr` sert les 245 vraies règles Opquast, `make api-regles-acceptance` passe intégralement contre l'instance staging réelle (245 règles, filtres, 4 jetons, boucle de revue). 4 bugs réels trouvés et corrigés en cours de route sur le premier déploiement (chacun avec son PR dédiée) :
  - `make` absent du PATH du runner self-hosted → installé sur cloclo
  - Ordre des étapes : migrations lancées avant que Postgres ne soit démarré sur une machine neuve → nouvelle cible `make up-db` + attente `pg_isready`
  - `logs/` non suivi par git → supprimé entièrement par `git clean -ffdx` (`actions/checkout`) à chaque run, recréé en `root` par le conteneur (`Dockerfile` sans `USER`), rendant tout `chown` manuel temporaire → `logs/.gitkeep` (fichier tracké) pour que le dossier survive
  - Acceptance lancée avant qu'uvicorn n'accepte les connexions après `make up` (`Connection reset by peer`) → attente sur `/health`
  - Build Docker en échec (DNS injoignable dans le conteneur de build) : corrigé côté infra cloclo (`/etc/docker/daemon.json`, hors dépôt)
  - Base staging bootstrappée pour de vrai : `make export_sql` en local → transfert → `make import_sql` sur cloclo
- **CD staging opérationnel** (`docs/superpowers/specs/2026-07-28-cd-staging-design.md`, `docs/superpowers/plans/2026-07-28-cd-staging-implementation.md`) : `.github/workflows/cd-staging.yml` (runner self-hosted sur cloclo, déclenché au merge d'une PR vers `staging`) — migrations, `docker compose up -d --build`, rejeu de la suite d'acceptance existante comme garde-fou. Runbook `docs/developpement/deploiement_staging.md`. Branche `staging` créée. **Tous les prérequis manuels réalisés pour de vrai par David sur cloclo** : `uv`, runner self-hosted (service systemd, en ligne), environnement GitHub `staging` + 7 secrets, DNS A (`regles.qualicheck.koabana.fr` → IP de cloclo), `docker-compose.override.yml` (réseau `cloudnet`, découverte en cours de route : Caddy proxie par nom de conteneur, pas par `localhost` — fichier déplacé hors du dossier checkouté pour survivre au nettoyage de `actions/checkout`), config Caddy (`reverse-proxy/Caddyfile`, 502 confirmé en attendant le premier déploiement réel). Reste : bootstrap de la base staging (dump exporté, `backups/20260728_135208.sql`, transfert et import à faire), premier déploiement réel non encore déclenché
- **Environnement GitHub `staging` créé, avec ses 7 secrets** (`gh api` pour l'environnement, `gh secret set --env staging` pour les secrets) : `POSTGRES_USER`/`POSTGRES_DB` (`qualicheck_staging`), `POSTGRES_PASSWORD` (généré, `secrets.token_urlsafe`), et les 4 jetons `FASTAPI_API_KEY*` déjà générés localement (copiés tels quels, jamais affichés en clair dans ce commit). Premier prérequis manuel du plan `docs/superpowers/plans/2026-07-28-cd-staging-implementation.md` réalisé pour de vrai — reste : runner self-hosted, `docker-compose.override.yml` (réseau `cloudnet`), Caddy, DNS Infomaniak, bootstrap de la base staging, tous hors de portée de l'agent (infrastructure personnelle de David)
- **Logging ajouté à `api_regles`** (`app/logging_config.py` réutilisé, `logs/api_regles.log`, monté hors du conteneur via `docker-compose.yml`) : démarrage (clients déclarés), authentifications refusées (`WARNING`, sans jamais loguer le jeton reçu), sonde `/health` en échec (`WARNING`), et annotation réussie avec le **nom du client résolu** (`INFO`, ex. « Règle 1 annotée par elie-sloim ») — traçabilité minimale de qui annote quoi, sans colonne `reviewed_by` en base. `annoter_regle()` capture désormais le retour de `require_bearer()` (`client_nom: str = Depends(...)`) au lieu de l'ignorer via `dependencies=[...]`. Vérifié en conditions réelles (conteneur reconstruit et redémarré) : démarrage loggé, un 401 réel loggé, une annotation réelle (`elie-sloim`) loggée puis annulée, règle 1 revenue à `NULL` en base
- **`api_regles` tournant en permanence via Docker** (`Dockerfile` nouveau, service `api-regles` dans `docker-compose.yml`) : plus besoin de lancer `make api-regles` à la main, `make up` (déjà existant, `docker compose up -d --build`) démarre désormais aussi l'API en tâche de fond. Le conteneur atteint Postgres par le nom de service (`POSTGRES_HOST=postgres`, port interne `5432`), surchargeant les valeurs hôte de `.env` (`localhost:8832`) — `env_file: .env` fournit le reste (dont les 4 jetons Bearer). `CMD` en `uv run --no-sync` : un `uv run` nu resynchronise (et retélécharge les dépendances dev, ruff compris) à chaque démarrage du conteneur, contredisant le `--no-dev` du build — corrigé après l'avoir vu se produire réellement au premier démarrage. **Vérifié en conditions réelles** : build + démarrage du conteneur, `/health` → `ok`, `GET /regles` → 245, `PATCH` avec le jeton `dev` → `422` (authentification franchie, refusée par la validation du corps, aucune écriture). Reste local, non exposé à l'extérieur — l'exposition réelle (Caddy/domaine) reste à traiter avec le CD, volontairement mis de côté pour l'instant
- **Suite d'acceptance étendue à la vérification des 4 jetons** (`tests/acceptance/api_regles_acceptance.jsonl`, `app/api_regles/acceptance.py`) : champ `avec_jeton` (booléen) remplacé par `jeton` (`null`, `"invalide"`, ou le nom d'un client déclaré) — un cas par client (`dev`, `elie-sloim`, `david-legrand`, `formateur`) vérifie qu'il franchit bien l'authentification, via un corps volontairement invalide (`422` attendu, jamais `401`) : aucune écriture réelle n'est jamais tentée, donc aucun risque d'effacer une vraie annotation existante. **Exécutée pour de vrai (2026-07-28)** contre le serveur réellement démarré : les 4 jetons acceptés, jeton absent/invalide refusés (401), boucle de revue de la règle 124 intacte — état des règles 1 et 124 vérifié en base après coup (`review_status` toujours `NULL`)
- **`FASTAPI_API_ID` supprimé** (`.env`, `.env.example`) : son rôle initial (identifier l'appelant du `PATCH`) est désormais couvert par le nom de client résolu par `require_bearer()` — devenu obsolète avec l'ajout des clients nommés ci-dessous. `docs/agent/03_references_impl.md` mis à jour en conséquence. Les mentions dans les spec/plan historiques (`docs/superpowers/specs/2026-07-26-api-fastapi-regles-design.md`, `docs/superpowers/plans/2026-07-26-api-regles-implementation.md`) laissées intactes — elles décrivent une décision passée, pas l'état courant
- **3 clients réels ajoutés à l'API données** (`elie-sloim`, `david-legrand`, `formateur`), en plus de `dev` — jetons générés (`secrets.token_urlsafe(32)`), déclarés dans `app/api_regles/manifest.yml`, secrets dans `.env`/`.env.example`. Conséquence découverte en l'implémentant : `require_bearer()` appelle `clients_tokens()` à chaque requête authentifiée (pas seulement au démarrage) — la fixture `client` des tests d'intégration (`tests/integration/api_regles/test_regles.py`) doit donc désormais poser les 4 jetons (sinon `RuntimeError` dès qu'un test PATCH tourne en CI, où aucun `.env` réel n'existe). Tests `test_config.py`/`test_auth.py` isolés via `monkeypatch.setattr(config, "CLIENTS", ...)` pour ne plus dépendre du nombre réel de clients déclarés. Vérifié en conditions réelles (`make api-regles`) : les 3 nouveaux jetons passent l'authentification, un jeton inventé reste refusé (401)
- **Authentification multi-clients de l'API données** (`docs/jury/decisions/2026-07-28-cle-valeur-multi-clients-api-regles.md`) : `admin_token()` (jeton unique) remplacé par `config.clients_tokens()` — liste `clients` dans `app/api_regles/manifest.yml` (`nom` + `env_var_token`), un jeton par client déclaré. `auth.require_bearer()` compare le jeton reçu à chacun (`secrets.compare_digest`) et renvoie le nom du client résolu au lieu de `None`. Prépare l'ouverture du `PATCH` à Élie Sloïm et d'autres experts Opquast (un jeton nommé chacun) sans construire de table Postgres des utilisateurs, disproportionnée pour ce besoin — même patron que les rôles LLM de `app/ingestion/manifest.yml`. Client existant migré à l'identique (`nom: dev`, `FASTAPI_API_KEY`, aucun secret renommé). Solution volontairement provisoire et manuelle (ajouter/révoquer un client = éditer `manifest.yml`/`.env` à la main, aucune rotation ni interface) — voir statut dans la décision. 64 tests verts (`tests/unit/api_regles`, `tests/integration/api_regles`), vérifié aussi en conditions réelles (`make api-regles` : `401` sans jeton, passe l'authentification avec le jeton `dev`)
- **Séparation `api_regles`/`api_audit` actée** (`docs/jury/decisions/2026-07-28-separation-api-regles-api-audit.md`) : une seule base de données et un seul `app/models/`, mais deux services FastAPI distincts qui l'attaquent chacun directement. `app/api_data` renommé `app/api_regles` en conséquence (spec, plan, diagramme, décision de licence mis à jour) — voir aussi `TODO.md`, `IDEA.md`
- **API données implémentée** (spec `docs/superpowers/specs/2026-07-26-api-fastapi-regles-design.md`, plan `docs/superpowers/plans/2026-07-26-api-regles-implementation.md`), 11 tâches TDD (test rouge → implémentation → test vert → commit par tâche)
  - `app/db.py` (nouveau) : `build_database_url()`, `build_engine()`, `get_session()` — accès PostgreSQL partagé de l'étage données. Les 5 scripts qui dupliquent `build_engine()` restent volontairement inchangés (refactoring hors périmètre, coûte de l'argent à ré-exécuter)
  - `app/api_regles/manifest.yml` (nouveau) : source de vérité de la configuration non secrète (titre, description, version du contrat, port `8880`, origines CORS, longueur max de `review_note`, attribution de licence). `app/api_regles/config.py` en est le seul lecteur — aucun `os.getenv()` ni YAML ailleurs dans le paquet
  - `app/api_regles/schemas.py` (nouveau) : `RegleRead` (19 champs, dont `outils[]` dérivé de la grammaire `+`/`&` de `strategie_analyse`), `ReglePatch` et ses validations — note obligatoire pour `a_revoir`/`invalide` (sans elle `enrich_again` appellerait le LLM sans consigne), note refusée avec `review_status: null`, refus des titres markdown et des blocs de code qui pourraient détourner le prompt d'enrichissement
  - `app/api_regles/auth.py` (nouveau) : `require_bearer()` — token Bearer statique sur le `PATCH` uniquement, `secrets.compare_digest` (comparaison en temps constant), `HTTPBearer(auto_error=False)` pour renvoyer `401` et non le `403` par défaut, fail-fast au chargement de l'application si `FASTAPI_API_KEY` est absente ou vide
  - `app/api_regles/regles.py` (nouveau) : `GET /regles` (filtres répétables `?outil=` et `?review_status=`, OU en interne, ET entre eux), `GET /regles/{numero}`, `PATCH /regles/{numero}`. Le filtre `?outil=` est un « contient » et non une égalité, vérifié par test (une stratégie composite `statique&playwright` sort bien sur `?outil=playwright`). Chargement des collections (`tags`, `phases`, `objectifs`) en **4 requêtes groupées** quel que soit le nombre de règles : `app/models/` ne déclare aucun `relationship()`, `selectinload()` était donc hors de portée sans modifier des modèles partagés avec le pipeline d'ingestion
  - `app/api_regles/main.py` (nouveau) : objet ASGI, `CORSMiddleware` (origines depuis le manifeste, jamais `["*"]`, `allow_credentials=False` puisque l'auth passe par un header), `/health` avec vérification réelle de la base (`SELECT 1`, `503` si injoignable), documentation OpenAPI générée (`/docs`, `/redoc`, `/openapi.json`) portant l'attribution CC BY-SA 4.0 du référentiel Opquast (`license_info` + citation dans la description)
  - `Makefile` : nouvelle cible `make api-regles`, le port étant lu dans le manifeste par `grep` ; `FASTAPI_URL_DEV` retiré de `.env`/`.env.example` car déductible du port du manifeste
  - **64 tests, tous verts** (`uv run pytest tests/unit/api_regles tests/unit/test_db.py tests/integration/api_regles`) : 7 configuration, 21 schémas, 4 authentification, 2 accès base, 22 intégration, 8 suite d'acceptance (voir plus bas). Les tests d'intégration injectent leur session par `app.dependency_overrides[get_session]` : l'API sous test ne peut alors **pas** ouvrir de connexion vers `POSTGRES_DB`, garantie structurelle issue de l'incident du 2026-07-25. `ruff check` propre sur tout le périmètre
  - **Le `PATCH` n'écrit que `review_status`/`review_note`/`reviewed_at`** — le référent Opquast annote, le développeur corrige plus tard via `make enrich-again`. Cette API n'appelle aucun LLM et ne recalcule aucun embedding
- **Suite d'acceptance de l'API données** (`app/api_regles/acceptance.py`, `tests/acceptance/api_regles_acceptance.jsonl`, `scripts/check_api_regles_acceptance.py`, `make api-regles-acceptance`), sur le modèle de `app/ingestion/rag_acceptance.py` — vérifie l'API réellement démarrée (appels HTTP, pas `TestClient`) plutôt que la base des curls manuels prévue par le plan. Contrairement au RAG, `is_acceptable()` n'accorde aucune tolérance (`all()`, pas un taux) : le référentiel Opquast est figé, un seul cas en échec doit faire échouer la suite
  - **Chaque cas JSONL déclare sa méthode explicitement** (`"methode": "GET"` ou `"PATCH"`, à la demande de David) : rien n'est implicite côté script. Les cas `GET` comparent un nombre de règles retourné ; les cas `PATCH` comparent un code HTTP (ex. refus sans jeton → `401`), avec `avec_jeton`/`corps` déclarés dans le cas lui-même. La boucle de revue (annoter → `enrich_again --dry-run` → désannoter) reste orchestrée dans le script : scénario à plusieurs étapes impliquant un sous-processus externe, pas un simple appel HTTP à comparer
  - **Exécutée pour de vrai (2026-07-28)**, `make api-regles` démarré + `make api-regles-acceptance` : 245 règles au total, 85 via `?outil=playwright` (composites incluses), 44 via `?outil=manuel`, 124 via `?outil=statique`, 245 non revues, `PATCH` sans jeton refusé (401), boucle de revue complète sur la règle 124 (annotée, sélectionnée par `enrich_again --dry-run`, désannotée, plus sélectionnée) — 6 cas JSONL + boucle de revue, tous verts
  - **Bug trouvé et corrigé par ce premier run réel** : le script vérifiait `stdout` du sous-processus `enrich_again --dry-run` pour y chercher le numéro de règle, mais les logs d'`enrich_again` vont en fichier (`app/logging_config.py`), pas sur `stdout` — le vrai signal est l'aperçu JSON `tmp/enrich_again_preview.json`, qui n'est en plus **pas réécrit** quand aucune règle n'est à revoir (retour anticipé dans `enrich_again()`). Corrigé en supprimant ce fichier avant chaque appel `--dry-run` pour ne jamais lire un résultat périmé
  - Règle 124 confirmée revenue à son état d'origine (`review_status`/`review_note`/`reviewed_at` à `NULL`) en base après l'exécution

## 2026-07-27 — Claude Code

- **`dirty_retriever` (outil de veille perso, branche `veille_test`)** : recherche sémantique ad hoc dans les 245 règles Opquast — prend une question en langage naturel, calcule son embedding réel (Azure `text-embedding-3-small`) et affiche en JSON les 3 règles les plus proches (similarité cosinus pgvector), avec thème résolu et score. Réutilise l'infra existante (`EmbeddingClient`, pattern de `rag_acceptance.py`), pas de test formel (outil perso hors périmètre certification) — validé avec un vrai appel sur la question « comment rédiger un texte alternatif pour une image ? » (règles 118/116/117, thème Images et médias) — voir `app/ingestion/dirty_retriever.py`, `scripts/dirty_retriever.py`
- **Fix `dirty_retriever`** : le champ `embedding` (vecteur brut 1536 dimensions) fuitait dans chaque dict retourné, repéré via un usage réel (« souligner les titres » → sortie JSON illisible/énorme) — exclu explicitement de la construction du dict — voir `app/ingestion/dirty_retriever.py`

## 2026-07-26 — GitHub Copilot

- Dispatch de `CLAUDE.md` pour réduction de tokens : fichier racine compacté + extraction du détail dans `docs/agent/01_contexte_projet.md`, `docs/agent/02_regles_execution.md`, `docs/agent/03_references_impl.md` — voir `CLAUDE.md`, `docs/agent/`, `CHANGELOG.md`
- Reprise de la réorganisation documentaire sans toucher aux TODO : ajout de `docs/README.md`, `docs/agent/README.md`, `docs/agent/04_contexte_actif.md`, mise à jour de `CLAUDE.md` (nouveaux points d'entrée de contexte) et réalignement de `README.md` sur l'état réel (`pgvector` 1536, embedding actuel Azure `text-embedding-3-small`) — voir `docs/README.md`, `docs/agent/`, `CLAUDE.md`, `README.md`

## 2026-07-26 — Claude Code

- **Chunking, embedding, indexation (Étapes 5-7)** (spec `conception/2_ingestion/L_chunking_embedding_indexation.md`, plan `docs/superpowers/plans/2026-07-26-chunking-embedding-implementation.md`), implémenté en 5 tâches (TDD)
  - Migration 0011 : `regle.embedding` élargie de `vector(384)` (hérité du choix MiniLM, disqualifié : `max_token_input=128`) à `vector(1536)` (dimension native de `text-embedding-3-small`, pas de troncature) — testée up/down sur `qualicheck_test`, appliquée sur la vraie base (aucune donnée perdue, colonne vide avant migration)
  - `app/ingestion/chunking.py` — `build_chunk_text()` : une règle = un chunk, texte structuré avec labels (intitulé, contexte, solution, controle, guide_analyse, tags, phases), `contexte` omis si absent
  - `app/ingestion/embedding.py` — `EmbeddingClient` (client `openai` brut, pas `langchain`, pour accéder au `total_tokens` réel de la réponse), `embed_batch()` avec retry (3 tentatives, backoff), `dimensions=1536` passé explicitement — **vérifié avec un vrai appel Azure sur 1 règle réelle** (règle 65, 203 tokens, vecteur 1536 dimensions confirmé, coût négligeable) sans écrire en base
  - `app/ingestion/manifest.yml` — nouveau rôle `embedding` (modèle, `AZURE_MODEL_TEXT_EMBEDDING_SMALL`, prix estimé en attendant une vraie facture)
  - `app/ingestion/schema.py`/`stockage.py` — `EnrichedRule.embedding` et `upsert_rule()` écrivent la colonne
  - `scripts/embed_rules.py` (nouveau, backfill toutes règles) + Étape 6 dans `scripts/ingestion.py` + cible `make embed-rules` — **non exécutés pour de vrai sur les 245 règles** dans le cadre de ce chantier, réservé à une décision délibérée de David
- **Prompt d'enrichissement bumpé en `version: 6`** (spec `conception/2_ingestion/K_chantier_prompt_v6.md`, plan `docs/superpowers/plans/2026-07-26-prompt-v6-implementation.md`) — voir `app/ingestion/prompts/enrich_rule.md` : reformulation de la clause `manuel` (b) pour cesser de sur-appliquer `manuel` à des vérifications entièrement automatisables par navigateur ; deux nouveaux exemples few-shot ajoutés (Exemple 9 : `vision&statique`, différenciation produit indisponible — forme une paire minimale avec l'Exemple 5 pour contraster ET/PUIS ; Exemple 10 : `playwright` sur une règle de contraste WCAG, piège `manuel` sur un critère à formule déterministe). Chantier content-only, revu et corrigé suite à revue de code finale (contradictions internes de l'Exemple 9, outils hors périmètre déclaré dans l'Exemple 10). **Aucune ré-ingestion réelle n'a été lancée** — ce prompt n'a pas encore servi à un appel LLM payant, il est préparé pour une future ré-ingestion.
- **Réécriture ciblée des règles marquées à revoir (`enrich_again`)** (spec `conception/2_ingestion/J_chantier_enrich_again.md`, plan `docs/superpowers/plans/2026-07-26-enrich-again-implementation.md`), implémentée en 4 tâches (TDD)
  - `app/ingestion/llm_client.py` — `load_prompt()`/`enrich_single_rule()` acceptent désormais les paramètres optionnels `review_note`, `current_strategie_analyse` et `strategie_source` : insèrent une section « Contexte de revue humaine » dans le prompt quand `review_note` est fourni, comportement d'enrichissement initial strictement inchangé sinon
  - `app/ingestion/enrich_again.py` — nouveau module : `load_rules_to_review()` (sélectionne les règles `review_status IN (a_revoir, invalide)`), `clear_review_fields()` (remet `reviewed_at`/`review_status`/`review_note` à `NULL`), `enrich_again()` (orchestrateur — rappelle le LLM règle par règle, commit par règle, fail-fast)
  - `scripts/enrich_again.py` — point d'entrée CLI sur le modèle de `scripts/ingestion.py` (même logging, fail-fast)
  - Nouvelle cible `make enrich-again` : sauvegarde les données réelles avant **et** après le script (`export_sql` des deux côtés — le `review_note` humain, détruit par la correction, n'a sinon aucune copie récupérable), comme `make ingestion` pour le après — voir `Makefile`, `CLAUDE.md`
  - Revue finale (chantier complet) : correctif du champ `contexte`, perdu depuis toujours sur le round-trip `enrich_single_rule()` → `EnrichedRule` (bug pré-existant, affectait aussi l'ingestion normale) ; mode `--dry-run` (prévisualisation sans appel LLM) ; log avant/après par règle ; résumé de coût préservé même en cas d'échec partiel (`finally`) ; test renforcé sur le câblage réel `strategie_source`/`review_note` (l'ancien test validait un mock indépendant des arguments réels)
  - **Exécuté pour de vrai le 2026-07-26** (`uv run python scripts/enrich_again.py`, suivi de `make export_sql`) : les 11 règles corrigées pour 0,1610 € (contre ~4,29 € pour une ré-ingestion complète des 245) — 10/11 corrections tombent exactement sur ce que l'audit V6 avait anticipé (28, 62, 65, 94, 124, 164, 182, 202, 239) ; la 11e (règle 125) rejoint sa jumelle 124 en `statique&playwright`, cohérence retrouvée ; la 234 améliore même l'ordre suggéré par la revue (`playwright+statique` — le rendu JS doit précéder l'inspection du DOM, pas l'inverse). `review_status`/`review_note`/`reviewed_at` bien remis à `NULL` sur les 11 lignes, `strategie_source = ia_reingest` (première utilisation réelle de cette valeur). Règle 96 laissée intacte, volontairement non tranchée — voir `docs/problemes_rencontres/ingestion/5_recommandations_v6.md` §2 et §7
- `conception/annexes/C_pipeline_ingestion_reel.drawio` (nouveau) : points d'entrée réels du pipeline (`scripts/migration.py`, `clear_opquast_tables.py`, `ingestion.py`, `enrich_again.py`, `embed_rules.py`) et leurs options CLI, dont l'écart réel où l'embedding (étape 6) précède le stockage (étape 4) — convention `X_reel.drawio`. `C_pipeline_ingestion.drawio` (cible) : noms de modèles LLM codés en dur (`Kimi K2.6`, `All MiniLM L12 v2`) remplacés par un renvoi générique à `manifest.yml`, source de vérité
- **`make embed-rules` exécuté pour de vrai** : 245/245 règles vectorisées (1536 dimensions), 87 092 tokens, 0,0016 € — vérifié en base (`vector_dims`, index `regle_embedding_idx` présent) ; deux vérifications manuelles au rapprochement cosinus (requêtes libres, embedding calculé à la volée) confirment une recherche sémantique cohérente — voir entrée ajoutée à `TODO.md` (jeu de règles d'acceptance RAG en JSONL, reporté)
- `conception/conception.md` : légende d'image en incohérence US1/US2 corrigée (le flux de dialogue/validation est US1, SQL déterministe — la légende disait à tort US2, seule mention isolée sur 4 dans le document) — `TODO.md` mis à jour en conséquence
- Réorganisation de `CLAUDE.md` (David, réduction de tokens) en `docs/agent/*.md` : 3 règles comportementales perdues dans la compaction restaurées dans `docs/agent/02_regles_execution.md` (priorité de la validation à chaque étape sur le défaut autonome, exception `tests/migration/` + mise en garde CI/local sur l'isolation des tests, politique de branches mise à jour : travail au fil de l'eau sur `feature`, plus de découpage par sujet)
- **Table `etat_donnees`** (migration `0012_add_etat_donnees.py`, modèle `app/models/etat.py`) : traçabilité du dernier export/import de backup (fichier, type d'opération, horodatage), ligne unique mise à jour directement par `make export_sql`/`make import_sql` (docker exec psql) — exclue du dump lui-même (`--exclude-table`, comme `alembic_version`) ; testée en migration (`tests/migration/test_migration.py::test_table_etat_donnees`), vérifiée par un vrai `make export_sql`
- **Jeu d'acceptance RAG (JSONL)** (spec `docs/superpowers/specs/2026-07-26-rag-acceptance-jsonl-design.md`, plan `docs/superpowers/plans/2026-07-26-rag-acceptance-jsonl-implementation.md`), implémenté en 4 tâches (TDD) — formalise les deux vérifications manuelles du rapprochement cosinus déjà faites lors de `make embed-rules`
  - `tests/acceptance/rag_acceptance.jsonl` (nouveau) : 17 cas `{question, numero_regle_attendue}` — les 2 cas déjà vérifiés manuellement (règles 139, 181) + 15 nouveaux couvrant des thématiques variées (sécurité, accessibilité, e-commerce, formulaires, SEO, mentions légales), questions rédigées en paraphrase des règles (pas de recouvrement de mots-clés), validées par David avant intégration
  - `app/ingestion/rag_acceptance.py` (nouveau) : `load_cases()`, `query_top_n_numeros()` (requête pgvector, `Regle.embedding.cosine_distance()`), `evaluate_case()`, `compute_taux_reussite()`, `is_acceptable()` — logique pure testée unitairement (6 tests), `query_top_n_numeros()` non testée en unitaire (nécessite une base réellement vectorisée), validée par exécution réelle
  - `app/ingestion/manifest.yml` — nouvelle section `rag_acceptance` (`top_n: 3`, `taux_reussite_minimum: 0.8`) : le rappel imparfait du RAG est déjà assumé (voir `docs/jury/decisions/2026-07-25-rag-us2-petit-corpus.md`), on n'exige donc pas 100% de réussite par cas mais un taux global
  - `scripts/check_rag_acceptance.py` (nouveau, sur le modèle de `scripts/embed_rules.py`) + cible `make rag-acceptance` — volontairement **hors CI** (coût réel d'appel API à chaque exécution) ; point de contrôle formalisé en scénarios Gherkin dans la spec (documentation, pas de `pytest-bdd` réel)
  - **`make rag-acceptance` exécuté pour de vrai par David (2026-07-26)** : 17/17 cas passent, taux de réussite 100% (seuil 80%), 274 tokens, coût négligeable (0,0000 €) — voir `logs/ingestion.log`
  - **Suite proposée par David** : `app/ingestion/rag_acceptance.py` — `summarize_dataset_versions()`/`format_dataset_versions()`, logue la distribution `prompt_version`/`llm_model` des 245 règles à chaque run (visible immédiatement si le jeu de données est mélangé, ex. après un `enrich_again` partiel — constaté en vérifiant : le dernier `enrich_again` a tourné avant le bump vers `version: 6`, les 245 règles sont donc uniformément en `prompt_version = 5`). Proposition symétrique d'ajouter une version « source de vérité » dans `manifest.yml` écartée : deuxième source de vérité redondante avec `regle.prompt_version`, qui peut déjà diverger ligne par ligne
- **Conception de l'API données** (`app/api_data/`), issue du brouillon `tmp/brouillon_spec_api.md` et d'un brainstorming complet — aucune implémentation à ce stade, uniquement conception validée
  - Spec `docs/superpowers/specs/2026-07-26-api-fastapi-regles-design.md` : `GET /regles` (filtres `?outil=`/`?review_status=`, sémantique « contient » sur les stratégies composites), `GET /regles/{numero}`, `PATCH /regles/{numero}` (annotation de revue uniquement — `review_status`/`review_note`/`reviewed_at` — sans jamais appeler de LLM ni recalculer d'embedding), `/health`, documentation OpenAPI générée. Architecture n-tiers explicite : `app/api_data/` forme avec le pipeline d'ingestion l'étage données ; le futur `app/api_business/` (US1/US2) consommera cette API en HTTP sans jamais toucher PostgreSQL — seul l'écran de revue des enrichissements y accède directement, écart assumé et documenté (pas un CRUD passe-plat : l'API porte ses propres invariants de validation)
  - Configuration centralisée dans `app/api_data/manifest.yml` (port `8880`, origines CORS, longueur max de `review_note`, attribution de licence) + un unique `app/api_data/config.py` — aucune valeur éparpillée en `os.getenv()`, même frontière que `KIMI_PRICE_*` (secrets dans `.env`, données de référence versionnées dans un manifeste)
  - Décision actée `docs/jury/decisions/2026-07-26-lecture-ouverte-api-regles.md` : la lecture reste ouverte, sans jeton — le référentiel Opquast est sous licence **CC BY-SA 4.0** (partage à l'identique, viral sur le jeu de données diffusé), cohérent avec la veille du projet sur le pillage du savoir. Conséquence : attribution obligatoire ajoutée (`license_info` + citation Opquast, visibles dans `/docs`/`/openapi.json`) ; `README.md` mis à jour en conséquence
  - Plan d'implémentation en 12 tâches TDD, `docs/superpowers/plans/2026-07-26-api-regles-implementation.md` — **implémenté le 2026-07-28, voir plus bas**
  - Diagramme de flux `conception/annexes/flux_api_donnees.drawio` (les 3 endpoints en couloirs parallèles, convergence sur l'assemblage de réponse partagé)
  - `IDEA.md` : sous-cas de recherche vectorielle « vecteur déjà calculé » qui resterait légitimement côté données (même motif que `app/ingestion/rag_acceptance.py::query_top_n_numeros()`, aucun appel LLM) — volontairement non construit, US2 n'étant pas conçue
  - `CLAUDE.md`/`docs/agent/04_contexte_actif.md` : nouvelle règle non négociable — rester dans le périmètre du référentiel de certification (`conception/referentiel_competences.md`, `conception/certif_deroule.md`), ne pas élargir au-delà de ce qui valide les compétences visées

## 2026-07-25 — Claude Code (Part 2)

- **Incident** : un `pytest tests/` lancé juste après la ré-ingestion réelle (245 règles, 4,32 €) a effacé ces données via un test d'intégration qui vidait la vraie base de dev locale (`qualicheck`) — voir bullet ci-dessous pour le correctif
- **Isolation des tests d'intégration Postgres destructeurs** : nouvelle variable d'env `POSTGRES_TEST_DB` (base dédiée `qualicheck_test`) + nouvelle cible `make migration-test` (crée si absente et migre cette base) — voir `.env.example`, `Makefile`
  - `tests/integration/ingestion/test_stockage_contexte.py` et `test_stockage_provenance.py` basculés sur `POSTGRES_TEST_DB` au lieu de `POSTGRES_DB`
  - `.github/workflows/ci-feature.yml` : ajout de `POSTGRES_TEST_DB` (réutilise volontairement le secret `POSTGRES_DB`, le service CI étant déjà éphémère par run)
  - `CLAUDE.md` : règle posée dans « Principes généraux », scopée aux tests destructeurs (`tests/migration/` reste volontairement sur `POSTGRES_DB`, lecture seule sur le schéma de la vraie base de dev)
- Renommage `scripts/test_storage.py` → `scripts/storage_smoke.py` (contenu inchangé) : évitait qu'un `pytest` avec chemin explicite (hors `testpaths`) ne collecte ce script de smoke-test qui écrit en base au import, sur `POSTGRES_DB`
- Nouvelle cible `make export_sql` (`pg_dump --data-only` de la vraie base `qualicheck`, hors `alembic_version`, dans `backups/YYYYMMDD_HHMMSS.sql`, dossier gitignoré) — à lancer avant toute ré-ingestion réelle coûteuse, précisément le filet de sécurité qui aurait permis de récupérer les 245 règles V5 perdues — voir `Makefile`, `.gitignore`
- Nouvelle cible `make import_sql FILE=...` (restauration d'un dump `export_sql`) : `FILE=` obligatoire, échec explicite en cas de conflit de clé primaire plutôt que de vider la base automatiquement — voir `Makefile`
- La cible `make ingestion` chaîne désormais `make export_sql` juste après le pipeline — sauvegarde automatique des données réelles, plus besoin d'y penser manuellement — voir `Makefile`
- `conception/annexes/B_MCD_qualicheck.drawio` : relations MCD passées en traits simples sans flèche (sauf les deux segments DF, qui gardent leur sens de lecture) ; cardinalités retirées ; positions/espacement préservés
- Dictionnaire de données resynchronisé avec les migrations 0009/0010 (`llm_provider`→`llm_model`, ajout `prompt_version`/`created_at`/`updated_at`/`reviewed_at`/`review_status`/`review_note`) — nouvelle catégorie « Revue manuelle » (champs saisis à la main, pas par le pipeline) ajoutée à la feuille Légende — voir `conception/2_ingestion/A_dictionnaire_donnees_qualicheck.xlsx`, `conception/annexes/A_dictionnaire_donnees_qualicheck.xlsx`
- `Makefile` réorganisé en 5 sections thématiques (Docker, Migrations, Ingestion et données réelles, Tests, Accès direct à la BDD) — aucune recette modifiée, vérifié cible par cible
- Nouvelles cibles `make test-unit`, `make test-integration`, `make test-migration` (lancent respectivement `tests/unit`, `tests/integration`, `tests/migration` séparément) — `make test` continue de lancer toute la suite — voir `Makefile`

## 2026-07-25 — Claude Code

- **Spec E implémentée — Provenance des données et manifeste d'ingestion** (plan `docs/superpowers/plans/2026-07-25-provenance-manifeste-implementation.md`, spec `conception/2_ingestion/E_provenance_manifeste.md`), exécutée tâche par tâche (TDD, `superpowers:writing-plans` + `superpowers:executing-plans`), mergée sur `feature` (fast-forward, 10 commits)
  - `app/ingestion/manifest.yml` créé — décisions courantes du pipeline d'ingestion (rôle `enrichissement` → modèle + variable d'env à résoudre), lu par le code, aucun secret
  - `.env`/`.env.example` restructurés en inventaire par modèle (`AZURE_MODEL_KIMI` remplace `AZURE_DEPLOYMENT_INGESTION`) — seule la variable réellement lue par du code a été renommée, les 3 variables `AZURE_DEPLOYMENT_AUDIT_*`/`QUESTION_LIBRE` restent inchangées (US1/US2 non conçus)
  - `app/ingestion/prompts/enrich_rule.md` — frontmatter `version: 3` ajouté
  - Migration `0009_add_provenance_columns` — renomme `regle.llm_provider` → `llm_model` (VARCHAR 20→64), ajoute `prompt_version`, `created_at`, `updated_at` (toutes nullables, `NULL` = produit avant instrumentation) — voir `app/models/referentiel.py`
  - `app/ingestion/schema.py` — `EnrichedRule.llm_model`/`prompt_version` remplacent le défaut en dur `llm_provider="kimi-k2.6"`
  - `app/ingestion/llm_client.py` — `load_manifest()`/`load_prompt_version()` : le modèle et la version de prompt sont lus (manifeste + frontmatter), plus jamais écrits en dur ; la provenance stockée utilise structurellement les mêmes valeurs que celles ayant servi à l'appel LLM
  - `app/ingestion/stockage.py` — `upsert_rule()` renseigne les 4 colonnes de provenance (`created_at` à la création uniquement, `updated_at` à chaque upsert) ; `load_enriched_rules_from_db()` les relit
  - `scripts/ingestion_test.py` — bouchon aligné (`llm_model="test"`, `prompt_version=0`)
  - `scripts/ingestion.py` — correctif de visibilité du coût : le calcul/log des tokens (`Étape 3`) est déplacé **avant** la tentative de stockage (`Étape 4`), pour qu'un échec de stockage n'efface plus le coût déjà engagé (perte constatée le 19/07 : ~6€ jamais journalisés)
  - Tests : +7 unitaires (`test_enrichment.py`, manifeste + frontmatter + indépendance modèle/env var), +2 migration (`test_migration.py`), +2 intégration (`test_stockage_provenance.py`) — suite complète 55/55 verte, `ruff` propre
  - Documentation : `conception/2_ingestion/MLD_qualicheck.md` + `conception/annexes/MLD_qualicheck.md` (4 colonnes + règle de nommage), `conception/2_ingestion/ingestion.md` (dernière mention `llm_provider` corrigée)
  - PyYAML ajoutée comme dépendance (parsing manifeste + frontmatter)

- **Décision close : emplacement des tarifs `KIMI_PRICE_*`** — `app/ingestion/manifest.yml` (clé `enrichissement.prix_entree_par_million`/`prix_sortie_par_million`), pas `.env`. Ce sont des données de référence du projet, pas des secrets ; le manifeste versionné donne un historique gratuit via git, contrairement à `.env`. Cohérent avec le principe directeur de la spec E (§3) déjà appliqué au reste du manifeste. `scripts/ingestion.py` lit désormais ces valeurs via `load_manifest()` au lieu de `os.getenv("KIMI_PRICE_*")` — voir `conception/2_ingestion/E_provenance_manifeste.md` §6, `TODO.md`, `docs/jury/decisions/2026-07-21-perimetre-mlops-ingestion.md`
  - Au passage, correctif : `.env.example` avait hérité des vraies valeurs reconstruites (`0.8008`/`3.3875`) au lieu d'un gabarit vide, incohérent avec le reste du fichier — corrigé avant d'être remplacé par le manifeste

## 2026-07-23 — Claude Code

- **`docs/jury/veille/CLAUDE.md` créé** — orientation rapide pour la prochaine session sur le dossier veille : thème large (pas de vérification par veille), convention de dossier `fonds/`, format ODP/MD à deux rôles, pièges déjà rencontrés (duplication, gitlink imbriqué, `git add -A` qui re-suit un dossier exclu) — voir `docs/jury/veille/CLAUDE.md`

## 2026-07-21 — Claude Code (Part 9)

- **Dossier `docs/jury/`** — méta-documentation pour la certification — voir `docs/jury/`
  - `README.md` : index compétences C1-C21 → preuves, avec état honnête (✅/🟡/⬜) et mention explicite de ce qui manque par ligne. Deux règles posées : on pointe vers les preuves sans les recopier, et on n'écrit ici que ce qui n'a aucun autre domicile
  - `veille/` (`sources.md`, `journal.md`) : format posé, **aucune entrée inventée**. C6 exige une régularité (min. 1h/semaine) — seule exigence du référentiel impossible à produire rétroactivement
  - `decisions/` : un fichier par décision, avec options écartées. Format en clair (pas d'étiquette « ADR »). Le `README.md` indexe les décisions **antérieures** vers les documents qui les justifient déjà (`conception.md`, `bdd.md`, `1_prompt_engineering.md`...) plutôt que de les réécrire — une reconstruction tardive serait moins fidèle que l'original
  - Deux décisions documentées : périmètre MLOps de l'ingestion (7 options envisagées, 6 écartées) et choix du modèle d'enrichissement

- **`TODO.md` créé à la racine** — point d'entrée transverse (spec E, décisions en attente, veille C6, livrables de certification manquants). Ne duplique pas `TODO_PIPELINE_INGESTION.md`, qui reste la référence du pipeline

- **`conception/annexes/F_choix_llm.md` récupéré** — benchmark Azure AI Foundry (16 820 appels), argumentation C7, référencé deux fois par `conception.md` mais absent du dépôt (il était à la corbeille). Ses renvois vers `annexes/F1`-`F4` ne correspondent pas encore à l'arborescence réelle (`annexes/benchmark/`)

- **Dérive de spec détectée et corrigée dans `conception/conception.md`** — voir `conception/conception.md`, `docs/jury/decisions/2026-07-21-modele-enrichissement-latence.md`
  - Le tableau de stack annonçait `gpt-5.4-nano` pour l'enrichissement alors que le code, le `.env.example` et le `CLAUDE.md` utilisent **Kimi K2.6** — avec en plus une ligne dupliquée à l'identique, et l'exemple de configuration `ENRICHMENT_LLM = "gpt54_nano"` resté en place
  - **Origine du changement, jamais écrite jusqu'ici** : gpt-5.4-nano avait été retenu pour sa faible latence, critère sans objet sur un traitement par lot sans utilisateur en attente. Kimi K2.6 l'emporte sur la fenêtre de contexte (256K, utile à la ré-ingestion post-MVP) et la fiabilité du JSON
  - **Détectée en construisant l'index compétences → preuves** : vérifier qu'une preuve existe réellement plutôt que la supposer a fait apparaître la contradiction. C'est le *spec drift* identifié comme risque principal dans `CLAUDE.md`, confirmé en conditions réelles sur un document central
  - Constaté au passage : `conception.md` renvoie deux fois à `annexes/F_choix_llm.md`, absent du dépôt. Le matériau du benchmark existe (`annexes/benchmark/`), sa synthèse rédigée non — contenu exploitable pour C7 actuellement invisible dans le Git

## 2026-07-21 — Claude Code (Part 8)

- **Spec « Provenance des données et manifeste d'ingestion »** (conception seule, aucune implémentation) — voir `conception/2_ingestion/E_provenance_manifeste.md`
  - **Problème identifié** : une ligne de `regle` ne sait pas d'où elle vient. Aucun horodatage sur la table ; version de prompt absente de la donnée *et* du fichier `enrich_rule.md` (seulement en prose dans `1_prompt_engineering.md`) ; `llm_provider` est une chaîne en dur (`llm_client.py:129-130`, dupliquée en défaut Pydantic `schema.py:62-63`) — donc une valeur **affirmée par le code**, pas observée : elle continuerait d'annoncer `kimi-k2.6` après un changement de déploiement dans `.env`
  - **Principe directeur retenu** : une seule autorité par valeur (le code lit, ne recopie pas) et une seule responsabilité par couche — `.env` = annuaire + secrets, `manifest.yml` = décisions courantes, git = historique des décisions, colonnes de provenance = quelle décision a produit quelle ligne. Corollaire : le manifeste ne conserve **aucun** historique interne (ce serait réimplémenter git en moins bien)
  - **Décisions** : `.env` restructuré en inventaire par modèle (`AZURE_MODEL_KIMI`) et non plus par rôle ; `app/ingestion/manifest.yml` porte l'affectation rôle → modèle avec résolution explicite (`env_var:`) ; version du prompt en frontmatter de `enrich_rule.md`, format entier simple ; 4 colonnes de provenance nullables sur `regle` (`NULL` = produit avant instrumentation, donc signal de bug après le chantier 3) ; `llm_provider` **renommée** `llm_model` (elle contenait déjà un modèle sous un nom de fournisseur) ; table `ingestion_run` écartée (coût/durée déjà en prose, script lancé de façon anecdotique)
  - **Règle de nommage des colonnes formalisée** : métier en français, technique en anglais (*langage omniprésent* du DDD — le domaine Opquast **est** francophone). Le schéma l'appliquait déjà sans l'avoir écrite (`embedding`, `llm_provider` en anglais parmi des colonnes françaises). Explique pourquoi `audit.date_creation` et `regle.created_at` coexistent sans incohérence
  - **Limite assumée et documentée** : `kimi-k2.6` reste une **déclaration**, pas une observation — un déploiement Azure peut être repointé depuis la console sans qu'aucun fichier versionné ne change. À vérifier à l'implémentation si la réponse de l'API expose le modèle réellement utilisé
  - **Reste ouvert** : sort des `KIMI_PRICE_*` (relevés de tarifs Azure réels en cours de collecte)
  - Se place **entre le chantier 1 (fait) et le chantier 2 (prompt V4)**, et doit être livrée avant le chantier 3 (ré-ingestion réelle) — sinon la provenance nécessite une migration *et* une seconde ré-ingestion facturée

## 2026-07-19 — Claude Code (Part 7)

- **Chantier 1 — Correction du scraping + champ `contexte`** — voir `conception/2_ingestion/D_chantier1_scraping_contexte.md`, `app/ingestion/acquisition.py`, `app/ingestion/schema.py`, `app/ingestion/llm_client.py`, `app/ingestion/prompts/enrich_rule.md`, `app/ingestion/stockage.py`, `app/models/referentiel.py`, `app/migration/versions/0006-0007`
  - Spec validée (méthodo spec-driven, brainstorming + implementation plan via subagent-driven-development), exécutée tâche par tâche avec revue systématique
  - **`scrape_rule()` réécrite** : extraction bornée à `div.c-rule-content` (le pied de page Opquast en est structurellement exclu → plus besoin de sentinelle mot-clé), ciblage par classes émoji stables (`c-emoji-tools`, `c-emoji-check`). Corrige les 2 bugs identifiés en Part 6 (footer parasite, `<ul>` ignoré)
  - **2 variantes de structure supplémentaires découvertes en scrapant les 245 vraies règles** (non couvertes par les tests mockés initiaux) : contenu en nœud texte direct sans `<p>` (règle 14), contenu enveloppé dans `<div>` plutôt que `<p>` (règle 27). `extract_content_after()` généralisée pour traiter tout frère non-`<ul>`/`<h2>` comme un bloc de texte via `get_text()`
  - **Nouveau champ `contexte`** (texte explicatif, `c-rule-hero__subtitle`) : traverse tout le pipeline — scraping → schémas Pydantic (`RuleAcquisition`, `RuleAggregation`, hérité par `EnrichedRule`) → prompt d'enrichissement LLM (`{contexte}`, fallback `"(non disponible)"` si absent) → colonne BDD (`TEXT NULL`, migration 0006) → stockage (`upsert_rule`, `load_enriched_rules_from_db`)
  - **Recalibrage `solution`/`controle`** (migration 0007) : `VARCHAR(1024)` → `VARCHAR(2048)`. Le scraping corrigé capture désormais le contenu complet (non tronqué) ; les vraies données dépassent l'ancienne limite calibrée sur des données elles-mêmes tronquées par les bugs (max observé sur 245 règles réelles : solution 1880, controle 1156)
  - **Validation pré-LLM** : dump JSON des 245 règles acquises dans `tmp/rules_acquises.json` (scraping + stockage réels, enrichissement bouchonné) — scraping et stockage complets validés sans coût LLM avant de poursuivre vers la ré-ingestion réelle
  - **Revue finale whole-branch** (10 commits) : aucun Critical/Important, 2 findings mineurs corrigés (incohérence des numéros de règles cités en exemple dans une docstring ; `solution`/`controle` passés de `VARCHAR(2048)` à `TEXT`, migration 0008, pour aligner sur `contexte` et éviter un 3e recalibrage si Opquast allonge son contenu — Postgres stocke `TEXT`/`VARCHAR(n)` de façon identique, la limite n'apportait aucun gain)

## 2026-07-19 — Claude Code (Part 6)

- **Ingestion complète des 245 règles + analyse de la classification LLM** — voir `docs/problemes_rencontres/recommandations_v4.md`, `scripts/ingestion.py`, `app/ingestion/stockage.py`, `docs/schemas/ingestion_activite.drawio`, `conception/2_ingestion/C_pipeline_ingestion.drawio`
  - Ingestion réelle des 245 règles Opquast menée à terme (enrichissement Kimi K2.6, prompt V3) : ~1,2 M tokens, coût ~3 €. Distribution `strategie_analyse` : statique 46 %, playwright 42 %, vision 8 %, manuel 4 %
  - **Hook `--resume`** ajouté à `scripts/ingestion.py` + `load_enriched_rules_from_db()` dans `app/ingestion/stockage.py` : permet de reprendre le pipeline depuis les règles déjà enrichies en BDD (saute étapes 1-4, évite de refaire les appels LLM coûteux) — schémas d'activité mis à jour en conséquence
  - **Revue manuelle règle par règle** de la classification (démarche buffer `ob_start`/`ob_get_clean`) → document `docs/problemes_rencontres/recommandations_v4.md` (feuille de recommandations priorisées pour la V4)
  - **2 bugs de scraping critiques identifiés** (`scrape_rule()`) affectant > 60 règles (> 25 %) : (1) footer légal Opquast capturé à la place de solution/controle sur 43 règles ; (2) contenu en `<ul>` ignoré (seul le `<p>` d'intro pris) sur ~34 règles. Cause commune : `find_next("p")` non borné. Solution identifiée : cibler `<div class="c-rule-content">` + classes `c-emoji-tools`/`c-emoji-check` + capturer p+ul. Correction et ré-ingestion à venir
  - Pistes prompt V4 : stratégies composites (`vision+statique`, `playwright+vision`), critère « observation hors page web = manuel », factuel > spéculatif, acquisition du texte explicatif (`c-rule-hero__subtitle`) pour améliorer le contexte LLM
  - Déplacement `conception/3_enrichissement/prompt_engineering.md` → `docs/problemes_rencontres/prompt_engineering.md` (regroupement des docs de problèmes rencontrés)
  - `.gitignore` : ajout de `tmp/` (matériel de travail) et `.*.drawio.dtmp` (fichiers temporaires draw.io)

## 2026-07-19 — Claude Code (Part 5)

- **Schéma BDD — Calibrage des colonnes textuelles (VARCHAR vs TEXT)** — voir `app/models/referentiel.py`, `app/migration/versions/0002-0005`, `scripts/ingestion_test.py`, `docs/problemes_rencontres/schema_text_columns.md`
  - **Problème identifié** : première ingestion complète échoue à règle 154 → `objectif` dépasse `VARCHAR(256)`, puis à règle 166 → `solution` dépasse `VARCHAR(512)`
  - **Root cause** : colonnes `solution` et `controle` scrappées depuis le site Opquast (contenu HTML brut) peuvent dépasser les limites estimées ; `objectif` vient de l'API mais bien plus long que prévu
  - **Stratégie** : conversion temporaire en `TEXT` (migrations 0002-0004), puis script de test `ingestion_test.py` (bouchons LLM, pas d'appels coûteux) peuple la BD avec 245 règles réelles et révèle les max
  - **Mesure des données réelles** : `intitule` MAX 167 / `solution` MAX 569 / `controle` MAX 573 / `objectif` MAX 359
  - **Recalibrage final** (migration 0005) :
    - `intitule` : `VARCHAR(255)` (marge 88 chars)
    - `solution` : `VARCHAR(1024)` (marge 455 chars)
    - `controle` : `VARCHAR(1024)` (marge 451 chars)
    - `objectif` : `VARCHAR(512)` (marge 153 chars)
    - `strategie_analyse`, `strategie_source` : `VARCHAR(32)` (énumérées, court)
    - Conservé en `TEXT` : `strategie_justification`, `guide_analyse` (enrichissement LLM, imprévisible)
  - **Validation** : 245 règles stockées sans erreur avec le schéma final
  - **Documentation** : document `schema_text_columns.md` trace la démarche (observation → hypothèse → test → mesure → décision) pour valeur pédagogique auprès du jury
  - **Économie** : script de test évite ~240 appels LLM supplémentaires (coûteux en tokens)

## 2026-07-19 — Claude Code (Part 4)

- **Correctif — Restauration de `theme` + `tags` optionnels (pipeline d'ingestion)** — voir `app/ingestion/schema.py`, `app/ingestion/acquisition.py`, `app/migration/versions/0001_schema_initial.py`, `app/models/referentiel.py`, `app/ingestion/stockage.py`, `app/ingestion/llm_client.py`, et fichiers de tests associés
  - Corrige la suppression erronée de `theme`/`theme_id` faite en Part 3 (le MCD prévoyait bien une relation 1-N via `regle.theme_id`, pas une relation many-to-many comme supposé à tort) — confirmé par les données réelles de l'API Opquast : les 245 règles ont chacune exactement une valeur `Thématiques`
  - Table `theme` + FK `regle.theme_id` (NOT NULL) restaurées dans la migration 0001 et dans `app/models/referentiel.py`
  - `RuleAcquisition`/`RuleAggregation` (Pydantic) : ajout du champ `theme: str` (non-vide), mappé depuis `metadata.Thématiques[0]` en acquisition
  - `tags` rendu optionnel (liste vide acceptée) côté validation Pydantic — confirmé par les données réelles : 64 des 245 règles Opquast n'ont aucun tag
  - `upsert_rule()` (stockage) résout `theme` via `get_or_create()` et assigne `regle.theme_id` directement (FK scalaire, pas de table d'association)
  - Tests unitaires mis à jour (fixtures acquisition/aggregation/enrichment avec `theme=...`) + nouveaux tests (tags vides acceptés, validation theme) ; tests de migration mis à jour (14 tables attendues)
  - Correctif production dans `llm_client.py` : `enrich_single_rule()` ne passait pas `theme` à `EnrichedRule` — aurait levé une `ValidationError` en production, découvert en mettant à jour les tests d'enrichissement
  - Vérification finale : 25 tests unitaires + 10 tests migration, tous verts ; `ruff check` clean sur `app/`, `tests/`, `scripts/`

## 2026-07-19 — Claude Code (Part 3)

- **Étape 4 — Stockage (pipeline d'ingestion)** — voir `app/ingestion/stockage.py`, `scripts/ingestion.py`
  - `get_or_create()` : fonction générique idempotente pour Objectif/Phase/Tag
  - `upsert_rule()` : upsert Regle via numero (UPDATE complet si présent, INSERT sinon), synchronise les associations many-to-many (delete + recrée)
  - `store_rules()` : orchestration de toute la collection EnrichedRules dans une transaction unique, fail-fast avec rollback complet
  - `embedding` reste NULL à cette étape (écrit plus tard, Étape 7)
  - `scripts/ingestion.py` : première version, orchestre Étapes 1-4, fail-fast avec log explicite par étape et code de sortie non-nul
  - Pas de suite pytest pour cette étape — validation par exécution réelle du script (3 règles Opquast réelles, appels LLM réels) + inspection directe des tables PostgreSQL, y compris test d'idempotence (ré-exécution → pas de doublons)
  - Correctif préalable : suppression de `theme`/`theme_id` du MCD (erreur de conception, relation déjà couverte par `tag`) — migration 0001 corrigée directement (jamais mergée dans `main`)
  - Bug corrigé en cours de validation : `LLMClient` utilisait `AzureChatOpenAI` (exige `api_version`, format d'URL Azure classique incompatible avec l'endpoint `/openai/v1` unifié) — remplacé par `ChatOpenAI` (client OpenAI standard, conforme à l'exemple du portail Azure AI Foundry)

## 2026-07-19 — Claude Code (Part 2)

- **Étape 3 — Enrichissement (pipeline d'ingestion)** — voir `app/ingestion/enrichment.py`, `app/ingestion/llm_client.py`, `tests/unit/ingestion/test_enrichment.py`
  - Classe Pydantic `EnrichedRule` (schema.py) : extension de `RuleAggregation` avec champs enrichissement
  - Classe `EnrichedRules` (aggregation.py) : collection non-vide d'`EnrichedRule`
  - Classe `LLMClient` : client LangChain + Azure Kimi K2.6
    - Chargement prompt depuis `prompts/enrich_rule.md` (few-shot), remplacement manuel de placeholders (pas de `PromptTemplate.format()` — le prompt contient des accolades JSON littérales dans les exemples)
    - Retry logic : 3 tentatives, backoff exponentiel 2s/4s via `tenacity` (`wait_exponential(multiplier=2, min=2, max=8)`)
    - `JsonOutputParser` (langchain_core) pour parsing réponse LLM stricte
  - Fonction `enrich_rules()` : orchestration Rules → EnrichedRules
  - Logging : erreur critique (3 timeouts), synthèse succès
  - Tests unitaires : 6 tests (réussite, retry, échec après 3 tentatives, transformation collection, logging erreur/succès)
  - Dépendances : langchain>=0.1.0 (résolu 1.3.14), langchain-openai>=0.1.0, tenacity>=8.2.0
  - Convention : code anglais, docs/comments français
  - Renommage `agregation.py` → `aggregation.py` (noms de fichiers en anglais, cohérent avec le code)
  - Total : 22 tests unitaires ingestion passants (3 acquisition + 13 aggregation + 6 enrichment)

## 2026-07-19 — Claude Code

- **Étape 2 — Agrégation (pipeline d'ingestion)** — voir `app/ingestion/aggregation.py`, `tests/unit/ingestion/test_aggregation.py`
  - Classe Pydantic `RuleAggregation` (schema.py) : validation stricte (strings/listes non-vides)
  - Classe `Rules` : collection non-vide de règles agrégées
  - Fonction `aggregate_rules()` : transforme dicts acquis en Rules validée
  - Fail-fast sur validation (lève ValueError + log erreur)
  - Log synthèse : "X règles validées" si succès
  - Convention : code anglais (Rule, Rules, RuleAggregation), docs/comments français
  - Tests unitaires : 13 tests (Regle création, validation champs, collection, agrégation)
  - Propriété `regles` : alias rétrocompatibilité pour accès à la liste

---

## 2026-07-18 — Claude Code

- **Étape 1 — Acquisition (pipeline d'ingestion)** — voir `app/ingestion/acquisition.py`, `tests/unit/ingestion/test_acquisition.py`
  - `build_rule_url(slug)` : construction URL scraping
  - `fetch_api()` : récupération API Opquast (245 règles)
  - `scrape_rule(slug)` : scraping BeautifulSoup (solution + controle)
  - `acquire_rules()` : orchestration fetch + scrape par règle
  - Exceptions levées si données manquantes (fail-fast)
  - Logging centralisé dans `app/logging_config.py` (fichier uniquement)
  - Tests unitaires avec mocks (`@patch` requests.get)
  - Dépendance `beautifulsoup4` ajoutée à `pyproject.toml`
  - Variables `.env` : `OPQUAST_API_BASE_URL`, `OPQUAST_SITE_BASE_URL` — voir `.env.example`, `conception/2_ingestion/ingestion.md`
- Création de `app/ingestion/schema.py` : modèle Pydantic `RuleAcquisition` (id, number, intitule, objectifs, tags, phases, slug, solution, controle)
- Structure de tests : `tests/unit/ingestion/`, `tests/integration/ingestion/`, `tests/migration/` — voir `tests/conftest.py` pour fixtures partagées
- TODO : `TODO_PIPELINE_INGESTION.md` pour tracker les étapes restantes (agrégation, enrichissement, stockage, chunking, embedding, indexation, orchestration)

---

## 2026-07-18 — OpenCode (Part 2)

- Initialisation du dépôt Git — voir `.git/`
- Ajout du `.gitignore` (protection `.env`, Python, logs, éditeurs) — voir `.gitignore`
- Ajout du `.env.example` (variables PostgreSQL, valeurs vides) — voir `.env.example`
- Création du `.env` local (non versionné, valeurs de dev) — voir `.env`
- Ajout du `docker-compose.yml` : service `postgres` (pgvector/pgvector:pg17, port 8832, réseau `qualicheck`, volume `postgres_data`) — voir `docker-compose.yml`
- Ajout des docs de conception de la brique Docker/BDD — voir `docs/superpowers/specs/2026-07-18-docker-bdd-design.md`, `docs/superpowers/plans/2026-07-18-docker-bdd.md`
- Nommage explicite du conteneur PostgreSQL (`qualicheck-postgres`) — voir `docker-compose.yml`
- Ajout du `README.md` — voir `README.md`
- Ajout des fichiers de conception dans la branche feature (docs, annexes, maquettes, CLAUDE.md) — voir `conception/`, `app/CLAUDE.md`, `scripts/CLAUDE.md`
- Exclusion des fichiers de backup draw.io du versionnement — voir `.gitignore`
- Ajout de la règle "CHANGELOG mis à jour à chaque commit" dans `CLAUDE.md` — voir `CLAUDE.md`
- Ajout de la règle "pas de commit/push sans validation explicite" dans `CLAUDE.md` — voir `CLAUDE.md`

## 2026-07-18 — OpenCode

- Ajout des dépendances Python (sqlalchemy, alembic, psycopg2-binary, pgvector, python-dotenv, pytest, ruff) — voir `pyproject.toml`, `uv.lock`
- Création des modèles SQLAlchemy : `app/models/base.py`, `app/models/referentiel.py`, `app/models/metier.py`
- Configuration Alembic : `app/migration/alembic.ini`, `app/migration/env.py`
- Première migration Alembic (schéma complet + extension pgvector + index HNSW) — voir `app/migration/versions/0001_schema_initial.py`
- Point d'entrée CLI pour les migrations — voir `scripts/migration.py`
- Tests d'intégration de la migration (10 tests) — voir `tests/test_migration.py`
- Makefile : cibles `up`, `down`, `migration`, `downgrade`, `test` — voir `Makefile`
- Diagramme de flux de la migration — voir `docs/schemas/migration_flux.drawio`
- Specs et plan de la brique migration — voir `docs/superpowers/specs/2026-07-18-migration-design.md`, `docs/superpowers/plans/2026-07-18-migration.md`
- CI GitHub Actions : lint ruff + migration + tests sur push (hors main) — voir `.github/workflows/ci.yml`
- Configuration Ruff dans `pyproject.toml` (exclusion `conception/`)

---
