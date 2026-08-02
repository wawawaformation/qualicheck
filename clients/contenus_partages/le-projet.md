---
title: Le projet QualiCheck
author: David LEGRAND
date: Août 2026
lang: fr-FR
---

## Présentation

QualiCheck est un assistant d'aide à l'audit de qualité web, construit
autour du référentiel Opquast (245 règles de qualité web).

## Comment ça fonctionne

Le référentiel Opquast est enrichi par un pipeline d'ingestion appuyé sur
un modèle de langage (LLM) : chaque règle reçoit une stratégie d'analyse
(statique, Playwright, vision, manuelle), des outils, des objectifs et un
guide d'analyse.

Cet enrichissement est ensuite revu par un référent humain, qui peut
annoter une règle mal classée ; l'agent d'enrichissement en tient compte
au prochain passage.

## Contexte du projet

QualiCheck est développé par David LEGRAND dans le cadre d'une formation
certifiante Développeur IA (titre professionnel / RNCP). Le projet est en
cours de construction ; certaines fonctionnalités (audit automatisé,
question libre) sont encore en conception.

## Licence du contenu

Le référentiel Opquast enrichi est diffusé sous licence CC BY-SA 4.0, avec
le soutien d'Élie Sloïm (Opquast). Voir la page « Mentions légales » pour
le reste du contenu et du code.
