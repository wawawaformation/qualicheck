# Périmètre MLOps de l'ingestion et traçabilité des données

2026-07-21 · retenu

## Contexte

L'ingestion des 245 règles Opquast était terminée, les données en base. La question
posée était de savoir si le pipeline d'ingestion devait adopter une démarche MLOps :
manifeste de configuration, versionnement des prompts et des modèles, évaluations,
métriques.

Deux contraintes réelles encadraient la question.

**Le référentiel de certification parle explicitement de MLOps** (C13, C16, C20) et
exige du monitorage de modèle (C11), des tests de modèle (C12) et une *feedback
loop* (C20). Il y avait donc une incitation à en faire.

**Mais le référentiel est écrit pour quelqu'un qui entraîne un modèle.** Il parle de
« préparation, entraînement, évaluation, validation », de « déclencheurs de
réentraînement », de *packaging* via ONNX. QualiCheck n'entraîne rien : ce qui tient
lieu de modèle est un prompt et une API hébergée.

Le risque était donc double : ne rien faire et passer à côté de compétences
évaluées, ou plaquer un appareillage sans objet réel — ce qu'un jury repère
immédiatement, puisque la pratique n'y serait reliée à aucune difficulté constatée.

## Options envisagées

### Employer le vocabulaire du réentraînement — écartée

Traduire « ré-ingestion » en « réentraînement » aurait fait correspondre le projet
au vocabulaire du référentiel. Écarté : aucun entraînement n'a lieu, et un mot
plaqué sur une pratique inexistante ne résiste pas à la première question.

Retenu à la place : dire explicitement que le projet n'entraîne pas de modèle, et
présenter ce qui en tient lieu. Une position assumée se défend, un faux
réentraînement non.

### Construire un jeu d'évaluation — écartée

Fabriquer des paires question/réponse pour mesurer la qualité de l'enrichissement
aurait produit une métrique. Écarté : il aurait fallu **inventer la vérité terrain**,
donc mesurer le modèle contre des réponses sorties de nulle part.

Deux sources de données non inventées existent en revanche, et ont été identifiées
comme les vraies bases d'évaluation : les 245 règles constituent un corpus fixe
permettant de comparer deux versions de prompt sur le même jeu, et les corrections
humaines produites par US1 fourniront de la vérité terrain réelle au fil de l'usage.

### Monitorer l'ingestion — déplacée vers US1

Écarté pour une raison structurelle, indépendante de la certification :
**l'ingestion est un batch lancé deux ou trois fois dans la vie du projet.** Il n'y
a ni flux, ni dérive à détecter, ni seuil d'alerte qui ait un sens. Le critère C11
« au moins un vecteur de restitution en temps réel » n'a aucun objet sur un script
lancé trois fois.

US1 produit au contraire du flux à chaque audit : latences, coûts, taux d'échec,
corrections humaines. Les métriques y existent naturellement, avec des données
réelles plutôt qu'un dispositif monté pour l'occasion.

### Créer une table `ingestion_run` — écartée

Une table portant une ligne par exécution (date, coût, tokens, distributions) aurait
donné un foyer structuré aux mesures aujourd'hui consignées en prose. Écarté : pour
un script lancé de façon anecdotique, le coût et la durée n'ont pas besoin d'être
requêtables. Trois colonnes suffisent à répondre à la seule question qui se pose
réellement — d'où vient cette ligne.

### Un manifeste conservant son propre historique — écartée

Le manifeste aurait pu accumuler ses versions successives. Écarté : cela
réimplémenterait git en moins bien, et créerait une source de vérité concurrente.
`git log manifest.yml` répond déjà à « qu'est-ce qui a changé et quand ».

### Enregistrer le nom de déploiement plutôt que le modèle — écartée

Le nom de déploiement Azure est plus proche de ce qui est techniquement appelé.
Écarté : c'est une **adresse propre à un compte**. Deux personnes exécutant la même
ingestion produiraient des provenances différentes pour le même modèle, rendant la
colonne incomparable — donc inutile pour la seule question qu'elle doit trancher.

### Une résolution implicite entre le manifeste et le `.env` — écartée

Le code aurait pu déduire le nom de la variable d'environnement à partir du nom du
modèle. Écarté au profit d'une déclaration explicite : un lien déduit ne s'écrit
nulle part et casse en silence.

## Décision

Le pipeline d'ingestion reçoit une **traçabilité de la donnée**, et rien de plus :
quatre colonnes de provenance sur `regle`, un manifeste des décisions courantes lu
par le code, une version de prompt dans le fichier de prompt lui-même.

Spec complète : `conception/2_ingestion/E_provenance_manifeste.md`.

**Le critère qui a tranché**, et qui a servi aux sept arbitrages ci-dessus :

> Adopter une pratique quand on a mal, pas quand on apprend son nom.

Le besoin de provenance n'était pas théorique. Les données en base étaient connues
comme périmées **uniquement** parce que le `CHANGELOG.md` le disait : aucune requête
ne pouvait établir avec quel prompt ni à quelle date une règle avait été produite.
La douleur était constatée, l'instrumentation y répond.

Les six autres pratiques envisagées ne répondaient à aucune difficulté rencontrée.

**Un second critère** a servi à découper ce qui restait — demander à chaque couche
de quoi elle est responsable, et refuser qu'une couche fasse le travail d'une
autre :

| Couche | Responsabilité unique |
| --- | --- |
| `.env` | annuaire : ce que la machine peut joindre, avec quels secrets |
| `manifest.yml` | décisions : ce qui est vrai maintenant |
| git | historique des décisions |
| colonnes de provenance | quelle décision a produit cette ligne |

C'est ce critère qui a écarté l'historique interne du manifeste, et qui a conduit à
sortir du `.env` l'affectation des rôles — un fichier d'accès n'a pas à connaître le
métier du pipeline.

## Conséquences

**Calendrier contraint.** La ré-ingestion réécrira les 245 lignes et coûte environ
3 € d'appels LLM. Instrumenter avant, c'est gratuit ; instrumenter après imposerait
une migration *et* une seconde ré-ingestion facturée. D'où la décision de livrer cet
incrément avant le chantier 2.

**Une règle de nommage formalisée.** Le métier reste en français, le technique passe
en anglais. Le schéma appliquait déjà cette règle sans qu'elle ait été écrite. Elle
est désormais consignée dans `conception/MLD_qualicheck.md`.

**Une limite assumée.** L'identité du modèle reste une **déclaration**, pas une
observation : un déploiement Azure peut être repointé depuis la console sans qu'aucun
fichier versionné ne change. Si la réponse de l'API expose le modèle réellement
utilisé, cette information sera préférée. À vérifier à l'implémentation.

**Ce qui a été déplacé, pas abandonné.** Les métriques, le monitorage et la
*feedback loop* relèvent d'US1, où ils porteront sur des données réelles. Les
compétences C11 et C20 s'y démontreront, pas ici.

**Reste ouvert.** L'emplacement des tarifs `KIMI_PRICE_*`, en attente de relevés de
coûts Azure réels — le commentaire actuel du `.env` signale lui-même que la valeur
présente est une approximation.
