---
title: "Itération du prompt d'enrichissement — traçabilité"
subtitle: "Étape 3 (Enrichissement) — évolution du prompt LLM, versions successives et justifications"
author: "David LEGRAND"
date: "Juillet 2026"
lang: fr-FR
---

## Objectif de ce document

Le prompt qui pilote l'agent d'enrichissement (Kimi K2.6) n'a pas été figé dès le départ : il a évolué en observant son comportement sur des données réelles, à mesure que des biais ou des lacunes apparaissaient. Ce document trace cette itération — pas pour archiver chaque diff, mais pour expliquer **pourquoi** chaque version a changé, à partir de quelle observation, et ce qu'on en a conclu.

Fichier concerné : `app/ingestion/prompts/enrich_rule.md`.

## Version 1 — Prompt initial

**Contenu** : instructions + format JSON + 2 exemples few-shot (`statique`, `playwright`). Le champ `strategie_analyse` était présenté comme libre :

> "Exemples : 'statique' (analyse HTML), 'playwright' (navigation), 'manuel' (non-automatisable). Libre : tu peux proposer d'autres méthodes si pertinent."

**Hypothèse de départ** : laisser le LLM proposer une catégorie hors des 3 valeurs si aucune ne convenait, plutôt que de le forcer artificiellement.

## Observation 1 — Prolifération de catégories

Validation sur un petit échantillon (3 règles réelles, numéros 1, 3, 4). La règle 1 ("connaître les nouveaux contenus ou services") a été classée `"crawl"` — une 4e valeur inventée par le LLM, absente du few-shot.

