<map version="1.0.1">
<node TEXT="Référentiel de compétences — Développeur IA (RNCP37827)">

<node TEXT="E1 — Mise à disposition des données — 15 min — Rapport 2 à 5 p." POSITION="right" COLOR="#2F5597">
    <node TEXT="Flux automatisé de collecte depuis différentes sources" COLOR="#666666"/>
    <node TEXT="Requêtes de nettoyage et mise en forme des données" COLOR="#666666"/>
    <node TEXT="Création d'une base de données" COLOR="#666666"/>
    <node TEXT="Exposition des données dans une API" COLOR="#666666"/>

    <node TEXT="C1 — Automatiser l'extraction de données" COLOR="#2F5597">
      <node TEXT="Service web, page web (scraping), fichier, BDD, big data" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Script fonctionnel — toutes les données visées récupérées à l'exécution" COLOR="#999999"/>
        <node TEXT="Point de lancement, init dépendances/connexions, règles de traitement, gestion erreurs, fin de traitement, sauvegarde" COLOR="#999999"/>
        <node TEXT="Script versionné, dépôt Git" COLOR="#999999"/>
        <node TEXT="Mix d'au moins : API REST, fichier, scraping, BDD, big data" COLOR="#999999"/>
      </node>
    </node>

    <node TEXT="C2 — Développer des requêtes SQL d'extraction" COLOR="#2F5597">
      <node TEXT="SGBD + système big data" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Requêtes fonctionnelles — données effectivement extraites" COLOR="#999999"/>
        <node TEXT="Documentation des choix de sélection, filtrage, conditions, jointures" COLOR="#999999"/>
        <node TEXT="Documentation des optimisations appliquées" COLOR="#999999"/>
      </node>
    </node>

    <node TEXT="C3 — Développer des règles d'agrégation de données" COLOR="#2F5597">
      <node TEXT="Nettoyage, homogénéisation des formats, plusieurs sources" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Script fonctionnel — données agrégées, nettoyées, normalisées en un seul jeu" COLOR="#999999"/>
        <node TEXT="Script versionné, dépôt Git" COLOR="#999999"/>
        <node TEXT="Documentation complète : dépendances, commandes, enchaînements, choix de nettoyage" COLOR="#999999"/>
      </node>
    </node>

    <node TEXT="C4 — Créer une base de données" COLOR="#2F5597">
      <node TEXT="Modèles Merise (conceptuel/physique), respect du RGPD" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Modélisations respectant la méthode et le formalisme Merise" COLOR="#999999"/>
        <node TEXT="Modèle physique fonctionnel, intégré sans erreur" COLOR="#999999"/>
        <node TEXT="SGBD choisi au regard de la modélisation et des contraintes projet" COLOR="#999999"/>
        <node TEXT="Script d'import fonctionnel, documenté, versionné" COLOR="#999999"/>
        <node TEXT="Registre des traitements de données personnelles complet" COLOR="#999999"/>
        <node TEXT="Procédures de tri RGPD rédigées, avec fréquence d'exécution" COLOR="#999999"/>
      </node>
    </node>

    <node TEXT="C5 — Développer une API mettant à disposition le jeu de données" COLOR="#2F5597">
      <node TEXT="Architecture REST, autorisation, OWASP" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Documentation technique couvre tous les points de terminaison" COLOR="#999999"/>
        <node TEXT="Documentation couvre authentification/autorisation" COLOR="#999999"/>
        <node TEXT="Documentation respecte les standards du modèle choisi (ex. OpenAPI)" COLOR="#999999"/>
        <node TEXT="API fonctionnelle : accès restreint par autorisation, mise à disposition complète" COLOR="#999999"/>
      </node>
    </node>

  </node>

