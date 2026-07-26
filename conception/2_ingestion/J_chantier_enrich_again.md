# Chantier — Script `enrich_again` (réécriture ciblée)

> Spec d'incrément. Fait suite à l'audit V5
> (`docs/problemes_rencontres/ingestion/5_recommandations_v6.md`), qui a
> marqué 11 règles `review_status = a_revoir` avec un `review_note` détaillé
> chacune. Différé explicitement depuis la spec G
> (`conception/2_ingestion/G_revue_manuelle.md` §5) jusqu'à disposer de
> vraies données de revue — c'est fait. À valider avant implémentation.
>
> Date : 2026-07-26

## 1. Problème

11 règles sur 245 sont marquées `review_status = a_revoir`, chacune avec un
`review_note` expliquant le problème constaté et la correction attendue (ex.
règle 65 : « classée vision+statique, devrait être vision&statique »). Il
n'existe aujourd'hui aucun moyen de faire relire ces règles par le LLM en
tenant compte de cette annotation — la seule option actuelle est une
ré-ingestion complète des 245 règles, disproportionnée pour corriger 4,5 %
du référentiel (et qui a déjà, une fois, réintroduit une régression sur des
règles qui n'étaient pas concernées).

## 2. État actuel (vérifié)

- `app/ingestion/llm_client.py` : `LLMClient.load_prompt(rule)` charge
  `prompts/enrich_rule.md` et remplace 7 placeholders fixes (`intitule`,
  `contexte`, `solution`, `controle`, `objectifs`, `tags`, `phases`) — aucun
  placeholder pour un contexte de revue.
  `enrich_single_rule(rule)` code en dur `strategie_source="ia_import"`.
- `app/ingestion/stockage.py` : `upsert_rule()` gère déjà l'UPDATE complet
  d'une règle existante (par `numero`), y compris `strategie_source`,
  `llm_model`, `prompt_version`, `updated_at` — réutilisable tel quel.
  Aucune logique ne touche `review_status`/`review_note`/`reviewed_at`.
- `regle.strategie_source` : enum documenté dans le MLD
  (`ia_import | ia_reingest | admin`), mais **`ia_reingest` n'a jamais été
  écrit par aucun code**, y compris lors des ré-ingestions complètes déjà
  faites (V3, V4, V5) — première utilisation réelle avec ce chantier.
- Aucune migration nécessaire : les colonnes `reviewed_at`/`review_status`/
  `review_note` existent depuis la migration 0010.

## 3. Décisions de conception

| Point | Décision |
| --- | --- |
| Sélection des règles | `regle` où `review_status IS NOT NULL AND review_status != 'valide'` (couvre `a_revoir` et `invalide`) |
| Fichier de prompt | **Un seul fichier** : `enrich_rule.md` reste la source unique. Une section « Contexte de revue humaine » (classification actuelle + `review_note`) est ajoutée par le code juste avant l'instruction finale du prompt, uniquement quand un `review_note` est fourni — zéro duplication, zéro risque de divergence future |
| `strategie_source` écrit | `"ia_reingest"` — première utilisation réelle de cette valeur déjà documentée dans le MLD |
| `prompt_version` enregistré | Celui du frontmatter courant de `enrich_rule.md` — pas de version dédiée, c'est le même prompt de base |
| Retry LLM | Réutilise tel quel la politique existante (3 tentatives, backoff exponentiel 2/4/8s) — pas de nouvelle politique |
| Dry-run | Dump JSON des règles à traiter (+ leur `review_note`) dans `tmp/` avant tout appel LLM réel — même logique que le chantier 1 |
| `LIMIT=` | Non ajouté — le périmètre est déjà borné par `review_status`, un `LIMIT` irait à l'encontre de l'objectif (traiter tout ce qui est marqué) |
| Confirmation interactive | Aucune — cohérent avec `make ingestion` (le lancement manuel de la commande fait office de décision) |
| Commit | **Par règle**, pas un commit global pour tout le batch. Si une règle échoue, les règles précédentes déjà corrigées restent acquises ; la règle en échec garde son `review_status` intact pour un futur run. Diffère volontairement de `store_rules()` (un seul commit pour tout le batch) — cette dernière protège l'atomicité d'une ingestion initiale complète, une raison d'être qui ne s'applique pas ici (règles indépendantes, déjà existantes, correction incrémentale) |
| Vidage de `review_*` | Après upsert réussi d'une règle, remise à `NULL` de `reviewed_at`/`review_status`/`review_note` sur cette même ligne, dans la même transaction que l'upsert (donc le même commit par-règle) |
| Enchaînement Makefile | `make enrich-again` chaîne `make export_sql` ensuite, même logique que `make ingestion` |

## 4. Modifications

### 4.1 `app/ingestion/llm_client.py`

- `load_prompt(rule, review_note: str | None = None, current_strategie_analyse: str | None = None) -> str` :
  signature étendue. Quand `review_note` est fourni, insère avant la
  dernière ligne du prompt (`Génère maintenant une réponse JSON pour la
  règle ci-dessus.`) un bloc :

  ```text
  ## Contexte de revue humaine

  Cette règle a déjà été classée une première fois avec le résultat suivant :
  strategie_analyse = "{strategie_analyse_actuelle}"

  Une revue humaine a identifié un problème sur cette classification :
  {review_note}

  Reclasse cette règle en tenant compte de cette remarque.
  ```

  Comportement inchangé (aucun bloc ajouté) quand `review_note` est `None` —
  rétrocompatible avec l'appel existant depuis `enrichment.py`.
- `enrich_single_rule(rule, review_note: str | None = None, strategie_source: str = "ia_import") -> EnrichedRule` :
  signature étendue de la même façon, transmet `review_note` à
  `load_prompt()` et écrit `strategie_source` (paramètre) au lieu de la
  valeur codée en dur actuelle. Appel existant depuis `enrichment.py`
  inchangé (les deux paramètres ont une valeur par défaut identique au
  comportement actuel).
- `strategie_analyse_actuelle` : à passer également en paramètre à
  `load_prompt()` (nécessaire pour le contexte de revue) — ou lu directement
  depuis l'objet `rule` si ce champ y est déjà présent (à trancher à
  l'implémentation selon la forme exacte de l'objet utilisé, cf. §4.2).

