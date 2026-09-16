---
title: "Le jugement LLM sur les candidats plafonnait à 50% de refus corrects"
subtitle: "Biais de sélection — pourquoi montrer des candidats à un LLM l'empêche de dire « aucun »"
author: "David LEGRAND"
date: "Septembre 2026"
lang: fr-FR
---

## Objectif de ce document

Ce document trace un écart entre une hypothèse d'architecture raisonnable et
son comportement réel mesuré, et la méthode qui a permis d'en sortir — pas en
améliorant un prompt, mais en isolant une variable expérimentale. Même
démarche que `docs/problemes_rencontres/retrieval/1_temperature_llm_non_fixee.md` :
garder la trace du raisonnement plutôt que de la lisser après coup.

Fichiers concernés : `app/retrieval/jugement.py`, `app/retrieval/guardrail.py`,
`app/api_regles/regles.py`,
`docs/superpowers/specs/2026-09-11-retrieval-refus-temps2-design.md`,
`docs/eval/mesure_guardrail_perimetre_2026-09-11_214327.md`.

## Hypothèse de départ

Le mécanisme de refus (« que répond l'API à une question hors périmètre
Opquast, type recette de cuisine ou tarif de certification ? ») avait été
confié à `JugementClient` : un LLM qui reçoit la question **et** les 15
règles candidates retrouvées par la recherche vectorielle, avec pour tâche de
dire lesquelles répondent réellement — liste vide si aucune. L'hypothèse
implicite : un bon prompt, avec des exemples explicites de ce qu'il ne faut
pas confondre, suffirait à faire dire « aucune » au LLM quand c'est le cas.

## Ce que la mesure réelle a révélé

Mesuré sur les 20 cas `sans_reponse` du jeu d'acceptance (2026-09-11) :
**plafond de 40 à 55% de refus corrects selon le modèle**
(`gpt-5.4-mini` 40-45%, `gpt-5.4` 55%), malgré un prompt renforcé avec des
contre-exemples explicites (distinction Opquast-organisme vs contenu d'une
règle, gestion de projet vs qualité web).

Le cas le plus révélateur : *« Quel est le palmarès de la dernière Coupe du
monde de football ? »* → la règle 12 était citée à tort, **deux fois de
suite**, malgré un contre-exemple dédié à ce cas précis dans le prompt.
Retravailler le prompt n'a fait progresser le taux que de 5 points (40% →
45%) — un signal que le levier utilisé n'était pas le bon.

## Diagnostic

Le réflexe naturel face à un taux de refus insuffisant est d'améliorer le
prompt : plus d'exemples, des instructions plus explicites, un « en cas de
doute, réponds liste vide » renforcé. Ça a été fait, sans effet réel.

Le vrai problème n'était pas la formulation — c'était l'architecture
elle-même. **Présenter une liste de candidats à un LLM et lui demander
« lesquels répondent » le pousse structurellement à en choisir un**, même
quand rien ne convient. Ce n'est pas un défaut de prompt qu'on peut corriger
en l'améliorant : le simple fait de montrer des candidats introduit un biais
que la formulation ne neutralise pas.

## La méthode qui a débloqué : isoler la variable

Plutôt que de continuer à itérer sur le prompt, la question posée a changé :
est-ce le *prompt* qui est en cause, ou le fait de *montrer des candidats* ?
Pour trancher, il fallait isoler cette seule variable — même LLM, même
question, mais **sans aucun candidat sous les yeux**.

`GuardrailClient` (`app/retrieval/guardrail.py`) a été écrit dans ce seul but
: classer une question dans/hors périmètre Opquast, sans jamais voir de
règle candidate. Mesuré isolément sur le même jeu de cas :
**100% sur les 20 cas `sans_reponse`, 97,9% sur les 94 cas valides**
(`docs/eval/mesure_guardrail_perimetre_2026-09-11_214327.md`). Retirer les
candidats retire le biais — la preuve que le problème était bien
architectural, pas une question de formulation.

## Décision prise

Le refus n'est pas une décision unique mais **trois décisions à trois
endroits distincts** du pipeline US2 :

1. **Guardrail de périmètre** — sans candidat, avant tout le reste.
2. **Jugement sur les candidats retrouvés** (`JugementClient`) — reste utile
   pour la précision de citation (quelles règles, parmi les 15 candidates,
   répondent vraiment), mais plafonné pour le refus pur.
3. **Jugement final avec mémoire/contexte** (niveau agent) — hors périmètre,
   pas construit.

Le `GuardrailClient`, d'abord conçu pour vivre « au niveau agent » (avec
l'historique de conversation), a finalement été intégré directement en
premier maillon de `POST /regles/dense` le 2026-09-13 — il est stateless,
rien n'empêchait de le brancher tout de suite dans l'outil plutôt que
d'attendre une couche agent pas encore conçue. Mesuré en réel : `sans_reponse`
stable à 100% sur 4 runs.

## Leçon méthodologique

Face à un plafond de performance qui résiste à l'amélioration du prompt, la
question à se poser n'est pas seulement « comment mieux formuler l'instruction
? » mais **« qu'est-ce que je montre au LLM, et est-ce que ça biaise la
réponse en soi ? »**. Un prompt qui ne progresse pas malgré des itérations
successives est un signal qu'il faut isoler expérimentalement les variables
de l'architecture (ce qui est montré au modèle) avant de continuer à
retravailler la formulation. À rapprocher de la leçon du document 1 du même
dossier (tester un LLM à répétition plutôt qu'en un seul appel) — même
discipline de mesure, deux pièges différents.

## Coût réel

Mesure Temps 2 (`JugementClient` seul) et mesure isolée du guardrail :
détail dans `docs/eval/mesure_guardrail_perimetre_2026-09-11_214327.md`,
coût 0,0063 € pour cette dernière.
