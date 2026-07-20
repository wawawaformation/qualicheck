---
title: "Recommandations V4 — Pipeline d'ingestion & classification LLM"
subtitle: "Analyse des 245 règles enrichies : bugs de scraping, stratégies composites, affinages du prompt"
author: "David LEGRAND"
date: "Juillet 2026"
lang: fr-FR
---

## Objectif de ce document

Après l'ingestion complète des 245 règles Opquast (enrichissement Kimi K2.6, prompt V3), une revue manuelle de la classification `strategie_analyse` a été menée règle par règle. Cette revue a révélé à la fois des **bugs de scraping critiques** (données d'entrée corrompues) et des **pistes d'affinage du prompt** (stratégies composites, critères de classification). Ce document consolide les **recommandations priorisées** issues de cette analyse — le **quoi** et le **pourquoi**, pas le **comment** (specs, plans, implémentation : étape suivante, en spec-driven).

La revue a suivi une démarche de type buffer (`ob_start` / `ob_get_clean`) : accumulation des observations brutes au fil de la relecture, puis consolidation en recommandations structurées.

## Résumé exécutif

L'ingestion des 245 règles a produit une classification globalement **saine sur le fond** (V3 : biais V2 corrigé, distribution équilibrée, `manuel` 100 % justifié). Mais l'analyse a révélé **deux bugs de scraping** qui corrompent les données d'entrée de **plus de 25 % des règles** — ce qui impose une **ré-ingestion** avant tout affinage du prompt.

Les recommandations se répartissent en **3 chantiers séquentiels** :

1. 🔴 **Corriger le scraping** (bloquant — corrompt les données)
2. 🟠 **Faire évoluer le modèle & le prompt** (composites, consignes V4)
3. 🟢 **Ré-ingérer & re-valider** (sur données saines)