**Analyse** : `crawl` était en soi défendable (exploration multi-pages, différent de `playwright` qui implique plutôt de l'interaction JS/formulaire). Mais le risque identifié n'était pas la valeur elle-même — c'était l'effet à l'échelle des 245 règles : si le LLM se sent libre d'inventer une nuance à chaque règle un peu particulière, on peut se retrouver avec 8-10 catégories différentes sur l'ensemble du référentiel, dont certaines ne différeraient que par la formulation, pas par une vraie distinction métier. Or `strategie_analyse` a un rôle précis : orienter directement le comportement de l'agent d'audit US1. Plus de catégories = plus de branches de comportement à gérer côté US1, pour un gain de nuance non prouvé.

## Version 2 — Resserrement vers 3 catégories

**Modification** : la clause de liberté totale est remplacée par une consigne de priorité forte :

> "Choisis **en priorité** parmi ces trois valeurs [...]. N'invente une autre valeur que si la règle ne correspond **réellement à aucune** des trois — pas simplement parce qu'elle a une nuance particulière."

**Vérification** : re-enrichissement de la règle 1 avec le prompt modifié → `strategie_analyse = "manuel"` (au lieu de `"crawl"`), justification cohérente ("jugement éditorial et exploration contextuelle du site").

**Résultat en apparence positif** : plus aucune 4e catégorie sur les runs suivants.

## Observation 2 — Sur-représentation de "manuel"

Validation sur un échantillon élargi (10 règles réelles, numéros 1 à 10). Distribution obtenue :

```text
manuel   : 9
statique : 1
playwright : 0
```

**Analyse** : 90 % de `manuel` sur cet échantillon rend le champ `strategie_analyse` quasi inutile pour l'agent d'audit US1 — si presque tout finit en jugement humain, l'automatisation qu'on cherchait à orienter n'a plus lieu d'être. Deux causes identifiées en relisant le prompt de la Version 2 :

1. **`manuel` était défini trop largement** ("jugement éditorial, contextuel ou visuel qu'aucun script ne peut fiabiliser") — cette formulation couvre en réalité une grande partie des règles Opquast, qui portent souvent sur du contenu (dates, mentions légales, contenus publicitaires...).
2. **Aucun exemple few-shot pour `manuel`** — le LLM n'avait que 2 modèles concrets (`statique`, `playwright`) et zéro repère sur le niveau de subjectivité qui justifie vraiment `manuel`. Par excès de prudence, dès qu'une règle demandait une once d'interprétation, le LLM basculait vers l'option la plus sûre : `manuel`.

Un facteur supplémentaire a été identifié en parallèle : jusqu'ici, `strategie_analyse` ne reflétait que 2 méthodes concrètes disponibles pour l'agent d'audit (`statique` via BeautifulSoup, `playwright` via navigateur automatisé). Beaucoup de règles nécessitant une appréciation visuelle (ex. "un contenu publicitaire est-il identifié comme tel ?") n'avaient techniquement aucune méthode adaptée dans ces deux catégories — d'où le repli vers `manuel`, qui n'était pas toujours faux, mais parfois évitable.

## Décision — Ajout d'un 4e outil : la vision

**Constat** : l'agent d'audit US1 disposera in fine de trois façons d'observer une page : analyse statique du DOM (BeautifulSoup), interaction navigateur complète (Playwright), et analyse visuelle via capture d'écran + LLM multimodal (vision). Cette 3e capacité n'était pas reflétée dans le prompt d'enrichissement, ce qui empêchait le LLM de la proposer même quand elle est la solution la plus adaptée.

**Modification prévue (Version 3)** :

- `strategie_analyse` passe à 4 valeurs : `statique`, `playwright`, `vision`, `manuel` (ordre de préférence décroissant).
- `manuel` est redéfini comme une vraie exception, réservée aux cas où même une analyse visuelle par LLM ne pourrait pas trancher de façon fiable (ex. jugement légal fin, contexte métier propre au site que rien dans la page ne permet de déduire).
- Un exemple few-shot est ajouté pour `vision` et un pour `manuel` (0 exemple auparavant pour cette dernière catégorie — cause probable du biais identifié).

**Précision sur le périmètre** : le crawler (parcours d'un échantillon de pages) et les regex (détection de patterns textuels) ne sont **pas** ajoutés comme catégories supplémentaires de `strategie_analyse`. Ce sont des détails d'implémentation qui peuvent être mentionnés dans `guide_analyse` (ex. "crawler les pages du menu principal, puis rechercher via regex..."), pas une méthode d'accès au contenu à part entière — ils s'appliquent en combinaison avec `statique`, `playwright` ou `vision`, pas en remplacement.

## Validation — Échantillon élargi (50 règles)

Ingestion complète relancée sur 50 règles réelles avec le prompt Version 3. Distribution obtenue :

```text
playwright : 24
statique   : 23
vision     :  2
manuel     :  1
```

**Résultat** : `manuel` redevient l'exception (1/50, soit 2 %) au lieu de la majorité (9/10 avec la Version 2). Distribution `statique`/`playwright` équilibrée, `vision` utilisée avec parcimonie sur des cas pertinents.

**Vérification qualitative de l'unique règle "manuel"** — n°19, *"Un mécanisme de prévention des usurpations de compte ou d'identité est proposé."* Justification du LLM : la vérification nécessite un accès authentifié aux paramètres de sécurité ou une expertise sur des dispositifs backend invisibles (ex. envoi d'email de confirmation, détection d'IP suspecte, 2FA) — aucune observation frontale (statique, playwright ou vision) ne peut trancher, ce sont des mécanismes qui s'exécutent côté serveur, hors de portée de toute inspection de page. Classification jugée correcte : ce n'est pas un repli par prudence excessive, mais un vrai cas irréductible d'automatisation front-end.

**Conclusion** : le prompt Version 3 est validé sur cet échantillon. La correction du biais identifié à l'Observation 2 (sur-représentation de `manuel`) est confirmée à plus grande échelle, pas seulement sur les 10 règles du premier test.

## Principe retenu pour la suite

Chaque changement de comportement observé sur des données réelles (pas seulement une intuition de conception) doit être : (1) documenté ici avec l'échantillon et les chiffres exacts qui l'ont motivé, (2) traduit en modification du prompt avec une justification explicite, (3) revérifié sur un nouvel échantillon avant d'être considéré comme acquis.
