# Lecture d'une règle par numéro

**En tant que** professionnel du web  
**je veux** citer un numéro de règle et en obtenir le détail  
**afin de** vérifier rapidement un point que je connais déjà.

*Mesure* : taux de bon choix entre trois outils (mots-clés, sémantique, lecture
par numéro). Elle ne sera calculable qu'après A3 : jusque-là l'agent n'a que
deux outils.

## Décisions

- **Un outil à part**, `lire_regle(numero)`, à côté de `rechercher_regles` —
  pas une option de la recherche par mots-clés.
- **Règle complète, sans troncature** (les 13 champs exposés par
  `GET /regles/{numero}`). L'agent doit pouvoir décider à partir de la règle
  entière ; la troncature à 300 caractères de la recherche n'a pas de sens ici.
- **Règle inconnue = 404 remonté à l'agent** : l'outil lui renvoie, comme un
  résultat et non comme une exception, le **code 404** et le message de l'API
  (« Règle N inconnue »), soit `{"statut": 404, "erreur": "Règle 999 inconnue"}`.
  Le code HTTP est gardé même si l'agent n'est pas lui-même en HTTP : c'est un
  vocabulaire commun entre l'API, l'outil, les traces et le modèle, qui en
  connaît le sens (« la ressource n'existe pas »).
- **Une panne remonte comme un 5xx, pas comme une exception** : le statut
  d'erreur renvoyé par l'API est transmis tel quel à l'agent (`{"statut": 503,
  "erreur": "..."}`). Il sait ainsi distinguer « cette règle n'existe pas »
  (404) de « le service est en panne » (5xx), et ne présente jamais l'un
  comme l'autre. Même principe pour tout autre statut d'erreur.
- **Le service ne répond pas** (délai dépassé, connexion impossible) : aucune
  réponse HTTP n'existe, l'outil renvoie de lui-même `{"statut": 503, ...}`
  (service indisponible).
- **Même contrat pour `rechercher_regles`** (décision de David : « il faut
  vraiment que notre produit soit résilient ») : plus d'exception, le statut
  d'erreur de l'API est transmis à l'agent, 503 si aucune réponse. Cela
  modifie l'outil d'A1 (le `raise_for_status()` disparaît), au même titre que
  le marqueur `solution_tronquee`.
- **Deux usages** : l'utilisateur cite un numéro, **ou** l'agent lui-même veut
  lire en entier une règle qu'une recherche lui a montrée tronquée (la
  recherche coupe la solution à 300 caractères). Le second usage est la vraie
  raison d'être de l'outil : l'agent doit pouvoir approfondir avant de décider.
- **La recherche signale ce qu'elle a coupé** : chaque règle du résultat de
  `rechercher_regles` porte un indicateur `solution_tronquee` (vrai quand la
  solution dépasse 300 caractères). Sans lui, un extrait coupé en pleine phrase
  ressemble à une règle complète et l'agent n'a aucune raison de la lire en
  entier. C'est une petite modification de l'outil d'A1, imposée par A4.
  Le prompt système et la description des outils citent les deux outils.
- **Une panne d'outil n'est pas « rien ne correspond »** : quand l'agent
  a reçu un statut 5xx d'un outil et ne cite aucune règle, la réponse de
  `POST /questions` porte le nouveau statut `service_indisponible`, en HTTP
  200 (contrat `openapi.json`, version 0.3.0, ajout additif). Sans lui, la
  panne serait classée `aucune_regle_pertinente`, ce qui est faux. Règle
  retenue (à valider) : `service_indisponible` seulement si un outil a renvoyé
  un 5xx **et** qu'aucune règle n'est citée ; si une nouvelle tentative a
  réussi et que des règles sont citées, la réponse reste `repondu`. **Où vit
  cette règle** (décision de David) : dans la boucle, qui expose un indicateur
  de panne dans son résultat (`ResultatAgent.panne_outil`, vrai dès qu'un outil
  a renvoyé un 5xx) ; l'API se contente de le traduire en statut.
- **Une règle lue compte comme règle citée.** La boucle construit
  `regles_citees` à partir des résultats d'outils, et ne connaît aujourd'hui
  que le format de la recherche (`resultats`). Sans changement, une règle lue
  par `lire_regle` ne serait pas comptée et la réponse serait classée
  `aucune_regle_pertinente` alors qu'elle s'appuie sur la règle 116.
- **Le span d'un appel d'outil porte le nom de l'outil** :
  `questions_libres.appel_outil.rechercher_regles` /
  `questions_libres.appel_outil.lire_regle` (choix de David : sinon deux outils
  donnent des spans indiscernables dans Langfuse). Le nom vient de l'outil
  demandé par le LLM, pas d'une liste écrite en dur ; le préfixe
  `questions_libres.appel_outil` reste commun pour filtrer. L'attribut `outil`
  est conservé.
- **Une panne n'est plus invisible** (elle ne lève plus d'exception, donc le
  span la verrait comme un succès) : quand un outil renvoie un statut d'erreur,
  le span porte `outil.statut` ; il passe en erreur seulement pour un 5xx (une
  panne), pas pour un 404 (une règle inconnue est un résultat normal). L'outil
  journalise aussi un avertissement. À valider.
- **Un 200 dont le corps n'est pas du JSON** (proxy, page d'erreur) est une
  mauvaise réponse d'un service amont : l'outil renvoie 502, jamais une
  exception. À valider.
- Aucune modification de l'API des règles : la route existe et est en accès
  libre, sans jeton.

## Gherkin

```gherkin
Fonctionnalité : Lecture d'une règle par son numéro

  Scénario : L'utilisateur cite un numéro de règle
    Étant donné que la règle 116 existe dans le référentiel
    Quand l'utilisateur demande « Que dit la règle 116 ? »
    Alors l'agent appelle l'outil de lecture par numéro avec 116
    Et sa réponse s'appuie sur l'intitulé et la solution de la règle 116

  Scénario : L'agent approfondit une règle vue dans une recherche
    Étant donné que la recherche par mots-clés sur « accessibilité » a renvoyé
      une liste de règles dont la solution est tronquée
    Quand l'agent a besoin du détail exact de l'une d'elles pour décider de sa
      réponse
    Alors il appelle l'outil de lecture par numéro avec le numéro de cette règle
    Et il s'appuie sur la règle complète, pas sur l'extrait tronqué

  Scénario : La recherche signale les solutions qu'elle a coupées
    Étant donné une règle dont la solution dépasse 300 caractères
    Et une règle dont la solution tient en moins de 300 caractères
    Quand l'agent lance une recherche par mots-clés qui renvoie les deux
    Alors la première est marquée `solution_tronquee` à vrai
    Et la seconde n'est pas marquée comme tronquée

  Scénario : L'outil renvoie la règle complète
    Étant donné que la règle 116 existe dans le référentiel
    Quand l'outil de lecture est appelé avec le numéro 116
    Alors il renvoie tous les champs de la règle : intitulé, thème, contexte,
      solution, contrôle, stratégie d'analyse, outils, justification, source,
      guide d'analyse, objectifs et tags
    Et aucun champ n'est tronqué

  Scénario : Le numéro cité n'existe pas
    Étant donné qu'aucune règle 999 n'existe dans le référentiel
    Quand l'outil de lecture est appelé avec le numéro 999
    Alors il renvoie à l'agent le statut 404 et le message « Règle 999 inconnue »
    Et l'agent indique à l'utilisateur que cette règle n'existe pas
    Et il n'invente aucun contenu pour la règle 999

  Scénario : Une panne du service remonte comme un 5xx
    Étant donné que l'API des règles répond par une erreur serveur 503
    Quand l'outil de lecture est appelé avec le numéro 116
    Alors il renvoie à l'agent le statut 503 et le message d'erreur
    Et cette panne n'est pas présentée comme « Règle 116 inconnue »

  Scénario : Le service ne répond pas
    Étant donné que l'API des règles ne répond pas dans le délai imparti
    Quand l'outil de lecture est appelé avec le numéro 116
    Alors il renvoie à l'agent le statut 503
    Et l'agent n'affirme pas que la règle 116 n'existe pas

  Scénario : La recherche remonte une panne comme un 5xx
    Étant donné que l'API des règles répond par une erreur serveur 503
    Quand l'agent lance une recherche par mots-clés
    Alors l'outil de recherche renvoie à l'agent le statut 503 et le message
      d'erreur
    Et l'agent n'affirme pas qu'aucune règle ne correspond

  Scénario : La recherche ne reçoit aucune réponse
    Étant donné que l'API des règles ne répond pas dans le délai imparti
    Quand l'agent lance une recherche par mots-clés
    Alors l'outil de recherche renvoie à l'agent le statut 503
    Et l'agent n'affirme pas qu'aucune règle ne correspond

  Scénario : Une panne d'outil n'est pas présentée comme « rien ne correspond »
    Étant donné que l'API des règles répond par une erreur serveur 503
    Et qu'aucune règle n'a pu être citée
    Quand l'utilisateur pose une question dans le sujet
    Alors la réponse HTTP est un 200
    Et son statut est `service_indisponible`, pas `aucune_regle_pertinente`

  Scénario : Une question sans numéro commence par une recherche par mots-clés
    Étant donné une question qui ne cite aucun numéro de règle
    Quand l'utilisateur demande « Comment traiter les images décoratives ? »
    Alors l'agent commence par la recherche par mots-clés
    Et il n'appelle l'outil de lecture que pour une règle que cette recherche
      lui a fait découvrir

  Scénario : La lecture d'une règle est tracée comme tout appel d'outil
    Étant donné une question qui cite le numéro de règle 116
    Quand l'agent appelle l'outil de lecture par numéro
    Alors une trace est émise pour cet appel, nommée `questions_libres.appel_outil.lire_regle`
    Et elle contient la durée et le résultat (succès ou erreur)

  Scénario : Une règle lue par son numéro compte comme règle citée
    Étant donné que l'agent a lu la règle 116 avec l'outil de lecture par numéro
    Quand il répond à l'utilisateur
    Alors la règle 116 figure dans les règles citées de la réponse
    Et le statut de la réponse est `repondu`, pas `aucune_regle_pertinente`
```

Les scénarios 3 à 10 et 13 sont déterministes (tests unitaires des outils et
de la boucle, API simulée). Les scénarios 1, 2 et 11 dépendent du choix du modèle :
ils se vérifient par un test d'intégration réel et alimentent la mesure de la
carte. Le scénario 12 protège la trace d'A2 quand la boucle passe à deux
outils.

## Schémas

[A4_lecture_regle_par_numero.drawio](A4_lecture_regle_par_numero.drawio) (rendu : `A4_lecture_regle_par_numero.png`) — choix de l'outil par
l'agent (mots-clés ou lecture par numéro), les deux chemins vers la lecture
(numéro cité par l'utilisateur, ou règle vue tronquée dans une recherche),
appel `GET /regles/{numero}` et les issues : règle trouvée, 404
(règle inconnue) ou 5xx (panne), toutes remontées à l'agent.
