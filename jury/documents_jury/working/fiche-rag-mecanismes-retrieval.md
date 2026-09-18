# Fiche de révision — RAG US2 : pourquoi, ce qui a été testé, ce qui a été écarté

Support de préparation orale (E2/E3). Synthétise trois décisions déjà
tranchées et sourcées — cette fiche ne remplace pas les preuves, elle sert
à les avoir en tête dans l'ordre pour répondre à l'oral. Sources : `jury/decisions/2026-07-25-rag-us2-petit-corpus.md`,
`jury/decisions/2026-09-08-mesurer-avant-mecanismes-retrieval.md`,
`jury/decisions/2026-09-09-recommandations-suite-mesure-retrieval.md`,
`jury/decisions/2026-09-09-seuil-acceptance-rag-90-pourcent.md`.

## 1. Pourquoi un RAG, alors que le corpus tient dans le contexte du LLM

245 règles Opquast, chunks de 300-500 tokens : le corpus entier tiendrait
dans les 50-120K tokens, largement sous la fenêtre de Kimi K2.6 (256K).
Techniquement, rien n'empêchait d'injecter tout le référentiel à chaque
question et de sauter la recherche vectorielle.

RAG retenu quand même, sur 3 arguments (pas par défaut) :
- **coût** : quelques chunks par requête plutôt que 50-120K tokens à *chaque* question
- **qualité** : évite le "lost in the middle" (LLM moins fiable sur du contexte long)
- **extensibilité** : si le corpus grossit (glossaire/VPTCS/ecosysteme envisagés dans `IDEA.md`), le calcul devient encore plus favorable au RAG

