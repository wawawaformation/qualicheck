# Chantier — Prompt d'enrichissement V5

> Spec d'incrément. Fait suite au chantier 2 (prompt V4, fait) et à la
> ré-ingestion réelle qui l'a validé. Précède une nouvelle ré-ingestion
> complète des 245 règles avec ce prompt V5. À valider avant implémentation.
>
> Date : 2026-07-25

## 1. Problème

La ré-ingestion réelle des 245 règles avec le prompt V4 a été suivie d'une
revue manuelle ciblée et d'un balayage complet par 5 agents en parallèle,
consolidés dans
`docs/problemes_rencontres/ingestion/4_recommandations_v5.md`. Cette revue a
confirmé une classification globalement de très bonne qualité (généralisation
réelle au-delà des few-shot, `manuel` bien maîtrisé, zéro guide spéculatif —
voir §5 du document), mais a identifié trois défauts distincts, tous corrigés
dans cette spec :

- **Le format composite n'encode que l'ordre**, jamais la nature de la
  relation entre deux stratégies — implicitement toujours "PUIS" alors que
  certaines règles (marqueur "ET" de R2.5) décrivent en réalité deux
  vérifications indépendantes.
- **Le critère "manuel" (R2.4) est trop étroit** : il ne couvre que
  l'observation hors-page via un canal externe nommé, pas le cas plus général
  d'une vérification qui exige de constater qu'un mécanisme fonctionne
  *effectivement*, au-delà de sa simple présence syntaxique (5 règles
  affectées : 24, 69, 96, 113, 243).
- **Incohérence indépendante entre `playwright` et `statique`** sur les
  vérifications HTTP brutes (en-têtes, code de statut) — 7 règles classées
  `playwright` pour une opération que 6 règles analogues font en `statique`.

## 2. État actuel (vérifié)

