# TODO général — QualiCheck

Point d'entrée transverse. Le détail du pipeline d'ingestion (étapes 1 à 7, chantiers)
reste dans `TODO_PIPELINE_INGESTION.md`, qui n'est pas dupliqué ici.

Légende : `[ ]` à faire · `[x]` fait · **Qui** : `D` = David, `A` = assistant

## Prochain gros morceau

- [ ] **Plan d'implémentation de la spec E** (provenance + manifeste) — `A`
  - Spec validée et commitée : `conception/2_ingestion/E_provenance_manifeste.md`
  - À livrer **avant le chantier 2** (prompt V4) et impérativement **avant le
    chantier 3** (ré-ingestion réelle) : après, il faudrait une migration *et* une
    seconde ré-ingestion facturée (~3 €)
  - Mérite une session dédiée
  - Intègre désormais le correctif de visibilité du coût sur échec de stockage
    (spec E §1 quatrième manque, §5.10, critère de validation #8) — gap découvert
    le 2026-07-22 en analysant `logs/ingestion.log` : ~6 € de tokens facturés le
    19 juillet sur des runs échoués au stockage, jamais journalisés

## Décisions en attente

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
- [ ] **9 images `annexes/*.png` référencées par `conception.md`, toujours
  manquantes** — seule `G_user_stories_qualicheck.png` existe réellement
  (converti depuis le `.jpg` récupéré la veille, pas juste renommé). Restent :
  `B_MCD_qualicheck.png`, `C_pipeline_ingestion.png`, `D1/D2/D3_...png`,
  `D_pipeline_audit.png`, `E_pipeline_dialogue.png`, `I_feedback_loop.png`,
  `J_personas_qualicheck.png`. L'export drawio → image n'a jamais suivi la
  création des sources `.drawio` — `conception.md` ne peut toujours pas se
  compiler en PDF sans schémas cassés. `E_pipeline_dialogue.png` ne correspond
  même pas au nom du fichier source réel (`E_pipeline_question_libre.drawio`) —
  nom qui a aussi dérivé — `D`
  - Export manuel, volontairement pas automatisé : David veut relire chaque
    schéma avant de le figer en image (même logique que la flèche incorrecte
    trouvée dans B_MCD — un export automatique aurait masqué l'erreur)
- [x] **`G_user_stories_qualicheck.drawio` récupéré** — source + export `.jpg`
  copiés depuis la corbeille vers `conception/annexes/`, nom déjà conforme à ce
  qu'attendait `conception.md` — `A` (2026-07-23)
- [x] **`H_architecture_globale.drawio` — laissé en l'état, décision prise** —
  trop tôt pour figer cette annexe : la stack backend/frontend n'est pas encore
  construite (US1/US2 ni conçus ni implémentés), donc tout schéma d'architecture
  documenterait une intention non stabilisée plutôt qu'un état réel. Reste à la
  corbeille jusqu'à ce que l'architecture soit assez avancée pour valoir la peine
  d'être figée. Note au passage : le brouillon existant confond le modèle
  d'enrichissement (Kimi) et le modèle d'audit dans sa case « LLM Audit » — à
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

- [ ] **Registre des traitements de données personnelles** (C4) — livrable à part
  entière, pas une section de spec — `D`
- [ ] **Procédures de tri RGPD** avec leur fréquence d'exécution (C4) — `D`
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

- [ ] **Pousser la branche `feature`** — 18 commits d'avance sur `origin/feature` — `D`
