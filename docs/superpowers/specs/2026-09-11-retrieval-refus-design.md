# Mécanisme de refus du retrieval — design

2026-09-11 · carte Kanboard #17

## Contexte

`rag_acceptance.py::evaluate_case()` traite aujourd'hui tout cas
`sans_reponse` (aucune règle attendue) comme **toujours FAIL** : aucun
mécanisme de refus n'existe dans `retrieve()`, qui retourne systématiquement
`top_n` candidats même quand aucun n'est réellement pertinent.

Explication détaillée de pourquoi un score cosinus bas n'est en soi pas un
problème (classement, jamais un filtre lu à ce jour) :
`jury/documents_jury/working/fiche-rag-similarite-cosinus.md`. Cette fiche
identifie ce chantier comme l'un des deux points ouverts avant de
considérer le retrieval terminé — l'autre (combien de règles citer dans
une réponse) est un chantier séparé, hors périmètre ici (voir plus bas).

## Objectif

Quand aucune règle Opquast ne répond réellement à la question posée,
`/regles/dense` doit retourner une liste vide plutôt que `top_n` candidats
hors sujet.

## Hors périmètre

- **Décider où poser le refus dans l'agent US2** : écarté. US2 (agent
  conversationnel) n'est pas encore conçu
  (`conception/3_autre_us/us2_question_libre/`). Le refus se décide dans
  `/regles/dense` (couche API données), cohérent avec le fait qu'un LLM
  (décomposition) y tourne déjà depuis le chantier du 2026-09-09 — pas
  besoin d'attendre l'agent pour statuer.
- **Combien de règles citer dans une réponse** (le second point ouvert de
  la fiche cosinus) : chantier distinct, carte Kanboard séparée à créer
  quand celui-ci sera terminé.
- **Reranker, RRF, HyDE** : déjà écartés par les décisions du
  2026-09-08/09 (`jury/decisions/`), rien ici ne rouvre ces mécanismes.

## Plan en deux temps : mesurer, puis construire selon le résultat

Même méthode que le reste du chantier retrieval (`jury/decisions/
2026-09-08-mesurer-avant-mecanismes-retrieval.md`) : le mécanisme de
détection n'est pas choisi à la table, il est tranché par une mesure.

### Temps 1 — Mesure (déterministe, toujours exécutée)

