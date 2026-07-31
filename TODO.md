# TODO général — QualiCheck

Point d'entrée transverse. Le détail du pipeline d'ingestion (étapes 1 à 7, chantiers)
reste dans `TODO_PIPELINE_INGESTION.md`, qui n'est pas dupliqué ici.

Légende : `[ ]` à faire · `[x]` fait · **Qui** : `D` = David, `A` = assistant

## Prochain gros morceau

- [x] **Spec E implémentée** (provenance + manifeste) — `A` (2026-07-25)
  - Plan `docs/superpowers/plans/2026-07-25-provenance-manifeste-implementation.md`,
    exécuté tâche par tâche, mergé sur `feature`. Les 8 critères de validation de
    la spec sont vérifiés — détail dans `CHANGELOG.md`
  - Débloque le chantier 2 (prompt V4) et le chantier 3 (ré-ingestion réelle)

- [x] **Prompt V5 puis V6** — recommandations exploitées, prompt bumpé en
  `version: 6` (`app/ingestion/prompts/enrich_rule.md`) ; 11 règles à revoir
  corrigées via `make enrich-again` sur la base des anticipations de l'audit
  V6 (0,1610 € vs ~4,29 € pour une ré-ingestion complète des 245 règles) — `D`/`A`
  (2026-07-26)
  - Jeu de données déjà propre après cette correction ciblée : une
    ré-ingestion complète sur le prompt V6 n'est **pas nécessaire dans
    l'immédiat** — reportée, à reprendre si un futur audit révèle un besoin
    plus large que les 11 règles déjà traitées

- [x] **Étapes 5-7 (chunking, embedding, indexation)** — `make embed-rules`
  exécuté pour de vrai : 245/245 règles vectorisées (modèle du rôle `embedding`
  du manifest, 1536 dimensions), 0,0016 € — `A` (2026-07-26)

- [x] **Jeu de règles d'acceptance RAG (JSONL)** — `D`/`A` (2026-07-26)
  - Spec `docs/superpowers/specs/2026-07-26-rag-acceptance-jsonl-design.md`,
    plan `docs/superpowers/plans/2026-07-26-rag-acceptance-jsonl-implementation.md`
  - `tests/acceptance/rag_acceptance.jsonl` : 17 cas `{question,
    numero_regle_attendue}` (les 2 vérifiés manuellement + 15 nouveaux,
    validés par David) ; `app/ingestion/rag_acceptance.py` (logique testée
    unitairement) ; `scripts/check_rag_acceptance.py` + `make
    rag-acceptance` (top_n/taux_reussite_minimum dans `manifest.yml`)
  - Suite volontairement hors CI (coût réel à chaque run)
  - **`make rag-acceptance` lancé pour de vrai par David (2026-07-26)** :
    17/17 cas passent, taux de réussite 100% (seuil 80%), 274 tokens, coût
    négligeable

## Décisions en attente

- [x] **Découpage des responsabilités `api_regles` / `api_audit` / `api_business`
  — résolu (2026-07-28)** : une seule base de données et un seul
  `app/models/`, mais **deux services FastAPI distincts** qui l'attaquent
  chacun directement — `app/api_regles` (référentiel + revue, renommé depuis
  `api_data` et implémenté le 2026-07-28) et `app/api_audit` (tables métier de
  l'audit, à concevoir avec la spec US1). `app/api_business` reste l'étage
  d'orchestration, sans jamais toucher Postgres. Raisonnement complet et
  options écartées : `docs/jury/decisions/2026-07-28-separation-api-regles-api-audit.md` — `D`
  - Reste ouvert, hors périmètre de cette décision : la frontière CRUD
    (`api_audit`) vs orchestration (`api_business`) — ex. « créer un audit »
    est-il un simple CRUD ou déclenche-t-il déjà une action métier (crawl) ?
    À trancher avec la spec US1, pas avant.
- [ ] **Champ `contexte` vide en base** — `NULL` sur les 245 règles alors que le
  correctif de code existe (migration 0006 et correction du round-trip du
  2026-07-26) : aucune ingestion réelle ne l'a alimenté depuis. L'API données
  l'expose donc systématiquement vide. À arbitrer : ré-ingestion ciblée du seul
  champ `contexte` (scraping, sans appel LLM) ou statu quo — `D`
- [ ] **Licence du code et des étages applicatif/présentation** — non arrêtée.
  L'étage données est sous licence libre (CC BY-SA 4.0 s'imposant au jeu de
  données par partage à l'identique — décision actée
  `docs/jury/decisions/2026-07-26-lecture-ouverte-api-regles.md`), mais CC BY-SA
  porte sur le contenu, pas sur le code : la séparation n-tiers laisse donc le
  choix libre pour `app/api_business/`, `app/api_audit/` et le front — `D`