<node TEXT="E2 — Cas pratique de veille — 15 min — Rapport 15 à 20 p." POSITION="right" COLOR="#A23B2E">
    <node TEXT="Problématique technique/fonctionnelle d'IA à partir de l'expression de besoin" COLOR="#666666"/>
    <node TEXT="Inventaire des outils et services d'IA accessibles" COLOR="#666666"/>
    <node TEXT="Préconisation d'un ou plusieurs services d'IA" COLOR="#666666"/>
    <node TEXT="Étapes de configuration et d'installation du/des service(s) préconisé(s)" COLOR="#666666"/>

    <node TEXT="C6 — Veille technique et réglementaire" COLOR="#A23B2E">
      <node TEXT="Sélection de sources, collecte, partage, recommandations" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Temps de veille planifiés régulièrement (minimum 1h/semaine)" COLOR="#999999"/>
        <node TEXT="Choix des outils d'agrégation cohérent avec sources et budget" COLOR="#999999"/>
        <node TEXT="Synthèses communiquées dans un format accessible (Valentin Haüy, AcceDe)" COLOR="#999999"/>
        <node TEXT="Sources/flux fiables (auteur identifié, compétences confirmées, contenu daté et sourcé)" COLOR="#999999"/>
      </node>
    </node>

    <node TEXT="C7 — Identifier des services d'IA préexistants" COLOR="#A23B2E">
      <node TEXT="Benchmark, adéquation fonctionnelle, éco-responsabilité" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Expression de besoin reformulée, objectifs et contraintes présentés" COLOR="#999999"/>
        <node TEXT="Benchmark liste services étudiés et non étudiés, avec raisons d'écarter" COLOR="#999999"/>
        <node TEXT="Benchmark détaille adéquation fonctionnelle, démarche éco-responsable, contraintes techniques" COLOR="#999999"/>
        <node TEXT="Conclusions délimitent clairement services répondant/ne répondant pas au besoin" COLOR="#999999"/>
      </node>
    </node>

    <node TEXT="C8 — Paramétrer un service d'IA" COLOR="#A23B2E">
      <node TEXT="Installation, config, monitorage, documentation" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Service installé, accessible, avec authentification si nécessaire" COLOR="#999999"/>
        <node TEXT="Service configuré correctement (besoins fonctionnels et contraintes techniques)" COLOR="#999999"/>
        <node TEXT="Monitorage disponible opérationnel" COLOR="#999999"/>
        <node TEXT="Documentation couvre accès, installation, test, dépendances, interconnexions, données" COLOR="#999999"/>
        <node TEXT="Documentation accessible (format conforme)" COLOR="#999999"/>
      </node>
    </node>

  </node>

<node TEXT="E3 — Intégration de l'IA — 20 min — Rapport 15 à 20 p." POSITION="right" COLOR="#A23B2E">
    <node TEXT="Développement d'une API pour exposer un modèle d'IA" COLOR="#666666"/>
    <node TEXT="Intégration de l'API dans une application existante" COLOR="#666666"/>
    <node TEXT="Monitorage et tests du modèle" COLOR="#666666"/>
    <node TEXT="Chaîne de livraison continue du modèle" COLOR="#666666"/>
    <node TEXT="Démo des différents composants" COLOR="#666666"/>

    <node TEXT="C9 — Développer une API exposant un modèle d'IA" COLOR="#A23B2E">
      <node TEXT="REST, authentification, OWASP, tests d'intégration" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="API restreinte par authentification" COLOR="#999999"/>
        <node TEXT="Accès aux fonctions du modèle conforme aux spécifications" COLOR="#999999"/>
        <node TEXT="Recommandations OWASP intégrées" COLOR="#999999"/>
        <node TEXT="Sources versionnées, dépôt Git distant" COLOR="#999999"/>
        <node TEXT="Tests couvrant tous les points de terminaison, sans bug, résultats correctement interprétés" COLOR="#999999"/>
        <node TEXT="Documentation complète (architecture, endpoints, auth), standards (OpenAPI), accessibilité" COLOR="#999999"/>
      </node>
    </node>

    <node TEXT="C10 — Intégrer l'API d'un modèle/service d'IA dans une application" COLOR="#A23B2E">
      <node TEXT="Auth + renouvellement, accessibilité, tests d'intégration" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Application de départ installée et fonctionnelle en développement" COLOR="#999999"/>
        <node TEXT="Communication avec l'API fonctionnelle" COLOR="#999999"/>
        <node TEXT="Authentification et renouvellement (expiration des jetons) intégrés correctement" COLOR="#999999"/>
        <node TEXT="Tous les points de terminaison concernés intégrés selon les spécifications" COLOR="#999999"/>
        <node TEXT="Adaptations d'interface intégrées en accord avec les spécifications" COLOR="#999999"/>
        <node TEXT="Tests d'intégration couvrant tous les endpoints exploités, sans bug" COLOR="#999999"/>
        <node TEXT="Sources versionnées, dépôt Git de l'application" COLOR="#999999"/>
      </node>
    </node>

    <node TEXT="C11 — Monitorer un modèle d'IA" COLOR="#A23B2E">
      <node TEXT="Métriques, collecte, alerte, restitution temps réel" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Métriques expliquées sans erreur d'interprétation" COLOR="#999999"/>
        <node TEXT="Outils adaptés au contexte et aux contraintes techniques" COLOR="#999999"/>
        <node TEXT="Au moins un vecteur de restitution en temps réel (dashboard, feuille de calcul...)" COLOR="#999999"/>
        <node TEXT="Enjeux d'accessibilité pris en compte" COLOR="#999999"/>
        <node TEXT="Chaîne testée en bac à sable avant mise en état de marche" COLOR="#999999"/>
        <node TEXT="Sources versionnées, dépôt Git distant" COLOR="#999999"/>
        <node TEXT="Documentation technique complète et accessible" COLOR="#999999"/>
      </node>
    </node>

    <node TEXT="C12 — Programmer les tests automatisés d'un modèle d'IA" COLOR="#A23B2E">
      <node TEXT="Validation jeux de données, préparation, entraînement, éval" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Cas à tester listés et définis (partie visée, périmètre, stratégie)" COLOR="#999999"/>
        <node TEXT="Outils de test cohérents avec l'environnement technique" COLOR="#999999"/>
        <node TEXT="Tests intégrés, couverture établie respectée, exécution sans problème" COLOR="#999999"/>
        <node TEXT="Sources versionnées, dépôt Git distant (DVC, Gitlab...)" COLOR="#999999"/>
        <node TEXT="Documentation installation, dépendances, exécution, calcul de couverture" COLOR="#999999"/>
      </node>
    </node>

    <node TEXT="C13 — Créer une chaîne de livraison continue d'un modèle d'IA" COLOR="#A23B2E">
      <node TEXT="MLOps : validation, test, packaging, déploiement" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Documentation couvre toutes les étapes, tâches, déclencheurs" COLOR="#999999"/>
        <node TEXT="Déclencheurs intégrés comme définis" COLOR="#999999"/>
        <node TEXT="Fichiers de configuration reconnus et exécutés correctement" COLOR="#999999"/>
        <node TEXT="Étapes de test des données, d'entraînement et de validation intégrées, sans erreur" COLOR="#999999"/>
        <node TEXT="Étape de livraison (ex. pull request) intégrée avec rapports d'évaluation attachés" COLOR="#999999"/>
        <node TEXT="Sources versionnées, dépôt Git distant" COLOR="#999999"/>
      </node>
    </node>

  </node>

