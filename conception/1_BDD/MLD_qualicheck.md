---
title: "Modèle Logique de Données — QualiCheck"
subtitle: "Dérivé du MCD Merise et du dictionnaire de données"
author: "David LEGRAND"
date: "Juillet 2026"
lang: fr-FR
toc: true
toc-depth: 2
numbersections: true
---

\newpage

## Conventions

- **PK** : clé primaire
- **FK** : clé étrangère
- **NN** : NOT NULL
- **U** : UNIQUE
- `*` : champ généré par l'agent IA à l'ingestion
- Les types SERIAL correspondent à COUNTER (auto-incrémenté)
- **Ce document décrit le schéma réellement en place** (vérifié contre la base
  le 2026-09-08), pas une cible. En cas de doute, la source de vérité reste les
  migrations Alembic (`app/migration/versions/`) — voir
  `docs/agent/03_references_impl.md`. La table `etat_donnees` n'y figure pas :
  bookkeeping opérationnel, hors modèle métier (cf. `app/CLAUDE.md`)

---

## Cardinalités du MCD

Portées sur `annexes/B_MCD_qualicheck.drawio`. Chacune est établie sur une
preuve — contrainte de schéma, ou comptage sur les 245 règles réellement
ingérées — et non sur une intuition de modélisation.

| Relation | Côté | Card. | Sur quoi elle repose |
| --- | --- | --- | --- |
| theme — DF — regle | theme | 1,n | Aucun thème sans règle (mesuré) |
| | regle | 1,1 | `regle.theme_id` NOT NULL |
| objectif — objectif_regle — regle | objectif | 1,n | Aucun objectif sans règle (mesuré) |
| | regle | 1,n | Aucune règle sans objectif, jusqu'à 6 (mesuré) |
| phase — phase_regle — regle | phase | 1,n | Aucune phase sans règle (mesuré) |
| | regle | 1,n | Aucune règle sans phase, jusqu'à 3 (mesuré) |
| tag — regle_tag — regle | tag | 1,n | Aucun tag sans règle (mesuré) |
| | regle | **0,n** | **64 des 245 règles n'ont aucun tag** — vérifié à la source, pas seulement en base (voir ci-dessous) |
| utilisateur — DF — audit | utilisateur | 0,n | Un compte peut n'avoir lancé aucun audit |
| | audit | 1,1 | `audit.utilisateur_id` NOT NULL |
| regle — audit_regle — audit | regle | 0,n | Une règle peut n'être retenue dans aucun audit |
| | audit | 0,n | Cycle de vie : `statut = en_cours` avant sélection des règles |
| audit — audit_page — page | audit | 0,n | Cycle de vie : audit créé avant le crawl |
| | page | 1,n | Une page n'existe que découverte par au moins un crawl |
| audit_page — constat — regle | audit_page | 0,n | Une page retenue peut n'avoir encore aucun constat |
| | regle | 0,n | Une règle peut n'avoir aucun constat |

**Sur le `0,n` des tags — pourquoi la mesure locale ne suffisait pas.** Constater
64 règles sans tag en base ne dit pas si c'est une règle métier ou un trou
d'ingestion : les deux produisent le même comptage. La vérification a donc été
refaite contre l'API Opquast (`metadata.Tags`) pour les 245 règles : **aucun
écart** entre la source et la base, et les 64 règles concernées sont exactement
les mêmes de part et d'autre (règles 2, 6, 9, 10, 11, 13, 28, 31, 32, 33…). Le
`0,n` est donc bien une propriété du référentiel, et non un défaut du pipeline
— lequel se trouve validé au passage sur la fidélité des tags.

