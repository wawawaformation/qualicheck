# Mesure recall — rag_dense_acceptance (2026-09-09)

## Taux de réussite par famille × top_n

| Famille | top_n=3 | top_n=5 | top_n=10 | top_n=15 |
|---|---|---|---|---|
| paraphrase_intitule | 100% | 100% | 100% | 100% |
| vocabulaire_source_opquast | 80% | 80% | 90% | 100% |
| vocabulaire_genere_llm | 85% | 85% | 85% | 92% |
| multi_sujets | 67% | 67% | 67% | 100% |
| sans_reponse | 0% | 0% | 0% | 0% |
| regles_concurrentes | 100% | 100% | 100% | 100% |

## Cas PARTIEL/FAIL persistants à top_n=15

(famille `sans_reponse` exclue : toujours FAIL par construction, pas un signal — voir le taux dans le tableau ci-dessus)

- **FAIL** [vocabulaire_genere_llm] « Un menu qui se déplie doit-il annoncer son état aux outils d'assistance ? » — attendu [185], retourné [157, 86, 162, 78, 55, 225, 146, 238, 160, 90, 98, 73, 109, 164, 163]
- **PARTIEL** [multi_sujets] « Je lance une boutique : quelles informations légales afficher, et comment rendre mes vidéos compréhensibles pour tous ? » — attendu [106, 122], retourné [2, 39, 100, 121, 124, 15, 40, 51, 37, 48, 46, 47, 122, 54, 101]
- **PARTIEL** [multi_sujets] « Comment un client peut-il nous joindre, et où lit-il les conditions de vente ? » — attendu [107, 46], retourné [46, 54, 112, 53, 51, 43, 47, 50, 44, 40, 42, 45, 109, 48, 37]
