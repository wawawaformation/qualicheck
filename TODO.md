# TODO général — QualiCheck

Point d'entrée transverse. Le détail du pipeline d'ingestion (étapes 1 à 7, chantiers)
reste dans `TODO_PIPELINE_INGESTION.md`, qui n'est pas dupliqué ici.

Légende : `[ ]` à faire · `[x]` fait · **Qui** : `D` = David, `A` = assistant

## Prochain gros morceau

- [x] **Scission en deux bases (référentiel / audit)** — décidée le
  2026-09-08, **plan à 9 tâches exécuté et poussé (CI verte, run 26)** — `D`/`A`
  - Décision et critères observables :
    `jury/decisions/2026-09-08-deux-bases-referentiel-audit.md`
    (révise partiellement celle du 2026-07-28)
  - Conception et étapes vérifiables :
    `docs/superpowers/specs/2026-09-08-scission-bases-design.md` — **validée
    le 2026-09-08**
  - **Plan d'implémentation exécuté** :
    `docs/superpowers/plans/2026-09-08-scission-bases-implementation.md`
    (9 tâches, chacune avec son cycle de test et son commit) — détail
    tâche par tâche dans `CHANGELOG.md` (2026-09-08, Part 7)
  - **Pourquoi maintenant** : les six tables métier étaient vides (0 ligne)
    et seules 2 FK traversaient la frontière — la scission était gratuite à
    ce moment-là, ce sera une migration de données après le premier audit
    réel.
  - Résultat : deux bases dans la même instance (`qualicheck` référentiel,
    `qualicheck_audit` métier), `regle_numero` à la place de `regle_id` sur
    la frontière, deux bases déclaratives, deux chaînes Alembic, sauvegarde
    ramenée au référentiel, CI créant et migrant les deux bases. Documents
    de conception (`conception/1_BDD/bdd.md`,
    `conception/1_BDD/MLD_qualicheck.md`, `docs/rgpd/registre_traitements.md`)
    alignés sur ce résultat.
  - Hors périmètre, non traité par ce chantier : `GET /dense` (désigné,
    construit avec US2), `app/api_audit` (avec US1).
  - **Rôle PostgreSQL scopé pour `api_audit`, à décider avec US1, pas
    maintenant** (2026-09-08) — `qualicheck` (le rôle admin) est
    **superutilisateur** (`rolsuper=t`, vérifié), créé ainsi par l'image
    Docker officielle : un `REVOKE CONNECT ON DATABASE qualicheck` sur ce
    rôle ne changerait rien, un superutilisateur contourne toute
    vérification de privilège. Frontière crédible seulement si `api_audit`
    se connecte via un **second rôle, non-superutilisateur**, propriétaire
    de `qualicheck_audit` uniquement — `POSTGRES_USER` resterait le rôle
    d'administration (migrations). Non traité dans le chantier de scission :
    aucun service ne consomme encore ce rôle, même principe que `GET /dense`
    et le filtre par numéros — `D`/`A`

