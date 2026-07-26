# Chantier — Prompt d'enrichissement V6

> Spec d'incrément. Fait suite à l'audit du prompt V5
> (`docs/problemes_rencontres/ingestion/5_recommandations_v6.md`) et à la
> correction ciblée déjà appliquée en base via `enrich_again` (11 règles,
> 2026-07-26) — cette correction a réutilisé le prompt V5 tel quel ; ce
> chantier corrige le prompt lui-même, pour que de futures ré-ingestions ne
> reproduisent pas les mêmes écarts. À valider avant implémentation.
>
> Date : 2026-07-26

## 1. Problème

Deux écarts confirmés sur les 245 règles réellement ré-ingérées avec le
prompt V5, tous deux corrigés manuellement en base via `enrich_again` mais
non corrigés dans le prompt lui-même :

- **Grammaire composite `&` (ET) jamais adoptée** : 0 occurrence sur 245
  règles, alors que 5 cas réels l'exigeaient (règles 65, 28, 124, 164, 239).
  Diagnostic : le prompt V5 décrit `&` uniquement en prose (§1 du prompt),
  aucun few-shot ne le démontre — principe de prompt engineering bien
  documenté : un LLM suit plus fidèlement un exemple concret qu'une règle
  énoncée en prose seule.
- **Critère `manuel` (R2.4) sous- *et* sur-appliqué** : sous-appliqué sur la
  règle 94 (jugement sémantique sans canal externe, restée `statique`) ;
  sur-appliqué sur 3 règles (62, 202, 182) — classées `manuel` alors que
  leur propre `guide_analyse` décrit une procédure Playwright/vision
  entièrement automatisable, sans aucun canal externe requis. La sur-
  application est un effet non anticipé par la spec V5.

## 2. État actuel (vérifié)

- `app/ingestion/prompts/enrich_rule.md` : frontmatter `version: 5`, 8
  exemples few-shot, tous les composites utilisent `+` (aucun `&`).
- Texte actuel de la clause (b) du critère `manuel` : « toute exigence de
  vérifier qu'un mécanisme fonctionne effectivement/réellement, au-delà de
  sa simple présence syntaxique, dès qu'aucune méthode automatisée ne peut
  observer ce résultat — même si une partie du parcours reste automatisable
  sur la page. » Cette clause n'est pas fausse dans l'absolu (elle exclut
  bien les cas observables automatiquement, en théorie), mais son
  application réelle par le LLM a été incohérente dans les deux sens : trop
  restrictive sur la règle 94, trop permissive sur 62/202/182.

## 3. Décisions de conception

| Point | Décision |
| --- | --- |
| Few-shot pour `&` | **Règle 65** (`vision&statique`, différenciation visuelle + mention textuelle), pas la 28. Crée une paire minimale avec l'Exemple 5 existant (`vision+statique`, PUIS) — même famille de stratégies, seul l'opérateur change : signal pédagogique direct sur la distinction PUIS/ET |
| Few-shot pour la sur-application de `manuel` | **Règle 182** (contraste WCAG), pas 62 ni 202. Ces deux dernières illustrent seulement « tâche comportementale = playwright », déjà couvert par l'Exemple 2. La 182 enseigne un piège distinct et précisément ciblé sur le bug constaté : un critère qui *sonne* subjectif/visuel (le contraste) a une formule déterministe automatisable |
| Reformulation de la clause (b) | Restructurée pour insister explicitement sur la condition disqualifiante, avec contre-exemples concrets (remplir un formulaire, cliquer un bouton, télécharger un fichier, calculer un ratio) — texte exact en §5.2 |
| Nombre total de few-shot | 8 → 10 (ajout net de 2, aucun retiré) |
| Clause (a) et le reste du critère `manuel` | Inchangés — fonctionnent déjà bien (24, 69, 113, 243, 205, 217, 240, 241 tous corrects) |
| HTTP headers (O6) | Rien à faire — déjà stable à 100 % sur l'audit V5 (13/13), aucune régression à corriger |
| Numéro de version | `version: 6` dans le frontmatter |

