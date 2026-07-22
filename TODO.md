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
- [ ] **`G_user_stories.drawio`** — référencé dans la stack, absent du dépôt, présent
  à la corbeille — `D`
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

## Divers

- [ ] **Pousser la branche `feature`** — 19 commits d'avance sur `origin/feature` — `D`
