---
title: "Référentiel de compétences — Développeur IA"
subtitle: "Simplon.co — RNCP37827"
lang: fr-FR
toc: true
toc-depth: 2
---

## Bloc de compétences 1 — Réaliser la collecte, le stockage et la mise à disposition des données d'un projet en IA

### C1 — Automatiser l'extraction de données

Depuis un service web, une page web (*scraping*), un fichier de données, une base de données et un système *big data*, en programmant le script adapté afin de pérenniser la collecte des données nécessaires au projet.

**Activités couvertes (A1)** : identification des contraintes techniques propres aux sources, rédaction des spécifications d'extraction, requêtes HTTP (REST), lecture de fichiers, scraping HTML, connexion programmatique à un SGBD/big data, filtrage/parsing, exécution de requêtes SQL et big data.

**Évaluation (E1)** : rapport professionnel individuel + soutenance orale.

**Critères** :
- Script d'extraction fonctionnel — toutes les données visées sont récupérées à l'exécution
- Le script comprend point de lancement, initialisation des dépendances/connexions, règles de traitement, gestion des erreurs/exceptions, fin de traitement, sauvegarde des résultats
- Script versionné, accessible depuis un dépôt Git
- Extraction faite depuis un mix d'au moins : service web (API REST), fichier de données, scraping, base de données, système big data

### C2 — Développer des requêtes SQL d'extraction

Depuis un système de gestion de base de données et un système big data, en appliquant le langage de requête propre au système, pour préparer la collecte des données.

**Critères** :
- Requêtes SQL fonctionnelles — données effectivement extraites
- Documentation des choix de sélection, filtrage, conditions, jointures
- Documentation des optimisations appliquées

### C3 — Développer des règles d'agrégation de données

Issues de différentes sources, en programmant (sous forme de script) la suppression des entrées corrompues et l'homogénéisation des formats, pour préparer le stockage du jeu de données final.

**Critères** :
- Script d'agrégation fonctionnel — données agrégées, nettoyées, normalisées en un seul jeu
- Script versionné, accessible depuis un dépôt Git
- Documentation complète : dépendances, commandes, enchaînements logiques, choix de nettoyage/homogénéisation

### C4 — Créer une base de données

Dans le respect du RGPD, en élaborant les modèles conceptuels et physiques à partir des données préparées, et en programmant leur import.

**Activités couvertes (A2)** : modélisation Merise, choix du SGBD, création de la base, documentation d'installation, registre des traitements de données personnelles (RGPD), procédures de tri, script d'import.

**Critères** :
- Modélisations respectant la méthode et le formalisme Merise
- Modèle physique fonctionnel, intégré sans erreur
- SGBD choisi au regard de la modélisation et des contraintes du projet
- Script d'import fonctionnel, documenté et versionné (même dépôt Git)
- Registre des traitements de données personnelles complet
- Procédures de tri RGPD rédigées, avec fréquence d'exécution

### C5 — Développer une API mettant à disposition le jeu de données

En utilisant l'architecture REST, pour permettre l'exploitation du jeu de données par les autres composants du projet.

**Activités couvertes** : spécifications d'accès (API REST + accès direct BDD), configuration des accès, réception/validation des requêtes client, réponses, règles d'autorisation, sécurisation (Top 10 OWASP API), documentation.

**Critères** :
- Documentation technique de l'API couvre tous les points de terminaison
- Documentation couvre authentification/autorisation
- Documentation respecte les standards du modèle choisi (ex. OpenAPI)
- API fonctionnelle : accès restreint par autorisation, mise à disposition complète du jeu de données selon les spécifications

---

## Bloc de compétences 2 — Intégrer des modèles et des services d'intelligence artificielle

### C6 — Organiser et réaliser une veille technique et réglementaire

En animant le travail collectif de sélection des sources, collecte, traitement et partage des informations, pour formuler des recommandations en phase avec l'état de l'art.

**Évaluation (E2)** : rapport professionnel individuel + soutenance orale.

**Critères** :
- Temps de veille planifiés régulièrement (minimum 1h/semaine)
- Choix des outils d'agrégation cohérent avec sources et budget
- Synthèses communiquées dans un format accessible (Valentin Haüy, AcceDe)
- Sources et flux répondant aux critères de fiabilité (auteur identifié, compétences confirmées, contenu daté et sourcé)

