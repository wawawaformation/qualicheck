# Construction par incréments — agent US2

Écrit le 2026-09-19. Ordre de construction de l'agent, marche par marche.
Rien n'est encore implémenté.

## Pourquoi découper à ce point

Trois raisons, et les deux dernières ne sont pas évidentes.

**Comprendre le système de bout en bout.** L'agent complet (9 outils,
5 points de garde-fous, mémoire de discussion) est trop gros pour être
tenu en tête d'un coup. Chaque marche ajoute une seule chose, assez
petite pour être comprise entièrement avant de passer à la suivante.

**Produire les mesures qui règlent les garde-fous.** La fiche sur la
limite d'itérations dit explicitement que le seuil est à mesurer une fois
l'agent construit, pas à deviner. Construire d'abord l'agent nu donne la
distribution réelle du nombre d'itérations, et le seuil se pose ensuite
sur une donnée.

**Servir le monitorage exigé par la certification** (C11 et C20). C20
demande une liste de métriques avec leurs seuils et leurs valeurs
d'alerte. Chaque marche définit les siennes au moment où elle devient
mesurable, plutôt que de tout inventer d'avance.

D'où la règle d'ordonnancement retenue : **on n'avance pas du plus
important au moins important, mais dans l'ordre où la mesure devient
possible.**

## Les deux règles de découpage

**Une marche = une seule chose.** Beaucoup de petites marches valent mieux
que peu de grosses : une marche qui embarque plusieurs ajouts et plusieurs
paramètres à régler en même temps redevient impossible à comprendre et à
mesurer, ce qui annule le bénéfice du découpage.

**Une marche n'est finie que si elle est exécutable et observable seule** :
une commande pour la lancer, quelque chose à regarder en sortie.

### L'exception : ce qu'on ne découpe pas

Un garde-fou de sécurité **voyage avec la capacité qu'il protège**.
Livrer l'outil de lecture d'URL sans son contrôle d'autorisation ni
l'isolation réseau ne serait pas une petite marche, mais une faille
déployée. Deux couples restent donc soudés :

- lire une URL **avec** l'autorisation sur le site et l'isolation réseau ;
- vérifier une page au navigateur **avec** l'accord de l'utilisateur.

## L'échelle

Chaque marche porte son **« afin de »**. L'acteur est le même presque
partout — *un professionnel du web qui prépare ou mène un audit* — il
n'est donc rappelé que lorsqu'il change.

Écrire ces « afin de » a un effet diagnostique : **une marche pour
laquelle on n'y arrive pas ne sert personne directement.** C'est le cas de
l'instrumentation, dont le bénéficiaire est l'exploitant. Ce n'est pas un
défaut, mais autant le savoir.

Les scénarios Gherkin complets s'écrivent **au moment d'attaquer chaque
marche**, pas d'avance : écrire vingt jeux de scénarios pour des
comportements qui bougeront encore, c'est spéculer.

### Phase A — l'agent nu

| Marche | Ce qu'on ajoute | Afin de | Ce que ça mesure |
|---|---|---|---|
| A1 | Question → réponse rédigée, **un seul outil : la recherche par mots-clés** | obtenir une réponse appuyée sur des règles, pas sur une opinion | Latence, coût par question, nombre d'itérations, taux d'erreur |
| A2 | **L'instrumentation** : chaque étape devient une trace observable | *(exploitant)* diagnostiquer où passent le temps et l'argent | Rien de neuf — mais tout ce qui suit devient visible en arrivant |
| A3 | La recherche sémantique | être compris sans employer les mots exacts du référentiel | L'agent **choisit** son outil ; coût réel (cet outil appelle lui-même trois modèles) |
| A4 | La lecture d'une règle par numéro | obtenir le détail d'une règle dont je cite le numéro | Taux de bon choix entre trois outils |

### Phase B — ce qui sort de l'agent

| Marche | Ce qu'on ajoute | Afin de | Ce que ça mesure |
|---|---|---|---|
| B1 | Contrôle des citations | pouvoir me fier aux règles citées, qui existent réellement | **Taux de citations inventées — seuil d'alerte à zéro**, toute occurrence est un incident |
| B2 | Contrôle final après la boucle | *(exploitant)* rattraper en dernier recours ce qui aurait échappé | Écarts rattrapés |

### Phase C — ce qui entre, et à quel prix

| Marche | Ce qu'on ajoute | Afin de | Ce que ça mesure |
|---|---|---|---|
| C1 | Limite d'itérations | recevoir une réponse honnête plutôt qu'une attente sans fin | **Le seuil se fixe ici**, avec la distribution observée en phases A et B |
| C2 | Anonymisation + règles de journalisation | *(personne concernée)* que mes données ne partent ni chez un tiers ni dans les journaux | Taux de détection ; rien de personnel nulle part |
| C3 | Détection d'identifiants techniques (clé, jeton) | ne pas divulguer une clé visible à l'écran sans m'en apercevoir | Occurrences détectées |
| C4 | Authentification de l'utilisateur | que mon accès soit contrôlé et mes appels attribuables | Tentatives rejetées, appels par client |
| C5 | Contrôle du sujet | recevoir un refus clair plutôt qu'une réponse inventée hors sujet | Taux de refus correct, **taux de faux refus** |
| C6 | Contrôle de l'intention | *(exploitant)* ne pas aider à contourner une règle ou à nuire | Refus de ce qui est dans le sujet mais malveillant |

### Phase D — regarder une vraie page

