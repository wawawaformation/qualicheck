# Lecture ouverte de l'API données, et licence CC BY-SA 4.0

2026-07-26 · retenu

## Contexte

La spec de l'API données (`docs/superpowers/specs/2026-07-26-api-fastapi-regles-design.md`)
ouvre un accès HTTP aux 245 règles enrichies. La question s'est posée pendant
sa conception : faut-il exiger un jeton en lecture ?

L'argument pour fermer était réel. La base contient deux natures de données
mêlées dans la même table :

| Donnée | Origine |
| --- | --- |
| `intitule`, `solution`, `controle`, `contexte`, `objectifs`, `tags`, `phases` | Opquast |
| `strategie_analyse`, `strategie_justification`, `guide_analyse`, `embedding` | Pipeline d'ingestion du projet, environ 4 € d'appels LLM |

La seconde ligne est la valeur ajoutée du projet. Exposée sans jeton sur
`FASTAPI_URL_PROD`, elle devient téléchargeable par n'importe qui.

**Élément découvert pendant l'arbitrage** : le référentiel Opquast est diffusé
sous **Creative Commons Attribution – Partage dans les Mêmes Conditions 4.0
International (CC BY-SA 4.0)** — voir
[la page de licence d'Opquast](https://checklists.opquast.com/fr/qualite-numerique/licence/).
Le `README.md` du projet ne mentionnait que « utilisé avec l'accord d'Élie
Sloïm », ce qui est une autorisation personnelle : plus faible et moins
vérifiable qu'une licence publique qui s'applique de toute façon, sans
autorisation préalable.

## Options envisagées

**Lecture ouverte, jeton sur l'écriture seulement (retenu)** — pour : le
partage à l'identique de CC BY-SA rend l'ouverture cohérente avec la licence
de la source, pas seulement généreuse ; aucun mécanisme à construire ; un
client tiers peut consommer le référentiel enrichi sans négociation. Contre :
le corpus enrichi devient téléchargeable intégralement, sans contrepartie ni
mesure de ce qui est consommé.

**Jeton Bearer aussi sur les `GET`** — pour : la valeur ajoutée du projet reste
sous contrôle, et on sait qui consomme. Contre : contredit le partage à
l'identique dès lors qu'on distribue une adaptation du référentiel ; oblige
tout client, même un simple `curl` de vérification, à détenir un secret ;
ferme un contenu dont la majeure partie est déjà publique chez Opquast.

**Jetons par client, avec droits distincts en lecture et en écriture** —
envisagé le 2026-07-26 puis écarté le même jour. Pour : granularité réelle,
traçabilité du consommateur, et le risque d'exposition disparaissait. Contre :
la lecture cessait d'être ouverte, ce qui était l'inverse de l'intention ; une
ACL complète pour un seul client réellement existant. La forme « plusieurs
jetons en écriture, un par client » reste envisageable plus tard sans remettre
en cause la présente décision.

**Trois-tiers strict — `api_data` sur réseau privé, seule `api_business`
exposée** — pour : le problème d'exposition disparaît par construction plutôt
que par un réglage. Contre : l'écran de revue des enrichissements dépendrait
d'une API applicative non conçue ; et surtout, cette option répond à un
problème que la présente décision ne considère plus comme un problème. Elle
reste pertinente pour d'autres raisons (cloisonnement, surface réseau), pas
pour celle-là.

## Décision

**La lecture reste ouverte, sans jeton. C'est un choix, pas un défaut.**

Deux critères ont tranché, dans cet ordre :

1. **La licence de la source.** Le partage à l'identique de CC BY-SA 4.0 est
   viral : une adaptation doit être diffusée sous la même licence. La base
   reproduisant littéralement le contenu Opquast, la diffusion du jeu de
   données relève de CC BY-SA quel que soit le statut juridique de
   l'enrichissement pris isolément. Fermer la lecture aurait travaillé contre
   la licence dont le projet bénéficie.
2. **La cohérence avec le positionnement du projet.** La veille documentée du
   projet porte sur le pillage du savoir par les acteurs de l'IA
   (`docs/jury/veille/fonds/britanica_openai_le_pillage_savoir_2026-05-20/`) et
   sur la souveraineté (`.../ia_souverain/`). Produire de la donnée à partir
   d'un commun, puis la fermer, serait difficile à défendre après avoir
   documenté ces sujets. L'ouverture n'est donc pas seulement conforme, elle
   est assumée philosophiquement.

Le **soutien d'Élie Sloïm** (fondateur d'Opquast) reste mentionné et garde sa
valeur propre : il légitime l'usage expérimental du référentiel et du serveur
MCP dans le cadre de la certification, ce que la licence seule ne couvre pas.
Licence et soutien se cumulent, ils ne se remplacent pas.

## Conséquences

- **L'attribution devient obligatoire, et elle manquait.** CC BY-SA exige le
  crédit et un lien vers la licence. L'API les porte désormais via le champ
  OpenAPI standard `license_info` et la citation recommandée par Opquast dans
  sa description — visibles dans `/docs` et `/openapi.json`. Les valeurs
  vivent dans `app/api_data/manifest.yml`, source de vérité de la
  configuration.
- **L'obligation suit le contenu, pas l'étage.** Toute brique qui *distribue*
  du contenu du référentiel doit porter l'attribution — y compris
  `app/api_business/` le jour où elle relaiera des règles à ses clients. Ce
  n'est pas acquis par le simple fait que l'étage données le fait déjà.
- **La séparation n-tiers est aussi une frontière de licence.** Le tiers
  données (`app/ingestion/`, `app/api_data/`, `app/models/`, et le jeu de
  données lui-même) forme un tout sous licence libre. La licence des autres
  étages — API applicative, interface Vue.js — **n'est pas encore décidée**, et
  le cloisonnement préserve cette liberté : CC BY-SA porte sur le contenu, pas
  sur le code qui le manipule.
- **Limite assumée** : n'importe qui peut récupérer l'intégralité du corpus
  enrichi, sans mesure de ce qui est consommé ni limitation de débit. Aucune de
  ces deux briques n'est prévue à ce stade.
- **Ce que la décision ne dit pas** : elle ne se prononce pas sur la licence du
  code du projet, ni sur celle des étages applicatif et présentation. Deux
  sujets distincts à trancher séparément.
- **Ce document n'est pas un avis juridique.** Savoir si l'enrichissement pris
  isolément constitue une œuvre dérivée au sens de la licence est une question
  de droit que le projet ne tranche pas. La conclusion pratique n'en dépend
  pas : le jeu de données diffusé contient du contenu Opquast littéral, donc
  CC BY-SA s'applique à sa diffusion.
