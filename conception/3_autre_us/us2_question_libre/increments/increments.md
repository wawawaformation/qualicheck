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

Chaque phase est un **epic**, chaque marche une **user story** quand elle
sert quelqu'un — et une **tâche technique** assumée quand ce n'est pas le
cas.

Deux acteurs seulement :

- **le professionnel du web**, qui prépare ou mène un audit — l'acteur par
  défaut ;
- **l'exploitant** (nous), quand la marche sert à faire tourner ou à
  protéger le service, pas à rendre un service à l'utilisateur.

Écrire ces stories a un effet diagnostique : **quatre marches sur
vingt-et-une n'ont aucun bénéficiaire côté utilisateur.** Ce n'est pas un
défaut — mais mieux vaut l'assumer que leur inventer un faux argument
produit.

Les scénarios Gherkin s'écrivent **au moment d'attaquer chaque marche**,
pas d'avance : écrire vingt jeux de scénarios pour des comportements qui
bougeront encore, c'est spéculer.

---

### Epic A — l'agent nu

**A1 · La boucle et un premier outil** (recherche par mots-clés)

> En tant que professionnel du web, je veux poser une question en langage
> libre sur la qualité web, afin d'obtenir une réponse appuyée sur des
> règles Opquast plutôt que sur une opinion.

*Mesure* : latence, coût par question, nombre d'itérations, taux d'erreur.

**A2 · L'instrumentation** — *tâche technique*

> En tant qu'exploitant, je veux voir le détail de chaque étape d'une
> réponse, afin de savoir où passent le temps et l'argent.

*Mesure* : rien de neuf en soi — mais tout ce qui suit devient observable
dès son arrivée.

**A3 · La recherche sémantique**

> En tant que professionnel du web, je veux être compris même si je
> n'emploie pas les termes exacts du référentiel, afin de ne pas avoir à
> deviner le vocabulaire d'Opquast.

*Mesure* : choix d'outil par l'agent, coût réel (cet outil appelle
lui-même trois modèles).

**A4 · La lecture d'une règle par numéro**

> En tant que professionnel du web, je veux citer un numéro de règle et
> en obtenir le détail, afin de vérifier rapidement un point que je
> connais déjà.

*Mesure* : taux de bon choix entre trois outils.

---

### Epic B — ce qui sort de l'agent

**B1 · Contrôle des citations**

> En tant que professionnel du web, je veux que chaque règle citée existe
> réellement, afin de pouvoir m'appuyer sur la réponse devant mon client.

*Mesure* : taux de citations inventées — **seuil d'alerte à zéro**, toute
occurrence est un incident.

**B2 · Contrôle final après la boucle** — *tâche technique*

> En tant qu'exploitant, je veux un dernier filtre avant l'envoi, afin de
> rattraper ce qui aurait échappé aux contrôles précédents.

*Mesure* : écarts rattrapés.

---

### Epic C — ce qui entre, et à quel prix

**C1 · Limite d'itérations**

> En tant que professionnel du web, je veux recevoir une réponse même
> quand l'agent peine, afin de ne pas attendre indéfiniment sans
> explication.

*Mesure* : **le seuil se fixe ici**, avec la distribution observée en
phases A et B.

**C2 · Anonymisation et règles de journalisation**

> En tant que personne dont les données figurent dans une question, je
> veux qu'elles ne soient transmises ni à un fournisseur de modèle ni aux
> journaux, afin que ma vie privée ne dépende pas de la vigilance de celui
> qui pose la question.

*Mesure* : taux de détection, absence de donnée personnelle dans les
journaux.

**C3 · Détection d'identifiants techniques**

> En tant que professionnel du web, je veux qu'une clé ou un jeton collé
> dans ma question ne soit pas transmis, afin de ne pas divulguer un
> secret sans m'en apercevoir.

*Mesure* : occurrences détectées.

**C4 · Authentification de l'utilisateur**

> En tant que professionnel du web, je veux que mon accès soit identifié,
> afin que mes usages me soient attribués et que personne n'utilise le
> service à ma place.

*Mesure* : tentatives rejetées, appels par client.

**C5 · Contrôle du sujet**

> En tant que professionnel du web, je veux un refus clair quand ma
> question sort du domaine, afin de ne pas recevoir une réponse inventée
> que je croirais fondée.

*Mesure* : taux de refus correct, **taux de faux refus**.

**C6 · Contrôle de l'intention** — *tâche technique*

> En tant qu'exploitant, je veux refuser les questions qui relèvent du
> sujet mais visent à nuire, afin de ne pas outiller un usage malveillant.

*Mesure* : refus de ce qui est dans le sujet mais malveillant.

---

### Epic D — regarder une vraie page

**D1 · Lecture d'une URL** — *indissociable de l'autorisation sur le site
et de l'isolation réseau*

> En tant que professionnel du web, je veux faire analyser une page dont
> je suis responsable, afin d'obtenir une réponse qui porte sur mon site
> et pas seulement sur la théorie.

*Mesure* : taux d'échec de récupération, tentatives sur des adresses
internes.

**D2 · Capture d'écran**

> En tant que professionnel du web, je veux soumettre une capture quand la
> page n'est pas accessible publiquement, afin de poser ma question sur un
> site en développement ou protégé par un accès.

*Mesure* : taux d'illisibilité.

**D3 · Validation du marquage**

> En tant que professionnel du web, je veux savoir si mon code respecte
> les spécifications, afin de corriger ce qui est objectivement invalide
> avant de discuter du reste.

**D4 · Calcul du ratio de contraste**

> En tant que professionnel du web, je veux un chiffre de contraste plutôt
> qu'une appréciation, afin de pouvoir démontrer la conformité ou la
> non-conformité.

**D5 · Vérification au navigateur** — *indissociable de l'accord de
l'utilisateur*

> En tant que professionnel du web, je veux que l'agent vérifie lui-même
> ce qui ne se voit ni dans le code ni sur une image, afin de ne pas avoir
> à refaire la manipulation moi-même — et seulement si je l'y autorise.

*Mesure* : durée, taux d'échec.

---

### Epic E — la conversation

**E1 · La discussion, sans mémoire encore**

> En tant que professionnel du web, je veux retrouver mes échanges
> précédents, afin de ne pas perdre ce que j'ai déjà demandé.

*Mesure* : longueur des discussions.

**E2 · La mémoire**

> En tant que professionnel du web, je veux que l'agent se souvienne du
> contexte de la conversation, afin de ne pas répéter de quel site je
> parle à chaque question.

*Mesure* : effet sur les faux refus du contrôle de sujet.

**E3 · Nettoyage du contenu avant son entrée en mémoire** — *tâche
technique*

> En tant qu'exploitant, je veux nettoyer ce qu'un outil ramène avant que
> ça entre en mémoire, afin qu'une page piégée ne contamine pas les tours
> suivants.

*Mesure* : contenus écartés.

**E4 · « Demander à l'utilisateur »**

> En tant que professionnel du web, je veux être sollicité quand moi seul
> peux constater quelque chose sur ma page, afin d'obtenir une réponse sur
> les règles qu'aucun outil ne peut vérifier.

*Mesure* : taux de reprise, abandons.

---

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

## Contrat API

Voir `A_agent_nu/openapi.json` — contrat OpenAPI vivant, enrichi increment
par increment (pas répété ici pour éviter une double source de vérité).

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
