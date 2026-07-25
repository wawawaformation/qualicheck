# Prompt d'enrichissement V4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Faire évoluer `app/ingestion/prompts/enrich_rule.md` de la version 3 à la version 4 pour couvrir les 6 recommandations R2.1-R2.6 (stratégies composites, critère hors-page-web, factuel > spéculatif, marqueur « ET », consigne multi-pages), sans toucher au code applicatif au-delà d'une ligne de test.

**Architecture:** Un seul artefact modifié — le fichier de prompt lui-même — plus la ligne de test qui vérifie sa version (déjà lue dynamiquement par `load_prompt_version()`, spec E, aucun changement de mécanisme nécessaire).

**Tech Stack:** Markdown + frontmatter YAML (prompt), pytest (test de version existant).

**Spec source:** `conception/2_ingestion/F_chantier2_prompt_v4.md` (ne pas modifier son contenu dans ce plan — seul le prompt change).

## Global Constraints

- **Périmètre strict** : seuls `app/ingestion/prompts/enrich_rule.md` et `tests/unit/ingestion/test_enrichment.py` sont modifiés. Aucun changement de schéma, de migration, de modèle Pydantic, ou de logique applicative (spec §3).
- **Composites** : toujours une **paire** de stratégies parmi `statique`/`playwright`/`vision` (jamais trois, jamais `manuel` en composite), format `strategieA+strategieB`, l'ordre = séquence d'exécution (spec §4).
- **Aucun reclassement de règle en base** dans ce chantier — c'est une conséquence de la ré-ingestion réelle (chantier 3, hors périmètre), pas de ce plan (spec §4, §7).
- **`necessite_donnees_test` (D1)** : hors périmètre, ne pas l'ajouter (spec §4, §7).
- `ruff check` propre et `pytest` vert avant tout commit (`CLAUDE.md` racine du projet).
- Commits : titre en anglais, corps en français (`~/.claude/CLAUDE.md`).

---

### Task 1: Prompt V4 — contenu + test de version

**Files:**
- Modify: `app/ingestion/prompts/enrich_rule.md`
- Modify: `tests/unit/ingestion/test_enrichment.py`

**Interfaces:**
- Consumes: `load_prompt_version()` (déjà défini dans `app/ingestion/llm_client.py`, spec E — ne pas modifier, il lit déjà dynamiquement le frontmatter).
- Produces: rien de consommé par du code — cette tâche ne change que du contenu de prompt lu au runtime, aucune nouvelle fonction ni signature.

- [ ] **Step 1: Écrire le test qui échoue (bump de version)**

Dans `tests/unit/ingestion/test_enrichment.py`, classe `TestManifestAndPromptVersion`, modifier :

```python
    def test_load_prompt_version_reads_frontmatter(self):
        from app.ingestion.llm_client import load_prompt_version

        assert load_prompt_version() == 3
```

en :

```python
    def test_load_prompt_version_reads_frontmatter(self):
        from app.ingestion.llm_client import load_prompt_version

        assert load_prompt_version() == 4
```

- [ ] **Step 2: Run pour vérifier l'échec**

Run: `uv run pytest tests/unit/ingestion/test_enrichment.py::TestManifestAndPromptVersion::test_load_prompt_version_reads_frontmatter -v`
Expected: FAIL (`assert 3 == 4`) — le frontmatter du prompt est encore à `version: 3`.

- [ ] **Step 3: Frontmatter — bump de version (spec §5.1)**

Dans `app/ingestion/prompts/enrich_rule.md`, ligne 1-3, remplacer :

```yaml
---
version: 3
---
```

par :

```yaml
---
version: 4
---
```

- [ ] **Step 4: Extension de la définition de `manuel` (spec §5.2, R2.4)**

Dans le même fichier, remplacer la ligne 25 :

```markdown
   - `"manuel"` : **vraie exception**, réservée aux cas où même une analyse visuelle par LLM ne peut pas trancher de façon fiable — typiquement un jugement légal fin, éditorial, ou un contexte métier propre au site qu'aucune observation de la page ne permet de déduire.
```

par :

```markdown
   - `"manuel"` : **vraie exception**, réservée aux cas où même une analyse visuelle par LLM ne peut pas trancher de façon fiable — typiquement un jugement légal fin, éditorial, ou un contexte métier propre au site qu'aucune observation de la page ne permet de déduire. Inclut aussi tout critère nécessitant d'observer quelque chose hors de la page web auditée elle-même (boîte mail, DNS, document PDF externe, SMS, second appareil...), même si une partie du parcours est automatisable sur la page.
```

- [ ] **Step 5: Bloc « Stratégies composites » (spec §5.3, R2.1 + R2.5)**

Juste après la ligne 26 (`   - N'invente une autre valeur que si la règle ne correspond **réellement à aucune** des quatre.`) et avant la ligne 27 (`2. **strategie_justification**...`), insérer :

```markdown

   **Stratégies composites** : si le parcours optimal pour vérifier la règle enchaîne deux de ces méthodes, utilise une valeur composite au format `strategie1+strategie2` (toujours deux stratégies, jamais trois ; l'ordre = séquence d'exécution), même si une seule méthode suffirait à un niveau minimal. Ce n'est pas réservé aux deux familles ci-dessous — toute paire parmi `statique`/`playwright`/`vision` (jamais `manuel` en composite) reste possible si le même raisonnement s'applique, mais demeure l'exception :
   - `vision+statique` : une vérification visuelle identifie l'élément concerné, puis une inspection du DOM confirme le balisage HTML correct.
   - `playwright+vision` : une interaction navigateur prépare une condition de rendu (désactivation CSS, mode impression...), puis une analyse visuelle juge le résultat.

   **Signal supplémentaire** : un intitulé ou un contrôle contenant « ET » reliant deux critères de nature hétérogène (visuel et textuel, code et rendu...) est un signal fort de stratégie composite.
```