## 4. Hors périmètre (rappel, déjà tranché ailleurs)

- Toute correction ligne par ligne en base — déjà faite via `enrich_again`
  le 2026-07-26 (11 règles).
- La règle 96 (cas contesté, `docs/problemes_rencontres/ingestion/5_recommandations_v6.md`
  §2) reste non tranchée, hors périmètre de ce chantier.
- Une nouvelle ré-ingestion complète des 245 règles avec ce prompt V6 —
  aucune n'est prévue à ce stade ; ce chantier prépare seulement le prompt
  pour la prochaine fois qu'une ré-ingestion complète sera nécessaire.

## 5. Modifications

Un seul fichier touché : `app/ingestion/prompts/enrich_rule.md`.

### 5.1 Frontmatter

```yaml
---
version: 6
---
```

### 5.2 Reformulation de la clause (b) du critère `manuel`

Remplace le texte actuel de la puce `"manuel"` (dans la liste des 4
valeurs de `strategie_analyse`) par :

```text
"manuel" : **vraie exception**, réservée aux cas où même une analyse
visuelle par LLM ne peut pas trancher de façon fiable — typiquement un
jugement légal, éditorial ou sémantique fin, ou un contexte métier propre
au site qu'aucune observation de la page ne permet de déduire. Inclut
aussi (a) tout critère nécessitant d'observer quelque chose hors de la
page web auditée elle-même (boîte mail, DNS, document PDF externe, SMS,
second appareil...), et (b) toute exigence de vérifier qu'un mécanisme
fonctionne effectivement, **mais uniquement si aucune méthode automatisée
(Playwright, vision) ne peut exécuter ni observer cette vérification dans
le navigateur**. Attention à la sur-application de (b) : remplir un
formulaire, cliquer un bouton, se connecter, télécharger un fichier, ou
calculer un ratio/score (ex. contraste WCAG) sont des vérifications
« effectives » que Playwright ou vision peuvent réaliser elles-mêmes — ce
ne sont **pas** des cas de `manuel`, même quand le contrôle demande de
constater qu'un mécanisme « fonctionne réellement ». Ne retiens (b) que si
l'observation exige de sortir du navigateur (rejoint alors (a)) ou un
jugement humain qu'aucun calcul ni règle factuelle ne peut trancher.
```

Seule la clause (b) change — la phrase d'ouverture et la clause (a) restent
verbatim identiques au texte V5.

### 5.3 Nouveau few-shot — Exemple 9 : `&` (ET)

Ajouté après l'Exemple 8 existant :

````text
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
````

### 5.4 Nouveau few-shot — Exemple 10 : ne pas sur-appliquer `manuel`

Ajouté après l'Exemple 9 :

````text
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
````

## 6. Validation

1. Diff du prompt : uniquement frontmatter (`5`→`6`), clause (b) reformulée,
   2 nouveaux exemples ajoutés — rien d'autre modifié (clause (a),
   Exemples 1-8, section HTTP headers, tout le reste verbatim identique).
2. `tests/unit/ingestion/test_enrichment.py::test_load_prompt_version_reads_frontmatter`
   et `test_enrich_single_rule_success` : assertions `== 5` à mettre à jour
   en `== 6`.
3. `pytest`/`ruff` verts.
4. Pas de ré-ingestion réelle dans le cadre de ce chantier — validation par
   relecture du prompt final, pas par un appel LLM réel.

## 7. Hors périmètre (YAGNI)

- Ré-ingestion réelle des 245 règles avec le prompt V6 — aucune décidée à
  ce stade (cf. §4).
- Nouveau few-shot pour la règle 94 (sous-application de `manuel`) —
  l'Exemple 8 existant (règle 243, jugement sémantique sans canal externe)
  couvre déjà cette famille de cas ; pas de preuve qu'un second exemple
  soit nécessaire.
- Grammaire `OU` (alternative contextuelle) — toujours aucune occurrence
  réelle sur les 245 règles, cf. décision déjà actée en V5.
- Script `enrich_again` — déjà livré et exécuté (chantier séparé,
  `conception/2_ingestion/J_chantier_enrich_again.md`).
