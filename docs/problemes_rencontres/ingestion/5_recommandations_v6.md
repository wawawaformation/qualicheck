---
title: "Recommandations V6 — Pipeline d'ingestion & classification LLM"
subtitle: "Analyse des 245 règles ré-ingérées avec le prompt V5 : grammaire ET non adoptée, critère manuel sous- et sur-appliqué"
author: "David LEGRAND"
date: "Juillet 2026"
lang: fr-FR
---

## Objectif de ce document

Après la ré-ingestion réelle des 245 règles Opquast avec le prompt V5
(chantier `conception/2_ingestion/H_chantier_prompt_v5.md`), un balayage
complet des 245 règles par 5 agents en parallèle a été mené pour vérifier la
cohérence des diagnostics produits, complété par des vérifications SQL
ciblées sur les règles visées par les correctifs V5. Ce document consolide
les observations — le **quoi** et le **pourquoi**, pas le **comment** (spec
et plan : étape suivante). Démarche identique à `4_recommandations_v5.md`.

## Résumé exécutif

La classification V5 est globalement solide : les deux chantiers visés sont
en grande partie corrigés — le correctif en-têtes HTTP (O6) tient à 100 %
(13/13 règles vérifiées), et le critère `manuel` élargi (R2.4) a corrigé 4
des 5 règles visées. Le balayage complet (245/245, aucun lot ignoré) a
identifié **11 règles à problème confirmées** (≈4,5 % du référentiel) et **1
règle contestée**, concentrées sur 2 axes :

1. 🔴 **La grammaire composite `&` (ET) n'a jamais été adoptée** — 0
   occurrence sur 245 règles, alors que 5 cas réels l'exigeaient
2. 🟠 **Le critère `manuel` (R2.4) reste ambigu** — sous-appliqué sur 1
   règle, mais aussi **sur-appliqué** sur 3 règles (effet non anticipé par
   la spec V5)

Contrairement au cycle V4→V5, **pas de ré-ingestion complète prévue cette
fois** — le nombre de règles concernées est trop faible pour justifier de
retoucher les 234 autres (et le risque de régression collatérale s'est
déjà concrétisé une fois, cf. §2). Décision actée : correction ciblée via
`review_status`/`review_note` + script `enrich_again` (cf. §5).

## 1. Grammaire composite `&` (ET) jamais adoptée

**Constat** : sur les 38 règles composites du référentiel, **5 sont des cas
ET clairs** mais restent exprimées avec `+` (PUIS) :

| Règle | Volet A | Volet B | Nature de la relation |
| --- | --- | --- | --- |
| 65 | Différenciation visuelle | Mention textuelle exacte | Indépendants |
| 28 | Analyse HTML statique (liens/formulaires) | Soumission + vérif. URL finale | Indépendants |
| 124 | Attribut `autoplay` (statique) | Événements `play` au chargement/interaction (playwright) | Indépendants |
| 164 | Position dans le code source (statique) | Fonctionnement clavier effectif (playwright) | Indépendants |
| 239 | Balise `meta refresh`/en-tête (statique) | Redirection JS surveillée (playwright) | Indépendants |

Dans chaque cas, les deux volets sont systématiquement exécutés — aucun ne
conditionne l'autre, contrairement aux vraies séquences PUIS confirmées
ailleurs dans le référentiel (ex. règles 116, 156, 159, 187, 224, 235, 245 :
le volet 2 dépend du résultat du volet 1).

**Diagnostic** : la grammaire `&` a été introduite en V5 **uniquement en
prose** (`conception/2_ingestion/H_chantier_prompt_v5.md` §5.3), sans aucun
few-shot qui la démontre concrètement. Les 8 exemples du prompt V5 utilisent
tous `+`. Principe bien documenté en prompt engineering : un LLM suit plus
fidèlement un exemple concret qu'une règle énoncée en prose seule — une
instruction sans exemple qui l'illustre reste fragile, même bien écrite.

**Piste pour V6** : ajouter un few-shot démontrant `&` (règle 65 ou 28,
à choisir), et préciser dans le prompt la distinction opérationnelle entre
`+` (PUIS — B dépend du résultat de A) et `&` (ET — A et B s'exécutent
systématiquement, indépendamment l'un de l'autre).

## 2. Critère `manuel` (R2.4) — sous- **et** sur-appliqué

### Sous-appliqué (1 règle)

- **Règle 94** (ordre des options de formulaire) — `statique`, mais détecter
  un « ordre thématique cohérent » est un jugement sémantique, pas une
  vérification syntaxique. Le `controle` source Opquast dit lui-même
  explicitement : *« La vérification s'effectue manuellement en contrôlant
  visuellement l'ordre des éléments »*.

### Sur-appliqué (3 règles, effet non anticipé par la spec V5)

- **Règle 62** (facture en ligne) — `manuel`, mais son propre
  `guide_analyse` décrit un script Playwright standard entièrement
  automatisable (connexion, navigation, téléchargement, vérification du
  fichier) — aucun canal externe requis.
- **Règle 182** (contraste) — `manuel`, mais le `guide_analyse` décrit un
  calcul de ratio WCAG 2.0 déterministe, automatisable via Playwright/vision
  (ex. axe-core, Lighthouse) — pas un jugement humain.