| Marche | Ce qu'on ajoute | Afin de | Ce que ça mesure |
|---|---|---|---|
| D1 | Lecture d'une URL **+ autorisation sur le site + isolation réseau** (indissociables) | faire analyser une page que j'ai le droit d'auditer | Taux d'échec, tentatives sur des adresses internes |
| D2 | Capture d'écran | faire analyser une page que je ne peux pas exposer par une adresse | Taux d'illisibilité |
| D3 | Validation du marquage | savoir si mon code respecte les spécifications | — |
| D4 | Calcul du ratio de contraste | obtenir un chiffre fiable plutôt qu'une appréciation | — |
| D5 | Vérification au navigateur **+ accord de l'utilisateur** (indissociables) | faire vérifier ce qui ne se voit ni dans le code ni sur une image | Durée, taux d'échec |

### Phase E — la conversation

| Marche | Ce qu'on ajoute | Afin de | Ce que ça mesure |
|---|---|---|---|
| E1 | La discussion **sans mémoire** : on enregistre et on relit les échanges, l'agent ne s'en sert pas encore | retrouver mes échanges précédents | Longueur des discussions |
| E2 | La mémoire : l'agent lit l'historique | ne pas répéter le contexte à chaque question | Effet sur les faux refus du contrôle de sujet |
| E3 | Nettoyage du contenu ramené avant son entrée en mémoire | *(exploitant)* qu'une page piégée ne contamine pas les tours suivants | Contenus écartés |
| E4 | « Demander à l'utilisateur » : suspension et reprise du tour | être sollicité quand moi seul peux constater quelque chose | Taux de reprise, abandons |

### Pourquoi la recherche par mots-clés en premier

Deux raisons de ne pas commencer par la recherche sémantique, pourtant
plus emblématique :

- **Elle appelle trois modèles en interne** (contrôle de périmètre,
  découpage de la question, jugement de pertinence). Un agent qui appelle
  un outil qui appelle trois modèles, c'est beaucoup de pièces mobiles
  pour une marche censée être comprise. La recherche par mots-clés est
  une simple requête : déterministe, gratuite, on voit exactement pourquoi
  elle renvoie ce qu'elle renvoie.
- **Elle exige un jeton**, la recherche par mots-clés non (voir ci-dessous).

## Deux authentifications à ne pas confondre

- **L'utilisateur vers notre agent** : c'est la marche C4.
- **Notre agent vers l'API des règles** : nécessaire dès la marche A3, qui
  introduit la recherche sémantique. Cette route exige un jeton parce que
  chaque appel coûte réellement de l'argent ; la recherche par mots-clés
  et la lecture par numéro sont en accès libre.

Concrètement, l'agent devient un **client nommé de plus** de l'API des
règles, à côté des quatre existants — une entrée dans sa configuration et
une variable d'environnement pour son jeton. Bénéfice au passage : l'API
journalise déjà quel client a fait quelle recherche, donc **le coût de
l'agent devient attribuable**.

## Contrat API du premier jet

Tant que la discussion n'existe pas (avant la phase E), une question est
autonome :

```
POST /questions

{ "question": "texte de la question" }
```

Réponse :

```json
{
  "statut": "repondu",
  "reponse": "texte de la réponse argumentée",
  "regles_citees": [ { "numero": 182, "intitule": "..." } ]
}
```

`statut` vaut `repondu`, `aucune_regle_pertinente` (question dans le
sujet, rien ne correspond) ou `hors_perimetre`. Les trois répondent en
HTTP 200 : un refus est une réponse normale à une requête bien formée,
pas une erreur du client — même parti pris que l'API des règles, qui
renvoie une liste vide plutôt qu'une erreur.

**L'adresse changera à la marche E1** : une question deviendra une
sous-ressource d'une discussion. C'est accepté en connaissance de cause,
le projet versionne déjà son contrat d'API.

## Observabilité — construite avec, pas après

C11 et C20 demandent des métriques, des seuils, de la journalisation et un
outil de restitution. La colonne « métriques » ci-dessus en est la
matière première : chaque marche déclare ce qu'elle rend mesurable.

Trois principes pour ne pas surdimensionner :

- **L'instrumentation est une marche à part entière (A2), et elle arrive
  tôt** — pour que tout ce qui est ajouté ensuite soit observable en
  arrivant, au lieu d'être instrumenté après coup.
- **Instrumenter dans un format ouvert, pas avec le kit d'un produit
  précis.** Le code décrit *ce qu'on observe* ; la destination des traces
  devient un réglage. On peut alors changer d'outil de restitution sans
  réécrire l'instrumentation.
- **« Opérationnel au moins en local » suffit** : c'est le critère exact
  de C20. Pas de plateforme de production à monter.

**Choix de l'outil de restitution — non tranché.** Langfuse est le
candidat noté dans `TODO.md`, mais son auto-hébergement est devenu lourd :
cinq services (dont ClickHouse, Redis et un stockage objet) et 16 Go de
RAM recommandés. L'offre hébergée éviterait cette charge, au prix d'un
sous-traitant supplémentaire qui stockerait les questions et réponses en
entier — acceptable tant qu'il n'y a pas d'utilisateur réel (avant la
marche C4), à réévaluer avant. Décision reportée.

### Le piège de la journalisation

C20 exige le respect des données personnelles **dans la journalisation
elle-même**. Le garde-fou d'anonymisation protège ce qui part vers le
modèle ; il ne protège pas les journaux. Si on journalise la question
brute pour déboguer, on crée une seconde copie des données personnelles,
hors du garde-fou. **Les règles de journalisation sont donc définies en
même temps que l'anonymisation, dans la même marche (C2), pas après.**

Ce piège n'est pas théorique : **il existe déjà dans le code en
production.** La recherche dense journalise aujourd'hui la question
brute de l'utilisateur. À corriger indépendamment de tout ce qui précède.

## Encore ouvert

Les tests de chaque marche — unitaires, d'intégration, et leurs seuils.
À reprendre en s'inspirant du travail fait en formation (`lab/phase4`),
non encore consulté.
