# Mesurer avant d'ajouter des mécanismes de retrieval (US2)

2026-09-08 · retenu

## Contexte

US2 (question libre) est prévue en RAG sémantique pur — principe déjà acté
(`2026-07-25-rag-us2-petit-corpus.md`) mais dont la conception détaillée
n'existe pas encore.

Une conversation avec **Gemini** a produit une fiche d'architecture RAG
recommandant cinq mécanismes : *parent-child retrieval* (ne vectoriser que
`intitulé + objectifs + thématique + tags`), recherche **hybride** FTS +
pgvector fusionnée par **RRF**, **reformulation** de la requête par un LLM,
**décomposition en sous-requêtes**, et un RAG **multi-sources** typé par
`doc_type` pour accueillir l'écosystème Opquast (VPTCS, glossaire).

Le diagnostic de départ de la fiche : dilution sémantique (« smoothie
vectoriel ») et asymétrie entre une question courte et un chunk long,
normatif, contenant des instructions destinées au LLM.

Deux contraintes réelles encadrent la question. Le périmètre de
certification interdit d'élargir au-delà de ce qui valide les compétences
visées, avec un temps restreint. Et surtout : **le jeu d'acceptance existant
ne peut pas arbitrer ce débat**, ce qui rend toute décision « au fond »
indémontrable dans un sens comme dans l'autre.

## Ce que l'audit de la fiche a établi

La fiche a été confrontée au schéma réel et aux 245 règles en base avant
toute décision. Trois constats mesurés.

**Le mécanisme décrit est réel.** Le texte vectorisé fait ~1 620 caractères
en moyenne, dont 77 pour l'`intitulé` (~5 %) et 648 pour le `guide_analyse`
(~40 %). La dilution invoquée n'est pas une vue de l'esprit.

**Mais le remède proposé est auto-réfutant sur ces données.** Le vocabulaire
technique que la fiche veut capter ne vit pas dans les champs qu'elle
indexe :

| Terme | `intitule` | `solution` | `controle` | `guide_analyse` |
| --- | --- | --- | --- | --- |
| ARIA | **0** | 15 | 10 | **32** |
| `alt=` | **0** | 1 | 0 | 1 |
| 404 | 2 | 3 | 5 | 6 |
| cookie | 1 | 1 | 2 | 4 |

Le cas le plus net : « SIRET » n'apparaît **que** dans le `guide_analyse` de
la règle 106 — un cas du jeu d'acceptance qui passe aujourd'hui *grâce* au
champ que la fiche propose de retirer du vecteur. Et la contradiction est
interne à la fiche : elle justifie le FTS hybride par « capter les termes
exacts (`alt`, `ARIA`, `404`, `cookie`) » puis indexe ce FTS sur
`intitule, objectifs, tags`, où ces termes sont à zéro. Appliquée telle
quelle, elle **dégraderait** les requêtes qu'elle prétend réparer, sur les
deux voies à la fois.

**L'instrument de mesure ne voit pas le phénomène débattu.** Les 17 cas de
`tests/acceptance/rag_acceptance.jsonl` ont une cible unique, portent sur des
sujets disjoints, et 15 ou 16 sur 17 sont des paraphrases quasi directes de
l'intitulé (« Les vidéos comportent des sous-titres synchronisés » ← « Les
vidéos doivent-elles avoir des sous-titres ? »). Le 100 % obtenu à `top_n=3`
mesure donc un appariement paraphrase → intitulé sur 245 candidats : un
problème facile. Ni l'alerte de la fiche ni le score rassurant ne sont
falsifiables avec ce jeu.

Détail relevé au passage : `objectifs` n'est pas une colonne de `regle`
(tables `objectif` et `objectif_regle`), et `build_chunk_text()` ne les
reçoit pas. La proposition demande donc une jointure supplémentaire, pas une
modification de concaténation — signe qu'elle a été écrite sans le schéma.

## Options envisagées

**Appliquer la fiche** — pour : architecture RAG reconnue, qui répond à un
mécanisme réellement présent ; anticipe l'écosystème Opquast déjà envisagé
dans `IDEA.md`. Contre : réfutée par les mesures ci-dessus sur les données du
projet ; ajoute cinq sous-systèmes à une US non spécifiée, chacun avec ses
propres modes de défaillance ; et aucun ne serait démontrable comme une
amélioration, faute d'instrument. Devant un jury, « comment savez-vous que
c'est mieux ? » n'aurait pas de réponse.

**Écarter la fiche et ne rien faire** — pour : zéro travail, cohérent avec
YAGNI et le périmètre de certification. Contre : le mécanisme de dilution est
réel ; l'écarter sans mesure serait aussi arbitraire que l'appliquer sans
mesure. Et la question resterait sans trace, alors que c'est précisément ce
que ce dossier existe pour éviter.