### 4.2 `app/ingestion/enrich_again.py` (nouveau)

- `load_rules_to_review(session) -> list[tuple[RuleAggregation, str, str]]` :
  requête `regle` où `review_status IS NOT NULL AND review_status != 'valide'`,
  retourne pour chaque ligne un triplet (règle reconstituée en
  `RuleAggregation`, `review_note`, `strategie_analyse` actuelle).
- `clear_review_fields(session, numero: int) -> None` : remet
  `reviewed_at`/`review_status`/`review_note` à `NULL` sur la ligne
  correspondante (pas de commit ici — le commit est de la responsabilité de
  l'appelant, pour rester dans la même transaction que l'upsert).
- `enrich_again(session) -> None` (ou nom équivalent) : orchestre le flux
  complet (§3, ligne « Commit ») — dump JSON, boucle par règle, upsert +
  vidage + commit, log token/coût cumulé en fin de run (même format que
  `scripts/ingestion.py`).

### 4.3 `scripts/enrich_again.py` (nouveau)

Point d'entrée flat, sur le modèle de `scripts/ingestion.py` : connexion
DB, appel à `app.ingestion.enrich_again.enrich_again()`, gestion des logs
(`logs/ingestion.log`, même logger que le reste du pipeline — pas de fichier
de log séparé, c'est le même pipeline).

### 4.4 `Makefile`

Nouvelle cible `enrich-again` dans la section « Ingestion et données
réelles », juste après `import_sql` :

```makefile
## Relance le LLM sur les règles marquées review_status = a_revoir/invalide,
## en tenant compte de review_note, puis sauvegarde les données réelles
enrich-again:
	uv run python scripts/enrich_again.py
	$(MAKE) export_sql
```

## 5. Validation

1. Aucune règle `a_revoir`/`invalide` en base → le script log et sort sans
   appel LLM.
2. Sur les 11 règles actuellement marquées : chacune reçoit un nouvel appel
   LLM incluant son `review_note`, `strategie_source` passe à `ia_reingest`,
   `reviewed_at`/`review_status`/`review_note` repassent à `NULL` après
   succès.
3. Une règle dont l'appel LLM échoue (3 tentatives épuisées) conserve son
   `review_status` intact — les autres règles déjà traitées avec succès
   restent acquises (vérifiable en relançant le script : seule la règle en
   échec est reprise).
4. `load_prompt()` appelé sans `review_note` (chemin `enrichment.py`
   existant) produit un prompt strictement identique à l'actuel — aucune
   régression sur l'ingestion normale.
5. `pytest`/`ruff` verts.

## 6. Hors périmètre (YAGNI)

- **Décision sur la règle 96** (contestée, cf. recommandations V6 §2) — à
  trancher séparément avant de lui assigner un `review_status`, n'entre pas
  dans ce chantier.
- **Prompt V6 complet** (few-shot `&`, reformulation R2.4) — chantier
  séparé, pour une future ré-ingestion complète. `enrich_again` réutilise le
  prompt V5 actuel tel quel, augmenté du contexte de revue.
- **Invalidation automatique d'une revue après ré-ingestion complète** —
  limite déjà actée en spec G, non résolue ici.
- **Table d'historique des revues** — un seul état courant par règle reste
  suffisant (spec G §3).