L'explication tient à la nature des deux champs : une règle porte toujours
exactement une **Thématique** (d'où `theme` en `1,1`), tandis que les **Tags**
forment un vocabulaire contrôlé de 6 valeurs transverses (`Accessibilité`,
`Basics`, `SEO`, `Écoconception`, `Privacy`, `Mobile`) qu'une règle peut
légitimement ne pas porter.

Deux remarques de notation, à trancher si le MCD est présenté tel quel :

- Les deux liens **DF** (`theme → regle`, `utilisateur → audit`) portent une
  flèche vers l'entité dépendante. C'est un écart assumé à la notation Merise
  stricte (traits simples), retenu parce qu'il rend le sens de la dépendance
  fonctionnelle immédiatement lisible sur une relation 1-n sans table
  d'association. Les relations passant par une table d'association n'en
  portent aucune.
- `constat` est rattaché à `audit_page`, qui est elle-même une association.
  En Merise strict, une association relie des entités. La clé réelle
  (`PK (audit_id, page_id, regle_id)`) en fait une association **ternaire**
  entre `audit`, `page` et `regle` — la représenter ainsi supposerait de
  redessiner cette partie du schéma, non fait à ce stade.

---

## Référentiel Opquast

### theme

```
theme (
  id        SERIAL        PK, NN
  theme     VARCHAR(64)   NN, U
)
```

Une règle a exactement une thématique (`metadata.Thématiques` de l'API Opquast — toujours une liste à un seul élément sur les 245 règles observées), d'où une relation 1-N simple plutôt qu'une table d'association.

### regle

```
regle (
  id                      SERIAL          PK, NN
  theme_id                INT             FK → theme.id, NN
  numero                  INT             NN, U
  intitule                VARCHAR(255)    NN        -- source API, longueur contractuelle (max réel 167)
  solution                TEXT            NN        -- source scraping : voir docs/problemes_rencontres/ingestion/2_schema_text_columns.md
  controle                TEXT            NN        -- source scraping : idem
  contexte                TEXT                      -- texte explicatif Opquast (absent sur ~la moitié des règles)
  -- Champs générés par l'agent LLM à l'ingestion
  strategie_analyse *     VARCHAR(32)     NN        -- statique | playwright | vision | manuel, ou une paire (ex. vision+statique)
  strategie_justification * TEXT
  strategie_source *      VARCHAR(32)     NN        -- ia_import | ia_reingest | admin
  strategie_score *       DECIMAL(3,2)              -- calculé depuis constat.validation_humaine
  guide_analyse *         TEXT            NN
  llm_model *             VARCHAR(64)     -- nom logique du modèle (manifest.yml), pas un nom de déploiement
  prompt_version *        INT                       -- version du prompt (frontmatter enrich_rule.md)
  created_at *            TIMESTAMP                 -- NULL = produit avant instrumentation
  updated_at *            TIMESTAMP                 -- NULL = produit avant instrumentation
  reviewed_at *           TIMESTAMP                 -- NULL = pas encore revue manuellement
  review_status *         VARCHAR(16)               -- valide | a_revoir
  review_note *           TEXT                      -- notes de revue, matière pour un futur script de réécriture ciblée
  embedding *             vector(1536)              -- text-embedding-3-small (dimension native), index HNSW
)
```

**Règle de nommage des colonnes** : le vocabulaire du domaine reste en français,
le vocabulaire technique en anglais (principe de langage omniprésent, DDD). Test :
un auditeur qualité prononcerait-il ce mot en parlant de son métier ? Détail :
`conception/2_us0/enrichissement/E_provenance_manifeste.md` §7.

### objectif

```
objectif (
  id        SERIAL          PK, NN
  objectif  VARCHAR(512)    NN
)
```

### phase

```
phase (
  id      SERIAL        PK, NN
  phase   VARCHAR(64)   NN
)
```

### tag

```
tag (
  id    SERIAL        PK, NN
  tag   VARCHAR(50)   NN
)
```

---

## Tables d'association — Référentiel

### objectif_regle

```
objectif_regle (
  objectif_id   INT   FK → objectif.id, NN
  regle_id      INT   FK → regle.id, NN
  PK (objectif_id, regle_id)
)
```

### phase_regle

```
phase_regle (
  phase_id    INT   FK → phase.id, NN
  regle_id    INT   FK → regle.id, NN
  PK (phase_id, regle_id)
)
```

### regle_tag

```
regle_tag (
  regle_id   INT   FK → regle.id, NN
  tag_id     INT   FK → tag.id, NN
  PK (regle_id, tag_id)
)
```

`tags` est optionnel côté règle : 64 des 245 règles Opquast n'ont aucun tag (`metadata.Tags` vide), contrairement à `theme`, `objectifs` et `phases` qui sont toujours renseignés. Une règle sans tag n'a simplement aucune ligne dans `regle_tag`.

---

## Cœur métier QualiCheck

### utilisateur

```
utilisateur (
  id       SERIAL        PK, NN
  nom      VARCHAR(64)   NN
  prenom   VARCHAR(64)   NN
)
```

> Note MVP : utilisateur simulé. Les versions publiques intégreront une authentification complète.

### audit

```
audit (
  id                SERIAL          PK, NN
  utilisateur_id    INT             FK → utilisateur.id, NN    -- DF (1,1)/(0,n)
  url_depart        VARCHAR(512)    NN
  statut            VARCHAR(50)     NN    -- en_cours | pret_dialogue | termine
  date_creation     DATETIME        NN
  date_modification DATETIME
)
```

### page

```
page (
  id      SERIAL          PK, NN
  url     VARCHAR(512)    NN
  titre   VARCHAR(255)
)
```

### audit_page

```
audit_page (
  audit_id         INT           FK → audit.id, NN
  page_id          INT           FK → page.id, NN
  statut_http      VARCHAR(10)               -- stocké comme texte, sans calcul
  est_selectionnee BOOLEAN       NN
  date_crawl       DATETIME
  PK (audit_id, page_id)
  U  (audit_id, page_id)                    -- unicité composite
)
```

### audit_regle

```
audit_regle (
  audit_id    INT   FK → audit.id, NN
  regle_id    INT   FK → regle.id, NN
  PK (audit_id, regle_id)
  U  (audit_id, regle_id)
)
```

### constat

```
constat (
  audit_id           INT             FK → audit.id, NN
  page_id            INT             FK → page.id, NN
  regle_id           INT             FK → regle.id, NN
  statut             VARCHAR(32)     NN    -- conforme | non_conforme | non_applicable
  commentaire        VARCHAR(512)
  recommandation     VARCHAR(512)
  preuve             VARCHAR(512)
  validation_humaine BOOLEAN               -- true | false | null (non traité)
  feedback_auditeur  TEXT                  -- commentaire qualitatif — post-MVP : alimente strategie_score
  PK (audit_id, page_id, regle_id)        -- porte à elle seule l'unicité composite
                                          -- notée sur le MCD : un seul constat par
                                          -- (audit, page, règle). Pas de contrainte
                                          -- UNIQUE séparée en base, elle serait redondante
)
```

---

## Index notables

```sql
-- Recherche sémantique RAG
CREATE INDEX ON regle USING hnsw (embedding vector_cosine_ops);

-- Performances sur les constats d'un audit
CREATE INDEX ON constat (audit_id);

-- Performances sur les règles d'un audit
CREATE INDEX ON audit_regle (audit_id);
```

---

## Résumé des clés étrangères

| Table | Champ | Référence |
|---|---|---|
| regle | theme_id | theme.id |
| objectif_regle | objectif_id | objectif.id |
| objectif_regle | regle_id | regle.id |
| phase_regle | phase_id | phase.id |
| phase_regle | regle_id | regle.id |
| regle_tag | regle_id | regle.id |
| regle_tag | tag_id | tag.id |
| audit | utilisateur_id | utilisateur.id |
| audit_page | audit_id | audit.id |
| audit_page | page_id | page.id |
| audit_regle | audit_id | audit.id |
| audit_regle | regle_id | regle.id |
| constat | audit_id | audit.id |
| constat | page_id | page.id |
| constat | regle_id | regle.id |
