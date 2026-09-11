# Mesure des combinaisons de chunk — vague 2 (2026-09-11 19:13)

## Jeu d'exploration

| Variante | Famille | MRR | recall@1 | recall@3 | recall@5 | recall@10 | recall@15 |
|---|---|---|---|---|---|---|---|
| baseline | paraphrase_intitule | 0.909 | 0.818 | 1.000 | 1.000 | 1.000 | 1.000 |
| baseline | vocabulaire_source_opquast | 0.777 | 0.615 | 0.923 | 0.923 | 1.000 | 1.000 |
| baseline | vocabulaire_genere_llm | 0.933 | 0.933 | 0.933 | 0.933 | 0.933 | 0.933 |
| baseline | multi_sujets | 1.000 | 0.500 | 0.667 | 0.667 | 0.833 | 1.000 |
| baseline | regles_concurrentes | 0.850 | 0.300 | 0.600 | 0.800 | 1.000 | 1.000 |
| baseline | vocabulaire_objectif | 0.741 | 0.531 | 0.781 | 0.875 | 0.938 | 0.938 |
| A_chunk_epure | paraphrase_intitule | 0.864 | 0.727 | 1.000 | 1.000 | 1.000 | 1.000 |
| A_chunk_epure | vocabulaire_source_opquast | 0.792 | 0.692 | 0.846 | 0.846 | 1.000 | 1.000 |
| A_chunk_epure | vocabulaire_genere_llm | 0.933 | 0.933 | 0.933 | 0.933 | 0.933 | 0.933 |
| A_chunk_epure | multi_sujets | 1.000 | 0.500 | 0.667 | 0.667 | 0.833 | 1.000 |
| A_chunk_epure | regles_concurrentes | 0.840 | 0.300 | 0.500 | 0.800 | 1.000 | 1.000 |
| A_chunk_epure | vocabulaire_objectif | 0.688 | 0.469 | 0.719 | 0.875 | 0.938 | 0.938 |
| B_duo_generaliste | paraphrase_intitule | 0.826 | 0.727 | 0.909 | 1.000 | 1.000 | 1.000 |
| B_duo_generaliste | vocabulaire_source_opquast | 0.607 | 0.462 | 0.692 | 0.692 | 0.846 | 0.923 |
| B_duo_generaliste | vocabulaire_genere_llm | 0.833 | 0.733 | 0.933 | 0.933 | 0.933 | 0.933 |
| B_duo_generaliste | multi_sujets | 0.833 | 0.333 | 0.833 | 0.833 | 0.833 | 1.000 |
| B_duo_generaliste | regles_concurrentes | 0.850 | 0.300 | 0.600 | 0.733 | 1.000 | 1.000 |
| B_duo_generaliste | vocabulaire_objectif | 0.540 | 0.344 | 0.469 | 0.688 | 0.875 | 0.875 |
| C_duo_specialiste | paraphrase_intitule | 0.803 | 0.636 | 1.000 | 1.000 | 1.000 | 1.000 |
| C_duo_specialiste | vocabulaire_source_opquast | 0.571 | 0.385 | 0.769 | 0.846 | 0.846 | 0.846 |
| C_duo_specialiste | vocabulaire_genere_llm | 0.900 | 0.867 | 0.933 | 0.933 | 0.933 | 0.933 |
| C_duo_specialiste | multi_sujets | 1.000 | 0.500 | 0.833 | 0.833 | 1.000 | 1.000 |
| C_duo_specialiste | regles_concurrentes | 0.850 | 0.300 | 0.533 | 0.733 | 1.000 | 1.000 |
| C_duo_specialiste | vocabulaire_objectif | 0.747 | 0.531 | 0.781 | 0.875 | 0.938 | 1.000 |
| D_source_opquast | paraphrase_intitule | 0.955 | 0.909 | 1.000 | 1.000 | 1.000 | 1.000 |
| D_source_opquast | vocabulaire_source_opquast | 0.819 | 0.692 | 0.923 | 0.923 | 1.000 | 1.000 |
| D_source_opquast | vocabulaire_genere_llm | 0.817 | 0.733 | 0.867 | 0.933 | 0.933 | 0.933 |
| D_source_opquast | multi_sujets | 1.000 | 0.500 | 0.667 | 0.667 | 0.667 | 0.833 |
| D_source_opquast | regles_concurrentes | 0.850 | 0.300 | 0.500 | 0.800 | 0.933 | 1.000 |
| D_source_opquast | vocabulaire_objectif | 0.780 | 0.594 | 0.781 | 0.875 | 1.000 | 1.000 |
| E_enrichissement_seul | paraphrase_intitule | 0.708 | 0.636 | 0.727 | 0.727 | 1.000 | 1.000 |
| E_enrichissement_seul | vocabulaire_source_opquast | 0.615 | 0.538 | 0.615 | 0.615 | 0.846 | 0.846 |
| E_enrichissement_seul | vocabulaire_genere_llm | 0.867 | 0.800 | 0.933 | 0.933 | 0.933 | 0.933 |
| E_enrichissement_seul | multi_sujets | 0.556 | 0.167 | 0.500 | 0.667 | 0.833 | 0.833 |
| E_enrichissement_seul | regles_concurrentes | 0.500 | 0.067 | 0.333 | 0.633 | 0.933 | 1.000 |
| E_enrichissement_seul | vocabulaire_objectif | 0.303 | 0.094 | 0.344 | 0.594 | 0.688 | 0.688 |

