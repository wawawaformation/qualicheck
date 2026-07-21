# Modèle d'enrichissement : la latence ne compte pas pour un traitement par lot

2026-07-21 · retenu (formalise une décision prise plus tôt, jamais écrite)

## Contexte

Le benchmark Azure AI Foundry (16 820 appels, `conception/annexes/benchmark/`)
mesurait pour chaque modèle un taux d'erreur, une fiabilité du JSON et une latence
médiane. Le choix initial pour l'enrichissement s'était porté sur **gpt-5.4-nano**,
notamment pour sa faible latence.

## Ce qui a fait changer d'avis

L'enrichissement est une étape du pipeline d'ingestion : un **traitement par lot**,
lancé deux ou trois fois dans la vie du projet, sans utilisateur devant l'écran.

La latence y est donc sans objet. Qu'une règle prenne 800 ms ou 4 s à enrichir ne
change rien : personne n'attend, et le lot tourne de toute façon plusieurs dizaines
de minutes.

Ce qui compte réellement pour cet usage :

- **la fenêtre de contexte** — Kimi K2.6 offre 256K, utile pour la ré-ingestion
  avec injection des feedbacks prévue en post-MVP
- **la fiabilité du JSON produit**, puisque la sortie est parsée automatiquement

## Décision

**Kimi K2.6** pour l'enrichissement, au lieu de gpt-5.4-nano.

Le critère retenu, généralisable aux choix de modèles à venir :

> La latence est un critère de sélection pour les usages **interactifs**, pas pour
> les traitements **par lot**. Sur un lot, on optimise la fenêtre de contexte, la
> fiabilité de la sortie et le coût.

Ce qui explique la répartition actuelle : `gpt-5.4` et `gpt-5.4-mini` pour l'audit
et le dialogue — où un auditeur attend une réponse — et Kimi K2.6 pour l'ingestion.

## Conséquences

**Une dérive documentaire est restée en place plusieurs semaines.** Le changement a
été appliqué au code et au `.env` mais pas à `conception/conception.md`, dont le
tableau de stack a continué d'annoncer `gpt-5.4-nano` pour l'enrichissement — tout
en ajoutant une ligne Kimi sans retirer l'ancienne, jusqu'à une ligne dupliquée à
l'identique. Corrigé le 2026-07-21.

**Comment elle a été détectée** : en construisant l'index compétences → preuves de
`docs/jury/README.md`. Vérifier qu'une preuve existe réellement, plutôt que la
supposer, a fait apparaître la contradiction entre le document de conception et le
code. C'est le *spec drift* que le `CLAUDE.md` du projet identifie comme risque
principal — ici confirmé en conditions réelles, et sur un document central.
