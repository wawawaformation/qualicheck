# Veille — organisation et localisation

## Dispositif — « Mini Manifest »

La veille s'exerce dans un cadre **collectif**, organisé au sein de la formation
sous le nom **Mini Manifest**. Consignes officielles du collectif (canal Discord) :

> **Objectif** : Apprendre, s'informer & informer ses pairs.
>
> **Méthodo** : creuser un article/actualité et être capable d'en restituer le
> fonctionnement et répondre aux questions de clarification.
>
> **Format d'une session** : 3 présentations de 10 minutes, suivies de 20 minutes
> de discussion. Passage désigné par une roue de la chance, avec un cooldown d'une
> séance (qui passe ne repasse pas à la session suivante).

Ce point compte pour C6, dont l'intitulé porte sur le fait d'« animer le **travail
collectif** de sélection des sources, collecte, traitement et partage des
informations ». La veille n'est pas une lecture solitaire : la sélection, le
traitement et le partage sont répartis, et la restitution périodique en est le
mécanisme.

**Canal de diffusion** : les synthèses sont partagées sur le canal Discord du
collectif — c'est là que vivent la plupart des restitutions, en complément des
présentations orales. Le canal sert donc à la fois d'espace de partage entre deux
restitutions et d'archive des synthèses produites.

**Outils de collecte du collectif** : Perplexity, flux RSS, Twitter/LinkedIn/
YouTube/Medium/Reddit, plateformes e-learning (Pluralsight, Dyma). **Outil de
synthèse** : NotebookLM.

**Répartition des thèmes** — chaque participant suit un axe dans la durée, ce qui
permet à chacun de bénéficier de la veille des autres sur des sujets qu'il ne suit
pas lui-même :

| Participant | Thème |
| --- | --- |
| Sabine | DevSecOps x AI + Embedded AI |
| Steeve | Systèmes multi-agents |
| Tony | Approfondissement de la formation (technique) |
| **David** | **Développement durable x AI** (sociétal, environnemental, économique) |
| Alpha | Agentic systems efficiency |
| Sofiane | Tools and technologies around Agentic AI |
| Era | Agentic AI for personnalisation & Finance |
| Mehdi | Business — Applied AI |

**Thème suivi** : développement durable x IA — sociétal, environnemental,
économique. C'est cet axe qui explique la composition du fonds documentaire
ci-dessous — les sujets n'y sont pas choisis au fil de l'actualité, mais rattachés
au thème assigné.

## Où se trouve le fonds

Le matériau de veille **ne vit pas dans ce dépôt**. Il relève de la formation, pas
de QualiCheck, et sert à d'autres travaux que ce projet :

```text
/media/david/projets/formation_dev_ia_agentique/veille/
```

Il n'est pas recopié ici : une copie diverge de l'original dès la première mise à
jour. Ce dossier-ci **indexe et date**, il n'héberge pas.

## Inventaire

| Dossier | Contenu | Axe du thème |
| --- | --- | --- |
| `IA_et_legislation/` | AI Act (niveaux de risque, application au droit français), RGPD (le RGPD, incompatibilités), DSA/DMA | éthique, réglementaire |
| `ia_souverain/` | `synthese.md` + 3 visuels (souveraineté des données, parcours de décision cloud, Apertus-70B) | éthique, économie |
| `dev_durable/` | veille IA & environnement, points d'appui, scripts de restitution | écologie, développement durable |
| `britanica_openAI_le_pillage_savoir/` | analyse en 5W2H, évolution du savoir, web classique vs information prémâchée | éthique, économie |
| `LLM-Engineers-Handbook/` | référence technique | technique |

Le volet **réglementaire** est couvert explicitement (AI Act, RGPD, DSA/DMA). Le
référentiel l'exige au même titre que le volet technique, et c'est celui qu'on omet
le plus souvent.

## Lien avec le projet

La synthèse `ia_souverain/synthese.md` et ses trois visuels alimentent
directement l'argumentation de `conception/annexes/F_choix_llm.md` (choix de modèles
souverains, Apertus-70B et Mistral Small via Infomaniak en production) ainsi que la
section « Positionnement éthique et technique » de `conception/conception.md`.

C'est un cas où la veille a produit une décision d'architecture traçable, pas
seulement de la culture générale.

## Ce qui reste à formaliser

Le fonds est constitué ; il manque trois éléments de forme exigés par C6 :

| Manque | Où le combler |
| --- | --- |
| Preuve de **régularité** — les dossiers montrent des sujets, pas une cadence datée | `journal.md` |
| **Fiabilité des sources** — auteur identifié, compétences confirmées, contenu daté et sourcé | `sources.md` |
| **Outils d'agrégation** retenus et leur coût | `sources.md` |
| **Accessibilité des synthèses** — voir ci-dessous | les supports eux-mêmes |

### Le critère d'accessibilité des synthèses

Le référentiel formule ainsi le critère : « Synthèses communiquées dans un format
**accessible** », en renvoyant à **Valentin Haüy** et **AcceDe**.

Il ne s'agit pas de « facile à consulter » : ces deux références portent sur
l'accessibilité numérique au sens du handicap. AcceDe publie des guides
d'accessibilité pour les documents bureautiques et PDF, Valentin Haüy est une
association œuvrant pour les personnes déficientes visuelles.

Concrètement, un support de restitution doit donc respecter un ordre de lecture
explicite, porter des alternatives textuelles sur les images, offrir un contraste
suffisant, et ne pas véhiculer son contenu sous forme de texte incrusté dans une
image.

**Point de vigilance** : une partie des synthèses existantes est constituée de
visuels (`.png`, `.jpg`, carrousel PDF) et de présentations `.pptx`. Ce sont
précisément les formats où l'accessibilité se perd — un contenu porté par une
infographie est illisible pour un lecteur d'écran.

Aide-mémoire pratique pour ces deux formats : `docs/jury/accessibilite-formats.md`.

L'enjeu dépasse la seule C6 : l'exigence de documentation accessible revient sur C8,
C11, C18, C19 et C20. Et elle se remarquerait d'autant plus sur un projet dont
l'objet même est l'audit de qualité et d'accessibilité web.
