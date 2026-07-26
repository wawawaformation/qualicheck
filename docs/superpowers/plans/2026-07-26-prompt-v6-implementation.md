# Prompt V6 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mettre à jour `app/ingestion/prompts/enrich_rule.md` (V5 → V6) :
reformuler la clause (b) du critère `manuel`, ajouter 2 few-shot (`&` et
anti-sur-application de `manuel`), bumper le frontmatter.

**Architecture:** Un seul fichier de contenu modifié, aucun changement de
code applicatif — `load_prompt_version()` lit déjà dynamiquement le
frontmatter, aucune logique Python à toucher au-delà de deux assertions de
test.

**Tech Stack:** Markdown (prompt), pytest.

## Global Constraints

- Spec source : `conception/2_ingestion/K_chantier_prompt_v6.md` (validée,
  commit `1f06cf0`) — tout texte de ce plan en est extrait verbatim.
- Seul fichier de contenu touché : `app/ingestion/prompts/enrich_rule.md`.
- La phrase d'ouverture et la clause (a) du critère `manuel` restent
  **verbatim identiques** — seule la clause (b) change.
- Exemples 1 à 8 restent **verbatim identiques** — seuls 2 exemples
  s'ajoutent après l'Exemple 8 (Exemple 9 puis Exemple 10).
- Aucune ré-ingestion réelle dans ce chantier (spec §6) — validation par
  relecture + `pytest`/`ruff` uniquement.
- Pas de nouvelle branche : travail sur `feature`, dans la continuité des
  chantiers D à K.

---

### Task 1 : Mettre à jour le prompt V6 et les assertions de version

**Files:**

- Modify: `app/ingestion/prompts/enrich_rule.md`
- Modify: `tests/unit/ingestion/test_enrichment.py`

**Interfaces:**

- Consumes : rien (contenu de prompt, pas de code).
- Produces : `app/ingestion/prompts/enrich_rule.md` en version 6 — consommé
  par `LLMClient.load_prompt()`/`load_prompt_version()` (déjà existants,
  aucune modification nécessaire).

- [ ] **Step 1 : Bumper le frontmatter**

Le fichier commence par :

```yaml
---
version: 5
---
```

Remplacer par :

```yaml
---
version: 6
---
```

- [ ] **Step 2 : Reformuler la clause (b) du critère `manuel`**

La ligne actuelle (une seule ligne dans le fichier) :

```text
   - `"manuel"` : **vraie exception**, réservée aux cas où même une analyse visuelle par LLM ne peut pas trancher de façon fiable — typiquement un jugement légal, éditorial ou sémantique fin, ou un contexte métier propre au site qu'aucune observation de la page ne permet de déduire. Inclut aussi (a) tout critère nécessitant d'observer quelque chose hors de la page web auditée elle-même (boîte mail, DNS, document PDF externe, SMS, second appareil...), et (b) toute exigence de vérifier qu'un mécanisme fonctionne effectivement/réellement, au-delà de sa simple présence syntaxique, dès qu'aucune méthode automatisée ne peut observer ce résultat — même si une partie du parcours reste automatisable sur la page.
```

Remplacer par (une seule ligne aussi, ne pas introduire de retour à la
ligne au milieu) :

```text
   - `"manuel"` : **vraie exception**, réservée aux cas où même une analyse visuelle par LLM ne peut pas trancher de façon fiable — typiquement un jugement légal, éditorial ou sémantique fin, ou un contexte métier propre au site qu'aucune observation de la page ne permet de déduire. Inclut aussi (a) tout critère nécessitant d'observer quelque chose hors de la page web auditée elle-même (boîte mail, DNS, document PDF externe, SMS, second appareil...), et (b) toute exigence de vérifier qu'un mécanisme fonctionne effectivement, **mais uniquement si aucune méthode automatisée (Playwright, vision) ne peut exécuter ni observer cette vérification dans le navigateur**. Attention à la sur-application de (b) : remplir un formulaire, cliquer un bouton, se connecter, télécharger un fichier, ou calculer un ratio/score (ex. contraste WCAG) sont des vérifications « effectives » que Playwright ou vision peuvent réaliser elles-mêmes — ce ne sont **pas** des cas de `manuel`, même quand le contrôle demande de constater qu'un mécanisme « fonctionne réellement ». Ne retiens (b) que si l'observation exige de sortir du navigateur (rejoint alors (a)) ou un jugement humain qu'aucun calcul ni règle factuelle ne peut trancher.
```

- [ ] **Step 3 : Ajouter les Exemples 9 et 10 après l'Exemple 8**

La fin actuelle du fichier (Exemple 8 puis séparateur puis instruction
finale) est :

````text
### Exemple 8 : "manuel" — vérification partiellement automatisable, mais le jugement de fond ne l'est pas

**Règle :** Les titres des tableaux de données sont renseignés.

