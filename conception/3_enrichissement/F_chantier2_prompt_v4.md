# Chantier 2 — Prompt d'enrichissement V4

> Spec d'incrément. Fait suite au chantier 1 (scraping, fait) et à la spec E
> (provenance + manifeste, faite). Précède le chantier 3 (ré-ingestion réelle) —
> le prompt V4 est ce que le chantier 3 appliquera aux 245 règles. À valider
> avant implémentation.
>
> Date : 2026-07-25

## 1. Problème

L'ingestion complète des 245 règles Opquast (enrichissement Kimi K2.6, prompt
V3) a été suivie d'une revue manuelle règle par règle de la classification
`strategie_analyse`. Cette revue a produit un document consolidé,
`docs/problemes_rencontres/ingestion/3_recommandations_v4.md`, qui identifie
deux catégories de problèmes indépendantes des bugs de scraping déjà corrigés
au chantier 1 :

- **Le modèle de données force une seule stratégie par règle**, alors que
  certaines vérifications enchaînent naturellement plusieurs méthodes (ex.
  repérer visuellement un élément puis vérifier son balisage). Le LLM produit
  déjà des guides multi-stratégies en V3 ; le champ `strategie_analyse` ne le
  reflète pas.
- **Le prompt V3 sous-pondère certains critères de classification** : un guide
  peut spéculer au lieu de constater un fait vérifiable (règle 187), et un
  critère nécessitant une observation hors de la page web auditée (boîte mail,
  DNS...) peut être classé automatisable alors qu'il devrait être `manuel`
  (règle 111).

Cette spec couvre les 6 recommandations du chantier 2 du document
(R2.1 à R2.6) — uniquement le contenu du prompt, pas le code.

## 2. État actuel (vérifié)

- `app/ingestion/prompts/enrich_rule.md` : frontmatter `version: 3` (spec E),
  4 exemples few-shot (`statique`, `playwright`, `vision`, `manuel`), pas de
  notion de stratégie composite.
- `regle.strategie_analyse` : `VARCHAR(32)`, `NOT NULL`, **aucune contrainte de
  vocabulaire fermé en base ni en Pydantic** (`str` simple, non-vide) — la
  discipline de vocabulaire est portée entièrement par le prompt, pas par le
  code. Un composite du type `playwright+vision` (17 caractères) tient
  largement dans la colonne actuelle.
- Distribution V3 à préserver (indicative, sur données pré-chantier 1, donc à
  reconfirmer après ré-ingestion) : `statique` 46 %, `playwright` 42 %,
  `vision` 8 %, `manuel` 4 % — `manuel` 100 % justifié.

## 3. Principe directeur

**Cette spec ne modifie que `app/ingestion/prompts/enrich_rule.md`** (+ une
ligne de test qui vérifie sa version). Aucun changement de schéma, de modèle
Pydantic, de migration, ou de logique applicative — le mécanisme de lecture de
version (spec E, `load_prompt_version()`) est déjà en place et n'a besoin
d'aucune modification pour absorber `version: 4`.

**Regrouper avant de payer.** Toute évolution du prompt doit être en place
*avant* la ré-ingestion réelle (chantier 3, ~3 € de LLM) : une ré-ingestion
sur un prompt encore incomplet imposerait une seconde ré-ingestion facturée.
C'est pourquoi la décision D1 du document source (champ `necessite_donnees_test`)
est explicitement tranchée ci-dessous plutôt que laissée ouverte.

## 4. Décisions de conception