- [ ] **Retrieval US2 — mesurer avant d'ajouter des mécanismes** (plan arrêté
  le 2026-09-08) — `D`/`A`
  - **Dépendance** : si `/dense` devient le seul accès au retrieval pour
    `api_business` (cf. scission ci-dessus), les étapes 3 et 4 de ce plan
    mesurent toujours en SQL direct — c'est l'outil de mesure, pas le
    chemin de production. À garder distinct.
  - **Déclencheur** : une fiche d'architecture RAG issue d'une conversation
    avec Gemini (parent-child retrieval, FTS hybride + RRF, décomposition de
    la requête, `doc_type` multi-sources). Auditée contre le schéma et les
    données réelles avant toute décision.
  - **Ce que l'audit a établi** : le mécanisme de dilution décrit est réel
    (l'intitulé ne pèse que ~5 % du texte vectorisé — 77 car. sur ~1 620),
    mais le remède proposé est **auto-réfutant** : les termes techniques
    qu'il prétend capter ne vivent pas dans les champs qu'il indexe (ARIA :
    0 occurrence en `intitule`, 15 en `solution`, 10 en `controle`, 32 en
    `guide_analyse` ; « SIRET » uniquement en `guide_analyse` ; `alt=` : 0 en
    `intitule`). Détail : `jury/decisions/` (étape A ci-dessous).
  - [x] **Étape 0+1 — passe de cohérence des documents de données**
    (2026-09-08) : récit embedding, types/tailles réels, cardinalités du MCD —
    voir `CHANGELOG.md` — `A`
  - [x] **Étape A — décision jury écrite** (2026-09-08) —
    `jury/decisions/2026-09-08-mesurer-avant-mecanismes-retrieval.md` — `A`
    - Variante proposée écartée **sur mesure** ; hybride gardé ouvert *en
      général* avec une condition de réouverture testable (rappel
      insuffisant sur la famille « termes exacts » → FTS sur le **texte
      complet**, jamais sur `intitule/objectifs/tags`) ; source (Gemini) et
      audit nommés.
    - Volontairement **pas** de « pas de FTS / pas de RRF » au fond : ça
      exige la mesure de l'étape 3.
  - [ ] **Étape 2 — cas d'acceptance durs = amorce de spec US2** — `D`/`A`
    - Pourquoi ce n'est pas de l'outillage : les 17 cas actuels sont des
      paraphrases d'intitulés, à cible unique, sujets disjoints — le 100 %
      obtenu ne mesure pas ce dont on débat. Écrire ces cas, c'est spécifier
      le comportement attendu d'US2 en BDD ; c'est le chemin critique.
    - 4 familles : vocabulaire vivant uniquement dans
      `guide_analyse`/`controle` (ARIA, SIRET, `alt=`) ; questions
      multi-sujets (seul vrai cas d'usage du découpage LLM) ; questions
      méthodologiques sans réponse dans le corpus (teste le « je ne sais
      pas » honnête, cf. `IDEA.md`) ; règles voisines concurrentes (teste la
      précision, que le recall@3 à cible unique ne mesure jamais).
    - **Prérequis de format** : le JSONL actuel
      `{question, numero_regle_attendue}` ne sait exprimer ni plusieurs
      cibles acceptables, ni « aucune réponse attendue ». À étendre avant
      d'écrire les cas.
    - Demande le jugement métier de David (même schéma que les 17 initiaux :
      proposition puis validation).
  - [ ] **Étape 3 — mesurer `recall@3/5/10/15`, pipeline inchangé** (quelques
    centimes) — `A`
    - Il y a une vraie chance que ça referme le débat : si le rappel couvre
      les cas durs, la fiche devient sans objet, mesure à l'appui.
  - [ ] **Étape 4 — agir uniquement sur échec mesuré**, dans cet ordre, en
    s'arrêtant dès que ça passe — `A`
    1. augmenter `top_n` (`manifest.yml`, zéro code) ;
    2. A/B des variantes de chunk (complet / sans `guide_analyse` /
       intitulé+tags) — `embed_rules.py` recalcule les 245 pour 0,0016 € par
       variante, séquentiellement, sans colonne supplémentaire ;
    3. FTS hybride en dernier recours, et alors sur le **texte complet** de
       la règle — pas sur `intitule/objectifs/tags`, où les termes exacts ne
       sont pas.
  - **Ne pas construire** : RRF, décomposition de sous-requêtes, HyDE,
    reformulation LLM, `doc_type`/écosystème VPTCS. Aucun n'est démontrable
    comme amélioration avant l'étape 3 ; l'écosystème Opquast est un projet
    d'acquisition de corpus (sources, droits, chunking d'une autre nature) et
    reste dans `IDEA.md`, hors périmètre certification.
  - **Détail technique à ne pas oublier** : `objectifs` n'est pas une colonne
    de `regle` (table `objectif` + `objectif_regle`), et
    `build_chunk_text()` ne les reçoit pas. La proposition « vectoriser
    intitulé + objectifs + thématique + tags » demande une jointure
    supplémentaire, pas une modification de concaténation.

- [ ] **Outillage C16/C18/C19 — décisions actées le 2026-08-29, exécution en cours**
  — Kanboard auto-hébergé (`kanban.david-legrand.fr`) pour le pilotage
  agile, Gitea auto-hébergé sur `cloclo` en remplacement de GitHub pour le
  dépôt/CI, via un essai non destructif (second remote, sans toucher
  `origin` tant que non validé). Raisonnement complet et alternatives
  écartées : `jury/decisions/2026-08-29-outil-pilotage-kanban.md` et
  `jury/decisions/2026-08-29-hebergement-git-gitea.md` — `D`
  - [x] **Kanboard déployé pour de vrai** (2026-08-29) — `kanban.david-legrand.fr`,
    Docker + Caddy (en-têtes de sécurité alignés sur les autres domaines de
    `cloclo`), connexion admin confirmée — `D`
  - [ ] Activer le plugin `AgileIndicators`
  - [x] **`.gitea/workflows/` validé réellement** (2026-08-30) —
    `ci-dev.yml` et `cd-staging.yml` (image + registre OCI + déploiement
    SSH-push vers hôte générique, API/BDD + client Vue.js) tournent de bout
    en bout sur `git.david-legrand.fr` — `A`
  - [x] **`staging` ne se pousse plus vers `origin`** (2026-09-08) —
    `origin/staging` était resté sur son état pré-migration (`.github/`
    encore présent, runner self-hosted `cloclo` toujours en ligne : risque
    réel de double déploiement). Runner désinscrit, `.github/` retiré de
    `origin/staging`, puis arrêt des push. `dev`/`main` inchangés. Détail :
    précision ajoutée à `jury/decisions/2026-08-29-hebergement-git-gitea.md`
    — `D`/`A`
  - [ ] **Bascule définitive complète** (DNS, `git remote set-url`,
    invitation des collaborateurs) — toujours pas tranchée pour `dev`/`main`,
    seul le risque opérationnel sur `staging` a été traité — `D`

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

- [ ] **Séparer `jury/` (et notamment `veille/`) du dépôt QualiCheck —
  question soulevée le 2026-08-25** : responsabilités mélangées dans un même
  dépôt — le **produit** (code QualiCheck), la **veille** (pratique
  personnelle C6, sans lien avec le produit — ce soir-là : IA et médecine)
  et le **jury** (preuves de certification RNCP37827 dans leur ensemble :
  livrets, décisions, RGPD, veille). Que QualiCheck soit le projet fil rouge
  ne justifie pas que toute preuve de compétence vive dans son dépôt —
  particulièrement flagrant pour la veille, qui n'a structurellement aucun
  rapport avec le produit — `D`
  - **Pourquoi pas fait ce soir-là** : refactor invasif (dizaines de
    fichiers, chemins croisés à réécrire) à quelques heures d'une
    présentation — pas le bon moment pour un chantier de cette taille.
  - **Reste à trancher avant d'agir** :
    1. Périmètre — seule `veille/`, ou tout `jury/` (livrets +
       `decisions/` + RGPD aussi) ? Les `decisions/` documentent des choix
       d'architecture QualiCheck : les séparer du code qu'elles expliquent a
       un coût différent de séparer la veille, sans rapport avec le produit.
    2. Destination — `formation_dev_ia_agentique` évoqué, mais **attention** :
       un renvoi externe vers ce même dossier a déjà existé pour la veille et
       a été abandonné le 2026-07-23 au profit d'une centralisation complète
       (raisonnement : `jury/veille/CLAUDE.md`, section « Pièges déjà
       rencontrés »). Ne pas répéter une duplication ambiguë — un déplacement
       propre, sans copie résiduelle, un seul exemplaire qui fait foi.
    3. Découvrabilité côté jury — si la preuve C6 ne vit plus dans le dépôt
       fil rouge, comment le jury la retrouve ? Un renvoi clair et documenté
       depuis QualiCheck, pas une simple absence.
  - À traiter posément, avec une vraie decision doc dans
    `jury/decisions/` une fois le périmètre tranché — pas dans
    l'urgence d'une session de veille.

- [x] **Découpage des responsabilités `api_regles` / `api_audit` / `api_business`
  — résolu (2026-07-28), partiellement révisé le 2026-09-08** : le découpage
  en trois étages tient — `app/api_regles` (référentiel + revue, implémenté),
  `app/api_audit` (tables métier, à concevoir avec US1), `app/api_business`
  (orchestration, sans jamais toucher Postgres). **Ce qui a changé le
  2026-09-08** : deux bases de données au lieu d'une, et `api_audit` n'accède
  plus au référentiel en base mais en HTTP. Voir
  `jury/decisions/2026-09-08-deux-bases-referentiel-audit.md` — `D`
  - Reste ouvert, hors périmètre de cette décision : la frontière CRUD
    (`api_audit`) vs orchestration (`api_business`) — ex. « créer un audit »
    est-il un simple CRUD ou déclenche-t-il déjà une action métier (crawl) ?
    À trancher avec la spec US1, pas avant.
- [x] **Champ `contexte` vide en base — résolu, constaté le 2026-09-08** :
  `contexte` est aujourd'hui renseigné sur **245/245 règles** (294 caractères
  en moyenne), une ingestion réelle l'a donc alimenté depuis la rédaction de
  cet item. Aucune ré-ingestion ciblée nécessaire. Conséquence pour le RAG :
  `build_chunk_text()` inclut bien la section `Contexte` dans le chunk
  vectorisé — `A`
