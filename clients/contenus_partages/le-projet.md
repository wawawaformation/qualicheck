---
title: Le projet QualiCheck
author: David LEGRAND
date: Août 2026
lang: fr-FR
---

## Présentation

QualiCheck est un assistant d'aide à l'audit de qualité web, construit
autour du référentiel Opquast (245 règles de qualité web).

## Comment ça fonctionne aujourd'hui

Le référentiel Opquast est enrichi par un pipeline d'ingestion appuyé sur
un modèle de langage (LLM) : chaque règle reçoit une stratégie d'analyse
(statique, Playwright, vision, manuelle), des outils, des objectifs et un
guide d'analyse.

Cet enrichissement est ensuite revu par un référent humain, qui peut
annoter une règle mal classée ; l'agent d'enrichissement en tient compte
au prochain passage. C'est ce que fait cette interface.

## Les fonctionnalités à venir

### Question libre (prochain développement)

Un utilisateur pose une question sur une URL ou une capture d'écran ; le
système répond par recherche sémantique (RAG) dans le référentiel Opquast
enrichi, avec des garde-fous (guardrails) et une mémoire de la session en
cours. C'est la prochaine fonctionnalité développée.

### Audit assisté

Un crawl léger explore un site, l'utilisateur sélectionne les pages et les
règles à auditer, un agent LLM génère des constats page par page, dialogue
avec l'utilisateur pour les affiner, puis produit un rapport final validé
par un humain à chaque étape — l'IA assiste l'auditeur, elle ne se
substitue jamais à sa décision.

## Contexte du projet

QualiCheck est développé par David LEGRAND dans le cadre d'une formation
certifiante Développeur IA (titre professionnel / RNCP). La revue du
référentiel (ce que vous utilisez ici) est implémentée ; la question libre
et l'audit assisté sont encore en conception.

## Licence du contenu

Le référentiel Opquast enrichi est diffusé sous licence CC BY-SA 4.0, avec
le soutien d'Élie Sloïm (Opquast). Voir la page « Mentions légales » pour
le reste du contenu et du code.