**Solution :** Utiliser et renseigner l'élément HTML caption pour chaque tableau de données.

**Contrôle :** Vérifier la présence de l'élément caption. Contrôler la pertinence de l'élément caption, qui doit permettre d'identifier la nature des informations apportées par le tableau. Cette vérification peut être partiellement automatisée pour la présence de l'élément, mais le contrôle de sa pertinence nécessite un examen manuel.

**Réponse attendue :**
```json
{
  "strategie_analyse": "manuel",
  "strategie_justification": "Le contrôle lui-même indique que la présence de l'élément caption est automatisable, mais que juger sa pertinence (identifie-t-il bien la nature du tableau ?) nécessite un examen manuel — un jugement sémantique qu'aucune inspection factuelle du DOM ne peut fiabiliser. Le volet automatisable est absorbé par le volet manuel, pas de composite avec manuel.",
  "guide_analyse": "Pour chaque tableau de données du site, identifiez la présence de l'élément caption. Faites relire par un humain le texte de chaque caption présent : vérifiez qu'il décrit effectivement la nature des données du tableau (et non un intitulé générique ou décoratif). Signalez les tableaux sans caption, ainsi que les captions présents mais non pertinents au regard du contenu réel du tableau."
}
```

---

Génère maintenant une réponse JSON pour la règle ci-dessus.
````

Remplacer par (insertion des deux nouveaux exemples entre le séparateur
qui suit l'Exemple 8 et l'instruction finale) :

````text
### Exemple 8 : "manuel" — vérification partiellement automatisable, mais le jugement de fond ne l'est pas

**Règle :** Les titres des tableaux de données sont renseignés.

**Solution :** Utiliser et renseigner l'élément HTML caption pour chaque tableau de données.

**Contrôle :** Vérifier la présence de l'élément caption. Contrôler la pertinence de l'élément caption, qui doit permettre d'identifier la nature des informations apportées par le tableau. Cette vérification peut être partiellement automatisée pour la présence de l'élément, mais le contrôle de sa pertinence nécessite un examen manuel.

**Réponse attendue :**
```json
{
  "strategie_analyse": "manuel",
  "strategie_justification": "Le contrôle lui-même indique que la présence de l'élément caption est automatisable, mais que juger sa pertinence (identifie-t-il bien la nature du tableau ?) nécessite un examen manuel — un jugement sémantique qu'aucune inspection factuelle du DOM ne peut fiabiliser. Le volet automatisable est absorbé par le volet manuel, pas de composite avec manuel.",
  "guide_analyse": "Pour chaque tableau de données du site, identifiez la présence de l'élément caption. Faites relire par un humain le texte de chaque caption présent : vérifiez qu'il décrit effectivement la nature des données du tableau (et non un intitulé générique ou décoratif). Signalez les tableaux sans caption, ainsi que les captions présents mais non pertinents au regard du contenu réel du tableau."
}
```

---

### Exemple 9 : composite `vision&statique` — deux vérifications indépendantes (ET)

**Règle :** Les produits indisponibles font l'objet d'une différenciation visuelle et textuelle.

**Solution :** Préciser, dans le contenu présentant chaque produit, une mention textuelle ou graphique du type « indisponible » ou « disponible ».

**Contrôle :** Dans les pages produits : vérifier la présence d'une mention textuelle sur la disponibilité des produits ; ou contrôler la présence d'une indication graphique différenciant les produits disponibles de ceux qui ne le sont pas (icône, couleur, etc.) accompagnée d'une alternative textuelle appropriée.

**Réponse attendue :**
```json
{
  "strategie_analyse": "vision&statique",
  "strategie_justification": "La règle combine deux critères indépendants de nature hétérogène : la différenciation visuelle des produits indisponibles (icônes, couleurs, opacité) requiert une appréciation visuelle, tandis que la mention textuelle exacte du statut de disponibilité est directement vérifiable dans le DOM. Ces deux volets ne se déduisent pas l'un de l'autre et doivent être contrôlés en parallèle.",
  "guide_analyse": "Vérification [statique] : crawlez un échantillon représentatif de pages produits. Pour chaque produit indisponible, inspectez le DOM et recherchez une mention textuelle explicite de sa disponibilité ('indisponible', 'épuisé', 'rupture de stock'...) ou une alternative textuelle appropriée sur tout indicateur graphique. Vérification [vision] (indépendante) : capturez les écrans des mêmes pages et faites-les analyser par un LLM vision pour identifier si les produits indisponibles sont visuellement distinguables des produits disponibles (opacité, badge, icône, couleur...). Signalez l'absence de mention textuelle OU l'absence de différenciation visuelle — les deux vérifications sont indépendantes, pas séquentielles."
}
```

---

### Exemple 10 : "playwright" — critère d'apparence subjective, mais formule déterministe (piège `manuel`)