### C7 — Identifier des services d'intelligence artificielle préexistants

À partir de l'expression de besoin en fonctionnalités IA, en réalisant un benchmark de services existants et en analysant leurs caractéristiques pour formaliser une ou plusieurs recommandations.

**Critères** :
- Expression de besoin reformulée, objectifs et contraintes présentés
- Benchmark liste les services étudiés et non étudiés, avec raisons d'écarter
- Benchmark détaille l'adéquation fonctionnelle, la démarche éco-responsable, les contraintes techniques et pré-requis pour chaque solution
- Conclusions délimitent clairement les services répondant/ne répondant pas au besoin

### C8 — Paramétrer un service d'intelligence artificielle

En suivant sa documentation technique et en respectant les spécifications du projet, pour permettre l'intégration des connecteurs du service dans le système d'information.

**Critères** :
- Service installé, accessible, avec authentification si nécessaire
- Service configuré correctement (besoins fonctionnels et contraintes techniques)
- Monitorage disponible opérationnel
- Documentation couvre accès, installation, test, dépendances, interconnexions, données impliquées
- Documentation accessible (format conforme)

### C9 — Développer une API exposant un modèle d'intelligence artificielle

En utilisant l'architecture REST, pour permettre l'interaction entre le modèle et les autres composants du projet.

**Activités couvertes (A4)** : analyse des spécifications, conception de l'architecture API, choix des outils/langages, vérification/transformation des paramètres client, exécution du modèle, réponse au client, règles d'autorisation, sécurisation OWASP, tests d'intégration, versionnement, documentation.

**Évaluation (E3)** : rapport professionnel individuel + soutenance orale avec démonstration.

**Critères** :
- API restreinte par authentification
- Accès aux fonctions du modèle conforme aux spécifications
- Recommandations OWASP intégrées
- Sources versionnées, dépôt Git distant
- Tests couvrant tous les points de terminaison, sans bug, résultats correctement interprétés
- Documentation complète (architecture, points de terminaison, authentification), respectant les standards (ex. OpenAPI) et l'accessibilité

### C10 — Intégrer l'API d'un modèle ou d'un service d'intelligence artificielle dans une application

En respectant les spécifications du projet et les normes d'accessibilité, à l'aide de la documentation technique de l'API, pour créer les fonctionnalités IA de l'application.

**Critères** :
- Application de départ installée et fonctionnelle en développement
- Communication avec l'API fonctionnelle
- Authentification et renouvellement (expiration des jetons) intégrés correctement
- Tous les points de terminaison concernés intégrés selon les spécifications
- Adaptations d'interface intégrées en accord avec les spécifications
- Tests d'intégration couvrant tous les points de terminaison exploités, sans bug
- Sources versionnées, dépôt Git de l'application

### C11 — Monitorer un modèle d'intelligence artificielle

À partir des métriques courantes et spécifiques au projet, en intégrant les outils de collecte, d'alerte et de restitution, pour permettre l'amélioration itérative du modèle.

**Activités couvertes (A5)** : liste des métriques et déclencheurs de réentraînement, choix d'un outil de monitorage, intégration des collecteurs/déclencheurs, outil de restitution (Grafana, Dash, Kibana...), alertes, test/validation, versionnement, documentation.

**Critères** :
- Métriques expliquées sans erreur d'interprétation
- Outils adaptés au contexte et aux contraintes techniques
- Au moins un vecteur de restitution en temps réel (dashboard, feuille de calcul...)
- Enjeux d'accessibilité pris en compte
- Chaîne testée en bac à sable avant mise en état de marche
- Sources versionnées, dépôt Git distant
- Documentation technique complète (installation, configuration, utilisation) et accessible

### C12 — Programmer les tests automatisés d'un modèle d'intelligence artificielle

En définissant les règles de validation des jeux de données, des étapes de préparation, d'entraînement, d'évaluation et de validation du modèle, pour permettre son intégration continue et garantir un niveau de qualité élevé.

**Critères** :
- Cas à tester listés et définis (partie visée, périmètre, stratégie)
- Outils de test cohérents avec l'environnement technique
- Tests intégrés, couverture établie respectée, exécution sans problème
- Sources versionnées, dépôt Git distant (DVC, Gitlab...)
- Documentation de l'installation, des dépendances, de l'exécution et du calcul de couverture

