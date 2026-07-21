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

## Décisions en attente

- [ ] **Tarifs `KIMI_PRICE_*`** — rester dans `.env` ou passer dans le manifeste ? — `D`
  - En attente des relevés de coûts réels Azure (le commentaire du `.env` signale
    lui-même que la valeur actuelle est une approximation Moonshot/OpenRouter)
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

- [ ] **Comptes LinkedIn, chaînes YouTube et flux RSS précis** → `docs/jury/veille/sources.md` — `D`
  - Le critère de fiabilité porte sur l'auteur, pas sur la plateforme : il faut des
    comptes identifiés, pas « LinkedIn ». Cinq à dix sources bien caractérisées
    suffisent
- [ ] **Capture d'écran de l'instance FreshRSS** comme preuve de l'outil — `D`
- [ ] **Démarrer les entrées datées** de `docs/jury/veille/journal.md` — `D`
  - Seule exigence du référentiel qu'on ne peut pas produire rétroactivement
- [ ] **Accessibilité des synthèses** (Valentin Haüy / AcceDe) — `D`
  - Les supports actuels passent beaucoup par des visuels et des `.pptx` : ordre de
    lecture, alternatives textuelles, contraste, pas de texte incrusté dans une image
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
