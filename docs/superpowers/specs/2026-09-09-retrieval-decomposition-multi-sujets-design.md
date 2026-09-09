# Décomposition LLM des questions multi-sujets — design

2026-09-09 · carte Kanboard #10

## Contexte

`jury/decisions/2026-09-09-recommandations-suite-mesure-retrieval.md`
(recommandation 3) : 2 cas sur 4 de la famille `multi_sujets` échouent
structurellement, quel que soit `top_n` (mesuré jusqu'à 15) — un sujet
écrase complètement l'autre dans l'espace vectoriel. C'est la seule
famille du jeu d'acceptance (71 cas) où le même défaut se reproduit sur
plusieurs cas, pas un échec isolé.

Portée : brique retrieval isolable, ne dépend pas de la spec complète
d'US2 (agent conversationnel, guardrails, mémoire — encore non conçus,
`conception/3_autre_us/us2_question_libre/`).

## Objectif

Une question qui porte sur plusieurs sujets distincts (ex. « quelles infos
légales afficher, et comment sous-titrer mes vidéos ? ») doit retrouver
les règles des **deux** sujets, pas seulement celui qui domine dans
l'espace vectoriel.

## Hors périmètre (décidé le 2026-09-09)

- **Agent ReAct avec tool de recherche** : écarté. La fusion (union simple)
  et le nombre de recherches (une par sous-question) sont déjà des
  décisions fixées en code déterministe — un agent devrait re-décider ces
  points lui-même à l'exécution, ce qui réintroduit un mécanisme non
  mesuré et rend l'acceptance non déterministe à tester.
- **RRF ou tout autre scoring de fusion pondéré** : écarté depuis le
  2026-09-09 (recommandation 3), union simple uniquement.
- **Plafond après fusion** (ex. replafonner à `top_n` après union) : écarté
  — chaque sous-question a déjà son propre filtre qualité (`top_n=15`,
  seuil déjà mesuré) ; replafonner réintroduirait une éviction qu'on vient
  d'éviter en décomposant.