| Point | Décision |
| --- | --- |
| Sémantique du composite | **Parcours optimal** : composite dès qu'un enchaînement améliore la fiabilité ou l'économie de moyens, même si une seule méthode suffirait à un niveau minimal — pas réservé aux cas où l'enchaînement est strictement indispensable |
| Vocabulaire des composites | **Grammaire hybride** : toute **paire** (deux stratégies, jamais trois) parmi `statique`/`playwright`/`vision` (jamais `manuel` en composite) est autorisée si le même raisonnement s'applique, mais les deux familles déjà observées (`vision+statique`, `playwright+vision`) restent les few-shot d'ancrage — pas une liste fermée, mais pas un vocabulaire sans garde-fou non plus |
| Format des composites | `strategieA+strategieB`, l'ordre = séquence d'exécution (déjà le format envisagé par le document source) |
| Champ `necessite_donnees_test` (D1) | **Hors périmètre de cette spec.** N'influence pas la qualité de l'enrichissement (constat du document source) ; à évaluer séparément, sans lien avec le calendrier du prompt V4 |
| Critère « hors page web = manuel » (R2.4) | Rattaché à la **définition de `manuel`** dans le prompt (extension naturelle d'une règle de classification existante), pas à une instruction séparée dans `guide_analyse` |
| Format du guide pour un composite (R2.2) | Étapes numérotées et étiquetées par sous-stratégie : `Étape 1 [vision] : ... Étape 2 [statique] : ...` |
| Nombre de few-shot | 4 existants conservés + 2 nouveaux (composite, manuel hors-page-web) = 6 au total |
| Source des nouveaux few-shot | Contenu réel Opquast (règles 235 et 111, récupéré depuis `tmp/rules_acquises.json`) plutôt qu'un exemple inventé |
| Reclassement de règles (ex. 111) | **Ne se produit pas dans cette spec.** C'est une conséquence de la ré-ingestion réelle (chantier 3) qui appliquera le nouveau prompt — aucune donnée en base n'est modifiée ici |

## 5. Modifications

### 5.1 `app/ingestion/prompts/enrich_rule.md` — frontmatter

```yaml
---
version: 4
---
```

### 5.2 Extension de la définition de `manuel` (item 1, R2.4)

Le bullet `"manuel"` de la liste des 4 valeurs de base devient :

```markdown
- "manuel" : vraie exception, réservée aux cas où même une analyse visuelle par LLM ne peut pas trancher de façon fiable — typiquement un jugement légal fin, éditorial, ou un contexte métier propre au site qu'aucune observation de la page ne permet de déduire. Inclut aussi tout critère nécessitant d'observer quelque chose hors de la page web auditée elle-même (boîte mail, DNS, document PDF externe, SMS, second appareil...), même si une partie du parcours est automatisable sur la page.
```

### 5.3 Bloc « Stratégies composites » (item 1, après la liste des 4 valeurs, R2.1 + R2.5)

```markdown
**Stratégies composites** : si le parcours optimal pour vérifier la règle enchaîne deux de ces méthodes, utilise une valeur composite au format `strategie1+strategie2` (toujours deux stratégies, jamais trois ; l'ordre = séquence d'exécution), même si une seule méthode suffirait à un niveau minimal. Ce n'est pas réservé aux deux familles ci-dessous — toute paire parmi `statique`/`playwright`/`vision` (jamais `manuel` en composite) reste possible si le même raisonnement s'applique, mais demeure l'exception :
- `vision+statique` : une vérification visuelle identifie l'élément concerné, puis une inspection du DOM confirme le balisage HTML correct.
- `playwright+vision` : une interaction navigateur prépare une condition de rendu (désactivation CSS, mode impression...), puis une analyse visuelle juge le résultat.

**Signal supplémentaire** : un intitulé ou un contrôle contenant « ET » reliant deux critères de nature hétérogène (visuel et textuel, code et rendu...) est un signal fort de stratégie composite.
```

### 5.4 Trois ajouts à l'item 3 (`guide_analyse`, R2.2 + R2.3 + R2.6)

```markdown
Si la stratégie est composite, structure le guide en étapes numérotées et étiquetées par sous-stratégie, dans l'ordre d'exécution, en précisant ce que produit chaque étape et comment la suivante l'exploite. Format : « Étape 1 [vision] : ... Étape 2 [statique] : ... »

Ancre chaque vérification sur un critère factuel et vérifiable (présence ou absence d'un élément, d'un attribut, d'un texte) plutôt que sur une spéculation (« serait-il possible de... »).

Si la règle porte sur une cohérence à vérifier sur plusieurs pages, le guide doit explicitement demander de comparer plusieurs pages représentatives, quelle que soit la stratégie retenue.
```

### 5.5 Nouveaux few-shot (section « Exemples »)

**Exemple 5 : composite `vision+statique`** — basé sur la règle 235 réelle
(« Les éléments visuellement présentés sous forme de liste sont balisés de
façon appropriée dans le code source ») :

````markdown
### Exemple 5 : composite `vision+statique` — identification visuelle puis vérification du balisage

**Règle :** Les éléments visuellement présentés sous forme de liste sont balisés de façon appropriée dans le code source.

**Solution :** Utiliser les éléments HTML appropriés (ul/li, ol/li, dl/dt/dd) ou les rôles ARIA list/listitem équivalents.

**Contrôle :** Pour chaque page contenant une liste visuelle (puces, tirets, énumération), vérifier que le code source utilise le balisage correspondant.

**Réponse attendue :**
```json
{
  "strategie_analyse": "vision+statique",
  "strategie_justification": "Une identification visuelle repère les contenus présentés comme des listes (puces, tirets, numéros), une vérification du DOM confirme ensuite que le balisage HTML utilisé est correct.",
  "guide_analyse": "Étape 1 [vision] : parcourez visuellement chaque page et repérez tout contenu présenté comme une liste (puces, tirets, énumération numérotée). Étape 2 [statique] : pour chaque liste repérée, inspectez le DOM et vérifiez qu'elle utilise ul/li, ol/li, dl/dt/dd, ou les rôles ARIA list/listitem. Signalez toute liste visuelle sans balisage HTML correspondant."
}
```
````

**Exemple 6 : `manuel` — observation hors de la page web auditée** — basé sur la
règle 111 réelle (« Tous les mails fournissent au moins un moyen de contact »),
le cas mal classé identifié par la revue V3 :

````markdown
### Exemple 6 : "manuel" — observation hors de la page web auditée

**Règle :** Tous les mails fournissent au moins un moyen de contact.

**Solution :** Dans chaque mail adressé à l'utilisateur, y compris ceux en "no-reply", indiquer au moins un moyen de contact.

**Contrôle :** Vérifier pour chaque mail envoyé à l'utilisateur par le site qu'il fournit au moins un moyen de contact.

**Réponse attendue :**
```json
{
  "strategie_analyse": "manuel",
  "strategie_justification": "Vérifier le contenu des emails effectivement envoyés par le site nécessite d'observer une boîte mail réelle, hors de la page web auditée — aucune méthode automatisée sur le site seul ne peut confirmer ce point.",
  "guide_analyse": "Identifiez les déclencheurs d'envoi d'email du site (inscription, confirmation, notification, réinitialisation de mot de passe...). Déclenchez chaque scénario avec une adresse de test et consultez la boîte mail réelle. Vérifiez que chaque email reçu, y compris ceux en no-reply, mentionne au moins un moyen de contact (adresse postale, téléphone, formulaire, autre email)."
}
```
````

### 5.6 `tests/unit/ingestion/test_enrichment.py`

`test_load_prompt_version_reads_frontmatter` : assertion mise à jour de
`== 3` à `== 4`. Seule touche de code de cette spec — mécanique, conséquence
directe de 5.1.

## 6. Validation

### Critères vérifiables immédiatement (sans appel LLM)

1. `enrich_rule.md` : frontmatter à `version: 4`
2. Les 3 blocs d'instructions (5.2 manuel étendu, 5.3 composites + signal
   « ET », 5.4 format composite + factuel + multi-page) sont présents
