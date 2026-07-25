# Prompt d'enrichissement V5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Faire évoluer `app/ingestion/prompts/enrich_rule.md` de la version 4 à la version 5 : grammaire composite étendue (`+` PUIS / `&` ET), critère "manuel" élargi, correctif en-têtes HTTP, 2 nouveaux few-shot — sans toucher au code applicatif au-delà de deux lignes de test.

**Architecture:** Un seul artefact modifié — le fichier de prompt — plus les deux lignes de test qui vérifient sa version (déjà lues dynamiquement par `load_prompt_version()`, spec E, aucun changement de mécanisme nécessaire).

**Tech Stack:** Markdown + frontmatter YAML (prompt), pytest (tests de version existants).

**Spec source:** `conception/2_ingestion/H_chantier_prompt_v5.md` (ne pas modifier son contenu dans ce plan — seul le prompt change).

## Global Constraints

- **Périmètre strict** : seuls `app/ingestion/prompts/enrich_rule.md` et `tests/unit/ingestion/test_enrichment.py` sont modifiés. Aucun changement de schéma, de migration, de modèle Pydantic, ou de logique applicative (spec §3).
- **Composites** : toujours une **paire** de stratégies parmi `statique`/`playwright`/`vision` (jamais trois, jamais `manuel` en composite). Deux formats distincts : `strategieA+strategieB` (PUIS, séquentiel) et `strategieA&strategieB` (ET, indépendant) (spec §4).
- **Aucun reclassement de règle en base** dans ce chantier — conséquence de la ré-ingestion complète décidée séparément, pas de ce plan (spec §3, §7).
- **`enrich_again`** et **grammaire OU** : hors périmètre, ne pas les implémenter (spec §7).
- `ruff check` propre et `pytest` vert avant tout commit (`CLAUDE.md` racine du projet).
- Commits : titre en anglais, corps en français (`~/.claude/CLAUDE.md`).

---

### Task 1: Prompt V5 — contenu + tests de version

**Files:**
- Modify: `app/ingestion/prompts/enrich_rule.md`
- Modify: `tests/unit/ingestion/test_enrichment.py`

**Interfaces:**
- Consumes: `load_prompt_version()` (déjà défini dans `app/ingestion/llm_client.py`, spec E — ne pas modifier, il lit déjà dynamiquement le frontmatter).
- Produces: rien de consommé par du code — cette tâche ne change que du contenu de prompt lu au runtime, aucune nouvelle fonction ni signature.

- [ ] **Step 1: Écrire les tests qui échouent (bump de version, 2 assertions)**

Dans `tests/unit/ingestion/test_enrichment.py`, classe `TestManifestAndPromptVersion`, modifier :

```python
    def test_load_prompt_version_reads_frontmatter(self):
        from app.ingestion.llm_client import load_prompt_version

        assert load_prompt_version() == 4
```

en :

```python
    def test_load_prompt_version_reads_frontmatter(self):
        from app.ingestion.llm_client import load_prompt_version

        assert load_prompt_version() == 5
```

Et dans la classe `TestLLMClient`, méthode `test_enrich_single_rule_success`, modifier :

```python
        assert enriched.prompt_version == 4
```

en :

```python
        assert enriched.prompt_version == 5
```

- [ ] **Step 2: Run pour vérifier l'échec**

Run: `uv run pytest tests/unit/ingestion/test_enrichment.py -v -k "test_load_prompt_version_reads_frontmatter or test_enrich_single_rule_success"`
Expected: les deux FAIL (`assert 4 == 5`) — le frontmatter du prompt est encore à `version: 4`.

- [ ] **Step 3: Frontmatter — bump de version (spec §5.1)**

Dans `app/ingestion/prompts/enrich_rule.md`, lignes 1-3, remplacer :

```yaml
---
version: 4
---
```

par :

```yaml
---
version: 5
---
```

- [ ] **Step 4: Extension de la définition de `manuel` (spec §5.2)**

Remplacer la ligne :

```markdown
   - `"manuel"` : **vraie exception**, réservée aux cas où même une analyse visuelle par LLM ne peut pas trancher de façon fiable — typiquement un jugement légal fin, éditorial, ou un contexte métier propre au site qu'aucune observation de la page ne permet de déduire. Inclut aussi tout critère nécessitant d'observer quelque chose hors de la page web auditée elle-même (boîte mail, DNS, document PDF externe, SMS, second appareil...), même si une partie du parcours est automatisable sur la page.
```

par :

