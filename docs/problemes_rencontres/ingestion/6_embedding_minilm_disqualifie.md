---
title: "Le modèle d'embedding prévu (All MiniLM L12 v2) s'est révélé inutilisable"
subtitle: "Étape 6 (Embedding) — écart entre l'hypothèse de conception et les données réelles"
author: "David LEGRAND"
date: "Juillet 2026"
lang: fr-FR
---

## Objectif de ce document

Ce document trace un écart réel entre `conception.md` et l'implémentation,
volontairement **non corrigé a posteriori** : réécrire `conception.md` pour
qu'il corresponde après coup à la solution retenue effacerait la trace du
raisonnement qui a mené au changement, et ferait passer un vrai ajustement
technique pour une évidence de départ. C'est exactement ce que ce dossier
existe pour éviter.

Fichiers concernés : `app/ingestion/embedding.py`, `app/ingestion/manifest.yml`,
`app/migration/versions/0011_widen_embedding_dimension.py`,
`conception/2_ingestion/L_chunking_embedding_indexation.md`.

## Hypothèse de départ

`conception.md`, `conception/annexes/F_choix_llm.md` et le MLD décrivent un
choix acté « toutes phases » (dev et production) :

- Modèle : **All MiniLM L12 v2**, via **Infomaniak**
- Dimension : `vector(384)`
- Argument principal : gratuit, léger (33M paramètres), cohérent avec le
  positionnement éco-conception affiché du projet (`conception.md` §Éco-
  conception)

Cette hypothèse a été posée **avant** que les Étapes 5-7 (chunking,
embedding, indexation) ne soient réellement implémentées — `regle.embedding`
est resté `NULL` sur les 245 lignes depuis le tout début du projet, sans que
personne n'ait vérifié le modèle contre les données réelles.

## Ce que les données réelles ont révélé

En construisant réellement l'Étape 5 (chunking, 2026-07-26), la décision
actée « 1 règle = 1 chunk » (texte structuré : intitulé + contexte + solution
+ contrôle + guide_analyse + tags + phases) a été mesurée sur les 245 règles
réelles :

- **~319 tokens en moyenne** par chunk
- **jusqu'à ~952 tokens** pour la règle la plus longue (règle 164)

Or **All MiniLM L12 v2 a un `max_token_input` de 128 tokens**. Le modèle
initialement retenu aurait donc tronqué la quasi-totalité des chunks — pour
la règle 164, plus de 86 % du contenu aurait été perdu avant même le calcul
du vecteur. Un embedding calculé sur un quart ou un huitième du texte réel
ne représente plus la règle : la recherche sémantique (US2) aurait cherché
sur du bruit plutôt que sur du contenu.

Ce n'est pas une erreur de configuration — c'est une hypothèse de conception
posée sans donnée réelle pour la vérifier, qui ne survit pas au contact des
245 vraies règles. Exactement le genre d'écart que `docs/problemes_rencontres/`
existe pour documenter honnêtement plutôt que dissimuler.

## Décision prise

Pivot vers **Azure `text-embedding-3-small`**, dimension **native 1536**
(aucune troncature — le coût de stockage/calcul supplémentaire est
négligeable sur 245 lignes). Détail technique et migration de schéma :
`conception/2_ingestion/L_chunking_embedding_indexation.md`. Exécuté pour de
vrai le 2026-07-26 (`make embed-rules`, 245/245 règles vectorisées,
0,0016 €).

## Conséquence sur la cible future (Infomaniak, production)

Le plan initial prévoyait MiniLM « toutes phases », y compris en production.
Cette disqualification s'applique tout autant à la cible future : elle n'est
donc plus MiniLM non plus. Aucun modèle de remplacement n'est encore tranché
côté Infomaniak — BGE Multilingual Gemma2 est nommé comme candidat à évaluer,
explicitement hors périmètre du chantier du 2026-07-26. Sujet ouvert, pas
d'urgence tant que la bascule production n'est pas engagée.

## Ce qui reste volontairement incohérent, et pourquoi

`conception.md`, `conception/annexes/F_choix_llm.md` et les MLD
(`conception/2_ingestion/MLD_qualicheck.md`,
`conception/annexes/MLD_qualicheck.md`) continuent de décrire MiniLM et
`vector(384)` comme le choix actif, à plusieurs endroits. Ce n'est **pas un
oubli à corriger** : c'est la trace de ce qui était cru vrai au moment où ces
documents ont été écrits. La réalité actuelle vit dans le code
(`app/ingestion/manifest.yml`, la migration 0011) et dans ce document — pas
en réécrivant l'histoire dans le dossier de conception.

Si `conception.md` doit un jour être mis à jour pour refléter l'état réel
(utile avant une soutenance, pour ne pas présenter une information fausse
comme si elle était à jour), ce sera un geste **explicite et distinct** —
une mise à jour datée, pas une correction silencieuse qui ferait disparaître
la question qui s'est réellement posée.