**Construire d'abord l'instrument, puis n'ajouter que ce qu'un échec mesuré
justifie (retenu)** — pour : le jeu d'acceptance durci est de toute façon
nécessaire, et l'écrire revient à spécifier le comportement attendu d'US2 en
BDD (que citer, que refuser, quand dire « je ne sais pas ») — donc ce n'est
pas de l'outillage, c'est le chemin critique ; chaque mécanisme devient
falsifiable ; et l'ordre d'intervention part du moins cher. Contre : retarde
toute amélioration éventuelle du rappel ; demande le jugement métier de David
pour rédiger les cas durs, donc ne peut pas être délégué entièrement.

## Décision

**Ne pas ajouter de mécanisme de retrieval avant que le jeu d'acceptance
puisse mesurer son apport.** Concrètement :

1. **La variante proposée est écartée sur mesure**, pas par principe :
   vectoriser `intitulé + objectifs + thématique + tags` et indexer le FTS
   sur ces mêmes champs retire le vocabulaire que ces champs ne contiennent
   pas.
2. **L'hybride reste ouvert** *en général*, avec une condition de réouverture
   testable : si le jeu d'acceptance étendu montre un rappel insuffisant sur
   la famille « termes exacts » (ARIA, SIRET, `alt=`), le FTS devient le
   premier candidat — indexé sur le **texte complet** de la règle, jamais sur
   `intitule/objectifs/tags`.
3. **Ordre d'intervention en cas d'échec mesuré**, en s'arrêtant dès que ça
   passe : augmenter `top_n` (paramètre de `manifest.yml`, zéro code) →
   comparer les variantes de chunk (complet / sans `guide_analyse` /
   intitulé+tags, à 0,0016 € la variante) → FTS hybride en dernier recours.
4. **Ne pas construire** : RRF, décomposition en sous-requêtes, HyDE,
   reformulation LLM, `doc_type`/écosystème VPTCS. Ce dernier reste dans
   `IDEA.md` : c'est un projet d'acquisition de corpus (sources, droits,
   chunking d'une autre nature), hors périmètre de certification.

Critère qui a tranché : **un mécanisme dont on ne peut pas mesurer l'apport
n'est pas une amélioration, c'est un pari.** L'instrument manquait ; le
construire coûte quelques centimes et sert de toute façon à spécifier US2.

## Conséquences

- **Le jeu d'acceptance doit être étendu à quatre familles** : vocabulaire
  vivant uniquement dans `guide_analyse`/`controle` ; questions multi-sujets
  (seul vrai cas d'usage de la décomposition) ; questions méthodologiques sans
  réponse dans le corpus, qui testent le « je ne sais pas » honnête ; règles
  voisines concurrentes, qui testent la précision — jamais mesurée par un
  `recall@3` à cible unique.
- **Son format doit évoluer** : `{question, numero_regle_attendue}` ne sait
  exprimer ni plusieurs cibles acceptables, ni « aucune réponse attendue ».
- **Une piste que la fiche n'envisage pas** : augmenter `top_n`. La décision
  du 2026-07-25 opposait 3 chunks à 245 ; l'espace entre les deux n'a jamais
  été exploré, alors qu'à 245 règles un `top_n` de 10 à 15 coûte ~5-8 k tokens
  par question, sans aucune pièce mobile supplémentaire.
- **La source est nommée, délibérément.** La proposition vient d'une
  conversation avec Gemini, auditée contre le schéma et les données réelles,
  et partiellement réfutée par cet audit. Pour une certification en IA
  agentique, avoir confronté une recommandation d'IA à ses propres données
  plutôt que de l'appliquer est la compétence attendue — le masquer
  affaiblirait le dossier au lieu de le protéger.
- **Limite assumée** : même étendu à une trentaine de cas, le jeu reste petit.
  Il borne le risque, il ne le supprime pas. Le rappel imparfait du RAG était
  déjà assumé par la décision du 2026-07-25 et le reste.
- **Cette décision ne remet pas en cause le principe du RAG**
  (`2026-07-25-rag-us2-petit-corpus.md`) : elle porte sur les mécanismes, pas
  sur l'architecture de récupération elle-même.
- **Articulation avec la scission des bases**
  (`2026-09-08-deux-bases-referentiel-audit.md`) : les mesures des étapes 3
  et 4 continuent d'interroger pgvector en SQL direct. C'est l'instrument de
  mesure, pas le chemin de production — lequel passera par `GET /dense`. Les
  deux ne doivent pas être confondus.
- **Reste ouvert** : la conception détaillée d'US2 elle-même. Les cas
  d'acceptance durs en sont l'amorce, pas le remplacement.
