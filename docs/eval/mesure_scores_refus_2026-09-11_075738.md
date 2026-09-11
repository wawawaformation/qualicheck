# Mesure des scores — refus du retrieval (2026-09-11 07:57)

`sans_reponse` : 20 cas — cas `PASS` (autres familles) : 91 cas

## Distributions par métrique

| Métrique | Groupe | min | max | moyenne |
|---|---|---|---|---|
| top1 | sans_reponse | 0.190 | 0.534 | 0.371 |
| top1 | PASS | 0.406 | 0.740 | 0.600 |
| top15 | sans_reponse | 0.149 | 0.486 | 0.320 |
| top15 | PASS | 0.325 | 0.570 | 0.455 |
| ecart | sans_reponse | 0.027 | 0.079 | 0.050 |
| ecart | PASS | 0.044 | 0.288 | 0.145 |

## Détail par cas

| Famille | Verdict | top1 | top15 | écart | Question |
|---|---|---|---|---|---|
| paraphrase_intitule | PASS | 0.535 | 0.423 | 0.112 | Peut-on souligner les titres ? |
| paraphrase_intitule | PASS | 0.482 | 0.394 | 0.088 | Il faut mettre en rouge les infos de danger |
| paraphrase_intitule | PASS | 0.630 | 0.518 | 0.112 | Le site doit-il être accessible uniquement en connexion sécurisée ? |
| paraphrase_intitule | PASS | 0.561 | 0.435 | 0.126 | Faut-il décrire les images importantes pour les personnes qui ne peuvent pas les voir ? |
| paraphrase_intitule | PASS | 0.657 | 0.431 | 0.226 | Où doit-on pouvoir trouver la politique de vie privée du site ? |
| paraphrase_intitule | PASS | 0.679 | 0.478 | 0.201 | Un site marchand doit-il proposer plusieurs façons de payer ? |
| paraphrase_intitule | PASS | 0.626 | 0.495 | 0.131 | Si un formulaire est refusé, faut-il montrer précisément quels champs posent problème ? |
| paraphrase_intitule | PASS | 0.665 | 0.524 | 0.141 | Le site doit-il éviter les liens cassés en interne ? |
| paraphrase_intitule | PASS | 0.653 | 0.399 | 0.254 | Les vidéos doivent-elles avoir des sous-titres ? |
| paraphrase_intitule | PASS | 0.666 | 0.490 | 0.176 | Le site peut-il ouvrir des fenêtres popup pendant la navigation ? |
| paraphrase_intitule | PASS | 0.679 | 0.478 | 0.201 | Le site doit-il avoir un moteur de recherche interne ? |
| paraphrase_intitule | PASS | 0.611 | 0.414 | 0.197 | Sur mobile, les boutons doivent-ils être assez grands pour être touchés facilement ? |
| paraphrase_intitule | PASS | 0.642 | 0.466 | 0.176 | Peut-on empêcher l'utilisateur de zoomer sur la page ? |
| paraphrase_intitule | PASS | 0.684 | 0.545 | 0.139 | Faut-il fournir un plan du site pour les moteurs de recherche ? |
| paraphrase_intitule | PASS | 0.605 | 0.392 | 0.213 | Le formulaire d'inscription doit-il accepter les adresses email avec un signe plus (+) dedans ? |
| paraphrase_intitule | PASS | 0.740 | 0.470 | 0.271 | Les messages d'erreur doivent-ils être dans la même langue que le formulaire ? |
| paraphrase_intitule | PASS | 0.622 | 0.441 | 0.181 | Le numéro SIRET (ou équivalent d'immatriculation légale) doit-il être affiché sur le site ? |
| vocabulaire_source_opquast | FAIL | 0.410 | 0.331 | 0.079 | Peut-on imposer un ordre de parcours des champs différent de celui du code, avec des numéros ? |
| vocabulaire_source_opquast | PASS | 0.552 | 0.483 | 0.069 | Faut-il prévoir des règles de style qui changent selon la largeur de l'écran ? |
| vocabulaire_source_opquast | PASS | 0.577 | 0.491 | 0.085 | La petite image affichée dans l'onglet du navigateur doit-elle être déclarée dans le code ? |
| vocabulaire_source_opquast | PASS | 0.512 | 0.425 | 0.087 | Les options payantes supplémentaires peuvent-elles être pré-cochées dans le panier ? |
| vocabulaire_source_opquast | PASS | 0.551 | 0.480 | 0.071 | Peut-on déclarer au navigateur depuis quels domaines il a le droit de charger scripts et images ? |
| vocabulaire_source_opquast | PASS | 0.640 | 0.478 | 0.163 | Si mon navigateur est réglé en allemand puis en anglais, le site doit-il respecter cet ordre ? |
| vocabulaire_source_opquast | PASS | 0.552 | 0.484 | 0.068 | Le serveur doit-il permettre au navigateur de savoir si une page a changé depuis sa dernière visite ? |
| vocabulaire_source_opquast | PASS | 0.607 | 0.410 | 0.197 | Dans un document téléchargeable issu d'un scan, doit-on pouvoir sélectionner le texte ? |
| vocabulaire_source_opquast | PASS | 0.613 | 0.397 | 0.216 | Faut-il prouver que les mails envoyés depuis mon domaine viennent réellement de moi ? |
| vocabulaire_source_opquast | PASS | 0.499 | 0.432 | 0.067 | Si la police choisie n'est pas disponible, le navigateur doit-il avoir une solution de repli ? |
| vocabulaire_genere_llm | PASS | 0.560 | 0.516 | 0.044 | Comment éviter que la même page soit vue comme deux pages distinctes selon l'adresse tapée ? |
| vocabulaire_genere_llm | PASS | 0.581 | 0.436 | 0.144 | Quand on saisit des données confidentielles, la redirection vers une connexion chiffrée doit-elle être définitive ? |
| vocabulaire_genere_llm | PASS | 0.571 | 0.488 | 0.084 | Faut-il un code temporaire envoyé à l'utilisateur pour sécuriser l'accès à son compte ? |
| vocabulaire_genere_llm | PASS | 0.617 | 0.384 | 0.233 | Dans mon espace personnel, puis-je récupérer mes données dans un fichier exploitable ? |
| vocabulaire_genere_llm | PASS | 0.580 | 0.413 | 0.167 | Pour un paiement en plusieurs fois, le coût réel du crédit doit-il être affiché ? |
| vocabulaire_genere_llm | PASS | 0.565 | 0.460 | 0.105 | Si l'utilisateur clique sur retour pendant une commande, doit-il être prévenu qu'il perdra sa saisie ? |
| vocabulaire_genere_llm | FAIL | 0.573 | 0.464 | 0.109 | Un menu qui se déplie doit-il annoncer son état aux outils d'assistance ? |
| vocabulaire_genere_llm | PASS | 0.620 | 0.455 | 0.165 | Une icône affichée via une police spéciale doit-elle avoir un équivalent lisible par les outils d'assistance ? |
| vocabulaire_genere_llm | PASS | 0.644 | 0.468 | 0.176 | L'indicateur de robustesse du mot de passe doit-il être annoncé au fil de la saisie ? |
| vocabulaire_genere_llm | PASS | 0.511 | 0.423 | 0.088 | La date d'un article doit-elle être lisible par une machine, pas seulement par un humain ? |
| vocabulaire_genere_llm | PASS | 0.633 | 0.478 | 0.155 | Le serveur doit-il réduire la taille des fichiers envoyés quand le navigateur sait les décompresser ? |
| vocabulaire_genere_llm | PASS | 0.677 | 0.491 | 0.186 | Peut-on empêcher l'utilisateur de sélectionner et copier le texte d'une page ? |
| vocabulaire_genere_llm | PASS | 0.656 | 0.543 | 0.113 | Si le site affirme respecter un référentiel d'accessibilité, doit-il indiquer lequel précisément ? |
| multi_sujets | PASS | 0.600 | 0.511 | 0.089 | Je lance une boutique : quelles informations légales afficher, et comment rendre mes vidéos compréhensibles pour tous ? |
| multi_sujets | PASS | 0.679 | 0.473 | 0.206 | Mon site a un moteur de recherche : les résultats sont-ils partageables par lien et indiquent-ils leur nombre ? |
| multi_sujets | PASS | 0.550 | 0.446 | 0.103 | Sur mobile, faut-il des boutons assez grands et laisser l'utilisateur agrandir la page ? |
| multi_sujets | PASS | 0.584 | 0.448 | 0.136 | Comment un client peut-il nous joindre, et où lit-il les conditions de vente ? |
| sans_reponse | FAIL | 0.534 | 0.486 | 0.048 | Comment recruter un panel d'utilisateurs en situation de handicap pour tester mon site ? |
| sans_reponse | FAIL | 0.474 | 0.421 | 0.054 | Combien de temps faut-il prévoir pour réaliser un audit qualité web complet ? |
| sans_reponse | FAIL | 0.373 | 0.344 | 0.029 | Quelle méthode d'estimation agile utiliser pour planifier les corrections d'un audit ? |
| sans_reponse | FAIL | 0.307 | 0.256 | 0.051 | Quel est le tarif d'une certification Opquast pour une équipe ? |
| sans_reponse | FAIL | 0.477 | 0.418 | 0.059 | Quel framework JavaScript choisir pour construire mon site ? |
| sans_reponse | FAIL | 0.237 | 0.181 | 0.056 | Quelle est la meilleure recette de tarte aux pommes ? |
| sans_reponse | FAIL | 0.301 | 0.248 | 0.052 | Comment planifier un voyage en Europe pas cher ? |
| sans_reponse | FAIL | 0.209 | 0.149 | 0.060 | Quel est le palmarès de la dernière Coupe du monde de football ? |
| sans_reponse | FAIL | 0.316 | 0.248 | 0.068 | Comment entretenir un jardin potager en hiver ? |
| sans_reponse | FAIL | 0.190 | 0.152 | 0.038 | Quelle est la différence entre un chat et un chien comme animal de compagnie ? |
| sans_reponse | FAIL | 0.454 | 0.402 | 0.051 | Quel est le meilleur CMS pour un petit site vitrine ? |
| sans_reponse | FAIL | 0.459 | 0.393 | 0.066 | Comment structurer une équipe de développement web en méthode Scrum ? |
| sans_reponse | FAIL | 0.525 | 0.459 | 0.066 | Quels indicateurs suivre pour mesurer le trafic d'un site e-commerce ? |
| sans_reponse | FAIL | 0.411 | 0.332 | 0.079 | Combien coûte un audit RGPD complet pour une PME ? |
| sans_reponse | FAIL | 0.522 | 0.463 | 0.059 | Comment rédiger un cahier des charges pour un projet web ? |
| sans_reponse | FAIL | 0.312 | 0.285 | 0.027 | Qu'est-ce que le modèle VPTCS et quelles sont ses cinq composantes ? |
| sans_reponse | FAIL | 0.274 | 0.245 | 0.029 | Qui a créé le modèle VPTCS et en quelle année ? |
| sans_reponse | FAIL | 0.387 | 0.355 | 0.032 | Quelle est la différence entre UX et UI selon le modèle VPTCS ? |
| sans_reponse | FAIL | 0.359 | 0.305 | 0.054 | Combien coûte la formation Référent Qualité Numérique chez Opquast ? |
| sans_reponse | FAIL | 0.295 | 0.264 | 0.031 | Quelles sont les conditions pour devenir formateur Opquast ? |
| regles_concurrentes | PASS | 0.723 | 0.535 | 0.188 | Que doit-on vérifier au sujet du HTTPS sur un site ? |
| regles_concurrentes | PASS | 0.665 | 0.416 | 0.249 | Comment aider l'utilisateur qui crée un mot de passe ? |
| regles_concurrentes | PASS | 0.710 | 0.526 | 0.184 | Quels moyens de contact un site doit-il proposer ? |
| regles_concurrentes | PASS | 0.599 | 0.490 | 0.109 | Que faut-il prévoir pour les vidéos d'un site ? |
| regles_concurrentes | PASS | 0.650 | 0.570 | 0.079 | Comment doit-on rédiger les liens d'un site ? |
| regles_concurrentes | PASS | 0.700 | 0.492 | 0.208 | Les liens doivent-ils se distinguer visuellement ? |
| regles_concurrentes | PASS | 0.702 | 0.503 | 0.199 | Que doit permettre une page de résultats de recherche ? |
| vocabulaire_objectif | PASS | 0.551 | 0.450 | 0.101 | Un utilisateur qui n'a qu'un bouton poussoir comme périphérique d'entrée peut-il interagir avec tous les services du site ? |
| vocabulaire_objectif | PASS | 0.561 | 0.439 | 0.123 | Que se passe-t-il si le navigateur ne reçoit pas l'information du jeu de caractères et doit le deviner lui-même ? |
| vocabulaire_objectif | PASS | 0.406 | 0.343 | 0.063 | Sur un réseau mobile de qualité variable, qu'est-ce qui risque d'interrompre la lecture et de faire consommer des données non désirées ? |
| vocabulaire_objectif | PASS | 0.547 | 0.392 | 0.155 | À quels endroits (FAI, proxy, historique du navigateur) des données sensibles risquent-elles de se retrouver stockées en clair ? |
| vocabulaire_objectif | PASS | 0.533 | 0.459 | 0.074 | Comment éviter de dépendre d'un acteur tiers dont la stratégie commerciale ou technique peut évoluer, pour accéder à un service ? |
| vocabulaire_objectif | PASS | 0.500 | 0.428 | 0.072 | Comment éviter qu'un utilisateur croie à tort que son action a réussi alors qu'il y a eu un problème ? |
| vocabulaire_objectif | PASS | 0.541 | 0.446 | 0.096 | Faut-il avertir l'internaute qu'il est sur le point de quitter le service en ligne qu'il consulte ? |
| vocabulaire_objectif | FAIL | 0.525 | 0.487 | 0.039 | Qu'est-ce qui provoque une interprétation hasardeuse du DOM d'une page selon les agents utilisateurs ? |
| vocabulaire_objectif | PASS | 0.576 | 0.523 | 0.053 | Comment éviter à un utilisateur en mode vocal de devoir défiler toute la page avant d'atteindre le contenu ? |
| vocabulaire_objectif | PASS | 0.633 | 0.502 | 0.131 | Comment éviter qu'un client s'aperçoive tardivement, en pleine commande, que ce qu'il voulait n'est pas disponible ? |
| vocabulaire_objectif | PASS | 0.541 | 0.440 | 0.101 | Comment éviter à un client des démarches inutiles et une perte de temps s'il n'est pas dans une zone desservie ? |
| vocabulaire_objectif | PASS | 0.638 | 0.466 | 0.172 | En quoi l'ouverture d'une nouvelle fenêtre désoriente-t-elle un utilisateur d'aide technique et perturbe-t-elle son historique de navigation ? |
| vocabulaire_objectif | PASS | 0.684 | 0.552 | 0.132 | En navigateur texte ou avec les images désactivées, comment l'utilisateur comprend-il le sens des images et des images-liens ? |
| vocabulaire_objectif | PASS | 0.608 | 0.494 | 0.114 | Comment permettre à l'utilisateur de décider en connaissance de cause avant de lancer ou de télécharger un média ? |
| vocabulaire_objectif | PASS | 0.542 | 0.476 | 0.066 | Que prévoir pour un utilisateur désorienté qui veut repartir de zéro sur le site ? |
| vocabulaire_source_opquast | PASS | 0.588 | 0.387 | 0.201 | Un flux RSS suffit-il à faire connaître les nouveautés d'un site ? |
| vocabulaire_source_opquast | PASS | 0.679 | 0.390 | 0.288 | Peut-on afficher une vignette en réduisant l'image d'origine via les attributs width et height ? |
| vocabulaire_source_opquast | PASS | 0.504 | 0.353 | 0.151 | Quel registre officiel fait référence pour les codes de langue à déclarer ? |
| vocabulaire_source_opquast | PASS | 0.701 | 0.447 | 0.254 | Un numéro de téléphone doit-il être cliquable via un lien href="tel:..." ? |
| vocabulaire_source_opquast | PASS | 0.692 | 0.511 | 0.181 | Faut-il envoyer un en-tête X-Frame-Options pour empêcher qu'un autre site affiche mes pages dans un cadre ? |
| vocabulaire_source_opquast | PASS | 0.578 | 0.404 | 0.174 | Peut-on ouvrir une fenêtre avec window.open en masquant la barre d'outils (toolbar="no") ? |
| vocabulaire_source_opquast | PASS | 0.589 | 0.405 | 0.184 | Comment déclarer qu'un répertoire ne doit pas être indexé (directive disallow) ? |
| vocabulaire_source_opquast | PASS | 0.406 | 0.344 | 0.062 | Un titre de niveau h2 peut-il être suivi directement d'un h4 ? |
| vocabulaire_source_opquast | PASS | 0.575 | 0.383 | 0.192 | Comment relier une cellule à son en-tête quand scope ne suffit pas ? |
| vocabulaire_source_opquast | PASS | 0.574 | 0.484 | 0.091 | Faut-il éviter d'imposer un ordre de tabulation avec l'attribut tabindex ? |
| vocabulaire_genere_llm | PASS | 0.497 | 0.453 | 0.044 | Faut-il prévenir l'utilisateur qu'il aura besoin de son RIB avant de commencer une démarche ? |
| vocabulaire_genere_llm | PASS | 0.594 | 0.325 | 0.270 | Faut-il regrouper les options d'un select avec optgroup ? |
| vocabulaire_genere_llm | PASS | 0.657 | 0.495 | 0.162 | Les éléments object et embed doivent-ils avoir une alternative textuelle ? |
| vocabulaire_genere_llm | PASS | 0.511 | 0.326 | 0.184 | Un fichier proposé au téléchargement peut-il s'appeler document.pdf ? |
| vocabulaire_genere_llm | PASS | 0.662 | 0.410 | 0.253 | Les majuscules décoratives doivent-elles être faites avec text-transform plutôt que saisies en dur ? |
| vocabulaire_genere_llm | PASS | 0.576 | 0.499 | 0.077 | À l'impression, faut-il retirer les éléments nav et footer de la page ? |
| vocabulaire_genere_llm | PASS | 0.645 | 0.423 | 0.222 | L'en-tête Content-Type doit-il préciser charset=utf-8 ? |
| vocabulaire_genere_llm | PASS | 0.577 | 0.386 | 0.191 | Un tableau de données peut-il être construit avec des div et des span ? |
| vocabulaire_genere_llm | PASS | 0.547 | 0.451 | 0.096 | Un menu déroulant doit-il exposer son état ouvert/fermé via aria-expanded ? |
| vocabulaire_objectif | PASS | 0.622 | 0.530 | 0.092 | Que doit permettre le titre d'une page dans les onglets et les favoris du navigateur ? |
| vocabulaire_objectif | PASS | 0.614 | 0.519 | 0.095 | Sur une page d'erreur, comment éviter que l'utilisateur se retrouve dans un cul-de-sac et doive utiliser le bouton Précédent ? |
| vocabulaire_objectif | PASS | 0.573 | 0.512 | 0.061 | Comment rassurer l'utilisateur que le problème ne vient pas de sa connexion quand un accès lui est refusé ? |
| vocabulaire_objectif | PASS | 0.599 | 0.416 | 0.183 | Pourquoi ne faut-il pas pouvoir renvoyer à l'utilisateur son mot de passe existant ? |
| vocabulaire_objectif | PASS | 0.596 | 0.518 | 0.078 | Que proposer à un utilisateur désorienté qui veut visualiser l'ensemble des contenus et la taille du site ? |
| vocabulaire_objectif | PASS | 0.618 | 0.492 | 0.126 | L'utilisateur doit-il pouvoir accéder au contenu tout de suite même si le site diffuse une publicité préalable ? |
| vocabulaire_objectif | PASS | 0.610 | 0.528 | 0.082 | Comment donner à l'utilisateur de la visibilité sur les étapes qu'il va accomplir et les informations nécessaires ? |
| vocabulaire_objectif | PASS | 0.654 | 0.406 | 0.247 | Où l'utilisateur apprend-il pour quelles raisons ses publications peuvent être modérées ? |
| vocabulaire_objectif | PASS | 0.487 | 0.347 | 0.140 | Que se passe-t-il si un client demande un remboursement après le délai légal ? |
