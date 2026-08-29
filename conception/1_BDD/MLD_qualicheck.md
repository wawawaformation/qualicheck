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
  intitule                VARCHAR(512)    NN
  solution                VARCHAR(512)    NN
  controle                VARCHAR(512)    NN
  -- Champs générés par l'agent LLM à l'ingestion
  strategie_analyse *     VARCHAR(20)     NN        -- statique | playwright | manuel
  strategie_justification * TEXT
  strategie_source *      VARCHAR(20)     NN        -- ia_import | ia_reingest | admin
  strategie_score *       DECIMAL(3,2)              -- calculé depuis constat.validation_humaine
  guide_analyse *         TEXT            NN
  llm_model *             VARCHAR(64)     -- nom logique du modèle (manifest.yml), pas un nom de déploiement
  prompt_version *        INT                       -- version du prompt (frontmatter enrich_rule.md)
  created_at *            TIMESTAMP                 -- NULL = produit avant instrumentation
  updated_at *            TIMESTAMP                 -- NULL = produit avant instrumentation
  reviewed_at *           TIMESTAMP                 -- NULL = pas encore revue manuellement
  review_status *         VARCHAR(16)               -- valide | a_revoir
  review_note *           TEXT                      -- notes de revue, matière pour un futur script de réécriture ciblée
  embedding *             vector(384)               -- All MiniLM L12 v2, index HNSW
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
  objectif  VARCHAR(256)    NN
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
  PK (audit_id, page_id, regle_id)
  U  (audit_id, page_id, regle_id)        -- unicité composite (cf. MCD)
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