- [ ] **Licence du code et des étages applicatif/présentation** — non arrêtée.
  L'étage données est sous licence libre (CC BY-SA 4.0 s'imposant au jeu de
  données par partage à l'identique — décision actée
  `jury/decisions/2026-07-26-lecture-ouverte-api-regles.md`), mais CC BY-SA
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
  (`jury/veille/fonds/ia_souverain/synthese.md`), plus besoin de choisir
  entre copier et pointer vers l'extérieur — `A` (2026-07-23)
  - Reste ouvert si souhaité : `F_choix_llm.md` cite ce fichier comme annexe
    (argumentation souveraineté, Bayart, Cloud Act) — copier spécifiquement
    dans `conception/annexes/` en plus, ou le renvoi vers `fonds/` suffit ?
- [ ] **Persister le retour pouce haut/bas d'US2 (question libre)** — la
  maquette (`conception/maquettes/directives/composants/ecran-question-libre.html`,
  `fil-dialogue.html`) affiche un bouton pouce haut/bas sous chaque réponse de
  l'agent, mais rien n'est encore spécifié côté modèle/API pour stocker ce
  retour. Intention actée : garder une trace exploitable pour améliorer le
  système plus tard (ex. jeu d'exemples pour affiner le prompt RAG, détection
  des réponses mal notées) — à spécifier avec la conception d'US2 (API
  `api_business`, pas encore conçue) — `D`
  - Volet RGPD déjà anticipé dans `docs/rgpd/registre_traitements.md`
    (section « Traitements anticipés, non actifs — US2 »), même logique que
    le volet audit US1 : rien à traiter tant qu'US2 n'a pas de spec, mais
    finalité/base légale/conservation à trancher à ce moment-là.

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
  du MCD est sans flèche). Le doublon dans `conception/2_us0/ingestion/` — identique
  avant correctif, aurait divergé sinon — a été supprimé, non référencé par aucun
  document — `A` (2026-07-23)