### C13 — Créer une chaîne de livraison continue d'un modèle d'intelligence artificielle

En installant les outils et appliquant les configurations souhaitées, dans une approche MLOps, pour automatiser les étapes de validation, de test, de *packaging* et de déploiement du modèle.

**Critères** :
- Documentation couvre toutes les étapes, tâches, déclencheurs
- Déclencheurs intégrés comme définis
- Fichiers de configuration reconnus et exécutés correctement
- Étapes de test des données, d'entraînement et de validation intégrées, sans erreur
- Étape de livraison (ex. pull request) intégrée avec rapports d'évaluation attachés
- Sources versionnées, dépôt Git distant

---

## Bloc de compétences 3 — Réaliser une application intégrant un service d'intelligence artificielle

### C14 — Analyser le besoin d'application d'un commanditaire intégrant un service d'IA

En rédigeant les spécifications fonctionnelles et en modélisant, dans le respect des standards d'utilisabilité et d'accessibilité, pour établir avec précision les objectifs de développement.

**Activités couvertes (A6)** : modélisation des données (entités-relations, MCD/MPD), modélisation des parcours utilisateurs, rédaction des user stories, objectifs d'accessibilité.

**Évaluation (E4)** : rapport professionnel individuel + soutenance orale avec démonstration.

**Critères** :
- Modélisation des données respectant un formalisme (Merise, entités-relations...)
- Modélisation des parcours respectant un formalisme (schéma fonctionnel, wireframes...)
- Chaque spécification fonctionnelle couvre contexte, scénarios, critères de validation
- Objectifs d'accessibilité intégrés aux critères d'acceptation des user stories, appuyés sur un standard (WCAG, RGAA...)

### C15 — Concevoir le cadre technique d'une application intégrant un service d'IA

À partir de l'analyse du besoin, en spécifiant l'architecture technique et applicative et en préconisant outils et méthodes, pour permettre le développement du projet.

**Activités couvertes** : architecture (n-tiers, serverless, micro-services, MVC...), choix des langages/outils, identification des flux de données et zones de stockage, choix des services externes, rédaction des spécifications techniques.

**Critères** :
- Spécifications couvrant architecture, dépendances, environnement d'exécution
- Services/prestataires éco-responsables favorisés
- Flux de données représentés par un diagramme
- Preuve de concept accessible et fonctionnelle en pré-production
- Conclusion de la preuve de concept permettant une prise de décision

### C16 — Coordonner la réalisation technique d'une application d'intelligence artificielle

En s'intégrant dans une conduite agile de projet et un contexte MLOps, en facilitant les temps de collaboration, pour atteindre les objectifs de production et de qualité.

**Critères** :
- Cycles, étapes, rôles, rituels et outils de la méthode agile respectés
- Outils de pilotage (kanban, burndown chart, backlog...) disponibles
- Objectifs et modalités des rituels partagés à toutes les parties prenantes
- Éléments de pilotage accessibles tout au long du projet

### C17 — Développer les composants techniques et les interfaces d'une application

En utilisant les outils et langages adaptés, en respectant les spécifications, les standards et normes d'accessibilité, de sécurité et de gestion des données.

**Critères** :
- Environnement de développement conforme aux spécifications
- Interfaces intégrées, conformes aux maquettes
- Comportements des composants et navigation conformes aux spécifications fonctionnelles
- Composants métier développés et fonctionnels
- Gestion des droits/accès conforme aux spécifications
- Flux de données intégrés conformément aux spécifications
- Bonnes pratiques d'éco-conception respectées (éco-index, Green IT)
- Top 10 OWASP implémenté si nécessaire
- Tests d'intégration/unitaires couvrant au moins composants métier et gestion des accès
- Sources versionnées, dépôt Git distant
- Documentation technique complète et accessible

### C18 — Automatiser les phases de tests du code source

Lors du versionnement des sources, à l'aide d'un outil d'intégration continue, pour garantir la qualité technique des réalisations.

**Critères** :
- Documentation couvre outils, étapes, tâches, déclencheurs
- Outil d'intégration continue cohérent avec l'environnement technique
- Chaîne intègre toutes les étapes préalables aux tests (build, configurations)
- Chaîne exécute les tests disponibles au déclenchement
- Configuration versionnée avec les sources, dépôt Git distant
- Documentation d'installation, configuration, test, accessible