**Règle :** Les contenus sont présentés avec un contraste suffisant par rapport à leur arrière-plan.

**Solution :** Veiller à conserver un ratio de contraste minimal de 3:1 entre le texte et son arrière-plan, tel qu'il peut être mesuré via l'algorithme WCAG2.0.

**Contrôle :** Dans l'ensemble des pages, repérer les contenus dont la différence de contraste avec leur arrière-plan est potentiellement insuffisante, calculer le ratio de contraste (méthode WCAG2.0), et vérifier qu'il est supérieur ou égal à 3:1.

**Réponse attendue :**
```json
{
  "strategie_analyse": "playwright",
  "strategie_justification": "Le calcul du ratio de contraste WCAG 2.0 est déterministe et entièrement automatisable via des outils s'exécutant dans un navigateur (axe-core, Lighthouse, scripts getComputedStyle) qui mesurent les couleurs calculées du texte et de l'arrière-plan, sans requérir de jugement humain ou une analyse visuelle par LLM. Ce n'est PAS un cas de manuel malgré l'apparence perceptuelle du critère : une formule déterministe remplace le jugement visuel.",
  "guide_analyse": "Parcourez un échantillon représentatif de pages via un crawler couplé à Playwright. Pour chaque page, exécutez un audit de contraste automatisé (axe-core, Lighthouse ou équivalent) évaluant les styles calculés de chaque nœud texte. Vérifiez que tous les textes respectent un ratio de contraste >= 3:1 avec leur arrière-plan selon l'algorithme WCAG 2.0. Pour les arrière-plans complexes (dégradés, motifs, images), contrôlez le pixel le plus défavorable au contact immédiat du texte. Signalez chaque élément dont le ratio calculé est inférieur au seuil requis."
}
```

---

Génère maintenant une réponse JSON pour la règle ci-dessus.
````

- [ ] **Step 4 : Mettre à jour les 2 assertions de version dans les tests**

Dans `tests/unit/ingestion/test_enrichment.py`, deux occurrences de `5`
(version de prompt) à passer à `6` :

1. `test_load_prompt_version_reads_frontmatter` (ligne 413, dans la classe
   `TestManifestAndPromptVersion`) : l'assertion
   `assert load_prompt_version() == 5` devient
   `assert load_prompt_version() == 6`.
2. `test_enrich_single_rule_success` (ligne 56, dans la classe
   `TestLLMClient`) : l'assertion `assert enriched.prompt_version == 5`
   devient `assert enriched.prompt_version == 6`.

(Repérer les deux lignes exactes par recherche du texte `== 5` dans ce
fichier — ce sont les deux seules occurrences liées à `prompt_version`/
version de prompt ; ne pas toucher à d'autres assertions numériques sans
rapport.)

- [ ] **Step 5 : Lancer la suite complète et ruff**

Run: `uv run pytest tests/unit/ingestion/test_enrichment.py -v`
Expected: tous les tests passent, y compris les deux mis à jour.

Run: `uv run pytest tests/ -v`
Expected: suite complète verte (aucune régression ailleurs).

Run: `uv run ruff check`
Expected: `All checks passed!`

- [ ] **Step 6 : Relecture manuelle du prompt final**

Ouvrir `app/ingestion/prompts/enrich_rule.md` et vérifier visuellement
(spec §6, point 1) :

- Frontmatter `version: 6`.
- Clause (b) reformulée, clause (a) et phrase d'ouverture inchangées.
- Exemples 1 à 8 inchangés, Exemple 9 (`vision&statique`) et Exemple 10
  (`playwright`, contraste) présents après l'Exemple 8, avant l'instruction
  finale.
- Aucun appel LLM réel effectué à cette étape — validation par lecture
  uniquement (spec §6, point 4).

- [ ] **Step 7 : Commit**

```bash
git add app/ingestion/prompts/enrich_rule.md tests/unit/ingestion/test_enrichment.py
git commit -m "$(cat <<'EOF'
feat: bump enrichment prompt to V6 (manuel clarification + & example)

Reformule la clause (b) du critère manuel (sur-application constatée en
V5 sur les règles 62/182/202) et ajoute 2 few-shot : Exemple 9
(vision&statique, règle 65 — paire minimale avec l'Exemple 5 existant en
vision+statique) et Exemple 10 (playwright, règle 182 — contre-exemple
au piège "critère subjectif mais formule déterministe"). Aucune
ré-ingestion réelle dans ce chantier.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Fin de plan

Après la Task 1, utiliser superpowers:finishing-a-development-branch — pas
de nouvelle branche (travail resté sur `feature`, comme les chantiers D à
K). Aucune ré-ingestion réelle dans ce plan — la prochaine ré-ingestion
complète (si elle a lieu un jour) reste une décision de David, hors
périmètre.