- [x] **Règle sur les flèches du MCD — révisée le 2026-09-08, remplace l'item
  ci-dessus** : une flèche est **acceptée sur les liens DF** (dépendance
  fonctionnelle 1-n sans table d'association), parce qu'elle rend le sens de
  la dépendance immédiatement lisible — arbitrage de David. Les relations
  passant par une table d'association restent sans flèche. État appliqué :
  une flèche par DF, orientée vers l'entité dépendante (`theme → regle`,
  `utilisateur → audit`) ; les flèches par défaut de draw.io sur les branches
  entrantes (`theme → DF`, `utilisateur → DF`) ont été explicitement
  neutralisées. **Ne pas « re-corriger » en retirant ces flèches** — `D`/`A`
- [ ] **MCD — `constat` rattaché à une association** : `constat` pend de
  `audit_page`, qui est elle-même une association. En Merise strict, une
  association relie des entités ; sa clé réelle
  (`PK (audit_id, page_id, regle_id)`) en fait une association **ternaire**
  entre `audit`, `page` et `regle`. La représenter correctement suppose de
  redessiner cette partie du schéma. Écart documenté dans
  `conception/1_BDD/MLD_qualicheck.md` (§ Cardinalités du MCD). À trancher si
  le MCD passe devant le jury : c'est la remarque la plus probable après les
  cardinalités — `D`