L'ordre est impératif : affiner le prompt sur des données corrompues n'a pas de sens (impossible de distinguer un défaut de prompt d'un défaut de données).

## Chantier 1 — 🔴 Corriger le scraping (priorité absolue, bloquant)

### R1.1 — Corriger l'extraction de `solution` et `controle`

**Problème** : `scrape_rule()` ne capture que le **premier `<p>`** après le heading, via un `find_next("p")` non borné. Deux corruptions en résultent :

- **Bug footer** (43 règles) : quand aucun `<p>` de contenu n'existe sous le heading, `find_next` déborde jusqu'au **pied de page légal** (« SAS au capital... Lucien Granet »).
- **Bug liste ratée** (~34 règles) : le contenu est un `<p>` d'intro **+ une liste `<ul>`** ; seul le `<p>` d'intro est pris (« Pour chaque formulaire : »), la substance (`<ul>`) est perdue.

**Ampleur** : **plus de 60 règles sur 245 (> 25 %)** ont des `solution`/`controle` corrompus ou amputés. L'enrichissement LLM a donc tourné sur des données partielles pour au moins une règle sur quatre.

**Recommandation** : réécrire l'extraction en s'appuyant sur la structure DOM réelle d'Opquast (confirmée par inspection) :

- Se borner au conteneur `<div class="c-rule-content">` → **élimine le risque footer**.
- Cibler les sections par leurs **classes CSS stables** (`c-emoji-tools` = solution, `c-emoji-check` = contrôle) plutôt que par le texte du heading.
- Capturer **tout le contenu** d'une section (`<p>` **+** `<ul>`/`<ol>` + `<li>`) jusqu'au `<h2>` suivant, en ignorant les `<p>` vides.

### R1.2 — Renforcer le garde-fou anti-corruption

**Problème** : le garde-fou actuel (`if not solution or not controle: raise`) n'a pas sauté car les champs n'étaient **pas vides** — ils contenaient le footer (faux négatif).

**Recommandation** :

- Lever une **vraie erreur** si une section est vide (au lieu de déborder).
- Ajouter une **sentinelle** : rejeter tout contenu contenant les marqueurs du footer (« SAS au capital », « Lucien Granet »).
- Principe : mieux vaut un échec explicite (fail-fast, déjà dans la philosophie du pipeline) qu'une donnée silencieusement fausse.

### R1.3 — Acquérir le texte explicatif de chaque règle

**Problème** : chaque page Opquast contient, juste après le `<h1>`, un **paragraphe pédagogique** (classe `c-rule-hero__subtitle`) qui explique le *pourquoi* de la règle (ex. règle 111 : « De nombreux services en ligne envoient des messages no-reply... » ; règle 19 : « Le nombre de tentatives d'usurpations... l'authentification à double facteur... »). Ce texte n'est **pas acquis** aujourd'hui — angle mort de la spec initiale, qui ne prévoyait que `solution` et `controle`. Il est **absent de l'API** → accessible uniquement par scraping.

**Pourquoi c'est prioritaire (et non « hors périmètre »)** : ce texte donne au LLM le **contexte métier** qui manque parfois à la seule lecture de l'intitulé/solution/contrôle. Il a une **influence directe attendue sur la qualité de la classification** — l'erreur sur la règle 111 (classée `playwright` au lieu de `manuel`) aurait probablement été évitée si le LLM avait lu ce paragraphe expliquant qu'il s'agit de mails *reçus*. Comme la ré-ingestion re-scrape de toute façon, acquérir ce champ **dans la même passe** est sans surcoût et améliore l'entrée de l'enrichissement V4.

**Recommandation** :

- Extraire le paragraphe `c-rule-hero__subtitle` lors du scraping (même passe que R1.1).
- L'ajouter comme nouveau champ de la règle (nom, nullabilité, entrée ou non dans le chunk RAG : à trancher au moment de la spec).
- L'injecter dans le contexte fourni au LLM à l'étape 3 (enrichissement) — c'est là que se situe le gain.

**Impact** : spec `ingestion.md`, MLD (nouvelle colonne `regle`), migration, `scrape_rule()`, prompt d'enrichissement, éventuellement chunk. À traiter en spec-driven avant la ré-ingestion.

## Chantier 2 — 🟠 Modèle & prompt (évolutions V4)

### R2.1 — Introduire les stratégies composites

**Problème** : le modèle force **une seule** `strategie_analyse` par règle, alors que certaines en enchaînent plusieurs. Le LLM produit déjà des guides multi-stratégies, mais le champ ne le reflète pas.

**Recommandation** : autoriser un **set fermé** de valeurs composites (format string `a+b`, l'ordre = séquence d'exécution). Composites identifiés comme robustes :

- **`vision+statique`** — identifier visuellement puis vérifier le balisage DOM. Cas : 116, 235, 245 (famille « présentation visuelle vs balisage sémantique »).
- **`playwright+vision`** — Playwright prépare une condition de rendu (grayscale, sans-CSS, mode print), la vision juge l'image. Cas : 181, 183, 196 (sous-motif « vision sur rendu manipulé »).

**Garde-fous** :

- **Vocabulaire fermé** : lister explicitement les composites autorisés dans le prompt (éviter le retour à la prolifération V1 : `statique+vision`, `visuel+dom`...).
- `VARCHAR(32)` actuel suffit (même un triple tient), à surveiller.
- **À trancher** : sémantique du composite = strict nécessaire ou parcours optimal ? → conditionne combien de règles deviennent composites (ex. 187 reste `vision` si « strict nécessaire », devient `statique+vision` si « optimal »).

### R2.2 — Le guide doit expliciter la séquence des composites

**Problème** : si `strategie_analyse` devient composite, le `guide_analyse` doit rendre l'orchestration lisible.

**Recommandation** : pour toute stratégie composite, le guide doit expliciter **l'ordre**, **l'articulation** (sortie étape 1 → entrée étape 2) et **le rôle** de chaque stratégie. Format type : « **Étape 1 [vision]** : repérer X. **Étape 2 [statique]** : pour chaque X, vérifier dans le DOM que Y. » Modèles déjà quasi conformes à réutiliser en few-shot : **235, 245**.

### R2.3 — Privilégier le factuel/vérifiable au spéculatif

**Problème** : certains guides demandent à la vision de **spéculer** (« un rendu CSS serait-il réalisable ? » — règle 187) au lieu d'un **constat factuel** (« le texte de l'image est-il dans le DOM ? oui/non »).

**Recommandation** : consigne au prompt V4 pour ancrer les vérifications sur un **critère factuel binaire** chaque fois que possible, plutôt qu'un jugement « serait-il possible de... ». Réécrire notamment le guide de la 187 (vérifier la présence du texte en HTML, pas spéculer sur le CSS). Cette recommandation découle de la méthode réelle d'audit : constater un fait vérifiable plutôt qu'émettre une hypothèse.

### R2.4 — Critère « observation hors page web = manuel »

**Problème** : la règle 111 (« Tous les mails fournissent au moins un moyen de contact ») est classée `playwright` alors qu'elle exige de lire une **boîte mail externe** — même critère que 63/66/67 (tous `manuel`). Le LLM avait l'information (`controle` explicite) mais l'a sous-pondérée.