- **Règle 202** (mot de passe personnalisable) — `manuel`, même profil que
  la règle 62 : le guide décrit une procédure entièrement scriptable
  (inscription, connexion, changement de mot de passe, vérification de la
  confirmation), sans canal externe.

### Cas contesté — Règle 96 (à trancher)

Toujours `playwright`, ce qui diverge de la spec V5 (§1, qui la listait
parmi les 5 règles à passer en `manuel`). Mais le `guide_analyse` réel ne
demande qu'une vérification 100 % observable en navigateur (cliquer sur
« renvoyer le code », vérifier un feedback UI) — **aucun canal externe
requis**, contrairement à 24/69/113/243. Correspond à l'objection déjà
soulevée par David pendant le brainstorming V5 (l'agent d'audit n'a pas
accès à un second écran/appareil pour vérifier la réception réelle d'un
code). Il est possible que le LLM ait ici raison, et que le ciblage initial
de la spec V5 sur cette règle ait été trop large — **à trancher avant
d'écrire son `review_status`.**

**Diagnostic** : la formulation R2.4 (« toute exigence de vérification
effective/réelle d'un mécanisme, au-delà de sa simple présence syntaxique »)
ne précise pas si un canal externe est une condition *nécessaire* pour
justifier `manuel`, ou seulement suffisante. Cette ambiguïté explique à la
fois la sous-application (94, jugement sémantique sans canal externe — mais
qui aurait dû compter) et la sur-application (62/182/202, vérifications
comportementales en navigateur — mais qui n'auraient pas dû compter).

**Piste pour V6** : reformuler R2.4 pour clarifier que **l'absence de canal
externe nommé et l'observabilité entière depuis le navigateur (même avec
jugement/calcul) excluent `manuel`**, sauf lorsque le jugement porte sur une
propriété sémantique/éditoriale non réductible à une règle factuelle (cas
94, 69, 243 — à conserver comme few-shot).

## 3. Anomalie ponctuelle — Règle 234 (contradiction interne)

Classée `statique`, mais son propre `guide_analyse` précise : *« l'analyse
porte sur le DOM final **après rendu JavaScript** afin d'inclure les titres
masqués ou injectés dynamiquement »* — ce qui contredit la définition même
de `statique` (« DOM/HTML brut, sans exécution »). Devrait être au minimum
`statique+playwright`. Cas isolé, pas de motif récurrent trouvé ailleurs
dans les 245 règles.

## 4. Points positifs à préserver

Constatés indépendamment par les 5 agents du balayage complet — à vérifier
par non-régression lors de la correction ciblée :

- **Correctif en-têtes HTTP (O6) : 100 % stable**, 13/13 règles vérifiées
  (197-200, 206-214, 226-228) toutes correctement `statique`.
- **Structure des composites intégralement respectée** : 0 composite à 3
  stratégies, 0 `manuel` combiné avec autre chose, sur les 245 règles.
- **Nouveaux few-shot V5 bien assimilés** : la règle 117 (image-lien)
  distingue proprement le cas exhaustif-factuel des règles voisines 116/118
  (jugement visuel requis) ; la règle 243 justifie clairement la règle
  d'absorption de `manuel` en composite.
- **La grande majorité des composites `+` restent de vraies séquences
  dépendantes**, correctement justifiées (ex. 5, 9, 40, 49, 116, 156, 159,
  187, 224, 235, 245) — le problème de grammaire (§1) est localisé à 5 cas
  sur 38 composites, pas un défaut généralisé.
- **Lot 4 quasi entier propre** (règles 148-196) : seules 2 anomalies sur 49
  règles (164, 182), confirmant que les problèmes restent concentrés, pas
  diffus.

## 5. Décisions actées (2026-07-25)

- **Pas de ré-ingestion complète.** Contrairement au cycle V4→V5, le nombre
  de règles concernées (11 confirmées + 1 contestée, sur 245) est trop
  faible pour justifier de retoucher l'ensemble du référentiel — et le
  risque de régression collatérale s'est déjà concrétisé une fois (§2,
  sur-application de `manuel`, effet de bord non anticipé d'une correction
  qui touchait tout).
- **Correction ciblée** : renseigner `review_status`/`review_note` pour les
  règles concernées, puis développer et lancer le script `enrich_again`
  (réécriture ciblée par LLM, s'appuyant sur `review_note` comme contexte) —
  différé depuis la spec G, condition désormais remplie (données de revue
  réelles disponibles).
- **Prompt V6** (pour les futures ré-ingestions complètes, pas pour cette
  correction ciblée) : ajout d'un few-shot démontrant `&` (règle 65 ou 28),
  complément textuel sur la distinction opérationnelle PUIS/ET, et
  reformulation de R2.4 pour clarifier la frontière `manuel`.

## 6. Hors périmètre immédiat

- **Spec et implémentation d'`enrich_again`** — chantier séparé, à
  spec-driver (script CLI, format du prompt de correction ciblée, lecture de
  `review_note`).
- **Décision finale sur la règle 96** — à trancher avant de lui assigner un
  `review_status` (§2).
- **Choix du few-shot exact pour `&`** (règle 65 vs 28) — à trancher en
  spec, au moment d'écrire le prompt V6.
- **Prompt V6 complet** (texte exact des modifications) — pas rédigé ici,
  suite logique une fois `enrich_again` conçu.