1. **Étoffer `sans_reponse`** dans `tests/acceptance/rag_acceptance.jsonl`
   (5 cas aujourd'hui → ~20), 3 catégories :
   - hors-domaine total (cuisine, sport, météo...) ;
   - domaine proche mais hors périmètre Opquast (méthode agile, tarifs,
     recrutement, choix techno — déjà entamé par les 5 cas actuels) ;
   - vocabulaire Opquast détourné (termes du champ lexical qualité
     web/accessibilité, mais question trop générale ou hors des 245
     règles, ex. « qu'est-ce que le RGAA ? »).
   Méthode : proposition de questions, validation de David avant ajout au
   jeu (même pattern que les vocabulaires précédents).
2. **Faire remonter le score de similarité jusqu'à `retrieve()`** (voir
   Architecture) — nécessaire à la mesure et réutilisable ensuite par
   l'agent US2.
3. **Script de mesure** (`scripts/mesure_scores_refus.py`) : pour chaque
   cas (99 existants + `sans_reponse` étoffé), calcule deux métriques —
   score du top-1 (valeur absolue, comparable ici : même modèle
   `text-embedding-3-small`, même corpus) et écart top-1/top-15 (le
   contraste). Rapport dans `docs/eval/` (même convention que les
   rapports RAG existants), comparant les distributions `sans_reponse`
   vs cas `PASS`.

### Temps 2 — Construction, conditionnelle au résultat

**Critère de bascule** : si l'une des deux métriques sépare nettement les
deux groupes (peu ou pas de chevauchement), seuil retenu sur cette
métrique. Si chevauchement significatif sur les deux, bascule vers le
jugement LLM.

- **Si seuil séparable** : la valeur rejoint `manifest.yml` (jamais de
  constante en dur), `retrieve()` l'applique après l'union
  multi-sous-questions et retourne `[]` si rien ne passe.
- **Si pas séparable** : un client LLM de jugement (`app/retrieval/`,
  même style que `decomposition.py`) reçoit question + candidats et
  tranche pertinent/non-pertinent — retry 3 tentatives avec backoff
  (règle non négociable du projet), coût par appel à chiffrer avant
  généralisation.

Le plan d'implémentation (à écrire après validation de cette spec)
couvrira le Temps 1 en totalité, puis une seule des deux branches du
Temps 2 selon le résultat mesuré — même logique que « Étape 4.2/4.3» du
chantier `top_n` (`TODO.md`) : on s'arrête dès qu'un mécanisme mesuré
suffit.

## Architecture

`query_top_n_numeros()` (`app/ingestion/rag_acceptance.py`, réutilisée par
import depuis `app/retrieval/`) change de signature : retourne
`list[tuple[int, float]]` (numéro, score de similarité) au lieu de
`list[int]`. Score exposé en similarité (`1 - cosine_distance`, 1 =
identique, 0 = aucun rapport) plutôt qu'en distance brute, pour rester
lisible.

`retrieve()` (`app/retrieval/retrieval.py`) change en conséquence :

```python
def retrieve(
    session: Session,
    question: str,
    top_n: int,
    decomposition_client: DecompositionClient,
    embedding_client: EmbeddingClient,
) -> list[tuple[int, float]]:
    """... Retourne [] si aucun candidat ne passe le critère de refus."""
```

- Union entre sous-questions : si un même numéro ressort de plusieurs
  sous-questions avec des scores différents, on garde le **meilleur**
  score (le plus similaire), pas le premier trouvé par ordre
  d'apparition (comportement actuel pour le dédoublonnage simple).
- Le critère de refus (seuil ou jugement LLM, Temps 2) s'applique après
  cette union, en dernière étape de `retrieve()`.

Contrat HTTP de `/regles/dense` (`app/api_regles/regles.py`) : le schéma
de réponse change de `list[RegleRead]` à un schéma qui embarque le score
par règle (ex. `list[RegleAvecScore]`, `{regle: RegleRead, score: float}`)
— changement de contrat public, impacte tout consommateur déjà existant de
l'endpoint. En cas de refus : réponse `[]`, HTTP 200 (pas de champ dédié
ni de code HTTP spécifique — contrat le plus simple, cohérent avec la
forme actuelle).

## Impact sur la mesure existante

`evaluate_case()` (`rag_acceptance.py`) change de règle : un cas
`sans_reponse` devient **PASS** si `retrieve()` retourne `[]`, FAIL sinon
(au lieu de toujours FAIL aujourd'hui).

`scripts/check_rag_acceptance.py` et `scripts/rag_dense_acceptance.py`
s'adaptent à la nouvelle signature de `retrieve()`/`query_top_n_numeros()`
(score en plus du numéro) : `evaluate_case()` garde une signature en
`list[int]` (elle ne juge que des numéros, pas des scores) — c'est
l'appelant qui extrait les numéros des tuples `(numero, score)` avant de
les lui passer.

## Non-régression

Point de vigilance spécifique, à isoler dans le rapport plutôt que noyé
dans un taux global : un **faux refus** sur les 99 cas existants (une
vraie question qui se fait refuser à tort) est une régression plus grave
qu'un taux qui baisse d'un point sur une famille secondaire.

## Tests

- **Unitaires** (`rag_acceptance.py::query_top_n_numeros`) : vérifie le
  retour `(numero, score)` et l'ordre par score décroissant.
- **Unitaires** (`retrieval.py::retrieve`) : session/clients mockés —
  vérifie l'union avec conservation du meilleur score en cas de doublon,
  et le retour `[]` quand le critère de refus est franchi (mécanisme
  mocké, indépendant du choix seuil/LLM).
- **Unitaires** (`evaluate_case`) : cas `sans_reponse` avec `retrieve()`
  retournant `[]` → PASS ; retournant des candidats → FAIL.
- **Acceptance** : `make rag-acceptance` / `make rag-dense-acceptance`
  rejoués sur les 99 cas + `sans_reponse` étoffé (coût réel, hors CI) —
  vérifie l'absence de faux refus sur les 99 cas existants en plus du
  taux de réussite sur `sans_reponse`.

## Traçage

`CHANGELOG.md` à la clôture de chaque temps ; fiche
`jury/documents_jury/working/fiche-rag-similarite-cosinus.md` mise à jour
avec le résultat mesuré (Temps 1) et le mécanisme retenu (Temps 2) ; case
correspondante cochée dans `TODO.md` (section « Retrieval US2 »).