- [ ] **Step 6: Trois ajouts à l'item `guide_analyse` (spec §5.4, R2.2 + R2.3 + R2.6)**

Remplacer la ligne (originale, item 3) :

```markdown
3. **guide_analyse** : instruction opérationnelle pour l'agent d'audit (3-5 phrases, concrète et actionnable). Précise si besoin la technique concrète à utiliser (crawler un échantillon de pages, rechercher un pattern via regex, etc.).
```

par :

```markdown
3. **guide_analyse** : instruction opérationnelle pour l'agent d'audit (3-5 phrases, concrète et actionnable). Précise si besoin la technique concrète à utiliser (crawler un échantillon de pages, rechercher un pattern via regex, etc.).

   Si la stratégie est composite, structure le guide en étapes numérotées et étiquetées par sous-stratégie, dans l'ordre d'exécution, en précisant ce que produit chaque étape et comment la suivante l'exploite. Format : « Étape 1 [vision] : ... Étape 2 [statique] : ... »

   Ancre chaque vérification sur un critère factuel et vérifiable (présence ou absence d'un élément, d'un attribut, d'un texte) plutôt que sur une spéculation (« serait-il possible de... »).

   Si la règle porte sur une cohérence à vérifier sur plusieurs pages, le guide doit explicitement demander de comparer plusieurs pages représentatives, quelle que soit la stratégie retenue.
```

- [ ] **Step 7: Nouveaux few-shot — Exemple 5 composite (spec §5.5, basé sur la règle réelle 235)**

Après l'Exemple 4 (qui se termine par le bloc JSON `"manuel"` / conditions de modération, juste avant la ligne `---`), insérer :

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

- [ ] **Step 8: Nouveaux few-shot — Exemple 6 manuel hors-page-web (spec §5.5, basé sur la règle réelle 111)**

Immédiatement après l'Exemple 5 inséré au Step 7, avant la ligne `---` finale, insérer :

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

Le fichier garde sa ligne `---` finale suivie de `Génère maintenant une réponse JSON pour la règle ci-dessus.` après ce nouvel exemple — ne pas la dupliquer, seulement insérer les deux exemples avant elle.

- [ ] **Step 9: Run pour vérifier le succès**

Run: `uv run pytest tests/unit/ingestion/test_enrichment.py -v`
Expected: tous PASS, y compris `test_load_prompt_version_reads_frontmatter` (`== 4`).

- [ ] **Step 10: Vérifications structurelles (spec §6, critères immédiats)**

Run: `head -3 app/ingestion/prompts/enrich_rule.md`
Expected :
```yaml
---
version: 4
---
```

Run: `grep -c "^### Exemple" app/ingestion/prompts/enrich_rule.md`
Expected: `6`

Run: `grep -c "vision+statique\|playwright+vision" app/ingestion/prompts/enrich_rule.md`
Expected: au moins `3` (bloc composites + Exemple 5)

Run: `grep -c "hors de la page web" app/ingestion/prompts/enrich_rule.md`
Expected: au moins `2` (définition `manuel` étendue + Exemple 6)

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
feat: bump enrichment prompt to V4 (composite strategies, manuel criteria)

Couvre les 6 recommandations R2.1-R2.6 (conception/2_ingestion/F_chantier2_prompt_v4.md) :
stratégies composites (grammaire hybride, parcours optimal), critère
hors-page-web = manuel, factuel > spéculatif, marqueur "ET", consigne
multi-pages. 2 nouveaux few-shot basés sur les règles réelles 235 et 111
(6 exemples au total). Aucun changement de schéma ni de code applicatif
au-delà de la ligne de test de version.
EOF
)"
```

---

### Task 2: Validation finale — récapitulatif des critères de la spec

**Files:** aucun (tâche de vérification uniquement).

- [ ] **Step 1: Récapitulatif des critères immédiats (spec §6)**

Cocher chacun, déjà vérifié dans la Task 1 :

1. Frontmatter `version: 4` → Task 1 Step 3, vérifié Step 10
2. Les 3 blocs d'instructions présents (manuel étendu, composites + signal « ET », guide composite + factuel + multi-page) → Task 1 Steps 4-6
3. 6 exemples few-shot au total → Task 1 Steps 7-8, vérifié Step 10
4. Test de version passe avec `== 4` → Task 1 Step 9
5. `git diff` limité aux deux fichiers attendus → Task 1 Step 12
6. `pytest`/`ruff` verts sur l'ensemble de la suite → Task 1 Step 11

- [ ] **Step 2: Rappel des critères différés (spec §6, hors périmètre de ce plan)**

Ces critères ne sont vérifiables qu'après la ré-ingestion réelle (chantier 3, spec/plan séparés, ~3 € de LLM) — ne pas tenter de les vérifier ici :

- Règle 111 reclassée `manuel`
- Règles 235/245 en composite `vision+statique` ou guide qui l'explicite
- Règle 65 réévaluée pour composite (marqueur « ET »)
- Règle 187 reformulée factuelle
- Revue manuelle comparative sur les règles déjà examinées en V3

- [ ] **Step 3: Rapport final**

Confirmer à David que le prompt V4 est en place et que le chantier 2 est prêt pour le chantier 3 (ré-ingestion réelle), qui reste une spec/plan à part.

---