**Recommandation** :

- Consigne V4 explicite : « Si une étape de vérification nécessite d'observer quelque chose **hors de la page web auditée** (boîte mail, DNS, PDF, SMS, second appareil...), la stratégie est `manuel`, même si une partie du parcours est automatisable. »
- Few-shot avec 111, 63, 66, 217.
- **Reclassement** : 111 → `manuel`.

### R2.5 — Exploiter le marqueur « ET » comme signal de composite

**Problème** : les intitulés contenant « **ET** » de natures différentes (ex. 65 « différenciation **visuelle et textuelle** ») sont de forts candidats aux composites, souvent mal classés en mono-stratégie.

**Recommandation** : consigne V4 — détecter dans l'intitulé/contrôle un « ET » reliant deux critères de nature hétérogène (visuel + textuel, code + rendu...) comme signal d'une stratégie composite.

### R2.6 — Consigne multi-pages pour les règles « toutes les pages »

**Problème** : les règles de cohérence inter-pages doivent produire un guide comparant explicitement plusieurs pages.

**Recommandation** : consigne V4 pour que toute règle « sur toutes les pages / cohérence globale » génère un guide multi-pages. Déjà bien géré sur `vision` (158, 180 vérifiés) → à confirmer sur `statique`/`playwright` équivalents (138, 140-143, 157, 163).

## Chantier 3 — 🟢 Ré-ingestion & re-validation

### R3.1 — Ré-ingérer sur données saines

**Recommandation** : après R1 (scraping corrigé), relancer le pipeline (re-scrape des 245 + ré-enrichissement LLM avec prompt V4). Le hook `--resume` ne suffit pas ici (le bug est en étape 1/acquisition) → ré-ingestion complète nécessaire. Coût LLM à réengager (~3 € ordre de grandeur).

### R3.2 — Re-valider les classifications

**Recommandation** : après ré-ingestion, refaire l'analyse `manuel`/`vision`/composites sur données saines. Plusieurs règles examinées dans cette revue (65, 96, 98, 116-118, 189, 206-217...) font partie des ~60 corrompues → leurs classifications actuelles ne sont pas fiables et doivent être re-jugées.

## Décisions hors périmètre immédiat (à évaluer séparément)

### D1 — Capturer l'axe « dépendance aux données de test »

Les règles 23/62/96 sont `playwright` simple mais exigent des **données de test** (compte, 2FA, historique). Cet axe (orthogonal à la stratégie) n'est pas modélisé. Piste : champ `necessite_donnees_test` (booléen) ou note dans le guide, plutôt que polluer `strategie_analyse`. Utile pour l'agent d'audit US1. → **À évaluer, ne pas mélanger avec les composites.** Contrairement au texte explicatif (remonté en R1.3), cet axe n'influence pas la qualité de l'enrichissement V4 — il peut donc attendre.

Note conceptuelle importante : « inspecter le DOM » dans un guide ne signifie **pas** `statique`. Si le DOM est celui d'après login/interaction, c'est `playwright`. Le `statique` = analyse du HTML **initial, brut, sans interaction**.

## Points positifs à préserver

Ne pas casser en V4 ce qui fonctionne déjà :

- Distribution équilibrée (88 % automatisable : `statique` 46 % + `playwright` 42 %), `manuel` exception à 4 %.
- `manuel` 100 % justifié, justifications toujours pertinentes.
- Familles cohérentes (headers HTTP → `playwright`, attributs HTML → `statique`).
- Vocabulaire fermé tenu depuis V2, biais `manuel` corrigé (90 % → 4 %).
- Guides multi-stratégies et factuels déjà spontanés sur les bons cas (235, 245).

> ⚠️ Ces constats positifs valent surtout pour les règles à **données saines** — à reconfirmer après ré-ingestion pour les ~60 règles corrompues.

## Ordre d'exécution recommandé

```text
R1 (scraping) → R3.1 (ré-ingestion, inclut prompt V4 = R2) → R3.2 (re-validation)
                                    ↑
        D1/D2 : décider AVANT la ré-ingestion si on veut les inclure
                (sinon 2e ré-ingestion coûteuse plus tard)
```

**Point d'attention budgétaire** : chaque ré-ingestion coûte ~3 € de LLM. Regrouper un maximum de changements (prompt V4 + éventuels champs D1/D2) dans **une seule** ré-ingestion plutôt que d'enchaîner plusieurs passes.
