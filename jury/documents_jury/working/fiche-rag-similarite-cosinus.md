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
différemment » est étroite. Deux pistes envisagées :

- un seuil **relatif** (écart top-1 / top-N, plutôt qu'une valeur absolue) ;
- un jugement du LLM de réponse sur la pertinence des chunks retournés —
  pas de seuil vectoriel du tout, coût d'un appel en plus.

**Tranché par la mesure (2026-09-11)** : `scripts/mesure_scores_refus.py`
(`docs/superpowers/plans/2026-09-11-retrieval-refus-implementation.md`,
Temps 1) a rejoué les 114 cas d'acceptance (dont 20 `sans_reponse`,
étoffé de 5 à 20 pour ce chantier — voir `docs/eval/
mesure_scores_refus_2026-09-11_075738.md`). Résultat : **aucune des
métriques mesurées (top-1, top-15, écart top-1/top-15) ne sépare
proprement `sans_reponse` des cas `PASS`** :

- top-1 : `sans_reponse` [0.190–0.534] vs `PASS` [0.406–0.740] — 8 cas de
  chaque groupe se chevauchent entre 0.406 et 0.534.
- écart top-1/top-15, pourtant la métrique la plus prometteuse a priori :
  un seuil calé pour capturer les 20 cas `sans_reponse` (≤0.079)
  classerait à tort **16 des 91 cas `PASS` (17,6 %) comme refus** — bien
  au-delà de ce qu'un faux refus tolérable permet (la spec identifie le
  faux refus comme la régression la plus grave à surveiller, plus grave
  qu'un taux qui baisse d'un point).

**Conséquence** : le seuil relatif est écarté, **pas par principe mais par
mesure** — la voie retenue pour la suite (Temps 2) est le jugement LLM sur
les chunks retournés. Cohérent avec la méthode déjà établie sur ce
chantier : mesurer avant de construire, et accepter que la mesure
retourne contre l'intuition initiale (ici, l'idée qu'un simple seuil de
score suffirait).

**Temps 2, construit et mesuré (2026-09-11)** : `JugementClient`
(`app/retrieval/jugement.py`) filtre les candidats de `retrieve()` par un
appel LLM avant citation dans `POST /regles/dense`. **Résultat mesuré sur
les 114 cas réels : la famille `sans_reponse` plafonne à 40-55 % selon le
modèle** (`gpt-5.4-mini`/`gpt-5.4`, prompt renforcé compris), très loin du
seuil garde-fou de 90 % — malgré des instructions explicites contre la
confusion proximité/pertinence. Le cas le plus net : *« quel est le
palmarès de la dernière Coupe du monde de football ? »* → une règle
Opquast citée à tort, **deux fois**, malgré un contre-exemple dédié dans
le prompt.

**Diagnostic, pas un échec de prompt** : présenter une liste de candidats
au LLM et lui demander « lesquels répondent » crée un **biais de
sélection** — il choisit, même quand rien ne convient. Vérifié en isolant
la variable : un second client (`GuardrailClient`, expérimental) classe
la même question dans/hors périmètre Opquast **sans voir aucun
candidat** — résultat : **100 % sur les 20 cas `sans_reponse`**, 97,9 %
sur les 94 cas valides
(`docs/eval/mesure_guardrail_perimetre_2026-09-11_214327.md`, coût
0,0063 €). Retirer les candidats retire le biais.

**Conclusion architecturale** : le refus n'est pas une décision unique,
ce sont **trois décisions à trois endroits** du pipeline US2 — un
guardrail de périmètre *avant* tout appel d'outil (sans candidats, mesuré
fiable, pas encore intégré — niveau agent), le jugement sur les candidats
retrouvés (ce Temps 2, construit, limite structurelle acceptée), et le
jugement final avec mémoire/contexte au moment de rédiger (niveau agent).
`is_acceptable()` exclut de nouveau `sans_reponse` de son seuil
garde-fou — plus par absence de mécanisme, mais parce que la mesure
prouve que ce n'est pas au bon endroit du pipeline. Détail complet :
mémoire assistant `refus_architecture_trois_decisions`, diagramme
`conception/3_autre_us/us2_question_libre/diagramme_retrieval_refus_citation.drawio`.

### 4.2 Combien de règles retourner dans la réponse

Résolu par construction du Temps 2 : le jugement LLM décide lui-même du
sous-ensemble à citer (0 à N parmi les candidats), pas de nombre fixe à
trancher séparément. `top_n=15` (pool de candidats interrogé par
`retrieve()`) est confirmé par la mesure recall@k : c'est le seul k où
les cas à cibles multiples de l'acceptance sont tous couverts (recall
1.000 sur 14 cas), contre 0.929 à k=10.
