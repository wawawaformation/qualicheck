# Sources et outils de veille

Complète le `journal.md`, qui enregistre les sessions, et le `README.md`, qui décrit
le dispositif collectif.

## Outils d'agrégation

| Outil | Usage | Coût |
| --- | --- | --- |
| **FreshRSS** auto-hébergé — `rss.david-legrand.fr` | agrégation des flux RSS, cœur du dispositif personnel | logiciel libre, pas d'abonnement ; coût = hébergement Docker déjà en place |
| **Discord** — canal veille du collectif (Mini Manifest) | partage et discussion entre participants, restitution croisée des thèmes | gratuit |
| **LinkedIn** | signaux faibles, publications de praticiens | gratuit |
| **YouTube** | formats longs, conférences, analyses | gratuit |
| **Perplexity** | outil de collecte retenu par le collectif (recherche augmentée) | selon usage collectif |
| **NotebookLM** | outil de synthèse retenu par le collectif pour préparer les restitutions | gratuit |

Perplexity et NotebookLM sont les outils **du collectif Mini Manifest**, distincts
du FreshRSS personnel — l'un collecte/interroge, l'autre synthétise avant
présentation. Les autres outils mentionnés dans les consignes du collectif
(Twitter/Medium/Reddit, plateformes e-learning Pluralsight/Dyma) ne sont pas encore
mobilisés côté David : à ajouter au tableau `sources.md` s'ils entrent en usage.

Le référentiel demande un choix « cohérent avec sources et budget ». La raison du
choix est directement celle-là :

**Les agrégateurs hébergés testés auparavant imposaient un compte premium** pour
dépasser leurs limites — nombre de flux, de dossiers ou de fonctions de tri.
L'instance FreshRSS auto-hébergée n'a aucune de ces restrictions, pour un coût
d'abonnement nul, sur une infrastructure Docker déjà en place.

C'est ce qui permet de **collecter largement sur l'IA**, au-delà du seul thème
assigné pour les restitutions collectives : le fonds documentaire par thème
(cf. `README.md`) est le produit d'une collecte plus étendue, pas son périmètre.

Le canal Discord mérite d'être signalé à part : c'est lui qui porte la dimension
**collective** exigée par C6 — le partage entre participants suivant des thèmes
différents, entre deux restitutions.

## Critères de fiabilité retenus

Le référentiel demande des sources « répondant aux critères de fiabilité : auteur
identifié, compétences confirmées, contenu daté et sourcé ». Une source n'entre dans
le tableau ci-dessous que si elle satisfait les trois.

**Une précision qui compte pour l'évaluation** : LinkedIn et YouTube sont des
**plateformes**, pas des sources. « Je suis LinkedIn » ne satisfait aucun des trois
critères. Ce qui les satisfait, c'est un compte ou une chaîne identifiée, dont on
peut nommer l'auteur et justifier la compétence. Le tableau doit donc lister des
comptes et des flux, pas des plateformes.

## Sources suivies

Export FreshRSS du 2026-07-22 (`feeds_2026-07-22.opml.xml`), 17 flux répartis en
8 dossiers thématiques. Les dossiers structurent la collecte : agents/workflow,
vulgarisation IA, LLM, MLOps, Python, réglementation, tutoriels.

| Source | Dossier FreshRSS | Auteur / organisation | Pourquoi fiable | Fréquence |
| --- | --- | --- | --- | --- |
| CrewAI Blog | Agents IA / workflow | CrewAI (éditeur du framework) | auteur = l'éditeur du framework documenté, source primaire | *à préciser* |
| n8n Blog | Agents IA / workflow | n8n (éditeur de l'outil) | source primaire, éditeur de l'outil | *à préciser* |
| ActuIA | IA — vulgarisation et outils | rédaction ActuIA | média spécialisé IA francophone identifié | *à préciser* |
| Korben.info | IA — vulgarisation et outils | Manuel Dorne (Korben) | auteur identifié, actif depuis 20 ans sur la tech | *à préciser* |
| LinuxFr — tag IA | IA — vulgarisation et outils | communauté LinuxFr, contributions modérées | plateforme communautaire francophone établie, modération par les pairs | *à préciser* |
| Blog du Modérateur — IA | LLM | rédaction BDM | média professionnel identifié, ligne éditoriale connue | *à préciser* |
| Hugging Face Blog | LLM | Hugging Face (acteur open source ML) | source primaire, un des principaux hébergeurs de modèles | *à préciser* |
| MLOps Community | LMOps | communauté MLOps (podcast, événements) | praticiens identifiés, contenu régulier et daté | *à préciser* |
| AFPy's Planet | Python | Association Francophone Python | association identifiée, agrégateur de blogs de contributeurs Python | *à préciser* |
| LinuxFr — tag Python | Python | communauté LinuxFr | idem ci-dessus | *à préciser* |
| Python Insider | Python | équipe cœur de développement Python | source officielle, la plus primaire possible sur le langage | *à préciser* |
| EU AI Act (artificialintelligenceact.eu) | Réglementation | suivi indépendant du règlement européen | veille juridique dédiée, textes officiels commentés | *à préciser* |
| CNIL — actualités | Réglementation | CNIL (autorité française) | source institutionnelle officielle | *à préciser* |
| MachineLearningMastery.com | Tutos | Jason Brownlee | auteur identifié, praticien ML publiant depuis plusieurs années | *à préciser* |
| LangChain Blog | Sans catégorie | LangChain (éditeur du framework) | source primaire, framework utilisé dans le projet | *à préciser* |
| Les Numériques — IA | Sans catégorie | rédaction Les Numériques | média tech grand public identifié | *à préciser* |
| Microsoft Foundry Blog | Sans catégorie | Microsoft (Azure AI Foundry) | source primaire, éditeur de l'infrastructure LLM du projet | *à préciser* |

**Deux flux touchent directement QualiCheck**, pas seulement la veille générale :
Microsoft Foundry Blog (Azure AI Foundry est la plateforme LLM du projet) et
LangChain Blog (framework utilisé dans `app/ingestion/llm_client.py`).

**À étoffer** — constat de David, pas un jugement porté sur ce qui existe :

- **Fréquence** de lecture par flux ou par dossier, à renseigner
- **Réglementation** : 2 flux sur 17, le plus mince des 8 dossiers alors que le
  thème de veille assigné (écologie, éthique, économie, développement durable, cf.
  `README.md`) est fortement réglementaire — RGAA/accessibilité notamment absent
- **« Sans catégorie »** contient 3 flux pertinents (dont 2 directement liés au
  projet) : les ranger clarifierait la collecte
- Aucun compte **LinkedIn** ni chaîne **YouTube** nommément identifié malgré leur
  mention comme sources (cf. plus haut) — à lister ici une fois précisés
- **YouTube** : les abonnements veille et personnels sont aujourd'hui mélangés sur
  un compte unique, ce qui empêche d'en extraire une liste de chaînes propre à la
  veille. Un compte dédié à la veille séparerait les deux et rendrait les chaînes
  suivies exportables/listables, comme pour le flux RSS

## Sources écartées

Documenter aussi ce qu'on ne suit **pas** et pourquoi : c'est ce qui montre que la
sélection est un choix et non un défaut de connaissance.

| Source | Raison de l'écarter |
| --- | --- |
| *à compléter* | |