```markdown
   - `"manuel"` : **vraie exception**, réservée aux cas où même une analyse visuelle par LLM ne peut pas trancher de façon fiable — typiquement un jugement légal, éditorial ou sémantique fin, ou un contexte métier propre au site qu'aucune observation de la page ne permet de déduire. Inclut aussi (a) tout critère nécessitant d'observer quelque chose hors de la page web auditée elle-même (boîte mail, DNS, document PDF externe, SMS, second appareil...), et (b) toute exigence de vérifier qu'un mécanisme fonctionne effectivement/réellement, au-delà de sa simple présence syntaxique, dès qu'aucune méthode automatisée ne peut observer ce résultat — même si une partie du parcours reste automatisable sur la page.
```

- [ ] **Step 5: Bloc "Stratégies composites" — ajout du séparateur ET (spec §5.3)**

Remplacer le bloc composite existant :

```markdown
   **Stratégies composites** : si le parcours optimal pour vérifier la règle enchaîne deux de ces méthodes, utilise une valeur composite au format `strategie1+strategie2` (toujours deux stratégies, jamais trois ; l'ordre = séquence d'exécution), même si une seule méthode suffirait à un niveau minimal. Ce n'est pas réservé aux deux familles ci-dessous — toute paire parmi `statique`/`playwright`/`vision` (jamais `manuel` en composite) reste possible si le même raisonnement s'applique, mais demeure l'exception :
   - `vision+statique` : une vérification visuelle identifie l'élément concerné, puis une inspection du DOM confirme le balisage HTML correct.
   - `playwright+vision` : une interaction navigateur prépare une condition de rendu (désactivation CSS, mode impression...), puis une analyse visuelle juge le résultat.

   **Signal supplémentaire** : un intitulé ou un contrôle contenant « ET » reliant deux critères de nature hétérogène (visuel et textuel, code et rendu...) est un signal fort de stratégie composite.
```

par :

```markdown
   **Stratégies composites** : si le parcours optimal pour vérifier la règle enchaîne deux de ces méthodes, utilise une valeur composite. Deux formats, jamais mélangés dans une même valeur, toujours deux stratégies (jamais trois, jamais avec `manuel`) :
   - `strategieA+strategieB` (PUIS) : B dépend du résultat de A, l'ordre = séquence d'exécution. Ex. `vision+statique` : une vérification visuelle identifie l'élément concerné, puis une inspection du DOM confirme le balisage HTML correct.
   - `strategieA&strategieB` (ET) : les deux vérifications sont indépendantes, sans dépendance causale entre elles — typiquement quand l'intitulé ou le contrôle contient « ET » reliant deux critères de nature hétérogène (visuel et textuel, code et rendu...).

   Ce n'est pas réservé aux familles ci-dessus — toute paire parmi `statique`/`playwright`/`vision` reste possible si le même raisonnement s'applique, mais demeure l'exception.

   **Précision** : la lecture d'un en-tête de réponse HTTP ou d'un code de statut (ex. 404, X-Frame-Options, Content-Type) est vérifiable par une simple requête, donc `statique` — même si atteindre la page nécessite un crawler. Ce n'est pas une interaction navigateur au sens de `playwright`.
```

(Ce remplacement couvre à la fois §5.3 — grammaire ET — et §5.5 — précision en-têtes HTTP, insérée juste après comme le demande la spec : "Ajout après le bloc composite".)

- [ ] **Step 6: Ajout au `guide_analyse` — format pour ET (spec §5.4)**

Remplacer :

```markdown
   Si la règle porte sur une cohérence à vérifier sur plusieurs pages, le guide doit explicitement demander de comparer plusieurs pages représentatives, quelle que soit la stratégie retenue.
```

par :

```markdown
   Si la règle porte sur une cohérence à vérifier sur plusieurs pages, le guide doit explicitement demander de comparer plusieurs pages représentatives, quelle que soit la stratégie retenue.

   Si la stratégie est `strategieA&strategieB` (ET), présente les deux vérifications comme indépendantes, sans numérotation séquentielle imposant un ordre : « Vérification [A] : ... Vérification [B] (indépendante) : ... »
```

- [ ] **Step 7: Nouveau few-shot — Exemple 7 (spec §5.6, basé sur la règle réelle 117)**

Après l'Exemple 6 (qui se termine par le bloc JSON de la règle 111, juste avant la ligne `---` finale), insérer :

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

- [ ] **Step 8: Nouveau few-shot — Exemple 8 (spec §5.6, basé sur la règle réelle 243)**

