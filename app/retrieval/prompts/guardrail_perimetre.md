Tu reçois une question qu'un utilisateur pose à un assistant spécialisé
dans le référentiel de qualité web Opquast (245 règles couvrant
accessibilité, ergonomie, référencement, sécurité, mentions légales,
performance, etc.).

Ta tâche : décider si cette question porte sur le **contenu d'une règle
de qualité web** — c'est-à-dire une vérification technique ou éditoriale
qu'on peut faire sur un site web.

Répond « non » (hors périmètre) si la question porte sur :

- un sujet totalement étranger au web (cuisine, voyage, animaux, sport...) ;
- l'organisme Opquast lui-même : tarifs, formations, certification,
  modèle VPTCS, conditions pour devenir formateur ;
- la gestion de projet ou la méthode de travail (Scrum, estimation
  agile, cahier des charges, recrutement de testeurs) plutôt qu'une
  règle de qualité précise.

Répond « oui » (dans le périmètre) si la question porte sur une
vérification technique ou éditoriale à faire sur un site web —
même formulée en langage courant, même si elle ne cite pas explicitement
une règle par son nom.

## Question posée

{question}

Réponds uniquement avec un objet JSON de la forme
{"dans_perimetre": true} ou {"dans_perimetre": false}, sans aucun texte
avant ou après.
