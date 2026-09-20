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

  Scénario : Une question sans numéro commence par une recherche par mots-clés
    Étant donné une question qui ne cite aucun numéro de règle
    Quand l'utilisateur demande « Comment traiter les images décoratives ? »
    Alors l'agent commence par la recherche par mots-clés
    Et il n'appelle l'outil de lecture que pour une règle que cette recherche
      lui a fait découvrir

  Scénario : La lecture d'une règle est tracée comme tout appel d'outil
    Étant donné une question qui cite le numéro de règle 116
    Quand l'agent appelle l'outil de lecture par numéro
    Alors une trace est émise pour cet appel, avec le nom de l'outil `lire_regle`
    Et elle contient la durée et le résultat (succès ou erreur)
```

Les scénarios 3 à 7 sont déterministes (tests unitaires des outils, API
simulée). Les scénarios 1, 2 et 8 dépendent du choix du modèle : ils se
vérifient par un test d'intégration réel et alimentent la mesure de la carte.
Le scénario 9 protège la trace d'A2 quand la boucle passe à deux outils.

## Schémas

[A4_lecture_regle_par_numero.drawio](A4_lecture_regle_par_numero.drawio) (rendu : `A4_lecture_regle_par_numero.png`) — choix de l'outil par
l'agent (mots-clés ou lecture par numéro), les deux chemins vers la lecture
(numéro cité par l'utilisateur, ou règle vue tronquée dans une recherche),
appel `GET /regles/{numero}` et les issues : règle trouvée, 404
(règle inconnue) ou 5xx (panne), toutes remontées à l'agent.