3. 6 exemples few-shot au total (4 existants + 2 nouveaux)
4. `test_load_prompt_version_reads_frontmatter` passe avec `== 4`
5. `git diff` limité à `enrich_rule.md` et à la ligne de test citée — aucun
   autre fichier Python, aucune migration, aucun changement de schéma
6. `pytest`/`ruff` restent verts sur l'ensemble de la suite

### Critères vérifiables seulement après la ré-ingestion réelle (chantier 3, hors périmètre de cette spec)

- Règle 111 classée `manuel` (au lieu de `playwright` en V3)
- Règles 235/245 : composite `vision+statique` ou guide qui l'explicite
- Règle 65 (marqueur « ET ») réévaluée pour composite
- Règle 187 : guide reformulé factuel, plus spéculatif
- Revue manuelle ciblée sur les mêmes règles que la revue V3 (65, 96, 98,
  116-118, 189, 206-217...) pour comparer avant/après
- Distribution globale (`statique`/`playwright`/`vision`/`manuel` + nouveaux
  composites) reconfirmée, en cohérence avec les points positifs à préserver
  (§2)

## 7. Hors périmètre (YAGNI)

- **`necessite_donnees_test`** (D1) — reporté, décision §4
- **Ré-ingestion réelle** → chantier 3. Cette spec ne modifie que le prompt,
  aucun appel LLM facturé ici
- **Reclassement effectif des règles** (111 et autres) → conséquence du
  chantier 3, pas de cette spec
- **Contrainte de vocabulaire fermé en base ou en Pydantic** — la discipline
  reste portée par le prompt, cohérent avec l'existant (§2)
- **Étapes 5-7** (chunking / embedding / indexation) — non touchées
