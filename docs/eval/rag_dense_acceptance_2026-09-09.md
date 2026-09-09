# Mesure recall — rag_dense_acceptance (2026-09-09)

## Taux de réussite par famille × top_n

| Famille | top_n=3 | top_n=5 | top_n=10 | top_n=15 |
|---|---|---|---|---|
| paraphrase_intitule | 100% | 100% | 100% | 100% |
| vocabulaire_source_opquast | 90% | 90% | 90% | 90% |
| vocabulaire_genere_llm | 77% | 92% | 92% | 92% |
| multi_sujets | 67% | 67% | 67% | 100% |
| sans_reponse | 0% | 0% | 0% | 0% |
| regles_concurrentes | 75% | 100% | 100% | 100% |

## Cas PARTIEL/FAIL persistants à top_n=15

(famille `sans_reponse` exclue : toujours FAIL par construction, pas un signal — voir le taux dans le tableau ci-dessus)

- **FAIL** [vocabulaire_source_opquast] « Peut-on imposer un ordre de parcours des champs différent de celui du code, avec des numéros ? » — attendu [167], retourné [57, 128, 72, 97, 145, 69, 74, 77, 71, 70, 32, 73, 236, 92, 181]
- **FAIL** [vocabulaire_genere_llm] « Un menu qui se déplie doit-il annoncer son état aux outils d'assistance ? » — attendu [185], retourné [157, 162, 238, 146, 225, 160, 55, 86, 78, 98, 163, 73, 90, 109, 161]
- **PARTIEL** [multi_sujets] « Je lance une boutique : quelles informations légales afficher, et comment rendre mes vidéos compréhensibles pour tous ? » — attendu [106, 122], retourné [2, 50, 124, 39, 121, 100, 54, 47, 37, 51, 122, 55, 15, 46, 53]
- **PARTIEL** [multi_sujets] « Comment un client peut-il nous joindre, et où lit-il les conditions de vente ? » — attendu [107, 46], retourné [46, 54, 50, 43, 51, 112, 53, 47, 42, 44, 45, 40, 109, 37, 48]