<node TEXT="E4 — Développement applicatif — 20 min — Rapport 15 à 20 p." POSITION="left" COLOR="#3F7D4A">
    <node TEXT="Projet d'application répondant au besoin" COLOR="#666666"/>
    <node TEXT="Tests et chaîne de livraison continue de l'application" COLOR="#666666"/>
    <node TEXT="Démo de l'application réalisée" COLOR="#666666"/>

    <node TEXT="C14 — Analyser le besoin d'application d'un commanditaire" COLOR="#3F7D4A">
      <node TEXT="Specs fonctionnelles, MCD/MPD, parcours, user stories, accessibilité" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Modélisation des données respectant un formalisme (Merise, entités-relations...)" COLOR="#999999"/>
        <node TEXT="Modélisation des parcours respectant un formalisme (schéma fonctionnel, wireframes...)" COLOR="#999999"/>
        <node TEXT="Chaque spécification fonctionnelle couvre contexte, scénarios, critères de validation" COLOR="#999999"/>
        <node TEXT="Objectifs d'accessibilité intégrés aux critères d'acceptation (WCAG, RGAA...)" COLOR="#999999"/>
      </node>
    </node>

    <node TEXT="C15 — Concevoir le cadre technique d'une application" COLOR="#3F7D4A">
      <node TEXT="Architecture, flux de données, PoC, éco-responsabilité" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Spécifications couvrant architecture, dépendances, environnement d'exécution" COLOR="#999999"/>
        <node TEXT="Services/prestataires éco-responsables favorisés" COLOR="#999999"/>
        <node TEXT="Flux de données représentés par un diagramme" COLOR="#999999"/>
        <node TEXT="Preuve de concept accessible et fonctionnelle en pré-production" COLOR="#999999"/>
        <node TEXT="Conclusion de la preuve de concept permettant une prise de décision" COLOR="#999999"/>
      </node>
    </node>

    <node TEXT="C16 — Coordonner la réalisation technique" COLOR="#3F7D4A">
      <node TEXT="Conduite agile, rituels, outils de pilotage" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Cycles, étapes, rôles, rituels et outils de la méthode agile respectés" COLOR="#999999"/>
        <node TEXT="Outils de pilotage disponibles (kanban, burndown chart, backlog...)" COLOR="#999999"/>
        <node TEXT="Objectifs et modalités des rituels partagés à toutes les parties prenantes" COLOR="#999999"/>
        <node TEXT="Éléments de pilotage accessibles tout au long du projet" COLOR="#999999"/>
      </node>
    </node>

    <node TEXT="C17 — Développer les composants techniques et les interfaces" COLOR="#3F7D4A">
      <node TEXT="Accessibilité, sécurité, OWASP, éco-conception" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Environnement de développement conforme aux spécifications" COLOR="#999999"/>
        <node TEXT="Interfaces intégrées, conformes aux maquettes" COLOR="#999999"/>
        <node TEXT="Comportements des composants et navigation conformes aux spécifications" COLOR="#999999"/>
        <node TEXT="Composants métier développés et fonctionnels" COLOR="#999999"/>
        <node TEXT="Gestion des droits/accès conforme aux spécifications" COLOR="#999999"/>
        <node TEXT="Flux de données intégrés conformément aux spécifications" COLOR="#999999"/>
        <node TEXT="Bonnes pratiques d'éco-conception respectées (éco-index, Green IT)" COLOR="#999999"/>
        <node TEXT="Top 10 OWASP implémenté si nécessaire" COLOR="#999999"/>
        <node TEXT="Tests d'intégration/unitaires couvrant composants métier et accès" COLOR="#999999"/>
        <node TEXT="Sources versionnées, dépôt Git distant" COLOR="#999999"/>
        <node TEXT="Documentation technique complète et accessible" COLOR="#999999"/>
      </node>
    </node>

    <node TEXT="C18 — Automatiser les phases de tests du code source" COLOR="#3F7D4A">
      <node TEXT="Intégration continue (CI)" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Documentation couvre outils, étapes, tâches, déclencheurs" COLOR="#999999"/>
        <node TEXT="Outil d'intégration continue cohérent avec l'environnement technique" COLOR="#999999"/>
        <node TEXT="Chaîne intègre toutes les étapes préalables aux tests (build, configs)" COLOR="#999999"/>
        <node TEXT="Chaîne exécute les tests disponibles au déclenchement" COLOR="#999999"/>
        <node TEXT="Configuration versionnée avec les sources, dépôt Git distant" COLOR="#999999"/>
        <node TEXT="Documentation d'installation, configuration, test, accessible" COLOR="#999999"/>
      </node>
    </node>

    <node TEXT="C19 — Créer un processus de livraison continue d'une application" COLOR="#3F7D4A">
      <node TEXT="Packaging, build, livraison (CD)" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Documentation couvre toutes les étapes, tâches, déclencheurs" COLOR="#999999"/>
        <node TEXT="Fichiers de configuration reconnus et exécutés" COLOR="#999999"/>
        <node TEXT="Étapes de packaging (compilation, minification, build containers...) sans erreur" COLOR="#999999"/>
        <node TEXT="Étape de livraison (ex. pull request) intégrée après validation du packaging" COLOR="#999999"/>
        <node TEXT="Sources versionnées, dépôt Git distant" COLOR="#999999"/>
        <node TEXT="Documentation d'installation, configuration, test, accessible" COLOR="#999999"/>
      </node>
    </node>

  </node>

