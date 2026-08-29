# Chantier 1 — Correction du scraping + champ `contexte`

> Spec d'incrément. Fait suite à `docs/problemes_rencontres/recommandations_v4.md`
> (R1.1 / R1.2 / R1.3). À valider avant implémentation (méthodo spec-driven).
>
> Date : 2026-07-19

## 1. Problème

L'ingestion réelle des 245 règles (prompt V3, ~3 €) a révélé que le scraping de
`solution` et `controle` est corrompu sur > 60 règles (> 25 %) :

- **Bug footer (OBS-8, ~43 règles)** : `find_next("p")` n'est pas borné. Quand une
  section n'a pas de `<p>` immédiat, la recherche déborde jusqu'au `<p>` du pied de
  page (« SAS au capital… Lucien Granet »).
- **Bug `<ul>` ignoré (OBS-11, ~34 règles)** : le code ne capture que le premier
  `<p>`. Quand le contrôle est une intro suivie d'une liste `<ul>`, la liste est
  perdue (ex. contrôle tronqué à « Pour chaque formulaire : »).

Cause racine commune : `find_next("p")` est **non borné** et **ne prend qu'un seul
bloc**.

De plus, chaque règle Opquast possède un **texte explicatif** (le *pourquoi* de la
règle) actuellement non acquis. Il a une influence directe sur la qualité de
classification `strategie_analyse` par le LLM (R1.3).

## 2. Structure HTML réelle (vérifiée)

Page règle : `OPQUAST_SITE_BASE_URL + slug`. Éléments fiables :

- `div.c-rule-content` : conteneur de tout le contenu de la règle (le footer est
  **hors** de ce div → le bornage rend le débordement footer structurellement
  impossible).
- À l'intérieur, headings `<h2>` porteurs de classes émoji **stables** :
  - `c-emoji-target` → « Objectif » (déjà fourni par l'API → ignoré ici)
  - `c-emoji-tools` → « Solution technique » → alimente `solution`
  - `c-emoji-check` → « Moyen de contrôle » → alimente `controle`
- `.c-rule-hero__subtitle` : texte explicatif → alimente `contexte`.

Sous chaque heading, le contenu est une **suite de frères** `<p>` et/ou `<ul>`,
jusqu'au `<h2>` suivant. Exemple règle 154 (contrôle = `p` + `p` + `ul`) : l'ancien
code ne prenait que le premier `p`.

## 3. Décisions de conception

| Point | Décision |
| --- | --- |
| Bornage extraction | Limité aux frères internes à `c-rule-content`, du heading jusqu'au `<h2>` suivant |
| Sérialisation `<ul>` | Chaque `<li>` → `- {texte}` sur sa propre ligne (`\n`) |
| Sentinelle footer | **Aucune** (mot-clé) — le bornage rend le débordement impossible ; pas de code défensif pour un scénario impossible |
| Fail-fast | Conservé : `solution` ou `controle` vide après extraction → `ValueError` |
| `contexte` (nullable) | `None` si `.c-rule-hero__subtitle` absent |
| Type BDD `contexte` | `TEXT` (texte rédactionnel de longueur non bornée — cas légitime de TEXT) |
| `contexte` → chunk RAG | Intention d'inclusion (étape 5, à concevoir plus tard) — noté, pas implémenté ici |
| `contexte` → prompt LLM | Branchement **minimal** ici (`Contexte : {contexte}` dans le template) ; le raffinage V4 relève du chantier 2 |

## 4. Modifications

### 4.1 `scrape_rule()` — `app/ingestion/acquisition.py`

Réécriture :

1. Récupérer `div.c-rule-content`. Absent → `ValueError` (fail-fast).
2. `contexte` : `.c-rule-hero__subtitle` → texte, ou `None`.
3. `solution` : heading `h2.c-emoji-tools` → `extract_content_after(heading)`.
4. `controle` : heading `h2.c-emoji-check` → `extract_content_after(heading)`.
5. `solution` ou `controle` vide → `ValueError`.

Fonction utilitaire `extract_content_after(heading)` :

- Parcourt les frères suivants du heading.
- S'arrête au premier `<h2>` rencontré (ou fin de conteneur).
- `<p>` → texte ; `<ul>` → chaque `<li>` en `- item` (une ligne par item).
- Joint les blocs par `\n`. Retourne la chaîne (éventuellement vide).

Retour de `scrape_rule()` : `{"solution": ..., "controle": ..., "contexte": ...}`.

### 4.2 Schémas Pydantic — `app/ingestion/schema.py`

Ajout `contexte: str | None = None` à :

- `RuleAcquisition` (sortie scraping)
- `RuleAggregation` (alias `Rule`)
- `EnrichedRule`

Le champ traverse le pipeline via `rule.update(scraped_data)` (mécanisme existant).
`fetch_api()` ne le fournit pas → peuplé uniquement par le scraping.

### 4.3 Modèle SQLAlchemy — `app/models/referentiel.py`

`Regle` : `contexte = Column(Text, nullable=True)`.

### 4.4 Migration Alembic — `app/migration/versions/0006_*.py`

- `upgrade` : `op.add_column("regle", sa.Column("contexte", sa.Text(), nullable=True))`
- `downgrade` : `op.drop_column("regle", "contexte")`

### 4.5 Stockage — `app/ingestion/stockage.py`

- `upsert_rule()` : mapper `contexte` sur la colonne.
- `load_enriched_rules_from_db()` : relire `contexte` à la reconstruction des
  `EnrichedRule` (hook `--resume`).

### 4.6 Prompt — `prompts/enrich_rule.md` + `app/ingestion/enrichment.py`

- Template : ajout d'une ligne `Contexte : {contexte}` (branchement minimal).
- `enrichment.py` : passer `contexte` au formatage, fallback propre si `None`
  (ligne omise ou « (non disponible) »).

## 5. Validation (avant tout appel LLM)

Exécuter l'acquisition + agrégation (étapes 1-2) **seules**, s'arrêter avant
l'enrichissement LLM, et **dumper l'objet `Rules` en JSON** dans `./tmp/`
(`tmp/rules_acquises.json`). Inspection visuelle avant toute dépense de tokens.

`scripts/ingestion_test.py` réalise déjà ce découpage (étapes 1-2 réelles, LLM
bouchonné) — on y ajoute le dump JSON, ou un mini-script dédié (à trancher à l'impl).

### Critères de réussite

1. Règle 154 → `controle` = 3 blocs (2 `p` + puces `ul`), **sans** footer.
2. Règle 166 → `controle` contient les puces `ul`.
3. Règle 111 → `contexte` non vide (~300 chars) ; aucun footer nulle part.
4. `tmp/rules_acquises.json` généré et inspectable **avant** tout appel LLM.
5. Migration 0006 up/down OK ; `pytest` vert.

## 6. Hors périmètre (YAGNI)

- Ré-ingestion LLM réelle → chantier 3.
- Prompt V4 complet (classification composite, hors-page = manuel, multi-pages) →
  chantier 2.
- Reclassement règle 111 → `manuel` → chantier 3.
- Sentinelle mot-clé footer → rendue inutile par le bornage.
- Étapes 5-7 (chunking / embedding / indexation) → non touchées.