- `app/ingestion/prompts/enrich_rule.md` : frontmatter `version: 4`, 6
  exemples few-shot, grammaire composite `strategieA+strategieB` (2
  stratégies parmi statique/playwright/vision, jamais trois, jamais avec
  `manuel`, ordre = séquence d'exécution).
- Aucune contrainte de vocabulaire en base ni en Pydantic sur
  `strategie_analyse` (`String(32)` sur `regle`, `str` simple côté Pydantic)
  — le caractère `&` proposé ci-dessous n'a besoin d'aucun changement de
  schéma, `vision&statique` (15 caractères) tient largement.

## 3. Principe directeur

Identique au chantier 2 : **cette spec ne modifie que
`app/ingestion/prompts/enrich_rule.md`** (+ une ligne de test de version).
Aucun changement de schéma, de modèle Pydantic, de migration.

**Décisions déjà actées avec David (2026-07-25), non rouvertes ici** :

- Une fois ce prompt V5 validé et implémenté, **ré-ingestion complète des
  245 règles** (pas de ré-ingestion ciblée) — pour valider la non-régression
  sur les points positifs de V4 autant que la correction des 3 défauts
- **`enrich_again`** (script de réécriture ciblée par LLM) — hors périmètre
  de ce chantier, reporté après le **prochain** audit (post-V5)

## 4. Décisions de conception

| Point | Décision |
| --- | --- |
| Séparateur ET | **`&`** — `strategieA&strategieB` signifie deux vérifications indépendantes (pas de dépendance causale), par opposition à `+` qui reste PUIS (séquentiel, l'ordre = séquence d'exécution) |
| Cardinalité du composite | **Toujours deux stratégies, jamais trois**, inchangé par rapport à V4 — aucune règle des 245 observées ne prouve un besoin réel de 3 étapes ; le prompt continue de l'interdire explicitement, mais le prochain audit post-V5 devra chercher des signes de compression forcée (un guide qui décrit implicitement 3 étapes malgré 2 labels) |
| `manuel` en composite | **Toujours interdit.** `manuel` reste une valeur pure qui absorbe l'intégralité du contrôle dès qu'une partie l'exige (ex. règle 24 : le volet "acceptée" automatisable est perdu, la règle passe entièrement `manuel`) — cohérent avec YAGNI, aucun consommateur (agent d'audit US1) n'existe encore pour exploiter une granularité mixte auto/manuel |
| OU (alternative contextuelle) | **Non implémenté.** Aucune occurrence sur 245 règles réelles (deux ingestions), et raison structurelle : les règles Opquast décrivent des procédures d'audit universelles, pas une logique conditionnelle dépendant de l'implémentation d'un site précis. À réévaluer seulement si un vrai cas apparaît |
| Critère "manuel" élargi (R2.4) | Reformulé pour couvrir toute exigence de vérification **effective/réelle** d'un mécanisme, au-delà de sa simple présence syntaxique, en plus du critère existant (canal externe nommé) |
| Nouveaux few-shot | **117** (`statique`, image-lien — exhaustif et factuel) et **243** (`manuel`, contrôle à deux volets — illustre à la fois le critère élargi et la règle d'absorption). 6 → 8 exemples, aucun retiré |
| Correctif en-têtes HTTP (O6) | Précision explicite ajoutée : la lecture d'un en-tête ou d'un code de statut de réponse HTTP est vérifiable par simple requête, donc `statique`, même si la page elle-même a été chargée via un crawler |
| Reclassement des 12 règles à problème | **Ne se produit pas dans cette spec.** Conséquence de la ré-ingestion complète décidée en §3, pas d'une correction manuelle en base |

## 5. Modifications

### 5.1 `app/ingestion/prompts/enrich_rule.md` — frontmatter

```yaml
---
version: 5
---
```

### 5.2 Extension de la définition de `manuel` (remplace le texte V4)

```markdown
- "manuel" : vraie exception, réservée aux cas où même une analyse visuelle par LLM ne peut pas trancher de façon fiable — typiquement un jugement légal, éditorial ou sémantique fin, ou un contexte métier propre au site qu'aucune observation de la page ne permet de déduire. Inclut aussi (a) tout critère nécessitant d'observer quelque chose hors de la page web auditée elle-même (boîte mail, DNS, document PDF externe, SMS, second appareil...), et (b) toute exigence de vérifier qu'un mécanisme fonctionne effectivement/réellement, au-delà de sa simple présence syntaxique, dès qu'aucune méthode automatisée ne peut observer ce résultat — même si une partie du parcours reste automatisable sur la page.
```

### 5.3 Bloc "Stratégies composites" — ajout de ET et rappel de la cardinalité

Remplace le bloc composite de V4 par :

```markdown
**Stratégies composites** : si le parcours optimal pour vérifier la règle enchaîne deux de ces méthodes, utilise une valeur composite. Deux formats, jamais mélangés dans une même valeur, toujours deux stratégies (jamais trois, jamais avec `manuel`) :
- `strategieA+strategieB` (PUIS) : B dépend du résultat de A, l'ordre = séquence d'exécution. Ex. `vision+statique` : une vérification visuelle identifie l'élément concerné, puis une inspection du DOM confirme le balisage HTML correct.
- `strategieA&strategieB` (ET) : les deux vérifications sont indépendantes, sans dépendance causale entre elles — typiquement quand l'intitulé ou le contrôle contient « ET » reliant deux critères de nature hétérogène (visuel et textuel, code et rendu...).

Ce n'est pas réservé aux familles ci-dessus — toute paire parmi `statique`/`playwright`/`vision` reste possible si le même raisonnement s'applique, mais demeure l'exception.
```

### 5.4 Ajout à l'item `guide_analyse` — format pour ET

Après les 3 phrases déjà présentes en V4 (composite en étapes, factuel, multi-page), ajouter :

```markdown
Si la stratégie est `strategieA&strategieB` (ET), présente les deux vérifications comme indépendantes, sans numérotation séquentielle imposant un ordre : « Vérification [A] : ... Vérification [B] (indépendante) : ... »
```

### 5.5 Correctif en-têtes HTTP (O6)

Ajout après le bloc composite (§5.3) :

```markdown
**Précision** : la lecture d'un en-tête de réponse HTTP ou d'un code de statut (ex. 404, X-Frame-Options, Content-Type) est vérifiable par une simple requête, donc `statique` — même si atteindre la page nécessite un crawler. Ce n'est pas une interaction navigateur au sens de `playwright`.
```

### 5.6 Nouveaux few-shot (section "Exemples")

**Exemple 7 : `statique` — image-lien** (règle 117 réelle) :

````markdown
### Exemple 7 : "statique" — alternative textuelle d'une image-lien

**Règle :** Chaque image-lien est dotée d'une alternative textuelle appropriée.

**Solution :** Donner à chaque élément `img`/`area` concerné un attribut `alt` indiquant la cible ou le rôle du lien ; indiquer la cible ou le rôle du lien dans le contenu de chaque élément `object`/`canvas` concerné.

**Contrôle :** Vérifier que l'attribut `alt` (ou le contenu pour `object`/`canvas`) de chaque image-lien indique la cible ou le rôle du lien.

**Réponse attendue :**
```json
{
  "strategie_analyse": "statique",
  "strategie_justification": "Les attributs alt des éléments img et area, ainsi que les contenus textuels des éléments object et canvas inclus dans des liens, sont directement inspectables dans le DOM sans exécution JavaScript ni interaction.",
  "guide_analyse": "Parcourez le DOM pour identifier chaque lien <a> ou élément à rôle de lien dont le contenu est exclusivement un <img>, <area>, <object> ou <canvas>. Vérifiez que chaque img/area dispose d'un attribut alt non vide indiquant la cible du lien, et que chaque object/canvas contient un texte non vide équivalent. Signalez tout élément de lien image dépourvu d'alternative textuelle appropriée."
}
```
````

**Exemple 8 : `manuel` — contrôle à deux volets, dont un nécessite un examen manuel** (règle 243 réelle) :

````markdown
### Exemple 8 : "manuel" — vérification partiellement automatisable, mais le jugement de fond ne l'est pas

**Règle :** Les titres des tableaux de données sont renseignés.

**Solution :** Utiliser et renseigner l'élément HTML `caption` pour chaque tableau de données.

**Contrôle :** Vérifier la présence de l'élément `caption`. Contrôler la pertinence de l'élément `caption`, qui doit permettre d'identifier la nature des informations apportées par le tableau. Cette vérification peut être partiellement automatisée pour la présence de l'élément, mais le contrôle de sa pertinence nécessite un examen manuel.

**Réponse attendue :**
```json
{
  "strategie_analyse": "manuel",
  "strategie_justification": "Le contrôle lui-même indique que la présence de l'élément caption est automatisable, mais que juger sa pertinence (identifie-t-il bien la nature du tableau ?) nécessite un examen manuel — un jugement sémantique qu'aucune inspection factuelle du DOM ne peut fiabiliser. Le volet automatisable est absorbé par le volet manuel, pas de composite avec manuel.",
  "guide_analyse": "Pour chaque tableau de données du site, identifiez la présence de l'élément caption. Faites relire par un humain le texte de chaque caption présent : vérifiez qu'il décrit effectivement la nature des données du tableau (et non un intitulé générique ou décoratif). Signalez les tableaux sans caption, ainsi que les captions présents mais non pertinents au regard du contenu réel du tableau."
}
```
````

### 5.7 `tests/unit/ingestion/test_enrichment.py`

Les deux assertions `prompt_version == 4` (déjà mises à jour de 3→4 au
chantier 2) passent à `== 5` :
`test_load_prompt_version_reads_frontmatter` et `test_enrich_single_rule_success`.
Seule touche de code de cette spec — mécanique.

## 6. Validation

### Critères vérifiables immédiatement (sans appel LLM)

1. `enrich_rule.md` : frontmatter à `version: 5`
2. Les blocs modifiés (manuel étendu §5.2, composites `+`/`&` §5.3, guide ET
   §5.4, précision en-têtes HTTP §5.5) sont présents
3. 8 exemples few-shot au total (6 existants + 2 nouveaux)
4. Les deux assertions de version passent avec `== 5`
5. `git diff` limité à `enrich_rule.md` et aux deux lignes de test citées
6. `pytest`/`ruff` restent verts sur l'ensemble de la suite

### Critères vérifiables seulement après la ré-ingestion réelle complète (hors périmètre de cette spec)

- Les 5 règles de la famille "manuel sous-appliqué" (24, 69, 96, 113, 243)
  reclassées `manuel`
- Les 7 règles d'en-têtes HTTP (206, 207, 210, 211, 222, 226, 227) reclassées
  `statique`
- Règle 65 : composite exprimé en `&` (ET) plutôt qu'en `+` (PUIS), si le
  marqueur "ET" s'applique réellement à une relation indépendante
- Non-régression sur les points positifs de V4 (§5 de
  `4_recommandations_v5.md`) : généralisation au-delà des few-shot, `manuel`
  toujours bien maîtrisé (pas de sur-classement), zéro guide spéculatif
- Recherche de signes de compression forcée à 3 étapes (cf. §4, cardinalité)
  lors du prochain audit

## 7. Hors périmètre (YAGNI)

- **`enrich_again`** — reporté après le prochain audit post-V5 (décision §3)
- **Ré-ingestion réelle elle-même** — décidée (§3) mais hors périmètre de
  cette spec, qui ne couvre que le contenu du prompt
- **Reclassement effectif des 12 règles à problème** — conséquence de la
  ré-ingestion, pas de cette spec
- **Grammaire pour OU** — aucune occurrence observée, raison structurelle
  (§4)
- **Composite à 3 stratégies** — maintenu interdit, à réévaluer seulement si
  le prochain audit trouve une preuve de compression forcée
- **`manuel` en composite** — maintenu interdit (§4)
- **Étapes 5-7** (chunking / embedding / indexation) — non touchées
