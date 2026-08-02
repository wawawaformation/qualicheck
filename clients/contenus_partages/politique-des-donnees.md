---
title: Politique des données
author: David LEGRAND
date: Août 2026
lang: fr-FR
---

## Quelles données sont traitées aujourd'hui

À ce stade, seule la revue du référentiel est disponible. Elle ne demande
aucune création de compte utilisateur.

La seule donnée saisie par l'utilisateur est la **clé API** nécessaire pour
annoter une règle du référentiel (écran « Clé API »). Cette clé :

- est stockée uniquement dans le `localStorage` du navigateur de
  l'utilisateur ;
- n'est jamais transmise à un autre destinataire que l'API QualiCheck
  elle-même (`app/api_regles`), via l'en-tête `Authorization` ;
- n'est associée à aucun nom d'utilisateur : le serveur identifie un client
  déclaré par la clé elle-même, il ne trace pas d'auteur individuel des
  annotations.

## Évolution prévue (audit et question libre)

Les fonctionnalités à venir (audit assisté, question libre) nécessiteront la
création d'un compte utilisateur et une gestion dédiée des données
personnelles associées. Cette page sera mise à jour en conséquence dès que
ces fonctionnalités seront disponibles.

Ces fonctionnalités s'appuieront aussi sur **Langfuse** pour le monitorage
des appels au modèle de langage. La question de l'anonymisation des données
tracées (contenu des questions, réponses) n'est pas encore tranchée — cette
page sera précisée dès que cette décision sera prise.

## Ce que QualiCheck ne fait pas

Aucun cookie de suivi ni outil d'analyse d'audience n'est mis en place à ce
stade du projet.

## Contenu du référentiel

Le référentiel Opquast enrichi, consulté sans authentification, est diffusé
sous licence
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.fr) —
voir la page « Mentions légales » pour l'attribution complète.

## Contact

Pour toute question relative aux données traitées par QualiCheck :
[contact@david-legrand.fr](mailto:contact@david-legrand.fr)