### C19 — Créer un processus de livraison continue d'une application

En s'appuyant sur une chaîne d'intégration continue et en paramétrant les outils d'automatisation et environnements de test, pour permettre une restitution optimale de l'application.

**Critères** :
- Documentation couvre toutes les étapes, tâches, déclencheurs
- Fichiers de configuration reconnus et exécutés
- Étapes de packaging (compilation, minification, build de containers...) intégrées, sans erreur
- Étape de livraison (ex. pull request) intégrée après validation du packaging
- Sources versionnées, dépôt Git distant
- Documentation d'installation, configuration, test, accessible

### C20 — Surveiller une application d'intelligence artificielle

En mobilisant des techniques de monitorage et de journalisation, dans le respect des normes de gestion des données personnelles, pour alimenter la *feedback loop* dans une approche MLOps et permettre la détection automatique d'incidents.

**Activités couvertes (A9)** : définition des métriques et seuils d'alerte, choix d'un outil de monitorage, configuration, intégration de la journalisation, intégration des alertes, documentation.

**Évaluation (E5)** : documentation technique (monitorage + résolution d'incident) + soutenance orale.

**Critères** :
- Documentation liste métriques, seuils et valeurs d'alerte par métrique à risque
- Documentation explicite les arguments des choix techniques
- Outils (collecteurs, journalisation, agrégateurs, filtres, dashboard) installés et opérationnels au moins en local
- Règles de journalisation intégrées selon les métriques à surveiller
- Alertes configurées et en état de marche
- Documentation d'installation/configuration, accessible

### C21 — Résoudre les incidents techniques

En apportant les modifications nécessaires au code de l'application et en documentant les solutions, pour garantir le fonctionnement opérationnel.

**Critères** :
- Causes du problème identifiées correctement
- Problème reproduit en environnement de développement
- Procédure de débogage documentée depuis l'outil de suivi
- Solution documentée, explicitant chaque étape de la résolution
- Solution versionnée dans le dépôt Git (ex. merge request)

---

## Glossaire (termes du référentiel)

- **Scraping** : extraction du contenu de sites web via script, pour réutilisation (ex. enrichissement de base de données).
- **Big data** : jeux de données caractérisés par variété, volume et vitesse (les "3V").
- **Script** : programme dédié à une tâche unique, souvent dans un cadre d'automatisation.
- **REST (API)** : architecture d'API pour la création de services web (HTTP).
- **SQL** : langage d'exploitation des bases de données relationnelles.
- **Dépôt Git** : entrepôt virtuel stockant les versions d'un projet (sources, dépendances).
- **Merise** : méthode d'analyse, de conception et de réalisation de systèmes d'information, aujourd'hui utilisée principalement pour la conception de structures de données relationnelles.
- **SaaS** : logiciel en tant que service, accessible via navigateur, hébergé par l'éditeur.
- **VPS** : serveur virtuel privé.
- **Packaging** (modèle IA) : transformation d'un modèle en format d'exécution générique et auto-suffisant (ex. via ONNX, Docker).
- **Mocks, fixtures** : initialiseurs personnalisés simplifiant la construction des dépendances de test.
- **MLOps** : pratique établissant des règles de collaboration entre concepteurs/développeurs et opérateurs d'infrastructure.
- **N-tiers** : architecture client-serveur où présentation, traitement et données sont physiquement séparés.
- **Serverless** : modèle d'exécution cloud où le fournisseur gère dynamiquement les ressources serveur.
- **Model-vue-contrôleur (MVC)** : modèle de conception divisant la logique en trois éléments interconnectés.
- **Micro-services** : architecture organisant une application en collection de services indépendants.
- **Back-end** / **Front-end** : couche serveur / couches visibles d'une application.
- **Déploiement** : mise en ligne/production d'un programme ou d'une application.
- **OpenAPI** : norme de description des interfaces de programmation conformes REST.
- **BaaS** : service cloud externalisant les aspects génériques d'un back-end (authentification, comptes, notifications...).
- **Feedback loop** : processus par lequel les résultats prédits d'un modèle sont réutilisés pour former de nouvelles versions du modèle.
