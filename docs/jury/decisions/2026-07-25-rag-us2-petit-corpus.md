# RAG sémantique pour US2 malgré un petit corpus (245 règles)

2026-07-25 · retenu

## Contexte

`conception/conception.md` prévoit US2 (question libre) en **RAG sémantique
pur** : pas de présélection, pgvector cherche les règles pertinentes en
réponse à une question libre de l'auditeur.

Le référentiel Opquast ne compte que **245 règles**. Avec des chunks
d'environ 300-500 tokens chacun, le corpus entier tiendrait dans les
50 000-120 000 tokens — largement dans la fenêtre de contexte de Kimi K2.6
(256K, déjà retenu pour l'enrichissement — voir `annexes/F_choix_llm.md`).
Techniquement, rien n'empêcherait d'injecter le référentiel entier à chaque
question US2, sans recherche vectorielle du tout. La question posée ici :
le RAG est-il justifié à cette échelle, ou est-ce de la sur-ingénierie ?

## Options envisagées

**Injection complète du corpus (full-context), sans recherche vectorielle**
— pour : simple, garantit qu'aucune règle pertinente n'est jamais ratée par
une recherche sémantique imparfaite (rappel de 100 %). Contre : coût en
tokens répété à *chaque* question (50-120K tokens à chaque appel, pas
seulement au moment de l'ingestion) ; risque de dégradation "lost in the
middle" (les LLM sont moins fiables sur l'information noyée au milieu d'un
contexte très long) ; ne passe pas à l'échelle si le corpus grossit un jour
(cf. `IDEA.md` — idée d'enrichir le RAG avec l'écosystème Opquast : glossaire,
VPTCS, infos pratiques).

**RAG sémantique (retenu)** — pour : coût par requête bien moindre (quelques
chunks pertinents plutôt que tout le corpus), évite le "lost in the middle",
extensible si le corpus grossit, cohérent avec le positionnement
éco-conception déjà affiché (`README.md` : "embedding léger, pas de base
vectorielle externe"). Contre : rappel imparfait — une règle réellement
pertinente peut être mal classée par l'embedding et ne jamais remonter ;
complexité d'implémentation (chunking, embedding, indexation) pour un gain
qui, à 245 éléments, est réel mais modeste.

## Décision

Garder le RAG sémantique malgré le petit corpus — sur trois arguments
(coût par requête, qualité de réponse, extensibilité), pas par défaut/habitude.
Le compromis (rappel imparfait vs coût/qualité) est jugé acceptable à ce
stade, US2 n'étant pas encore conçu en détail.

## Conséquences

- **Nuance assumée sur l'index HNSW** : HNSW est conçu pour de la recherche
  approximative à grande échelle (millions de vecteurs). À 245 vecteurs, un
  scan exact (cosinus, sans index ANN) serait tout aussi rapide et strictement
  plus précis (pas d'approximation). L'index existe depuis la migration 0001
  et ne coûte presque rien à garder — ce n'est pas une erreur, mais un détail
  qu'un jury pourrait légitimement questionner : le choix HNSW anticipe une
  échelle que le projet n'a pas encore, pas un besoin actuel.
- **Reste ouvert** : si le corpus grossit significativement (idée glossaire/
  VPTCS de `IDEA.md`), le choix RAG devient mécaniquement plus justifié — la
  décision n'a pas besoin d'être revisitée dans ce cas, seulement confirmée.
- Cette décision précède la conception détaillée d'US2 (pas encore spécée) —
  à référencer quand `conception/` accueillera sa spec.