- **Déplacer `query_top_n_numeros()`** hors de
  `app/ingestion/rag_acceptance.py` vers `app/retrieval/` : envisagé (la
  fonction est conceptuellement du retrieval, pas de l'ingestion) mais
  écarté par défaut — préférence projet « modifier peu > refactoriser
  beaucoup ». Réutilisée par import, sans déplacement.

## Architecture

```text
app/retrieval/
├── __init__.py
├── decomposition.py            # appel LLM (gpt-5.4-mini) : question → sous-questions
├── retrieval.py                 # orchestration : décompose → embed → pgvector → union
└── prompts/
    └── decompose_question.md    # prompt + few-shot Opquast
```

Premier module du futur système retrieval, construit en avance de la
conception API complète — même statut que `check_rag_acceptance.py`/
`rag_dense_acceptance.py` (scripts déjà isolables du reste d'US2).

Diagramme : `conception/3_autre_us/us2_question_libre/diagramme_decomposition_multi_sujets.drawio`
— rangé avec les autres diagrammes US2 (`diagramme_activite_us2.drawio`,
`cas_utilisation_us2.drawio`), c'est de la conception, pas un artefact
jetable de brainstorming.

## Composants

### `decomposition.py`

```python
class DecompositionOutput(BaseModel):
    sous_questions: list[str]

class DecompositionClient:
    def __init__(self):
        # manifest.yml, rôle "decomposition" (gpt-5.4-mini, nouveau rôle —
        # modèle et tarif distincts du rôle "enrichissement")
        ...

    def decomposer(self, question: str) -> list[str]:
        """Découpe une question en sous-questions (1 élément si mono-sujet).

        Retry 3 tentatives (tenacity, backoff 2s/4s/8s — règle non
        négociable du projet). Fail-open après échec final : retombe sur
        [question] telle quelle plutôt que de faire échouer toute la
        réponse à l'utilisateur.
        """
```

Timeout explicite : **2s** (paramètre `timeout` du client `ChatOpenAI`),
volontairement différent du rôle `enrichissement` (aucun timeout explicite
aujourd'hui, appels batch offline où personne n'attend) et du 30s
recommandé par le benchmark (`conception/annexes/F_choix_llm.md`), qui
suppose lui aussi un contexte batch. Ici, un utilisateur attend une
réponse en direct (US2), et la décomposition n'est qu'une étape parmi
d'autres avant la réponse finale (embedding, pgvector, puis un futur appel
LLM de génération de réponse, pas encore construit) : elle doit occuper le
moins de budget possible sur le temps de réponse total. Pas de repère
chiffré existant pour ce cas d'usage interactif — valeur choisie, à
corriger avec une vraie mesure de latence une fois le mécanisme construit.

Le nombre de sous-questions (N) est décidé par le LLM au cas par cas, pas
fixé à l'avance — la famille `multi_sujets` du jeu d'acceptance ne
contient que des exemples à 2 sujets, mais le mécanisme doit rester
généralisable à N.

### `retrieval.py`

```python
def retrieve(
    session: Session,
    question: str,
    top_n: int,
    decomposition_client: DecompositionClient,
    embedding_client: EmbeddingClient,
) -> list[int]:
    """Retrouve les numéros de règle pertinents pour une question.

    1. Décompose la question (1..N sous-questions).
    2. Vectorise toutes les sous-questions en un seul appel embed_batch.
    3. Une requête pgvector top_n par sous-question (réutilise
       app.ingestion.rag_acceptance.query_top_n_numeros par import).
    4. Union des numéros, dédoublonnés, ordre de première apparition.
       Pas de plafond après fusion : la taille du résultat varie selon N.
    """
```

`decomposition_client` et `embedding_client` sont injectés (pas construits
à l'intérieur de `retrieve()`) pour que l'appelant partage un seul client
sur plusieurs appels — nécessaire au suivi de coût cumulé
(`EmbeddingClient.total_tokens` s'accumule via `+=` à travers plusieurs
`embed_batch()`, cf. `app/ingestion/embedding.py`), même pattern que
`check_rag_acceptance.py` aujourd'hui.

### Prompt (`decompose_question.md`)

Informé du corpus (référentiel de 245 règles de qualité web, une règle =
un sujet), avec 2-3 exemples few-shot tirés du jeu d'acceptance réel :

- « Sur mobile, faut-il des boutons assez grands et laisser l'utilisateur
  agrandir la page ? » → 2 sous-questions (règles 186 et 193 distinctes).
- « Chaque image porteuse d'information est-elle dotée d'une alternative
  textuelle appropriée ? » → 1 seule sous-question malgré plusieurs
  notions mentionnées (une seule règle cible).

Sans ce calibrage, risque de découper trop fin (chaque notion mentionnée)
ou d'ignorer un vrai deuxième sujet — exactement le risque de régression
identifié sur les 56 cas mono-sujet du jeu d'acceptance.

## Configuration (`manifest.yml`)

Nouveau rôle, modèle et tarif distincts du rôle `enrichissement` (`kimi-k2.6`) :

```yaml
decomposition:
  modele: gpt-5.4-mini
  env_var: AZURE_MODEL_GPT_MINI
  prix_entree_par_million: <à documenter à l'implémentation>
  prix_sortie_par_million: <à documenter à l'implémentation>
```

## Gestion d'erreur

Après 3 tentatives échouées (timeout, JSON malformé) : **fail-open**,
`decomposer()` retombe sur `[question]` — la question est alors traitée
comme mono-sujet (comportement actuel, sans décomposition). Choisi plutôt
que fail-closed : dans un produit interactif (US2), faire échouer toute
la réponse à l'utilisateur pour un problème de décomposition est
disproportionné.

## Intégration à la mesure existante

`scripts/check_rag_acceptance.py` bascule entièrement sur `retrieve()`
pour les 71 cas / 7 familles — devient de fait un test de non-régression
grandeur nature : vérifie que le mécanisme ne découpe pas à tort les 56
cas mono-sujet (`paraphrase_intitule`, `vocabulaire_*`,
`regles_concurrentes`), pas seulement qu'il améliore `multi_sujets`.

Changement de structure : le script ne peut plus vectoriser toutes les
questions en un seul `embed_batch()` upfront (l'ancien pattern), puisque
les sous-questions ne sont connues qu'après décomposition de chaque
question individuellement. Le `embedding_client` reste partagé sur toute
la boucle pour garder un total de coût cumulé exact.

## Tests

- **Unitaires** (`decomposition.py`) : LLM mocké — question mono-sujet
  retourne `[question]`, question multi-sujets retourne N sous-questions,
  exception après 3 tentatives retombe sur `[question]` (fail-open).
- **Unitaires** (`retrieval.py`) : `decomposition_client`/`embedding_client`/
  `session` mockés — vérifie l'union/dédoublonnage, l'ordre de première
  apparition, l'absence de plafond.
- **Acceptance** : `make rag-acceptance` (71 cas existants, coût réel,
  hors CI) — aucun nouveau cas nécessaire dans l'immédiat, le jeu actuel
  suffit à mesurer régression et amélioration.
