# Mesure multi-vecteurs — vague 3 (2026-09-11 19:47)

## Jeu d'exploration

| Variante | Famille | MRR | recall@1 | recall@3 | recall@5 | recall@10 | recall@15 |
|---|---|---|---|---|---|---|---|
| baseline | paraphrase_intitule | 0.909 | 0.818 | 1.000 | 1.000 | 1.000 | 1.000 |
| baseline | vocabulaire_source_opquast | 0.779 | 0.615 | 0.923 | 0.923 | 1.000 | 1.000 |
| baseline | vocabulaire_genere_llm | 0.933 | 0.933 | 0.933 | 0.933 | 0.933 | 0.933 |
| baseline | multi_sujets | 1.000 | 0.500 | 0.667 | 0.667 | 0.833 | 1.000 |
| baseline | regles_concurrentes | 0.850 | 0.300 | 0.600 | 0.800 | 1.000 | 1.000 |
| baseline | vocabulaire_objectif | 0.687 | 0.469 | 0.719 | 0.812 | 0.938 | 0.938 |
| F_multi_vecteurs | paraphrase_intitule | 0.909 | 0.818 | 1.000 | 1.000 | 1.000 | 1.000 |
| F_multi_vecteurs | vocabulaire_source_opquast | 0.686 | 0.538 | 0.846 | 0.846 | 1.000 | 1.000 |
| F_multi_vecteurs | vocabulaire_genere_llm | 0.837 | 0.733 | 0.933 | 0.933 | 0.933 | 0.933 |
| F_multi_vecteurs | multi_sujets | 1.000 | 0.500 | 0.833 | 0.833 | 0.833 | 1.000 |
| F_multi_vecteurs | regles_concurrentes | 0.850 | 0.300 | 0.533 | 0.800 | 1.000 | 1.000 |
| F_multi_vecteurs | vocabulaire_objectif | 0.638 | 0.406 | 0.719 | 0.750 | 0.875 | 0.938 |

## Jeu réservé

| Variante | Famille | MRR | recall@1 | recall@3 | recall@5 | recall@10 | recall@15 |
|---|---|---|---|---|---|---|---|
| baseline | paraphrase_intitule | 0.917 | 0.833 | 1.000 | 1.000 | 1.000 | 1.000 |
| baseline | vocabulaire_source_opquast | 0.833 | 0.714 | 1.000 | 1.000 | 1.000 | 1.000 |
| baseline | vocabulaire_genere_llm | 0.646 | 0.571 | 0.571 | 0.857 | 1.000 | 1.000 |
| baseline | multi_sujets | 1.000 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 |
| baseline | regles_concurrentes | 1.000 | 0.292 | 0.875 | 1.000 | 1.000 | 1.000 |
| baseline | vocabulaire_objectif | 0.619 | 0.500 | 0.625 | 0.750 | 0.875 | 1.000 |
| F_multi_vecteurs | paraphrase_intitule | 0.875 | 0.833 | 0.833 | 1.000 | 1.000 | 1.000 |
| F_multi_vecteurs | vocabulaire_source_opquast | 0.738 | 0.571 | 1.000 | 1.000 | 1.000 | 1.000 |
| F_multi_vecteurs | vocabulaire_genere_llm | 0.636 | 0.571 | 0.571 | 0.571 | 1.000 | 1.000 |
| F_multi_vecteurs | multi_sujets | 1.000 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 |
| F_multi_vecteurs | regles_concurrentes | 1.000 | 0.292 | 0.875 | 1.000 | 1.000 | 1.000 |
| F_multi_vecteurs | vocabulaire_objectif | 0.552 | 0.375 | 0.625 | 0.750 | 0.875 | 0.875 |

## Décision

Candidats éliminés (régression vs baseline sur au moins une famille, jeu d'exploration) : F_multi_vecteurs.

Gagnant provisoire (MRR moyen non pondéré le plus haut, jeu d'exploration) : **baseline**.

Validation sur le jeu réservé : confirmée.

**Choix retenu : baseline**
