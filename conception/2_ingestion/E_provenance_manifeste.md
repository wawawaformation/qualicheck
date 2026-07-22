# Provenance des données et manifeste d'ingestion

> Spec d'incrément. S'intercale **entre le chantier 1 (scraping, fait) et le
> chantier 2 (prompt V4)**, et doit impérativement être livrée avant le
> chantier 3 (ré-ingestion réelle). À valider avant implémentation.
>
> Date : 2026-07-21

## 1. Problème

Une ligne de la table `regle` ne sait pas d'où elle vient.

Aujourd'hui, savoir qu'une classification est périmée repose entièrement sur la
lecture de `CHANGELOG.md` et de `docs/problemes_rencontres/ingestion/`. Aucune
requête SQL ne peut répondre à : *« cette règle a-t-elle été produite avec le
scraping corrigé ? avec quel prompt ? quand ? »*

Trois manques distincts :

- **La version du prompt n'existe nulle part dans la donnée**, ni même dans le
  fichier `enrich_rule.md`. L'information n'est qu'en prose dans
  `1_prompt_engineering.md`.
- **Aucun horodatage sur `regle`.** Le « quand » n'est pas seulement difficile à
  retrouver : il est absent, et seulement approximable par les dates du changelog.
- **Le modèle est affirmé, pas observé.** `llm_provider` vaut la chaîne littérale
  `"kimi-k2.6"`, écrite en dur dans le code. Si le déploiement change dans `.env`
  sans modification du code, la colonne continue d'annoncer `kimi-k2.6`.

Le troisième point est le plus insidieux : la colonne **a l'apparence** d'une
provenance sans en être une. C'est une décoration.

