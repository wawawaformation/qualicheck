# Couverture des sources d'extraction (C1) — 2 sur 5, justifiées

2026-07-28 · retenu

## Contexte

Le critère d'évaluation C1 (`conception/referentiel_competences.md`) exige :

> Extraction faite depuis un mix d'au moins : service web (API REST), fichier
> de données, scraping, base de données, système big data.

Question posée en promo (Tony, 2026-07-28) : faut-il couvrir les cinq sources ?
Réponse d'Helena Vicente (OCC, référente certification) : *« Idéalement oui,
on a eu des fois des jurés qui n'ont pas apprécié quand les 5 sources ne sont
pas couvertes (d'autres jurés se montrent un peu plus indulgents, mais au cas
où, il est mieux de toutes les couvrir) »* — mais aussi : *« L'autre option
est d'en couvrir deux… mais justifier cela dans votre discours, en expliquant
que le projet ne le demande pas ».*

État réel de `app/ingestion/acquisition.py`, vérifié dans le code : **2
sources sur 5**.

- `fetch_api()` — service web (API REST Opquast)
- `scrape_rule()` — scraping (BeautifulSoup, champs `solution`/`controle` non
  exposés par l'API)
- Aucun fichier de données ingéré (le `.xlsx` du dictionnaire de données est
  de la documentation, pas une source lue par le pipeline)
- Aucune base de données comme *source* — PostgreSQL est la destination de
  l'ingestion, jamais une origine
- Aucun système big data — 245 lignes fixes, l'opposé d'un cas d'usage big
  data

Tony (même échange) : *« Ce qui va être compliqué c'est de ne pas tomber dans
"faire un truc juste pour cocher une case" ».*

## Options envisagées

**Ajouter artificiellement les 3 sources manquantes** — pour : filet de
sécurité face à un jury strict. Contre : aucun des trois besoins n'est réel
pour ce projet (référentiel fixe de 245 lignes, pas de fichier source, pas de
base externe, pas de volume big data) ; contredit directement la règle déjà
actée du projet (`CLAUDE.md` : *« ne pas élargir au-delà de ce qui valide les
compétences visées… proposer plus large est un risque, pas un service »*) ;
risque de sonner artificiel si un juré demande *pourquoi* un système big data
traite 245 lignes.

**Rester à 2 sources, sans rien dire** — pour : honnête, simple. Contre :
risque réel de pénalité signalé directement par Helena, sur retour d'expérience
de jurys passés.

**Rester à 2 sources réelles, justifiées explicitement à l'oral (retenu)** —
pour : cohérent avec la discipline déjà appliquée partout ailleurs dans le
projet (YAGNI, périmètre de certification) ; montre au jury une compréhension
du critère plutôt qu'un oubli — exactement ce qu'Helena recommande (*« c'est
bien que le jury voie que vous avez compris ce qu'on vous demande »*). Contre :
reste un pari sur l'indulgence du jury face à une formulation ambiguë (« un mix
d'au moins » — lue comme « 2 ou plus suffisent », pas nécessairement 5).

## Décision

**2 sources réelles (API REST + scraping), avec une justification préparée
pour la soutenance** — pas d'extension artificielle du pipeline d'acquisition.

Texte de discours prêt à l'emploi (rapport E1 ou oral) :

> Le référentiel Opquast est un jeu de données fixe et documenté (245 règles),
> acquis pour l'essentiel via l'API REST publique d'Opquast, complétée par du
> scraping ciblé pour deux champs (`solution`, `controle`) non exposés par
> l'API. Ce mix de deux sources couvre l'intégralité du besoin réel du projet :
> il n'existe aucun fichier de données externe à ingérer, aucune base de
> données tierce à extraire, et le volume (245 lignes) est à l'opposé d'un cas
> d'usage big data. Ajouter artificiellement l'une de ces trois sources aurait
> produit un traitement sans utilité réelle pour le produit, seulement pour
> élargir la liste — ce que la démarche spec-driven du projet écarte
> explicitement. Le choix assumé est donc de couvrir deux sources réelles et
> pertinentes plutôt que cinq dont trois seraient artificielles.

## Conséquences

- Reste un risque assumé, pas éliminé : un juré strict peut pénaliser malgré
  la justification — Helena elle-même ne garantit que l'indulgence n'est pas
  uniforme selon les jurys.
- **Reste ouvert** : si une évolution future et réelle du projet fait
  naturellement apparaître un besoin de fichier de données ou de base externe
  (ex. import d'un référentiel complémentaire depuis un export tiers), le
  documenter à ce moment — jamais forcé pour combler une case aujourd'hui.
- Cette décision ne concerne que C1 (Bloc 1, E1). Les autres compétences dont
  les critères listent des options multiples (« un mix de… ») mériteraient la
  même vérification avant la soutenance plutôt que d'être découvertes à
  l'oral.
- **Complément envisagé, si le temps le permet** : un ou plusieurs POC
  démontrant les 3 sources manquantes (fichier, base de données comme source,
  big data), **séparés du pipeline réel de QualiCheck** — pas intégrés à
  `app/ingestion/`, pas versionnés comme faisant partie du produit. Renforce
  le discours plutôt que de le contredire : montre au jury une maîtrise
  réelle de ces patterns, sans les avoir forcés artificiellement dans le
  projet. Piste notée dans `IDEA.md`, pas engagée — le temps de certification
  restant (13 week-ends environ) reste la contrainte dominante.
