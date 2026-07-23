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
  (9,13 €) : 0,8008 / 3,3875 €/1M. Appliquées à `.env` + `.env.example` — `A`
- [ ] **Emplacement `KIMI_PRICE_*`** — rester dans `.env` ou passer dans le
  manifeste ? Toujours ouvert, indépendant des valeurs (spec E §6) — `D`
- [ ] **`ia_souverain/synthese.md`** — copier dans `conception/annexes/` ou pointer
  vers le dossier formation ? — `D`
  - `F_choix_llm.md` la cite comme annexe (argumentation souveraineté, Bayart,
    Cloud Act). Copier rend le document autonome pour qui lit le dépôt ; pointer
    évite une duplication qui divergera

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
  - Nécessite l'app ou une CLI drawio pour l'export, non vérifiée disponible
    dans cet environnement
- [x] **`G_user_stories_qualicheck.drawio` récupéré** — source + export `.jpg`
  copiés depuis la corbeille vers `conception/annexes/`, nom déjà conforme à ce
  qu'attendait `conception.md` — `A` (2026-07-23)
- [ ] **`H_architecture_globale.drawio`** — **différent de G** : `conception.md`
  marque lui-même cette annexe « en cours de révision » / « à venir » (lignes 712,
  734). Le brouillon en corbeille n'est probablement pas fini — pas récupéré comme
  G. À trancher : le récupérer quand même comme brouillon explicitement non final,
  ou attendre la finalisation avant de le faire entrer dans le dépôt ? — `D`
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
- [ ] **Écart de thème du PPTX métiers du web (15 juillet)** — non résolu,
  postérieur de 2 mois au lancement de Mini Manifest ; à clarifier une fois le MD
  généré (cf. `journal.md`) — `D`
- [ ] **Générer le MD manquant** du PPTX `veille-metiers-web-ia-202.pptx` — `D`
- [ ] **Archiver les 3 PDF/PPTX de veille** hors de `~/Téléchargements` (transitoire,
  comme la corbeille) — `12_mai_article-freshrss-docker_.pdf`,
  `veille_13_mai_David.pdf`, `veille-metiers-web-ia-202.pptx` — `D`
- [ ] **Nettoyer le dossier de veille** (`formation_dev_ia_agentique/veille/`) —
  constat de David, pas encore détaillé. Repéré en cours d'inventaire : fichiers
  hors sujet égarés (`whereisbrian.jpeg`), config d'éditeur versionnée par erreur
  (`.vscode/settings.json` dans `britanica_openAI_le_pillage_savoir/`), noms de
  fichiers incohérents (`veille-metiers-web-ia-202.pptx` vs `-2026.pptx`), pièces
  encore éparpillées en dehors du dossier de veille (`~/Téléchargements`) — `D`
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