**Quatrième manque, découvert en analysant `logs/ingestion.log` (2026-07-22)** :
le coût d'un run n'est journalisé qu'après un stockage réussi
(`scripts/ingestion.py`, calcul placé après le bloc `Étape 4 — Stockage`, qui
`sys.exit(1)` en cas d'échec). Le 19 juillet, deux runs complets à 245 règles ont
échoué au stockage (règles 154, 166 — dépassement `VARCHAR`, cf.
`docs/problemes_rencontres/ingestion/2_schema_text_columns.md`) après avoir
consommé et payé les tokens d'enrichissement, sans laisser aucune trace de coût
dans le log. Estimation reconstituée à partir des appels HTTP journalisés :
~9,9 € contre 9,13 € réellement facturés — écart cohérent avec l'imprécision déjà
connue des tarifs `KIMI_PRICE_*` (§6). Même famille de problème que les trois
manques ci-dessus : une information de provenance (ici, le coût réel d'un run)
qui existe en théorie mais n'est pas fiable en pratique dès qu'un cas d'échec
survient.

## 2. État actuel (vérifié)

### 2.1 Valeurs en dur, dupliquées

| Fichier | Ligne | Valeur |
| --- | --- | --- |
| `app/ingestion/llm_client.py` | 129-130 | `strategie_source="ia_import"`, `llm_provider="kimi-k2.6"` |
| `app/ingestion/schema.py` | 62-63 | mêmes valeurs, en défauts Pydantic |

La duplication permet aux deux emplacements de diverger.

### 2.2 Horodatage

`app/models/referentiel.py` n'a aucune colonne de date. `app/models/metier.py` en
possède : `audit.date_creation`, `audit.date_modification`, `audit_page.date_crawl`.

### 2.3 `.env`

Le fichier mélange deux natures. Les variables `AZURE_DEPLOYMENT_INGESTION`,
`AZURE_DEPLOYMENT_AUDIT_GENERATION`… encodent un **rôle du pipeline** dans un
fichier qui ne devrait porter que des accès. L'identité du modèle, elle, n'est
présente que dans un **commentaire** — donc illisible par le code :

```bash
AZURE_DEPLOYMENT_INGESTION=...       # Kimi K2.6 — enrichissement
```

Conséquence : lire cette variable donne un **nom de déploiement Azure**, chaîne
arbitraire propre à un compte, qui ne dit rien du modèle ayant réellement répondu.

## 3. Principe directeur

Deux règles gouvernent toutes les décisions qui suivent.

**Une seule autorité par valeur.** Le code lit l'autorité, il ne la recopie pas.
Toute valeur écrite à deux endroits finira par diverger — c'est exactement le
défaut de `llm_provider` aujourd'hui.

**Une seule responsabilité par couche.**

| Couche | Responsabilité unique |
| --- | --- |
| `.env` | annuaire : ce que la machine peut joindre, et avec quels secrets |
| `manifest.yml` | décisions : ce qui est vrai **maintenant** dans le pipeline |
| git | historique des décisions — déjà en place, gratuit |
| colonnes de provenance | quelle décision a produit **cette ligne** |

Corollaire important : **le manifeste ne conserve aucun historique interne.** Il
décrit l'état courant. `git log manifest.yml` répond à « qu'est-ce qui a changé et
quand ». Un manifeste qui s'auto-historiserait réimplémenterait git en moins bien
et redeviendrait une source de vérité concurrente.

## 4. Décisions de conception

| Point | Décision |
| --- | --- |
| Rôle du `.env` | Annuaire + secrets. Inventaire **par modèle** (`AZURE_MODEL_KIMI`), plus par rôle. Aucune connaissance du pipeline. |
| Rôle du manifeste | Affectation rôle → modèle. Commité. **Lu par le code**, donc porteur — un manifeste purement déclaratif serait pire que pas de manifeste. |
| Résolution manifeste → `.env` | **Explicite** : le manifeste nomme la variable (`env_var:`). Pas de convention implicite déduite du nom. |
| Contenu de `llm_model` | Le **nom logique** du manifeste (`kimi-k2.6`), jamais le nom de déploiement. Un nom de déploiement est une adresse propre à un compte : deux postes produiraient des provenances incomparables. |
| Version du prompt | Dans le **frontmatter de `enrich_rule.md`** — le fichier sait ce qu'il est et le sait encore après un déplacement. Absente du manifeste, pour ne pas dupliquer. |
| Format de version | **Entier simple** (`4`). Prolonge le vocabulaire « Version 1 / 2 / 3 » déjà employé dans `1_prompt_engineering.md`. Le semver n'a pas d'équivalent évident pour un prompt. |
| Nullabilité des colonnes | Toutes nullables. `NULL` = **produit avant l'instrumentation**. Après le chantier 3, une ligne encore à `NULL` signale un bug. |
| Sort de `llm_provider` | **Renommée** en `llm_model`, pas doublée. La colonne contient déjà un nom de modèle sous un nom de fournisseur : elle était mal nommée. |
| Emplacement du manifeste | `app/ingestion/manifest.yml` — cohérent avec `app/ingestion/prompts/` et avec le périmètre ingestion-seule. |
| Périmètre du manifeste | **Ingestion seule.** US1/US2 auront éventuellement le leur, une fois conçus. |
| Table `ingestion_run` | **Écartée.** Coût et durée sont déjà consignés en prose et le script est lancé de façon anecdotique. |
| Nommage des colonnes | Métier en français, technique en anglais (cf. §7). |

## 5. Modifications

### 5.1 `.env` et `.env.example`

Les variables passent d'un découpage par rôle à un inventaire par modèle :

```bash
# LLM — annuaire des modèles joignables
AZURE_AI_ENDPOINT=...
AZURE_AI_API_KEY=...

AZURE_MODEL_KIMI=...      # nom de déploiement Azure
AZURE_MODEL_GPT=...
```

L'affectation des rôles disparaît du `.env` : elle relève désormais du manifeste.

### 5.2 `app/ingestion/manifest.yml` *(créé)*

Emplacement retenu par cohérence avec `app/ingestion/prompts/`, qui héberge déjà
des ressources non Python du pipeline. Une racine `manifest.yml` serait plus
visible mais suggérerait une portée projet que l'on a écartée.

```yaml
# Décisions courantes du pipeline d'ingestion.
# Aucun historique ici : git s'en charge (git log manifest.yml).
# Aucun secret ici : voir .env.

enrichissement:
  modele: kimi-k2.6
  env_var: AZURE_MODEL_KIMI
```

Le fichier est volontairement mince au départ. Il grossira quand US1/US2
introduiront d'autres rôles — ou restera à ce périmètre s'ils reçoivent le leur.

### 5.3 `app/ingestion/prompts/enrich_rule.md`

Ajout d'un frontmatter :

```yaml
---
version: 3
---
```

La valeur reste `3` tant que le chantier 2 n'a pas produit la V4. C'est
volontaire : la version décrit le contenu actuel du fichier, pas une intention.

### 5.4 `app/ingestion/llm_client.py`

- Lecture du manifeste au démarrage : `modele` et `env_var`.
- Lecture du frontmatter de `enrich_rule.md` pour la version.
- L'appel LLM utilise le déploiement résolu depuis `env_var`.
- La provenance écrite utilise `modele` et `version` — **les mêmes valeurs que
  celles ayant servi à l'appel**, donc structurellement impossibles à désynchroniser.
- Suppression de `llm_provider="kimi-k2.6"` en dur (ligne 130).

### 5.5 `app/ingestion/schema.py`

- Ajout de `prompt_version: int | None` et `llm_model: str | None` à `EnrichedRule`.
- Suppression des défauts en dur `strategie_source` / `llm_provider` (lignes 62-63)
  s'ils s'avèrent morts — `llm_client.py` renseigne déjà ces champs explicitement.

### 5.6 `app/models/referentiel.py`

Sur `Regle`, `llm_provider` est **renommée** `llm_model` (même nature, nom correct),
et trois colonnes sont ajoutées :

```python
llm_model      = Column(String(64), nullable=True)   # renommage de llm_provider
prompt_version = Column(Integer, nullable=True)
created_at     = Column(DateTime, nullable=True)
updated_at     = Column(DateTime, nullable=True)
```

### 5.7 Migration Alembic `0009_*`

- `upgrade` : `alter_column` pour renommer `llm_provider` → `llm_model`, puis ajout
  des trois colonnes restantes, toutes nullables.
- `downgrade` : symétrique.

Aucune reprise de données : les 245 lignes existantes gardent leur `llm_model`
hérité (valeur périmée, qui sera écrasée au chantier 3) et restent à `NULL` sur les
trois nouvelles colonnes — ce qui est la sémantique voulue.

### 5.8 `app/ingestion/stockage.py`

- `upsert_rule()` : renseigne `prompt_version`, `llm_model`, `updated_at`, et
  `created_at` uniquement à la création.
- `load_enriched_rules_from_db()` : relit les champs de provenance (hook `--resume`).

### 5.9 `conception/MLD_qualicheck.md`

Consignation de la règle de nommage (§7) et des quatre nouvelles colonnes.

### 5.10 `scripts/ingestion.py` — visibilité du coût sur échec

Correctif ciblé, indépendant des colonnes de provenance mais découvert par la même
analyse (§1, quatrième manque) : déplacer le calcul et la journalisation du coût
(bloc `Tokens — entrée : ... coût estimé : ...`, actuellement après `Étape 4 —
Stockage`) juste après `Étape 3 — Enrichissement : terminée`, avant le bloc
`Étape 4`. `enriched.input_tokens`/`output_tokens` sont déjà entièrement
disponibles à ce point — aucun nouveau calcul, un déplacement de ~14 lignes.

Effet : un run qui échoue au stockage journalise désormais son coût réel, au lieu
de le perdre silencieusement.

## 6. Tarifs `KIMI_PRICE_*` — valeurs closes, emplacement encore ouvert

**Valeurs — closes (2026-07-22).** Reconstruites à partir d'une facture Azure
réelle (9,13 €, 19 juillet) et des tokens journalisés dans `logs/ingestion.log`
(6 runs journalisés + 2 runs à 245 règles échoués au stockage, jamais journalisés
— cf. §1 quatrième manque, §5.10 — dont l'entrée est estimée identique au run
réussi, même prompt et mêmes règles). Le facteur de correction (0,9205) est
appliqué aux deux tarifs publics Moonshot/OpenRouter en préservant leur ratio
entrée/sortie, faute de pouvoir séparer les deux taux à partir d'une facture
globale unique :

```text
KIMI_PRICE_INPUT_PER_1M  = 0,8008 €  (était 0,87 €)
KIMI_PRICE_OUTPUT_PER_1M = 3,3875 €  (était 3,68 €)
```

Ce n'est pas le tarif Azure officiel — c'est la meilleure reconstruction possible
avec une seule facture globale sans détail entrée/sortie. À corriger si un relevé
plus détaillé devient disponible. Appliquées dans `.env` et `.env.example`.

**Emplacement — reste ouvert.** L'argument de départ tient toujours : ce sont des
données de référence du projet, pas des secrets, et leur historique a de la
valeur (git le donnerait gratuitement si elles étaient dans le manifeste plutôt
que dans `.env`, non versionné). Décision non prise dans cet incrément — à
statuer, éventuellement en même temps que l'implémentation de `manifest.yml`
(§5.2).

## 7. Règle de nommage des colonnes

Le schéma applique déjà cette règle sans qu'elle ait été écrite — `embedding` et
`llm_provider` sont en anglais au milieu de colonnes françaises, et personne ne
l'a trouvé choquant.

**Le vocabulaire du domaine reste en français, le vocabulaire technique en anglais.**

C'est le principe de *langage omniprésent* du Domain-Driven Design (Eric Evans,
2003) : le code emploie les termes des experts du domaine plutôt qu'une traduction.
Ici l'argument est renforcé par le fait que le domaine **est** francophone —
`controle` en base provient littéralement d'un titre de section scrapé sur une page
française d'opquast.com. Le renommer `check` introduirait une couche de traduction
entre le code et sa source.

Le test qui tranche les cas futurs : *un auditeur qualité prononcerait-il ce mot en
parlant de son métier ?*

| Colonne | Français / Anglais | Pourquoi |
| --- | --- | --- |
| `objectif`, `controle`, `intitule` | français | termes Opquast |
| `audit.date_creation` | français | la date d'un audit est un fait métier, citée dans les rapports |
| `regle.created_at` | anglais | date d'insertion technique, sans intérêt métier |
| `embedding`, `llm_model` | anglais | objets techniques |

`audit.date_creation` en français et `regle.created_at` en anglais ne sont donc pas
une incohérence : ce sont deux dates de natures différentes.

Ce n'est pas un consensus universel — une école prône l'anglais intégral. Le choix
est assumé et argumenté ; ce qui compte est la cohérence, pas l'autorité.

## 8. Validation

### Critères de réussite

1. `manifest.yml` lu par le code : modifier `modele:` change la valeur écrite en
   base, sans toucher à aucun fichier `.py`.
2. Modifier `AZURE_MODEL_KIMI` dans `.env` change le déploiement appelé **sans**
   changer `llm_model` en base — l'adresse et l'identité sont bien séparées.
3. Modifier `version:` dans le frontmatter de `enrich_rule.md` change
   `prompt_version` en base.
4. Aucune chaîne de modèle en dur ne subsiste dans `app/` (`grep -rn "kimi"`).
5. Migration 0009 up/down OK ; les 245 lignes existantes passent à `NULL`.
6. Une ingestion de test (LLM bouchonné, `scripts/ingestion_test.py`) renseigne les
   quatre colonnes.
7. `pytest` vert, `ruff` propre.
8. Provoquer un échec de stockage (ex. réintroduire temporairement une valeur trop
   longue) sur un run à enrichissement réel ou simulé : le coût est journalisé
   malgré l'échec — vérifie le correctif §5.10.

### Ce qui n'est pas vérifiable ici

Que `kimi-k2.6` soit bien le modèle ayant réellement répondu reste une
**déclaration**, pas une observation : un déploiement Azure peut être repointé
depuis la console sans qu'aucun fichier du dépôt ne change. Si la réponse de l'API
expose le modèle utilisé, cette information serait supérieure. **À vérifier au
moment d'implémenter**, sans en faire un bloquant : la convention actuelle est déjà
très au-dessus de l'existant.

## 9. Hors périmètre (YAGNI)

- **Table `ingestion_run`**, coût, durée, distributions requêtables — écartée §4.
- **Manifeste pour US1/US2** — à concevoir avec eux, pas avant.
- **Prompt V4** → chantier 2. Cet incrément ne modifie pas le contenu du prompt,
  seulement son frontmatter.
- **Ré-ingestion réelle** → chantier 3. Aucun appel LLM facturé ici.
- **Reprise des 245 lignes existantes** — `NULL` est la valeur correcte.
- **Tableau de bord / monitorage temps réel** — relève d'US1, où les métriques
  existent réellement ; un script lancé trois fois n'a rien à surveiller.
- **Étapes 5-7** (chunking / embedding / indexation) — non touchées.