## Jeu réservé

| Variante | Famille | MRR | recall@1 | recall@3 | recall@5 | recall@10 | recall@15 |
|---|---|---|---|---|---|---|---|
| baseline | paraphrase_intitule | 0.917 | 0.833 | 1.000 | 1.000 | 1.000 | 1.000 |
| baseline | vocabulaire_source_opquast | 0.833 | 0.714 | 1.000 | 1.000 | 1.000 | 1.000 |
| baseline | vocabulaire_genere_llm | 0.646 | 0.571 | 0.571 | 0.857 | 1.000 | 1.000 |
| baseline | multi_sujets | 1.000 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 |
| baseline | regles_concurrentes | 1.000 | 0.292 | 0.875 | 1.000 | 1.000 | 1.000 |
| baseline | vocabulaire_objectif | 0.619 | 0.500 | 0.625 | 0.750 | 0.875 | 1.000 |
| A_chunk_epure | paraphrase_intitule | 0.917 | 0.833 | 1.000 | 1.000 | 1.000 | 1.000 |
| A_chunk_epure | vocabulaire_source_opquast | 0.929 | 0.857 | 1.000 | 1.000 | 1.000 | 1.000 |
| A_chunk_epure | vocabulaire_genere_llm | 0.753 | 0.714 | 0.714 | 0.714 | 1.000 | 1.000 |
| A_chunk_epure | multi_sujets | 1.000 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 |
| A_chunk_epure | regles_concurrentes | 1.000 | 0.292 | 0.875 | 0.875 | 1.000 | 1.000 |
| A_chunk_epure | vocabulaire_objectif | 0.528 | 0.375 | 0.625 | 0.625 | 1.000 | 1.000 |
| B_duo_generaliste | paraphrase_intitule | 0.889 | 0.833 | 1.000 | 1.000 | 1.000 | 1.000 |
| B_duo_generaliste | vocabulaire_source_opquast | 0.857 | 0.714 | 1.000 | 1.000 | 1.000 | 1.000 |
| B_duo_generaliste | vocabulaire_genere_llm | 0.748 | 0.714 | 0.714 | 0.714 | 0.857 | 1.000 |
| B_duo_generaliste | multi_sujets | 1.000 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 |
| B_duo_generaliste | regles_concurrentes | 1.000 | 0.292 | 0.750 | 0.875 | 1.000 | 1.000 |
| B_duo_generaliste | vocabulaire_objectif | 0.394 | 0.250 | 0.500 | 0.500 | 0.625 | 0.875 |
| C_duo_specialiste | paraphrase_intitule | 0.889 | 0.833 | 1.000 | 1.000 | 1.000 | 1.000 |
| C_duo_specialiste | vocabulaire_source_opquast | 0.773 | 0.714 | 0.857 | 0.857 | 0.857 | 1.000 |
| C_duo_specialiste | vocabulaire_genere_llm | 0.675 | 0.571 | 0.714 | 0.714 | 1.000 | 1.000 |
| C_duo_specialiste | multi_sujets | 1.000 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 |
| C_duo_specialiste | regles_concurrentes | 1.000 | 0.292 | 0.750 | 0.875 | 1.000 | 1.000 |
| C_duo_specialiste | vocabulaire_objectif | 0.589 | 0.500 | 0.625 | 0.625 | 1.000 | 1.000 |
| D_source_opquast | paraphrase_intitule | 0.917 | 0.833 | 1.000 | 1.000 | 1.000 | 1.000 |
| D_source_opquast | vocabulaire_source_opquast | 0.833 | 0.714 | 1.000 | 1.000 | 1.000 | 1.000 |
| D_source_opquast | vocabulaire_genere_llm | 0.614 | 0.571 | 0.571 | 0.571 | 0.714 | 1.000 |
| D_source_opquast | multi_sujets | 1.000 | 0.500 | 0.500 | 1.000 | 1.000 | 1.000 |
| D_source_opquast | regles_concurrentes | 1.000 | 0.292 | 0.750 | 1.000 | 1.000 | 1.000 |
| D_source_opquast | vocabulaire_objectif | 0.519 | 0.250 | 0.625 | 1.000 | 1.000 | 1.000 |
| E_enrichissement_seul | paraphrase_intitule | 0.783 | 0.667 | 0.833 | 1.000 | 1.000 | 1.000 |
| E_enrichissement_seul | vocabulaire_source_opquast | 0.714 | 0.571 | 1.000 | 1.000 | 1.000 | 1.000 |
| E_enrichissement_seul | vocabulaire_genere_llm | 0.567 | 0.429 | 0.571 | 0.714 | 1.000 | 1.000 |
| E_enrichissement_seul | multi_sujets | 1.000 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 |
| E_enrichissement_seul | regles_concurrentes | 1.000 | 0.292 | 0.583 | 0.875 | 0.875 | 0.875 |
| E_enrichissement_seul | vocabulaire_objectif | 0.351 | 0.250 | 0.375 | 0.625 | 0.625 | 0.750 |

## Décision

Candidats éliminés (régression vs baseline sur au moins une famille, jeu d'exploration) : A_chunk_epure, B_duo_generaliste, C_duo_specialiste, D_source_opquast, E_enrichissement_seul.

Gagnant provisoire (MRR moyen non pondéré le plus haut, jeu d'exploration) : **baseline**.

Validation sur le jeu réservé : confirmée.

**Choix retenu : baseline**
