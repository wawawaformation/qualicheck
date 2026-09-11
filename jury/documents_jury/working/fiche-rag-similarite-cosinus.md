# Fiche — Score de similarité cosinus (RAG) : pourquoi un score bas n'est pas grave, et ce qu'il reste à faire

Support de compréhension personnelle, pas de restitution jury. Répond à la
question « est-ce grave d'avoir des cos bas lors du retrieval ? ». Sources :
[app/retrieval/retrieval.py](../../../app/retrieval/retrieval.py),
[app/ingestion/rag_acceptance.py](../../../app/ingestion/rag_acceptance.py),
`app/ingestion/manifest.yml` (section `rag_acceptance`).

## 1. Ce que le cosinus fait réellement dans QualiCheck

`query_top_n_numeros()` (`rag_acceptance.py`) trie les 245 règles par
distance cosinus et garde les `top_n` premières :

```python
session.query(Regle.numero)
    .order_by(Regle.embedding.cosine_distance(vector))
    .limit(top_n)
```

C'est un **classement**, pas un **filtrage**. La valeur absolue du cosinus
n'est lue nulle part dans le pipeline — aucun seuil du type « si cos < X,
écarter ». Que le premier résultat soit à 0.62 ou à 0.31 ne change rien au
résultat retourné : les `top_n` (15 actuellement, `manifest.yml`) sortent
de toute façon.

## 2. Pourquoi un score bas n'est pas un problème en soi

Trois raisons structurelles, indépendantes de la qualité du retrieval :

1. **Le modèle d'embedding.** La valeur absolue du cosinus n'est comparable
   qu'à l'intérieur d'un même modèle. `text-embedding-3-small` (Azure,
   rôle `embedding` du manifeste) donne une distribution plus étalée et
   plus basse qu'un modèle comme `ada-002`, qui tassait tout entre 0.75 et
   0.85 — rassurant mais peu discriminant.
2. **L'asymétrie question / chunk.** Une question courte est comparée à un
   chunk enrichi de 300-500 tokens (`build_chunk_text()`,
   `app/ingestion/chunking.py` : intitulé + thème + objectifs + guide
   d'analyse). Deux textes de densité sémantique très différente ne
   peuvent pas produire un cosinus élevé, même sur une correspondance
   parfaite.
3. **L'homogénéité du corpus.** 245 règles qui parlent toutes de qualité
   web tassent l'échelle : tout se ressemble un peu, donc rien ne monte
   très haut.

## 3. Ce qui compte à la place : le contraste, pas le niveau

La seule lecture qui porte du signal, c'est l'écart entre le pertinent et
le bruit :

| Situation | Diagnostic |
|---|---|
| top-1 à 0.45, top-15 à 0.28 | bon — signal net malgré des valeurs basses |
| top-1 à 0.82, top-15 à 0.80 | mauvais — aucune discrimination malgré des valeurs hautes |

La vraie mesure de qualité du projet ne dépend pas de ça : ce sont les
99 cas d'acceptance (`tests/acceptance/rag_acceptance.jsonl`), verdict
PASS/FAIL/PARTIEL sur les numéros de règle effectivement retrouvés — une
mesure de bout en bout, indépendante de la valeur du cosinus.

## 4. Ce que ça implique : le retrieval n'est pas fini

Le score cosinus redevient un problème réel le jour où on veut lire une
information dans sa valeur, pas seulement dans son rang. Deux chantiers
identifiés, ouverts :

### 4.1 Le refus (dire « aucune règle Opquast ne correspond »)

Aujourd'hui `retrieve()` retourne toujours des règles, même hors sujet —
`rag_acceptance.py` le documente explicitement : un cas sans cible
attendue (famille `sans_reponse`) est toujours `FAIL`, faute de mécanisme
de refus.

Un seuil absolu de cosinus (« refuser si `cos_max` < X ») est **difficile
à calibrer précisément à cause de ce que montre cette fiche** : les scores
sont bas et peu contrastés par construction (§2-3), donc la marge entre
« question hors sujet » et « question pertinente mais formulée
différemment » est étroite. Deux pistes, non tranchées :

- un seuil **relatif** (écart top-1 / top-N, plutôt qu'une valeur absolue) ;
- un jugement du LLM de réponse sur la pertinence des chunks retournés —
  pas de seuil vectoriel du tout, coût d'un appel en plus.

### 4.2 Combien de règles retourner dans la réponse

`top_n=15` (`manifest.yml`) est le paramètre du **pool de candidats**
interrogé par `retrieve()` — pas nécessairement le nombre de règles à
citer dans une réponse en langage naturel à l'utilisateur final. Reste à
décider : le nombre cité doit-il être fixe, dépendre du nombre de
sous-questions détectées par la décomposition, ou être laissé au jugement
du LLM de réponse à partir du pool de 15 ?

Ces deux points sont ouverts, pas de décision prise — voir `TODO.md`
(section « Retrieval US2 ») pour le suivi.
