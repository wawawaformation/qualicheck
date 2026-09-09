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

- **FAIL** [vocabulaire_genere_llm] « Un menu qui se déplie doit-il annoncer son état aux outils d'assistance ? » — attendu [185], retourné [157, 86, 162, 78, 55, 225, 146, 238, 160, 90, 98, 73, 109, 164, 163]
- **PARTIEL** [multi_sujets] « Je lance une boutique : quelles informations légales afficher, et comment rendre mes vidéos compréhensibles pour tous ? » — attendu [106, 122], retourné [2, 39, 100, 121, 124, 15, 40, 51, 37, 48, 46, 47, 122, 54, 101]
- **PARTIEL** [multi_sujets] « Comment un client peut-il nous joindre, et où lit-il les conditions de vente ? » — attendu [107, 46], retourné [46, 54, 112, 53, 51, 43, 47, 50, 44, 40, 42, 45, 109, 48, 37]
- **FAIL** [sans_reponse] « Comment recruter un panel d'utilisateurs en situation de handicap pour tester mon site ? » — attendu [], retourné [166, 98, 107, 186, 194, 167, 163, 86, 97, 154, 170, 193, 17, 168, 189]
- **FAIL** [sans_reponse] « Combien de temps faut-il prévoir pour réaliser un audit qualité web complet ? » — attendu [], retourné [171, 66, 86, 220, 180, 39, 152, 55, 87, 108, 91, 35, 7, 198, 102]
- **FAIL** [sans_reponse] « Quelle méthode d'estimation agile utiliser pour planifier les corrections d'un audit ? » — attendu [], retourné [91, 81, 83, 66, 10, 229, 183, 171, 230, 87, 88, 86, 180, 80, 55]
- **FAIL** [sans_reponse] « Quel est le tarif d'une certification Opquast pour une équipe ? » — attendu [], retourné [198, 56, 115, 21, 36, 22, 226, 63, 41, 33, 227, 213, 210, 66, 233]
- **FAIL** [sans_reponse] « Quel framework JavaScript choisir pour construire mon site ? » — attendu [], retourné [230, 211, 194, 166, 167, 236, 234, 164, 183, 238, 237, 130, 233, 229, 180]
