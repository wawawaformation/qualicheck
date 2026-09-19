# Découper la construction de l'agent US2 en petites marches

2026-09-19 · retenu

## Contexte

La conception de l'agent US2 s'est accumulée sur deux jours : 9 outils,
5 points d'accroche de garde-fous et 10 fiches associées, 3 types
d'entrée utilisateur, 2 authentifications distinctes, 3 fournisseurs de
modèles. Chaque pièce se tient, et l'ensemble a été validé morceau par
morceau.

Le problème n'est pas la conception, c'est **sa taille d'un seul tenant**.
Le déclencheur est une contrainte réelle, formulée par David en cours de
travail : *« je galère à imaginer le système »*. Si la personne qui
construit ne peut pas tenir l'ensemble en tête, aucune étape ne peut être
attaquée sereinement — et un échec ne serait pas diagnosticable, puisque
plusieurs paramètres non réglés (seuil d'itérations, seuils de refus,
choix de modèle) agiraient en même temps.

C'est une contrainte de construction, pas un défaut de la conception.

## Options envisagées

**Construire l'agent complet tel que conçu.**
Pour : la conception est cohérente et déjà écrite, rien à réorganiser.
Contre : aucune étape intermédiaire vérifiable. En cas de mauvais
résultat, impossible de savoir quelle pièce est en cause — et plusieurs
seuils devraient être devinés simultanément, faute de données pour les
poser.

**Découper en trois ou quatre gros incréments.**
Pour : peu de cérémonie de suivi, découpage rapide à écrire.
Contre : chaque incrément resterait multi-paramètres. Le problème n'est
pas résolu, seulement déplacé — on retrouverait la même impossibilité de
diagnostic à l'intérieur de chaque bloc.

**Découper finement : une marche = un seul ajout.**
Pour : chaque marche est compréhensible et mesurable seule ; les seuils
se règlent avec les données produites par les marches précédentes au lieu
d'être devinés. L'ordre de construction devient lui-même un parcours
d'apprentissage du système.
Contre : beaucoup plus de cartes à piloter, davantage de suivi.

## Décision

Le découpage fin est retenu : **21 marches réparties en 5 phases**
(`conception/3_autre_us/us2_question_libre/increments.md`).

Le critère qui a tranché n'est pas la granularité en elle-même, mais
l'**ordre** qu'elle permet : *on n'avance pas du plus important au moins
important, mais dans l'ordre où la mesure devient possible*. L'agent nu
d'abord, ses garde-fous ensuite — réglés avec la distribution réellement
observée pendant les premières marches. La fiche sur la limite
d'itérations laissait justement son seuil ouvert en attendant cette
mesure : le découpage la produit.

Deux corollaires découverts en appliquant la règle :

- **Un garde-fou de sécurité ne se sépare pas de la capacité qu'il
  protège.** Livrer l'outil de lecture d'URL sans son contrôle
  d'autorisation ni l'isolation réseau ne serait pas une petite marche
  mais une faille déployée. Le découpage fin est la règle, la sécurité en
  est la limite.
- **L'instrumentation est une marche à part entière, et précoce** (A2),
  pour que tout ce qui arrive ensuite soit observable dès son arrivée
  plutôt qu'instrumenté après coup.

Chaque marche porte un « afin de » ; les scénarios Gherkin s'écrivent au
moment d'attaquer la marche, pas d'avance.

## Conséquences

**Ce que ça rend vérifiable.** Le bénéfice du découpage ne reste pas une
impression : les marches deviennent des cartes Kanboard avec durée estimée
et durée réelle, déjà pratiqué sur ce projet. L'écart entre estimation et
réalité sur les petites cartes, comparé aux grosses cartes antérieures,
mesure si la subdivision améliore réellement la prévisibilité. Le vécu
devient une donnée.

**Ce que ça révèle.** L'exercice du « afin de » a montré que certaines
marches n'ont pas de bénéficiaire côté utilisateur — l'instrumentation,
le contrôle final, le nettoyage de la mémoire servent l'exploitant. Utile
à savoir pour ne pas les justifier par un faux argument produit.

**Ce que ça coûte, assumé.** Plus de cartes à tenir à jour, et un contrat
d'API qui changera en cours de route : une question deviendra une
sous-ressource d'une discussion à la marche E1. Le projet versionne déjà
son contrat d'API, le changement est acté d'avance plutôt que subi.

**Ce qui reste ouvert.** Les tests de chaque marche et leurs seuils, et le
choix de l'outil de restitution des traces — Langfuse auto-hébergé s'est
révélé lourd (cinq services, 16 Go de RAM recommandés), l'arbitrage entre
hébergé et auto-hébergé est reporté.