- [ ] **MCD et dictionnaire — 3 colonnes réelles absentes** : `contexte`
  (migration 0006), `created_at` et `updated_at` (migration 0009) ne figurent
  ni dans `B_MCD_qualicheck.drawio` ni dans le dictionnaire xlsx (elles sont
  au MLD). Non ajoutées lors de la passe du 2026-09-08 : les boîtes du MCD
  sont dimensionnées au plus juste (140 px pour 5 lignes) et insérer une
  ligne dans le xlsx décale les références de cellules — deux gestes qui
  changent la mise en page, à valider visuellement — `D`/`A`
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

Dépôt séparé depuis le 2026-08-28 (`/projets/veille`) — les tâches encore
ouvertes ont été déplacées dans son propre `TODO.md`. Historique conservé
ci-dessous tel quel.

- [x] **17 flux RSS listés** (export OPML 2026-07-22) → `jury/veille/sources.md` — `D`
- [x] **Démarrer les entrées datées** de `jury/veille/journal.md` — 3 entrées
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
- [x] **Veille centralisée dans le dépôt** — `formation_dev_ia_agentique/veille/`
  (5 dossiers) et les 3 fichiers de `~/Téléchargements` déplacés (pas copiés) vers
  `jury/veille/fonds/`, avec une période approximative par dossier dans
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
  - Aide-mémoire de construction : `jury/accessibilite-formats.md` (PDF, ODP, MD/ODT)

## Certification — livrables manquants

Repérés en construisant l'index `jury/README.md`.

- [x] **Registre des traitements de données personnelles — résolu (2026-07-29)**
  (C4) : `docs/rgpd/registre_traitements.md`, scindé entre traitements réels
  (référentiel Opquast : hors champ RGPD ; jetons API nominatifs) et volet
  audit anticipé mais non actif (`utilisateur`/`audit`/`constat`, à compléter
  avec la spec US1) — raisonnement dans
  `jury/decisions/2026-07-29-perimetre-registre-rgpd.md` — `A`
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
  - Documenter comme preuve externe renvoyée depuis `jury/README.md` (comme la
    veille), ou en dossier de certification autonome ?
  - Si retenu : rédiger la résolution de l'incident HTTP 401 selon les critères C21
    (cause, reproduction, solution) — actuellement seulement constaté, pas résolu
    au sens du référentiel
  - Aligner les liens de `conception/annexes/F_choix_llm.md` sur la vraie source
    (`benchmark-azure/`) plutôt que sur `annexes/benchmark/`, qui n'en est qu'un
    sous-ensemble partiel

## Divers

- [x] **Pousser la branche `feature`** — poussée (2026-07-26) — `D`