- [x] **Valeurs `KIMI_PRICE_*`** — reconstruites depuis la facture réelle du 19/07
  (9,13 €) : 0,8008 / 3,3875 €/1M — `A`
- [x] **Emplacement `KIMI_PRICE_*` — résolu (2026-07-25) : `app/ingestion/manifest.yml`**,
  pas `.env`. Ce sont des données de référence, pas des secrets ; le manifeste
  donne un historique gratuit via git, `.env` non versionné ne le donnait pas
  (spec E §6) — `D`
- [x] **`ia_souverain/synthese.md` — question résolue par la centralisation
  de la veille** — le fichier vit désormais dans le dépôt
  (`docs/jury/veille/fonds/ia_souverain/synthese.md`), plus besoin de choisir
  entre copier et pointer vers l'extérieur — `A` (2026-07-23)
  - Reste ouvert si souhaité : `F_choix_llm.md` cite ce fichier comme annexe
    (argumentation souveraineté, Bayart, Cloud Act) — copier spécifiquement
    dans `conception/annexes/` en plus, ou le renvoi vers `fonds/` suffit ?

## Documentation

- [x] **Incohérence US1/US2 de `conception.md` — résolue (2026-07-26)** — la
  partie dialogue/validation des constats (§"US1 — Dialogue et validation")
  est bien **US1** (SQL déterministe, pas de RAG) : c'est ce que disaient déjà
  le titre de section, le corps du texte et le tableau comparatif. Seule la
  légende de l'image (`![Flux de dialogue — US2](...)`) contredisait le
  reste — corrigée en `US1` — `D`/`A`

- [ ] **`G_user_stories_qualicheck.drawio` — contenu réaligné (2026-07-29), export PNG toujours à refaire** —
  la source décrivait encore l'ancien découpage (US1 = génération des constats,
  US2 = dialogue/validation), périmé depuis que `conception.md` a fusionné
  génération + dialogue/validation dans US1 et redéfini US2 comme la question
  libre sur une page (RAG sémantique pur). Carte US1 et critère d'acceptation
  mis à jour, carte US2 réécrite. Les encarts « Scénario nominal » retirés
  (plus de place laissée aux 3 cartes, passées en pleine largeur ; le détail
  des scénarios reste dans `conception.md`) — `A` (2026-07-29). Reste à
  relire visuellement dans draw.io (espacement, retouche manuelle habituelle)
  puis exporter en `.png` — `D`
- [ ] **Liens de `F_choix_llm.md` vers le benchmark** — `A`
  - Le document attend `annexes/F1_FOUNDRY_NOTES.md`, `F2_FOUNDRY_SI_NOTES.md`,
    `F3_benchmark.py`, `F4_analyse_models_azure.pdf`
  - Les fichiers sont sous `annexes/benchmark/` sans préfixes
  - Soit renommer les fichiers, soit corriger les liens — les préfixes `F1`-`F4`
    suggèrent que le renommage était l'intention d'origine
- [x] **`C_pipeline_ingestion.drawio` divergent — résolu** — n'était pas un
  doublon périmé mais un couple cible/réel mal rangé : la version avec le hook
  `--resume` (découvert pratique en implémentant, non prévu en conception) a été
  déplacée vers `docs/schemas/C_pipeline_ingestion_reel.drawio`. La version sans
  hook reste la cible dans `conception/annexes/`. `ingestion.md` renvoie
  désormais explicitement vers les deux — `A` (2026-07-23)
