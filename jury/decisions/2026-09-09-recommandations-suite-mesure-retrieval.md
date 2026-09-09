# Recommandations suite à la mesure du retrieval (Étapes 3-4.1)

2026-09-09 · retenu

## Contexte

L'Étape 3 (mesurer `recall@3/5/10/15`, `docs/eval/rag_dense_acceptance_2026-09-09.md`)
et l'Étape 4.1 (`top_n` porté à 15) du plan retrieval
(`jury/decisions/2026-09-08-mesurer-avant-mecanismes-retrieval.md`) ont
produit un signal exploitable, mais pas univoque : `top_n` seul résout la
plupart des familles, sauf 3 cas qui persistent même à `top_n=15`. Ce
document tranche ce qu'on fait de ce signal, sans reproduire l'erreur
initiale (appliquer un mécanisme séduisant sans preuve de besoin sur ces
données) ni son inverse (ignorer un signal mesuré par confort).

## Ce que la mesure a établi

- **`multi_sujets`** : 2 cas sur 4 échouent structurellement — dans chacun,
  un sujet écrase complètement l'autre dans l'espace vectoriel, quel que
  soit `top_n`. C'est la famille explicitement conçue pour tester le seul
  vrai cas d'usage de la décomposition en sous-requêtes (`TODO.md` § Étape
  2) — le signal existe désormais, il n'était qu'anticipé avant cette
  mesure.
- **`vocabulaire_genere_llm`** : 1 échec sur 13 (règle 185, `aria-expanded`)
  persiste à `top_n=15`. Trop isolé pour trancher : signal réel de
  dilution, ou question mal formulée — indiscernable avec un seul cas.
- **`regles_concurrentes`** : le taux agrégé (« 100% ») masque que 5 cas
  sur 7 étaient `PARTIEL` à `top_n` bas — l'indicateur actuel
  (`compute_taux_par_famille`, qui exclut les `PARTIEL` du calcul) cache
  une partie du signal plutôt que de le montrer.
- **Ce qui n'a jamais été mesuré** : l'apport de `theme`/`objectif` dans le
  chunk vectorisé (absents de `build_chunk_text()`, carte Kanboard #8 pour
  `theme` — `objectif` jamais tracé, écarté au moment du chantier de
  chunking initial faute d'en voir l'utilité pour le RAG, avant que cette
  mesure ne la rende visible) ; la pertinence du FTS hybride (pas encore
  atteint dans l'ordre d'intervention : top_n → variantes de chunk → FTS).

## Recommandations retenues

### 1. Ajouter `theme` et `objectif` au chunk vectorisé

**Périmètre** : `theme` (jointure simple, 1:N) et `objectif` (jointure
many-to-many via `objectif_regle`) rejoignent `build_chunk_text()`
(`app/ingestion/chunking.py`), aux côtés de `intitulé/contexte/solution/
controle/guide_analyse/tags/phases`.

**Pourquoi maintenant** : ni l'un ni l'autre n'a de justification
documentée pour son absence (`theme`) ou a été écarté sans mesurer son
utilité pour le RAG (`objectif`, jointure jugée coûteuse au moment du
chantier de chunking, avant que l'importance du champ pour la recherche
sémantique ne soit visible). C'est une variante de chunk au sens de
l'ordre d'intervention de la décision du 2026-09-08 — mesurable à nouveau
avec le jeu d'acceptance existant, coût de ré-embedding négligeable
(~0,0016 € pour les 245 règles, comme les runs précédents).

**Remplace** la carte Kanboard #8 (`theme` seul) — étendue à `objectif`.

### 2. Étoffer les cas `vocabulaire_source_opquast`/`vocabulaire_genere_llm`

**Pourquoi** : 1 échec isolé sur 23 cas ne permet pas de distinguer un
signal réel de dilution d'un artefact de formulation. Avant de considérer
un mécanisme (HyDE ou autre) pour ces familles, la même discipline que
pour `multi_sujets` s'applique : mesurer sur un échantillon plus large
avant de conclure.

**Périmètre** : nouveaux cas des deux familles, même méthode que les 39
premiers (extraction automatique du vocabulaire par provenance de champ,
proposition puis validation). Peut se faire en même temps que la
recommandation 1 (rejouer le jeu d'acceptance après ajout de
`theme`/`objectif` au chunk, sur un échantillon plus large).

### 3. Concevoir puis implémenter un mécanisme de décomposition LLM pour `multi_sujets`

**Pourquoi** : contrairement aux deux familles ci-dessus, le signal ici
n'est plus isolé — 2 cas sur 4 échouent de la même façon, sur la famille
conçue spécifiquement pour tester ce mécanisme. C'est la condition
implicite (pas explicitement écrite, cf. échange du 2026-09-09) qui rend
la décomposition démontrable comme amélioration, là où elle ne l'était pas
le 2026-09-08.

**Portée volontairement limitée** : un LLM qui, face à une question
multi-sujets, la subdivise en sous-questions avant le retrieval (chaque
sous-question interroge le RAG séparément, les résultats sont fusionnés
par union simple des règles retrouvées — **pas de RRF**, qui reste écarté
comme les autres mécanismes de fusion pondérée non justifiés).

**Reste isolable du reste d'US2** : ce mécanisme appartient au système RAG
(retrieval), pas à l'agent conversationnel complet (guardrails, mémoire de
discussion, LLM de réponse). Il peut donc se concevoir et s'implémenter
comme brique autonome — même logique que le jeu d'acceptance et
`rag_dense_acceptance.py` — sans attendre la spec complète d'US2
(`conception/3_autre_us/us2_question_libre/`, `harness/` encore vide).

## Ce qui reste explicitement écarté

- **Reranker** (cross-encoder post-retrieval) pour `vocabulaire_*` :
  n'aide pas un candidat absent du pool initial (le cas règle 218,
  `canonical`, ne figurait dans aucun top-15) — un reranker ne fait que
  réordonner ce qui est déjà récupéré.
- **RRF, HyDE en production, reformulation LLM générique, FTS hybride** :
  toujours hors périmètre à ce stade, pour les mêmes raisons qu'actées le
  2026-09-08 — aucun n'a de signal mesuré à ce jour qui les justifie
  (HyDE pourrait devenir un candidat si la recommandation 2 révèle
  plusieurs échecs du même type que la règle 185, pas avant).
- **Corriger l'indicateur de `regles_concurrentes` en dehors d'une vraie
  refonte** : noté comme limite connue de `compute_taux_par_famille`, pas
  une correction à faire à la volée — à traiter comme son propre petit
  chantier (nouvel indicateur, ex. proportion moyenne de cibles retrouvées
  par cas) plutôt qu'un patch improvisé.

## Conséquences

- Carte Kanboard #8 à réviser (titre et description) pour couvrir
  `theme` **et** `objectif`, plus urgente qu'initialement notée (mesure à
  l'appui, pas juste un manque documenté).
- Nouvelles cartes à créer pour les recommandations 2 et 3.
- La recommandation 3 se conçoit et s'implémente comme brique retrieval
  autonome (même statut que le jeu d'acceptance et
  `rag_dense_acceptance.py`) — elle n'attend pas la spec complète d'US2
  (agent, guardrails, mémoire), seulement son propre cadrage.
