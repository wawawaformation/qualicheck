# Mécanisme de refus — Temps 2 (jugement LLM) — design

2026-09-11

## Contexte

Le Temps 1 (`docs/superpowers/specs/2026-09-11-retrieval-refus-design.md`,
exécuté) a mesuré qu'**aucun seuil de score cosinus** (absolu ou relatif —
top1, top15, écart top1/top15) ne sépare proprement les cas `sans_reponse`
des cas `PASS` sur les 114 cas d'acceptance : le meilleur seuil relatif
classerait à tort 16/91 cas valides (17,6 %) comme refus. Détail :
`docs/eval/mesure_scores_refus_2026-09-11_075738.md`,
`jury/documents_jury/working/fiche-rag-similarite-cosinus.md` §4.1.

Le protocole de mesure des chunks (vagues 1-3, conclu — chunk de
production conservé) confirme par ailleurs que la représentation
vectorielle ne va pas changer, ce qui débloque ce chantier (l'ordre
« mesure des chunks avant Temps 2 » était acté pour cette raison précise).

**Seule branche restante** : un jugement du LLM sur le contenu réel des
candidats retournés, plutôt qu'un seuil sur leur score. Cadrage de
conception mené avec David (2026-09-11), repris ici tel quel :

- Le mécanisme reste strictement dans le périmètre d'`api_regles` (l'outil
  de retrieval) — pas la couche agent de niveau supérieur (mémoire,
  historique de discussion, choix d'outils), hors périmètre, à concevoir
  séparément plus tard. Diagramme de référence :
  `conception/3_autre_us/us2_question_libre/diagramme_retrieval_refus_citation.drawio`.
- Un seul appel LLM fait le travail : celui qui juge la pertinence des
  candidats déjà retournés par `retrieve()` — pas un mécanisme séparé.
- Sortie : **liste plate**, pas de classement ni de score de pertinence.
  Décidé explicitement : aucun besoin de classement n'a été mesuré, et le
  cosinus est disqualifié pour ça (démontré à plusieurs reprises — score
  bas pas grave, seuil de refus impossible, écart qui varie d'un run à
  l'autre). Inventer un classement maintenant serait construire sur un
  besoin non mesuré.
- Une liste vide (`200 + []`) doit être non ambiguë : elle ne doit
  signifier qu'une chose, un refus explicite du jugement — jamais une
  panne technique déguisée. Le statut HTTP (`200` vs `503`) suffit à
  lever l'ambiguïté (voir « Résilience » ci-dessous) ; pas de champ
  supplémentaire dans le corps de la réponse.

## Objectif

Remplacer le retour brut de `POST /regles/dense` (tous les candidats du
pool, y compris hors sujet) par un retour **filtré par jugement LLM** :
citer les règles qui répondent réellement à la question, ou `[]` si
aucune ne répond.

## Hors périmètre

- La couche agent (mémoire de discussion, orchestration multi-outils,
  choix entre plusieurs outils) — voir le diagramme de référence, hors
  du rectangle « outil ».
- Un classement ou score de pertinence dans la réponse — voir ci-dessus.
- Une éventuelle limite du **nombre** de règles citées : aucune limite
  n'est imposée au-delà du pool déjà borné par `top_n=15` — le jugement
  peut retenir de 0 à 15 règles.
- Modifier `retrieve()` (`app/retrieval/retrieval.py`) : inchangé, le
  jugement s'insère **après**, dans l'endpoint.

## Architecture

### Nouveau composant : `JugementClient`

`app/retrieval/jugement.py`, même patron que `DecompositionClient`
(`app/retrieval/decomposition.py`) : client Azure OpenAI via
`langchain_openai.ChatOpenAI`, sortie structurée via
`JsonOutputParser(pydantic_object=...)`, retry `tenacity` (3 tentatives,
backoff exponentiel 2s/4s/8s), fail-open après échec.

```python
class JugementOutput(BaseModel):
    numeros_pertinents: list[int]


class JugementClient:
    def juger(self, question: str, candidats: list[RegleRead]) -> list[int]:
        """Juge lesquels des candidats répondent vraiment à la question.
        Retourne les numéros pertinents (liste vide si aucun)."""
```

- **Entrée** : la question originale + le texte complet de chaque
  candidat (`build_chunk_text(candidat)`, déjà existant — `RegleRead`
  porte les mêmes attributs qu'`EnrichedRule` : `intitule`, `theme`,
  `contexte`, `solution`, `controle`, `guide_analyse`, `objectifs`,
  `tags`, `phases`).
- **Sortie** : `numeros_pertinents: list[int]`, un sous-ensemble des
  numéros candidats (jamais un numéro hors du pool fourni — un numéro
  halluciné par le LLM hors de ce pool est filtré silencieusement avant
  retour, garde-fou contre une hallucination de numéro).
- **Modèle** : `gpt-5.4-mini`, même rôle/modèle que la décomposition
  (déjà configuré, rapide, sortie structurée) — nouveau rôle `jugement`
  dans `manifest.yml` :

```yaml
jugement:
  modele: gpt-5.4-mini
  env_var: AZURE_MODEL_GPT_MINI
  prix_entree_par_million: 0.15
  prix_sortie_par_million: 0.60
```

- **Prompt** : `app/retrieval/prompts/juger_pertinence.md`, même
  structure que `decompose_question.md` (rôle, tâche, gabarit de sortie
  JSON strict, placeholders `{question}`/`{candidats}`).

### Intégration dans `POST /regles/dense` (modifié en place)

`app/api_regles/regles.py::chercher_regles_dense` — après le chargement
et tri existants de `regles_triees: list[RegleRead]` (code inchangé
jusque-là), ajouter :

```python
jugement_client = JugementClient()
numeros_pertinents = set(jugement_client.juger(requete.question, regles_triees))
regles_retenues = [r for r in regles_triees if r.numero in numeros_pertinents]

return [RegleAvecScore(regle=r, score=scores[r.numero]) for r in regles_retenues]
```

Le contrat de réponse (`response_model=list[RegleAvecScore]`) ne change
pas de forme — chaque règle retournée garde son score cosinus d'origine
(information annexe, plus la source de vérité de la pertinence). Seule
la **liste** change : filtrée par le jugement plutôt que le pool brut.

### Résilience

Même convention que `DecompositionClient` (fail-open) :
`JugementClient.juger()` ne lève jamais d'exception vers l'appelant —
après 3 échecs (timeout, JSON malformé), elle retombe sur **tous les
candidats non filtrés** (comportement actuel du endpoint). Une panne
technique du jugement ne doit jamais se traduire par un refus par
accident.

Conséquence pour l'ambiguïté du corps de réponse (voir Contexte) :
`200 + []` ne peut arriver que par un jugement explicite (aucun
candidat retenu) ; toute panne technique (recherche vectorielle,
décomposition, ou jugement après ses 3 tentatives internes) reste
distincte — soit elle remonte en `503` (panne de `retrieve()`, déjà
gérée), soit elle dégrade silencieusement vers le comportement actuel
(fail-open du jugement, jamais vers `[]`).

## Critère d'acceptation

`is_acceptable()` (`app/ingestion/rag_acceptance.py`) n'exclut plus la
famille `sans_reponse` de son calcul — elle doit désormais atteindre le
même seuil garde-fou (`taux_reussite_minimum`, 90 %) que les familles à
cible. C'est la première fois que cette famille est réellement
testable : jusqu'ici `FAIL` par construction, faute de mécanisme.

## Tests

- **Unitaire** (`JugementClient`, mocké) : réponse JSON valide → filtre
  correctement ; numéro hors pool halluciné → filtré silencieusement ;
  échec après 3 tentatives → fail-open (tous les candidats).
- **Unitaire** (endpoint, `JugementClient` mocké) : mêmes conventions que
  les tests existants de `chercher_regles_dense` (`DecompositionClient`/
  `EmbeddingClient` déjà mockés) — ajouter le mock de `JugementClient`,
  vérifier le filtrage de la liste retournée.
- **Intégration** (`tests/integration/api_regles/test_regles_dense.py`,
  existant) : à adapter — le contrat retourné change (liste filtrée, pas
  brute). Les tests existants qui vérifient le pool brut complet doivent
  être ajustés pour mocker aussi `JugementClient`.
- **Acceptance réelle** (`scripts/check_api_regles_dense_acceptance.py`,
  existant, coût réel, hors CI) : rejoue les 114 cas via `POST
  /regles/dense` en HTTP réel — **c'est la mesure de décision** de ce
  chantier. `is_acceptable()` désormais avec `sans_reponse` inclus.

## Budget

Coût réel par question en production : décomposition (déjà existant) +
1 appel `gpt-5.4-mini` de jugement (nouveau), texte d'entrée = jusqu'à 15
chunks complets (~1600 caractères chacun au pire cas) + la question.
Ordre de grandeur comparable à la décomposition. Confirmation du coût
réel de l'exécution des 114 cas d'acceptance avec David avant de lancer
`make api-regles-dense-acceptance` (nécessite l'API démarrée,
`make api-regles`).

## Traçage

`CHANGELOG.md` à l'exécution ; `TODO.md` (Temps 2 passé de `[ ]` à `[x]`
ou reformulé selon le résultat de la mesure d'acceptance) ; mémoire
assistant si le résultat diffère de l'attendu.
