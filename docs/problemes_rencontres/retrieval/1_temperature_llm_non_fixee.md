---
title: "La température des clients LLM du retrieval n'était jamais fixée"
subtitle: "Variance run-à-run de la suite d'acceptance, cause trouvée et corrigée — et son effet de bord sur une décision prise entre-temps"
author: "David LEGRAND"
date: "Septembre 2026"
lang: fr-FR
---

## Objectif de ce document

Ce document trace un écart réel entre une hypothèse implicite (« les LLM du
retrieval sont raisonnablement stables d'un appel à l'autre ») et le
comportement réellement observé, ainsi que la chaîne de conséquences que ça a
entraînée sur une décision prise entre-temps (le prompt de jugement). Comme
pour `docs/problemes_rencontres/ingestion/6_embedding_minilm_disqualifie.md`,
l'objectif est de garder la trace du raisonnement, pas de la lisser après
coup.

Fichiers concernés : `app/retrieval/decomposition.py`, `jugement.py`,
`guardrail.py`, `app/ingestion/manifest.yml`,
`app/retrieval/prompts/juger_pertinence.md`.

## Ce qui n'avait jamais été vérifié

Les trois clients LLM du chemin `POST /regles/dense`
(`DecompositionClient`, `JugementClient`, `GuardrailClient`) construisent
chacun un `ChatOpenAI(...)` sans jamais passer le paramètre `temperature`.
Personne ne s'en était rendu compte : le code fonctionnait, les tests
unitaires (LLM entièrement mocké) ne pouvaient pas le révéler, et les mesures
réelles précédentes (Temps 2 du refus, guardrail isolé, vagues 1-3 de
chunking) avaient chacune été faites en un seul run — sans jamais comparer
deux runs identiques pour vérifier la stabilité.

Le défaut de `langchain_openai.ChatOpenAI` est `temperature=0.7` : les trois
rôles échantillonnaient donc au hasard à chaque appel, sur le chemin d'une
requête utilisateur en direct.

## Ce que la mesure réelle a révélé

Le 2026-09-13, après l'intégration du guardrail (`GuardrailClient`) en
premier maillon de `POST /regles/dense`, `make api-regles-dense-acceptance`
a été relancé plusieurs fois dans la même session pour valider le résultat.
Les taux par famille ne se sont jamais stabilisés :

| Famille | Run A | Run B | Run C |
| --- | --- | --- | --- |
| `regles_concurrentes` | 100% | 100% | **67%** |
| `vocabulaire_genere_llm` | 95% | 91% | **86%** |
| `paraphrase_intitule` | 94% | 88% | 94% |
| `vocabulaire_objectif` | 78% | 74% | 74% |

Aucun changement de code entre ces runs. Le premier réflexe a été de
soupçonner une régression liée au guardrail ou au prompt de jugement — mais
`sans_reponse`, elle, restait obstinément à 100% sur tous les runs, ce qui ne
collait pas avec « le pipeline est devenu instable en général ».

## Diagnostic

Deux pistes fausses éliminées avant la bonne :

- **Le fichier de cas d'acceptance** (`tests/acceptance/rag_acceptance.jsonl`)
  n'avait pas bougé (`git log` + absence de diff) — la variance ne venait pas
  d'un jeu de test mouvant.
- **`regles_concurrentes`** a une explication partielle distincte, sans
  rapport avec la température : seulement 7 cas, tous multi-cibles, et
  `compute_taux_par_famille()` exclut les cas `PARTIEL` du dénominateur — sur
  un échantillon de 2-3 cas non-partiels, une seule bascule vaut 33 à 50
  points. Ça amplifie la variance pour cette famille précise, mais n'explique
  pas les autres.

La bonne piste : `grep -n "temperature" app/retrieval/*.py` ne remontait
rien. Les trois `ChatOpenAI(...)` tournaient à 0.7 sans que ce soit un choix
délibéré.

## Correction

`temperature: 0` ajouté aux trois rôles (`decomposition`, `jugement`,
`guardrail`) dans `app/ingestion/manifest.yml` — pas en dur dans le code,
cohérent avec la convention du projet — puis passé aux trois
`ChatOpenAI(...)`. Trois tests unitaires ajoutés pour asserter
`temperature=0` à la construction.

**Vérifié sur 2 runs réels consécutifs après reconstruction de l'image**
(le conteneur `api-regles` a une image *bakée*, `docker compose up --build`
est nécessaire — un simple restart ne suffit pas, déjà rencontré le
2026-09-13 pour l'intégration du guardrail). Les effondrements de 30+ points
ont disparu ; il ne reste qu'un résidu de ±1 cas de variation par famille sur
~20-23 cas.

## Découverte inattendue : la température=0 ne garantit pas le déterminisme

En creusant plus loin sur deux cas connus pour être ambigus (règle 28 vs 25,
règle 127 vs 153 — des règles quasi-doublons), un test isolé a montré que
**même à température 0, le jugement LLM peut donner des réponses
différentes d'un appel à l'autre sur des candidats strictement identiques**.
Ce n'est pas un bug du code QualiCheck : c'est un comportement documenté des
API compatibles OpenAI — routage/traitement par lots côté fournisseur,
arithmétique flottante non-associative sur GPU — qui se manifeste surtout
quand la décision du modèle est proche d'une frontière (deux règles très
proches en pertinence). `temperature=0` réduit très fortement la variance,
il ne l'élimine pas.

## Conséquence : le test A/B du prompt de jugement était invalide

Le 2026-09-13, avant la découverte de ce bug, le prompt de jugement avait
été allégé (`app/retrieval/prompts/juger_pertinence.md`) puis **reverté** sur
la base d'un test A/B : un seul appel de chaque côté (ancien prompt vs
nouveau), à température 0.7. La règle 127 était retenue par l'ancien prompt,
perdue par le nouveau — conclusion à l'époque : l'allègement régresse.

Cette conclusion reposait sur une méthode qui ne peut pas être fiable : un
seul tirage à température 0.7 ne distingue pas un effet du prompt d'un
simple coup de dé. Une fois la température fixée, le même test répété
**10 fois par prompt** sur les mêmes candidats figés a montré l'inverse :
le prompt original échoue **0/10** sur la règle 28, l'allégé 1/10 ; la
règle 127 est retenue 3/10 par l'original contre 6/10 par l'allégé. Confirmé
ensuite sur 6 runs réels complets (3 par version de prompt, 684 évaluations
de cas au total) : l'allégé ne régresse sur aucune famille, et fait mieux
sur `vocabulaire_source_opquast` (100% stable contre 90-95%).

**Le prompt allégé a été réappliqué** — la décision du 2026-09-13 était une
fausse piste, pas un vrai défaut du prompt.

## Leçon retenue pour la suite

Un test A/B impliquant un LLM ne doit jamais se conclure sur un seul appel
par variante, **même à température 0**. La méthode correcte : figer les
entrées (candidats, question), répéter chaque variante un nombre suffisant
de fois (N ≥ 10 dans ce cas), comparer des taux plutôt que des réponses
uniques. Ça s'applique à toute future comparaison de prompts ou de modèles
sur ce projet — mémoire assistant `refus_architecture_trois_decisions` mise
à jour en ce sens.

## Coût réel

~0,03 € pour les 2 runs de vérification de la correction de température,
~0,10-0,12 € pour les 6 runs du nouveau test A/B du prompt — les deux hors
CI, lancés à la demande.