Immédiatement après l'Exemple 7 inséré au Step 7, avant la ligne `---` finale, insérer :

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

Le fichier garde sa ligne `---` finale suivie de `Génère maintenant une réponse JSON pour la règle ci-dessus.` après ce nouvel exemple — ne pas la dupliquer, seulement insérer les deux exemples avant elle.

- [ ] **Step 9: Run pour vérifier le succès**

Run: `uv run pytest tests/unit/ingestion/test_enrichment.py -v`
Expected: tous PASS, y compris `test_load_prompt_version_reads_frontmatter` et `test_enrich_single_rule_success` (`== 5`).

- [ ] **Step 10: Vérifications structurelles (spec §6, critères immédiats)**

Run: `head -3 app/ingestion/prompts/enrich_rule.md`
Expected :
```yaml
---
version: 5
---
```

Run: `grep -c "^### Exemple" app/ingestion/prompts/enrich_rule.md`
Expected: `8`

Run: `grep -c "strategieA&strategieB\|strategieA+strategieB" app/ingestion/prompts/enrich_rule.md`
Expected: au moins `4` (bloc composites mentionne les deux formats, plus la phrase du guide sur ET)

Run: `grep -c "en-tête de réponse HTTP" app/ingestion/prompts/enrich_rule.md`
Expected: au moins `1`

- [ ] **Step 11: Suite complète + lint**

Run: `uv run pytest tests/ -v && uv run ruff check .`
Expected: tous les tests PASS (pas seulement `test_enrichment.py`), `ruff` propre.

- [ ] **Step 12: Vérifier le périmètre du diff**

Run: `git status -s`
Expected: seuls `app/ingestion/prompts/enrich_rule.md` et `tests/unit/ingestion/test_enrichment.py` apparaissent modifiés (spec §6 critère 5).

- [ ] **Step 13: Commit**

```bash
git add app/ingestion/prompts/enrich_rule.md tests/unit/ingestion/test_enrichment.py
git commit -m "$(cat <<'EOF'
feat: bump enrichment prompt to V5 (ET composite, wider manuel, HTTP fix)

Couvre docs/problemes_rencontres/ingestion/4_recommandations_v5.md et
conception/2_ingestion/H_chantier_prompt_v5.md :
- Grammaire composite étendue : "+" reste PUIS, nouveau séparateur "&"
  pour ET (deux vérifications indépendantes, ex. marqueur "ET" R2.5)
- Critère "manuel" élargi : couvre toute exigence de vérification
  effective/réelle, pas seulement l'observation via un canal externe
- Précision : en-tête/code de statut HTTP = statique, pas playwright
- 2 nouveaux few-shot (règles réelles 117, 243), 6 → 8 exemples

Aucun changement de schéma ni de code applicatif au-delà des deux
assertions de version (prompt_version passe à 5).
EOF
)"
```

---

### Task 2: Validation finale — récapitulatif des critères

**Files:** aucun (tâche de vérification uniquement).

- [ ] **Step 1: Récapitulatif des critères immédiats (spec §6)**

Cocher chacun, déjà vérifié dans la Task 1 :

1. Frontmatter `version: 5` → Task 1 Step 3, vérifié Step 10
2. Les blocs modifiés présents (manuel étendu, composites `+`/`&`, guide ET,
   précision en-têtes HTTP) → Task 1 Steps 4-6, vérifié Step 10
3. 8 exemples few-shot au total → Task 1 Steps 7-8, vérifié Step 10
4. Les deux assertions de version passent avec `== 5` → Task 1 Step 9
5. `git diff` limité aux deux fichiers attendus → Task 1 Step 12
6. `pytest`/`ruff` verts sur l'ensemble de la suite → Task 1 Step 11

- [ ] **Step 2: Rappel des critères différés (spec §6, hors périmètre de ce plan)**

Ces critères ne sont vérifiables qu'après la ré-ingestion réelle complète
(décidée séparément, hors périmètre de cette spec/ce plan) — ne pas tenter de
les vérifier ici :

- Règles 24, 69, 96, 113, 243 reclassées `manuel`
- Règles 206, 207, 210, 211, 222, 226, 227 reclassées `statique`
- Règle 65 : composite exprimé en `&` (ET) si applicable
- Non-régression sur les points positifs de V4
- Recherche de signes de compression forcée à 3 étapes

- [ ] **Step 3: Rapport final**

Confirmer à David que le prompt V5 est en place et prêt pour la ré-ingestion
complète des 245 règles décidée séparément.

---