- [x] **`B_MCD_qualicheck.drawio` — flèche incorrecte — résolue** — `endArrow=
  block;endFill=1` retiré (seule ligne du fichier à en porter un, tout le reste
  du MCD est sans flèche). Le doublon dans `conception/2_ingestion/` — identique
  avant correctif, aurait divergé sinon — a été supprimé, non référencé par aucun
  document — `A` (2026-07-23)
- [x] **Références `annexes/*.jpg` → `.png`** — `conception.md` et
  `F_choix_llm.md` passés en `.png` (`sed 's/jpg/png/g'`, 2026-07-23), cohérent
  avec `markdown-pandoc` (« format PNG ou SVG recommandé »). Doublon
  `conception/choix_llm.md` (identique à `annexes/F_choix_llm.md`, jamais
  référencé) supprimé au passage — `A`
- [ ] **9 images `annexes/*.png` référencées par `conception.md`, 8 encore
  manquantes** — `G_user_stories_qualicheck.png` était la seule à exister
  réellement, supprimée le 2026-07-25 (voir entrée dédiée ci-dessus).
  `J_personas_qualicheck.png` **exporté le 2026-07-29** (CLI `drawio
  --export`, schéma relu au préalable), satisfait le renvoi Annexe J de
  `conception.md`. Restent :
  `B_MCD_qualicheck.png`, `C_pipeline_ingestion.png`, `D1/D2/D3_...png`,
  `D_pipeline_audit.png`, `E_pipeline_dialogue.png`,
  `G_user_stories_qualicheck.png`, `I_feedback_loop.png`. L'export drawio →
  image n'a jamais suivi la création des sources `.drawio` — `conception.md`
  ne peut toujours pas se compiler en PDF sans schémas cassés.
  `E_pipeline_dialogue.png` ne correspond même pas au nom du fichier source
  réel (`E_pipeline_question_libre.drawio`) — nom qui a aussi dérivé — `D`
  - Export manuel, volontairement pas automatisé : David veut relire chaque
    schéma avant de le figer en image (même logique que la flèche incorrecte
    trouvée dans B_MCD — un export automatique aurait masqué l'erreur).
    Exception faite pour `J_personas_qualicheck.png` : schéma déjà relu par
    David, export explicitement délégué
- [x] **`G_user_stories_qualicheck.drawio` récupéré** — source + export `.jpg`
  copiés depuis la corbeille vers `conception/annexes/`, nom déjà conforme à ce
  qu'attendait `conception.md` — `A` (2026-07-23)
- [x] **`H_architecture_globale.drawio` — laissé en l'état, décision prise** —
  trop tôt pour figer cette annexe : la stack backend/frontend n'est pas encore
  construite (US1/US2 ni conçus ni implémentés), donc tout schéma d'architecture
  documenterait une intention non stabilisée plutôt qu'un état réel. Reste à la
  corbeille jusqu'à ce que l'architecture soit assez avancée pour valoir la peine
  d'être figée. Note au passage : le brouillon existant confond le modèle
  d'enrichissement et le modèle d'audit dans sa case « LLM Audit » — à
  vérifier si le brouillon est repris un jour — `D`
- [x] **`ingestion_activite_reel.drawio` et `migration_flux_reel.drawio`
  renommés** — aucun des deux n'a de pendant cible écrit dans `conception/`
  (contrairement à `C_pipeline_ingestion`), mais tous deux documentent un
  comportement **constaté** (déroulé réel de `make ingestion`, exécution
  effective de `scripts/migration.py`) plutôt qu'une intention. Convention du
  skill `schemas-drawio` précisée en conséquence : le suffixe dépend de la
  nature du contenu, pas de l'existence d'un fichier jumeau — `A` (2026-07-23)
- [ ] Ajouter **Langfuse** au `CLAUDE.md` quand US1/US2 seront conçus — `D`
  - Décidé : monitorage sur US1/US2, pas sur l'ingestion

## Veille (C6)

Le fonds existe et couvre le volet réglementaire. Ne manque que la forme.

- [x] **17 flux RSS listés** (export OPML 2026-07-22) → `docs/jury/veille/sources.md` — `D`
- [ ] **Fréquence de lecture** par flux ou par dossier — `D`
- [ ] **Étoffer les flux FreshRSS** — outil principal ; RSS écrit privilégié pour
  des raisons de niveau d'anglais (oral B1, cf. `sources.md`) — `D`
- [ ] **Créer un compte YouTube dédié à la veille**, séparé du personnel, puis
  étoffer les abonnements IA / dev agentique — `D`
- [ ] **Lister les comptes LinkedIn suivis** — veille professionnelle
  spécifiquement, distincte du RSS technique — `D`
- [ ] **Évaluer la mise en place d'une newsletter** en complément du dispositif — `D`
- [ ] **Trier `docs/jury/veille/candidats-sources.md`** — 5 flux RSS vérifiés,
  3 chaînes YouTube, 5 newsletters (avec distinction RSS/email uniquement) sur le
  thème développement durable x IA. Ajouter les candidats retenus à `sources.md` — `D`
- [ ] **Étoffer le dossier Réglementation** (2 flux/17, le plus mince alors que le
  thème assigné — développement durable x IA — est fortement réglementaire) —
  RGAA/accessibilité notamment absent alors que central à QualiCheck — `D`
- [ ] Ranger les 3 flux **« Sans catégorie »** (dont 2 liés directement au projet :
  LangChain, Azure Foundry) — `D`
- [x] **Démarrer les entrées datées** de `docs/jury/veille/journal.md` — 3 entrées
  réelles ajoutées (2026-05-13 x2, 2026-07-15), antérieures ou concomitantes à la
  création du dossier `jury/` — `D`
  - Seule exigence du référentiel qu'on ne peut pas produire rétroactivement
- [x] **Écart de thème du rapport cybersécurité (13 mai)** — résolu : jour de
  lancement de Mini Manifest, antérieur à l'attribution du thème — `D`
- [x] **Écart de date FreshRSS** — résolu, 13 mai fait foi (nom de fichier erroné) — `D`
- [x] **Écart de thème du PPTX métiers du web — non pertinent** — le thème
  assigné (développement durable x IA) est large par construction ; pas besoin
  de vérifier le rattachement veille par veille — `D`
- [x] **MD généré** pour `veille-metiers-web-ia-202.odp` — reconstruit depuis
  le texte des 13 diapositives (tableaux de compétences inclus) :
  `metiers_web_ia_2026-07-15/final/script.md`. À relire — les couleurs/légendes
  visuelles des grilles n'ont pas pu être extraites, seul le texte des tableaux — `A`
  (2026-07-23)
- [x] **Format live converti PPTX → ODP** — conforme à la convention, original
  `.pptx` supprimé (un seul exemplaire) — `A` (2026-07-23)
- [ ] Confirmer que l'emplacement `final/` pour cette veille est bien
  définitif — `D`
- [x] **Veille centralisée dans le dépôt** — `formation_dev_ia_agentique/veille/`
  (5 dossiers) et les 3 fichiers de `~/Téléchargements` déplacés (pas copiés) vers
  `docs/jury/veille/fonds/`, avec une période approximative par dossier dans
  `README.md` (basée sur les dates de modification au moment du déplacement) — `A`
  (2026-07-23)
- [x] **Exploration complète du fonds de veille (forme + fond)** — `A` (2026-07-23) :
  - `whereisbrian.jpeg` : déjà disparu, résolu sans intervention
  - `.vscode/settings.json` (`britanica_openai_le_pillage_savoir_.../final/`) : supprimé
  - `dev_durable_2026-06-13/` : matériaux de travail déplacés de `final/` vers
    `working/` (`.kdenlive`, `videos/`, `RF-PIA-1.txt`) ; triple redondance
    aplatie (zip redondant supprimé, doublons stricts retirés, sous-dossier
    `veille_ia_environnement/` remonté et supprimé — un seul exemplaire de
    chaque fichier désormais)
  - `2_3_ai_act_application_droit_francais.md` : reformulé en style déclaratif
    (était à la première personne, façon sortie brute de conversation IA)
  - `3_evolution_du_savoir.md` : accents français restaurés (texte complet, UTF-8
    valide mais entièrement dépourvu d'accents)
  - `2_gattaca.txt` : phrase redondante retirée
  - 4 séparateurs de tableau compacts passés au style espacé (convention
    `markdown-pandoc`)
  - Note : les deux `.odp`/`.pdf` quasi-identiques de `dev_durable` n'étaient pas
    des versions divergentes à trancher — mêmes documents, exports différents
    (confirmé par comparaison de pages/contenu) — `D`
- [x] **Format retenu pour les futures veilles** (Valentin Haüy / AcceDe) — `D`
  - Double format systématique : ODP + notes (oral) et MD/ODT (lecture autonome)
  - Aide-mémoire de construction : `docs/jury/accessibilite-formats.md` (PDF, ODP, MD/ODT)
- [ ] **Vérifier l'accessibilité des synthèses passées** (visuels `.png`/`.jpg`,
  carrousels PDF) — hors périmètre du nouveau format, à traiter si elles sont
  réutilisées telles quelles — `D`
  - L'exigence revient aussi sur C8, C11, C18, C19, C20

## Certification — livrables manquants

Repérés en construisant l'index `docs/jury/README.md`.

- [x] **Registre des traitements de données personnelles — résolu (2026-07-29)**
  (C4) : `docs/rgpd/registre_traitements.md`, scindé entre traitements réels
  (référentiel Opquast : hors champ RGPD ; jetons API nominatifs) et volet
  audit anticipé mais non actif (`utilisateur`/`audit`/`constat`, à compléter
  avec la spec US1) — raisonnement dans
  `docs/jury/decisions/2026-07-29-perimetre-registre-rgpd.md` — `A`
- [x] **Procédures de tri RGPD — résolues (2026-07-29)** (C4) : couvertes dans
  `docs/rgpd/registre_traitements.md` §Procédures de tri (rien à purger côté
  référentiel, révocation manuelle des jetons API, volet audit à définir avec
  US1) — `A`
- [ ] **Reste ouvert pour US1** : le registre RGPD change de périmètre une fois
  `utilisateur`/`audit`/`constat` peuplés — ne plus le traiter comme une
  extension du registre référentiel, le repenser comme un traitement de
  données personnelles à part entière — `D`
- [ ] **Objectifs d'accessibilité dans les critères d'acceptation** des user stories
  (C14), appuyés sur WCAG ou RGAA — `D`
- [ ] **Décider du statut de `benchmark-azure/`** (C8, C11, C21) — projet externe
  (`formation_dev_ia_agentique/lab/benchmark-azure/`, dépôt git séparé) : monitorage
  réel de déploiements Azure LLM (cron 30 min, taux d'erreur/latence par modèle,
  rapport HTML, incident HTTP 401 identifié). Couvre C11 mieux que QualiCheck ne le
  pourra jamais (batch anecdotique vs flux réel à surveiller) — `D`
  - Documenter comme preuve externe renvoyée depuis `docs/jury/README.md` (comme la
    veille), ou en dossier de certification autonome ?
  - Si retenu : rédiger la résolution de l'incident HTTP 401 selon les critères C21
    (cause, reproduction, solution) — actuellement seulement constaté, pas résolu
    au sens du référentiel
  - Aligner les liens de `conception/annexes/F_choix_llm.md` sur la vraie source
    (`benchmark-azure/`) plutôt que sur `annexes/benchmark/`, qui n'en est qu'un
    sous-ensemble partiel

## Divers

- [x] **Pousser la branche `feature`** — poussée (2026-07-26) — `D`
