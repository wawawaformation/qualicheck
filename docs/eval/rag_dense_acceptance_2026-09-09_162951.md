# Mesure recall — rag_dense_acceptance (2026-09-09 16:29)

## Taux de réussite par famille × top_n

| Famille | top_n=3 | top_n=5 | top_n=10 | top_n=15 |
|---|---|---|---|---|
| paraphrase_intitule | 100% | 100% | 100% | 100% |
| vocabulaire_source_opquast | 95% | 95% | 100% | 100% |
| vocabulaire_genere_llm | 82% | 91% | 95% | 95% |
| multi_sujets | 100% | 100% | 100% | 100% |
| sans_reponse | 0% | 0% | 0% | 0% |
| regles_concurrentes | 75% | 100% | 100% | 100% |
| vocabulaire_objectif | 79% | 88% | 92% | 96% |

## Cas PARTIEL/FAIL persistants à top_n=15

(famille `sans_reponse` exclue : toujours FAIL par construction, pas un signal — voir le taux dans le tableau ci-dessus)

- **FAIL** [vocabulaire_genere_llm] « Un menu qui se déplie doit-il annoncer son état aux outils d'assistance ? » — attendu [185], retourné [157, 162, 238, 146, 225, 160, 55, 86, 78, 98, 163, 73, 90, 109, 161]
- **FAIL** [vocabulaire_objectif] « Qu'est-ce qui provoque une interprétation hasardeuse du DOM d'une page selon les agents utilisateurs ? » — attendu [236], retourné [224, 211, 228, 223, 222, 232, 206, 225, 213, 131, 210, 216, 153, 200, 130]
