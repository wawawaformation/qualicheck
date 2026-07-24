# Candidats de sources — développement durable x IA, et dev IA agentique

Fiche à part de `sources.md` : ce sont des **candidats vérifiés**, pas encore des
sources suivies. `sources.md` reste la liste de ce que David suit réellement — à
transférer là une fois qu'un candidat entre en usage.

Chaque flux RSS/Atom ci-dessous a été **récupéré et validé** (format, titre,
fraîcheur de contenu) avant d'être listé — aucune URL n'est donnée « probable » ou
reconstituée de mémoire.

Deux axes couverts, distincts l'un de l'autre :

- **Développement durable x IA** (sociétal, environnemental, économique) — le
  thème assigné à David dans le collectif Mini Manifest. Vérifié le 2026-07-22.
- **Développement IA agentique** — veille technique personnelle, plus large que
  le seul thème Mini Manifest (cohérent avec la collecte déjà étendue notée dans
  `sources.md`). Vérifié le 2026-07-23.

## Flux RSS/Atom — prêts à coller dans FreshRSS

| Source | URL du flux | Langue | Angle |
| --- | --- | --- | --- |
| **Bon Pote** | `https://bonpote.com/feed/` | FR | média indépendant écologie/démocratie/numérique, flux actif (maj horaire) |
| **GreenIT.fr** (Frédéric Bordage) | `https://www.greenit.fr/feed/` | FR | référence française sobriété numérique, écoconception, **IA frugale** — angle le plus directement recoupant le thème |
| **The Shift Project** | `https://theshiftproject.org/feed/` | FR | think tank transition carbone ; projet « Lean ICT » dédié à l'impact environnemental du numérique |
| **By the Numbers** (Hannah Ritchie, ex-Our World in Data) | `https://hannahritchie.substack.com/feed` | EN | soutenabilité pilotée par la donnée — bon contrepoint factuel aux discours alarmistes ou promotionnels sur l'IA |
| **MIT Technology Review** | `https://www.technologyreview.com/feed/` | EN | flux général (pas uniquement dev durable), mais couvre IA et climate tech avec une rigueur éditoriale reconnue |

Tous validés par récupération directe du flux (structure RSS 2.0 correcte,
contenu daté juillet 2026 pour la plupart) — pas de lien mort ni de flux abandonné
dans cette liste.

**Le plus directement pertinent** : GreenIT.fr est la seule source de la liste qui
traite nommément l'IA *et* la sobriété numérique comme un même sujet, plutôt que
deux sujets adjacents.

## Chaînes YouTube

Réponse au constat du compte personnel/veille mélangés (cf. `sources.md`) : ces
trois chaînes sont candidates pour le futur compte dédié.

| Chaîne | Handle | Langue | Angle |
| --- | --- | --- | --- |
| **Le Réveilleur** | `@lereveilleur` | FR | vulgarisation scientifique énergie/climat (Rodolphe Meyer, Loïc Giaccone) — traite occasionnellement le coût énergétique du numérique |
| **Undecided with Matt Ferrell** | `@UndecidedTechnology` | EN | clean tech, énergies renouvelables — 1,4M abonnés, ton pédagogique et sourcé |
| **Real Engineering** | *(recherche « Real Engineering »)* | EN | infrastructure, data centers, énergie — a traité spécifiquement le coût réel des data centers IA (avril 2026) |

Pas de doublon franco-anglais sur le même sujet précis (data center + IA) : Real
Engineering est la plus proche du thème exact, en anglais seulement.

## Newsletters

Distinction importante pour l'ajout dans FreshRSS : **certaines ont un flux RSS,
d'autres sont email uniquement.**

| Newsletter | Accès | Fréquence | Fiabilité |
| --- | --- | --- | --- |
| **AI Weekly** | RSS confirmé : `https://aiweekly.co/feed` | 3x/semaine | active depuis 2015, flux vérifié à jour |
| **The Algorithm** (MIT Technology Review) | **email uniquement**, pas de flux RSS trouvé | hebdomadaire (lundi) | rédigée par un journaliste identifié (James O'Donnell), spécifiquement IA |
| **By the Numbers** (Hannah Ritchie) | même flux RSS que ci-dessus | — | déjà listée comme flux ; à ne pas dupliquer si ajoutée |
| **15marches** | à vérifier — présence Substack repérée mais fréquence non confirmée directement | *à confirmer* | transformation numérique de la société, exemples concrets |
| **EcoInfo** (CNRS) | pas de flux RSS trouvé, newsletter périodique irrégulière | irrégulière (plusieurs mois d'écart) | source institutionnelle (CNRS), sérieuse mais peu fréquente |

**Réserve à noter** : une autre candidate repérée en recherche, *Cap écologique*
(Louis Vicart), montre un écart de plusieurs mois entre ses derniers numéros
connus — signe possible d'un arrêt ou d'une pause. Écartée de la liste plutôt que
recommandée avec un doute non levé.

## Flux RSS/Atom — développement IA agentique

| Source | URL du flux | Langue | Angle |
| --- | --- | --- | --- |
| **Simon Willison's Weblog** | `https://simonwillison.net/atom/everything/` | EN | voix individuelle de référence sur les LLM, les agents de code, le prompt engineering — très actif (plusieurs billets par 24-48h), a inventé le terme « prompt injection » |
| **Anthropic Engineering Blog** (via flux tiers) | `https://conoro.github.io/anthropic-engineering-rss-feed/anthropic_engineering_rss.xml` | EN | billets techniques directement sur l'agentique : Claude Agent SDK, MCP, tool use — **flux non officiel** (Anthropic ne publie pas de RSS natif), maintenu par un tiers via scraping automatisé, peut casser sans préavis |
| **Latent Space** | `https://www.latent.space/feed` | EN | newsletter + podcast AI Engineer, « comment les labs construisent agents, modèles, infra » — cadence irrégulière liée à la publication d'épisodes, pas hebdomadaire fixe |

**Déjà dans le FreshRSS personnel** (dossier « Agents IA / workflow », export
OPML du 2026-07-22, non re-vérifiés ici) : CrewAI Blog, n8n Blog. Et dans
« Sans catégorie » : LangChain Blog — directement lié au framework utilisé dans
`app/ingestion/llm_client.py`.

**Point de vigilance propre à ce lot** : l'unique flux Anthropic n'est pas
officiel. Si ce dépôt tiers est abandonné ou si Anthropic change la structure de
sa page, le flux cesse de fonctionner sans avertissement — à surveiller
spécifiquement, contrairement aux autres flux de cette fiche qui sont tous des
flux natifs des éditeurs.

## Ce qui reste à faire

- Ajouter à `sources.md` les candidats effectivement retenus, avec la fréquence de
  lecture réelle une fois en usage
- Vérifier soi-même l'activité de 15marches avant de l'ajouter (la recherche n'a
  pas confirmé la fréquence avec certitude)
- Étoffer le dossier « Réglementation » du FreshRSS — cette fiche ne le couvre pas,
  elle porte sur le volet sociétal/environnemental/économique du thème
