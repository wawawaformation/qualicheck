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

Le matériau de veille est **centralisé dans ce dossier**, sous `fonds/` — décision
du 2026-07-23, qui remplace le renvoi externe précédent vers
`formation_dev_ia_agentique/veille/` (le dossier source a été déplacé, pas copié :
un seul exemplaire existe désormais).

```text
docs/jury/veille/fonds/
```

**Convention de dossier** (2026-07-23) : chaque veille est un dossier
`nom_snake_case_AAAA-MM-JJ/`, contenant deux sous-dossiers :

- `working/` — matériaux de travail, brouillons, sources brutes
- `final/` — le livrable achevé (ce qui a été ou sera restitué)

Au moment du déplacement, tout le contenu existant a été rangé dans `final/`
(ce sont des notes déjà structurées, pas des brouillons) ; `working/` est créé
vide, prêt à accueillir les prochaines veilles. Reste à trier (David) : fichier
hors sujet égaré (`whereisbrian.jpeg` dans `ia_et_legislation_2026-06-03/`),
config d'éditeur versionnée par erreur (`.vscode/` dans
`britanica_openai_le_pillage_savoir_2026-05-20/`).

## Inventaire

Date = celle retenue pour le dossier (approximative pour les veilles
antérieures à cette convention, basée sur les dates de modification des
fichiers au moment du déplacement).

| Dossier | Contenu (`final/`) | Axe du thème |
| --- | --- | --- |
| `fonds/ia_et_legislation_2026-06-03/` | AI Act (niveaux de risque, application au droit français), RGPD (le RGPD, incompatibilités), DSA/DMA, fiche `European_Digital_Shield_compressed.pdf`, visuels de synthèse, sous-dossier `1_films/` (*Nosedive*/Black Mirror, *Gattaca* — fiches + visuels) | éthique, réglementaire |
| `fonds/britanica_openai_le_pillage_savoir_2026-05-20/` | analyse en 5W2H (avec source `1_article.url` et visuel), évolution du savoir, du web classique vers l'information prémâchée, conclusion — chaque section texte a son visuel associé, référence culturelle *Le Nom de la Rose* | éthique, économie |
| `fonds/ia_souverain_2026-05-27/` | `synthese.md` + 3 visuels (souveraineté des données, parcours de décision cloud, Apertus-70B) — argumentation reprise dans `conception/annexes/F_choix_llm.md` | éthique, économie |
| `fonds/dev_durable_2026-06-13/` | `presentation.odp` + `script.md` (format à deux rôles déjà appliqué : support live / document de partage), `Kit-dengagement-IA-frugale-1.pdf`, sous-dossier `veille_ia_environnement/` (variante antérieure), `videos/` (non suivi par git, ~180 Mo) | écologie, développement durable — pièce la plus directement dans l'axe du thème assigné |
| `fonds/freshrss_docker_2026-05-13/` | mise en place de l'instance FreshRSS (Docker + Caddy) — cf. `journal.md` | outillage |
| `fonds/cybersecurite_ia_2026-05-13/` | rapport cybersécurité x IA — cf. `journal.md` | cybersécurité (antérieur à Mini Manifest) |
| `fonds/metiers_web_ia_2026-07-15/` | métiers du web à l'ère de l'IA, MD de lecture pas encore généré — cf. `journal.md` | à clarifier (cf. écart de thème noté dans `journal.md`) |

`LLM-Engineers-Handbook` n'est **pas** de la veille — laissé dans
`formation_dev_ia_agentique/veille/`, hors de ce dépôt.

Le volet **réglementaire** est couvert explicitement (AI Act, RGPD, DSA/DMA). Le
référentiel l'exige au même titre que le volet technique, et c'est celui qu'on omet
le plus souvent.

## Lien avec le projet

La synthèse `fonds/ia_souverain_2026-05-27/final/synthese.md` et ses trois visuels alimentent
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

**Point de vigilance (constat sur les synthèses passées)** : une partie des
synthèses existantes est constituée de visuels (`.png`, `.jpg`, carrousel PDF) et
de présentations `.pptx`. Ce sont précisément les formats où l'accessibilité se
perd — un contenu porté par une infographie est illisible pour un lecteur d'écran.

### Format retenu pour les prochaines restitutions

Chaque veille produit systématiquement **deux formats, à des rôles distincts** —
ce n'est pas une simple duplication du même contenu :

- l'**ODP** est un **support de présentation live** — les notes qu'il porte
  guident l'oral, il n'est pas conçu pour être diffusé ni lu de façon autonome
- le **MD ou ODT est le document de partage réel**, structuré avec des styles
  sémantiques rigoureux (Titre 1, Titre 2...) — c'est lui qui porte la charge
  d'accessibilité, pas l'ODP

Cette discipline (styles sémantiques systématiques sur les documents partagés)
n'est pas adoptée pour ce dossier : elle vient d'une pratique professionnelle
antérieure — David est **expert Opquast qualité web**, l'accessibilité relève donc
de son cœur de métier, pas d'une conformité découverte à l'occasion de la
certification. L'aide-mémoire `docs/jury/accessibilite-formats.md` documente les
règles pour qui les découvre ; il ne remplace pas cette pratique déjà en place.

L'enjeu dépasse la seule C6 : l'exigence de documentation accessible revient sur C8,
C11, C18, C19 et C20. Et elle se remarquerait d'autant plus sur un projet dont
l'objet même est l'audit de qualité et d'accessibilité web.