<node TEXT="E5 — Amélioration d'une application existante — 10 min — Documentation 2 à 5 p." POSITION="left" COLOR="#3F7D4A">
    <node TEXT="Dispositif de monitorage applicatif" COLOR="#666666"/>
    <node TEXT="Description de l'incident technique (déclenchement, périmètre impacté)" COLOR="#666666"/>
    <node TEXT="Diagnostic" COLOR="#666666"/>
    <node TEXT="Résolution (méthodologie, tests en succès)" COLOR="#666666"/>
    <node TEXT="Documentation de l'incident et de sa résolution" COLOR="#666666"/>

    <node TEXT="C20 — Surveiller une application d'IA" COLOR="#3F7D4A">
      <node TEXT="Monitorage, journalisation, feedback loop, RGPD" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Documentation liste métriques, seuils et valeurs d'alerte par métrique à risque" COLOR="#999999"/>
        <node TEXT="Documentation explicite les arguments des choix techniques" COLOR="#999999"/>
        <node TEXT="Outils (collecteurs, journalisation, agrégateurs, filtres, dashboard) opérationnels" COLOR="#999999"/>
        <node TEXT="Règles de journalisation intégrées selon les métriques à surveiller" COLOR="#999999"/>
        <node TEXT="Alertes configurées et en état de marche" COLOR="#999999"/>
        <node TEXT="Documentation d'installation/configuration, accessible" COLOR="#999999"/>
      </node>
    </node>

    <node TEXT="C21 — Résoudre les incidents techniques" COLOR="#3F7D4A">
      <node TEXT="Cause, reproduction, solution documentée, versionnée" COLOR="#666666"/>
      <node TEXT="Critères" COLOR="#999999">
        <node TEXT="Causes du problème identifiées correctement" COLOR="#999999"/>
        <node TEXT="Problème reproduit en environnement de développement" COLOR="#999999"/>
        <node TEXT="Procédure de débogage documentée depuis l'outil de suivi" COLOR="#999999"/>
        <node TEXT="Solution documentée, explicitant chaque étape de la résolution" COLOR="#999999"/>
        <node TEXT="Solution versionnée dans le dépôt Git (ex. merge request)" COLOR="#999999"/>
      </node>
    </node>

  </node>

</node>
</map>