Contrepartie assumée dès le départ : rappel imparfait (une règle pertinente
peut être mal classée par l'embedding et ne jamais remonter).

## 2. Le point de départ : une fiche d'architecture proposant 5 mécanismes

Une conversation avec **Gemini** a produit une fiche recommandant :
parent-child retrieval (ne vectoriser que intitulé+objectifs+thème+tags),
recherche **hybride** FTS+pgvector fusionnée par **RRF**, **reformulation**
de requête par LLM, **décomposition** en sous-requêtes, RAG **multi-sources**
typé par `doc_type`.

Diagnostic de départ de la fiche : dilution sémantique ("smoothie
vectoriel") — un chunk long et normatif noie le signal utile face à une
question courte.

**Décision de méthode avant tout arbitrage** : ne rien construire tant que
le jeu d'acceptance ne peut pas mesurer l'apport d'un mécanisme. Le jeu
initial (17 cas, cible unique, quasi tous des paraphrases directes de
l'intitulé) ne pouvait arbitrer ni dans un sens ni dans l'autre — 100% de
réussite mesurait un problème facile, pas l'absence de dilution.

## 3. Ce que l'audit de la fiche a établi (avant toute décision)

| Constat | Donnée |
|---|---|
| La dilution invoquée est réelle | texte vectorisé ~1620 caractères, dont `guide_analyse` ~40% et `intitulé` ~5% |
| Le remède proposé est auto-réfutant | le vocabulaire technique (ARIA, `alt=`, 404, cookie) vit dans `guide_analyse`/`controle`, quasi absent des champs que la fiche propose d'indexer |
| Cas le plus net | "SIRET" n'existe que dans le `guide_analyse` de la règle 106 — le champ que la fiche voulait retirer du vecteur |
| Contradiction interne | la fiche justifie le FTS par "capter les termes exacts" puis l'indexe sur des champs où ces termes sont à zéro |
| Détail signe d'une proposition non vérifiée au schéma | `objectifs` n'est pas une colonne de `regle`, nécessite une jointure non prévue |

**Conclusion de l'audit** : appliquer la fiche telle quelle aurait dégradé
les requêtes qu'elle prétendait réparer. Elle a été écartée **sur mesure,
pas par principe**.

## 4. Décision (2026-09-08) : mesurer avant d'ajouter un mécanisme

Critère qui tranche : *un mécanisme dont on ne peut pas mesurer l'apport
n'est pas une amélioration, c'est un pari.*

- **Écarté d'emblée, sans construire** : RRF, décomposition en sous-requêtes,
  HyDE, reformulation LLM générique, `doc_type`/multi-sources — aucun signal
  mesuré ne les justifiait à ce stade.
- **Hybride laissé ouvert, avec condition de réouverture testable** : si le
  jeu d'acceptance étendu montre un rappel insuffisant sur la famille
  "termes exacts", le FTS devient le premier candidat.
- **Ordre d'intervention prévu, du moins cher au plus cher** : `top_n`
  (config, zéro code) → variantes de chunk (~0,0016€ par variante) → FTS
  hybride en dernier recours.
- **Le jeu d'acceptance devient le chantier critique**, pas un à-côté :
  l'étendre revient à spécifier en BDD le comportement attendu d'US2 (que
  citer, que refuser, quand dire "je ne sais pas"). Étendu à 7 familles,
  99 cas au total (`tests/acceptance/rag_acceptance.jsonl`).

## 5. Ce que la mesure a effectivement montré

`top_n` seul (3 → 15) résout la plupart des familles. Trois signaux
persistent à `top_n=15` :

- **`multi_sujets`** : 2 cas sur 4 échouent *structurellement* — un sujet
  écrase l'autre dans l'espace vectoriel quel que soit `top_n`. Seule
  famille où le signal n'est plus isolé : c'est la condition implicite qui
  rend un mécanisme démontrable.
- **`vocabulaire_genere_llm`** : 1 échec sur 13 (règle 185, `aria-expanded`)
  — trop isolé pour trancher (dilution réelle ou question mal formulée).
- **`regles_concurrentes`** : l'indicateur agrégé masquait des résultats
  `PARTIEL` — problème de mesure, pas de mécanisme.

## 6. Ce qui a été implémenté après mesure (et seulement après)

1. **`theme` + `objectif` ajoutés au chunk vectorisé** — ni l'un ni l'autre
   n'avait de justification documentée pour son absence.
2. **Jeu élargi de 28 cas** sur `vocabulaire_source_opquast`/
   `vocabulaire_genere_llm` pour tester la condition de réouverture de
   l'hybride/HyDE → **non déclenchée** : 97% de réussite sur 70 cas, les
   2 échecs restent isolés, acceptés comme limite connue du RAG plutôt que
   de construire un mécanisme pour 2 cas précis.
3. **Décomposition LLM, portée volontairement limitée** — un LLM subdivise
   une question multi-sujets en sous-questions, chaque sous-question
   interroge le RAG séparément, **union simple** des règles retrouvées
   (**pas de RRF**, qui reste écarté comme mécanisme de fusion pondérée non
   justifié). Implémentée dans `app/retrieval/` (`decomposition.py`,
   `retrieval.py::retrieve()`), exposée en production via
   `POST /regles/dense`.

## 7. Ce qui reste écarté, définitivement ou conditionnellement

| Mécanisme | Statut | Pourquoi |
|---|---|---|
| Reranker (cross-encoder) | écarté | n'aide pas un candidat absent du pool initial (règle 218 jamais dans le top-15) |
| RRF | écarté | fusion pondérée non justifiée par une mesure ; l'union simple suffit pour `multi_sujets` |
| HyDE, reformulation LLM générique | écarté, condition de réouverture testée et **non déclenchée** | 97% sur 70 cas vocabulaire, échecs trop isolés |
| FTS hybride | écarté à ce stade, réouverture possible | dernier recours dans l'ordre d'intervention, jamais atteint faute de nécessité mesurée |
| `doc_type` / multi-sources (VPTCS, glossaire, ecosysteme) | hors périmètre de certification | projet d'acquisition de corpus distinct, noté dans `IDEA.md` |

## 8. Résultat mesuré aujourd'hui

Taux par famille à `top_n=10` (`docs/eval/rag_dense_acceptance_2026-09-09_162951.md`) :

| Famille | Taux |
|---|---|
| paraphrase_intitule | 100% |
| vocabulaire_source_opquast | 100% |
| vocabulaire_genere_llm | 95% |
| multi_sujets | 100% |
| regles_concurrentes | 100% |
| vocabulaire_objectif | 92% |

Seuil garde-fou (`taux_reussite_minimum`) relevé de 80% à **90%** : pas un
seuil de qualité produit, un garde-fou de non-régression technique — 80%
avait été choisi au doigt mouillé le 2026-07-26, 90% colle aux taux
réellement mesurés avec une marge raisonnable.

## 9. Cause de variance trouvée après coup (2026-09-16)

Les taux de la section 8 avaient été mesurés à température LLM par défaut
(`0.7`, jamais fixée sur les trois clients du chemin retrieval :
`decomposition.py`, `jugement.py`, `guardrail.py`). Un effondrement observé
le 2026-09-13 (`regles_concurrentes` 100% → 67% sans aucun changement de
code entre deux runs) a mené à la cause racine : chaque appel échantillonnait
au hasard.

**Correctif** : `temperature: 0` ajouté aux trois rôles (`app/ingestion/
manifest.yml`), 3 tests unitaires ajoutés. **Vérification (2 runs
consécutifs)** : les effondrements massifs disparaissent, les autres
familles ne varient plus que d'1 cas sur ~20-23 (résidu de non-déterminisme
normal, même à température 0, côté fournisseur — pas comparable aux écarts
de 33 points observés avant correctif). `vocabulaire_objectif` reconfirmée
stable à 73-74% sur les 2 runs : un plafond réel, pas de la variance —
le seuil spécifique à 0,70 pour cette famille reste justifié, mais pour une
cause comprise (règles quasi-doublons piégeant le jugement LLM) et non plus
comme rustine en attente d'investigation.

**Effet de bord pour l'oral** : ça invalide un test A/B antérieur sur le
prompt de jugement (fait à température 0.7, un seul appel de chaque côté —
comparait deux tirages aléatoires, pas deux prompts). Détail complet :
`CHANGELOG.md` (2026-09-16), carte Kanboard #20.

## 10. L'argument à ne pas perdre à l'oral

La compétence démontrée n'est pas "avoir construit un RAG sophistiqué" —
c'est l'inverse : **avoir confronté une recommandation d'IA (Gemini) aux
données réelles du projet, l'avoir en partie réfutée par la mesure, puis
n'avoir construit que ce qu'un échec mesuré justifiait.** Chaque mécanisme
retenu ou écarté est falsifiable, pas un pari. La source (Gemini) est
nommée délibérément — l'auditer plutôt que l'appliquer est la compétence
attendue en IA agentique, la masquer affaiblirait le dossier.
