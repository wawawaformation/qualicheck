"""
Tests unitaires pour app/ingestion/rag_acceptance.py

Logique pure (load_cases, evaluate_case, compute_taux_par_famille,
is_acceptable, format_dataset_versions) — aucun appel réseau ni BDD
réelle. query_top_n_numeros et summarize_dataset_versions ne sont pas
testées ici (nécessitent une base réellement vectorisée), validées par
exécution réelle via `make rag-acceptance`.
"""

from datetime import datetime

import pytest

from app.ingestion.rag_acceptance import (
    calculer_mrr,
    calculer_recall_a_k,
    compute_taux_par_famille,
    construire_resume_markdown,
    cosine_similarity_matrix,
    evaluate_case,
    format_dataset_versions,
    is_acceptable,
    load_cases,
    mesurer_variante,
    metriques_scores,
    rang_meilleure_cible,
    retrieve_variante,
    tirer_jeu_reserve,
)


def test_load_cases_parses_jsonl(tmp_path):
    """load_cases lit un fichier JSONL, une entrée par ligne."""
    jsonl_path = tmp_path / "cases.jsonl"
    jsonl_path.write_text(
        '{"question": "Q1", "numero_regle_attendue": 1}\n'
        '{"question": "Q2", "numero_regle_attendue": 2}\n',
        encoding="utf-8",
    )

    cases = load_cases(jsonl_path)

    assert cases == [
        {"question": "Q1", "numero_regle_attendue": 1},
        {"question": "Q2", "numero_regle_attendue": 2},
    ]


def test_evaluate_case_pass_single_cible():
    """Un cas à cible unique réussit (PASS) si sa cible figure dans les résultats."""
    case = {
        "question": "Q1",
        "famille": "vocabulaire_source_opquast",
        "numeros_regle_attendus": [139],
    }

    result = evaluate_case(case, numeros_retournes=[42, 139, 7])

    assert result["verdict"] == "PASS"
    assert result["famille"] == "vocabulaire_source_opquast"
    assert result["numeros_regle_attendus"] == [139]
    assert result["numeros_retournes"] == [42, 139, 7]
    assert result["question"] == "Q1"


def test_evaluate_case_fail_single_cible_absente():
    """Un cas à cible unique échoue (FAIL) si sa cible est absente des résultats."""
    case = {
        "question": "Q1",
        "famille": "vocabulaire_source_opquast",
        "numeros_regle_attendus": [139],
    }

    result = evaluate_case(case, numeros_retournes=[42, 7, 8])

    assert result["verdict"] == "FAIL"


def test_evaluate_case_pass_toutes_cibles_multiples_trouvees():
    """Un cas à cibles multiples réussit (PASS) si toutes les cibles sont retrouvées."""
    case = {"question": "Q1", "famille": "regles_concurrentes", "numeros_regle_attendus": [58, 79]}

    result = evaluate_case(case, numeros_retournes=[58, 79, 152])

    assert result["verdict"] == "PASS"


def test_evaluate_case_partiel_certaines_cibles_trouvees():
    """Un cas à cibles multiples est PARTIEL si certaines cibles manquent."""
    case = {
        "question": "Q1",
        "famille": "regles_concurrentes",
        "numeros_regle_attendus": [58, 79, 152],
    }

    result = evaluate_case(case, numeros_retournes=[58, 152])

    assert result["verdict"] == "PARTIEL"


def test_evaluate_case_fail_aucune_cible_multiple_trouvee():
    """Un cas à cibles multiples échoue (FAIL) si aucune cible n'est retrouvée."""
    case = {"question": "Q1", "famille": "regles_concurrentes", "numeros_regle_attendus": [58, 79]}

    result = evaluate_case(case, numeros_retournes=[1, 2, 3])

    assert result["verdict"] == "FAIL"


def test_evaluate_case_fail_sans_reponse_attendue():
    """Un cas sans_reponse (numeros_regle_attendus vide) est toujours FAIL."""
    case = {"question": "Q1", "famille": "sans_reponse", "numeros_regle_attendus": []}

    result = evaluate_case(case, numeros_retournes=[1, 2, 3])

    assert result["verdict"] == "FAIL"


def test_compute_taux_par_famille_un_seul_groupe():
    """Le taux d'une famille est le ratio PASS / (total - PARTIEL)."""
    evaluations = [
        {"famille": "vocabulaire_source_opquast", "verdict": "PASS"},
        {"famille": "vocabulaire_source_opquast", "verdict": "PASS"},
        {"famille": "vocabulaire_source_opquast", "verdict": "FAIL"},
    ]

    resultat = compute_taux_par_famille(evaluations)

    assert resultat["vocabulaire_source_opquast"] == {
        "taux": 2 / 3,
        "reussis": 2,
        "total": 3,
        "partiels": 0,
    }


def test_compute_taux_par_famille_exclut_les_partiels():
    """Les cas PARTIEL sont retirés du dénominateur, comptés à part."""
    evaluations = [
        {"famille": "regles_concurrentes", "verdict": "PASS"},
        {"famille": "regles_concurrentes", "verdict": "PARTIEL"},
        {"famille": "regles_concurrentes", "verdict": "FAIL"},
    ]

    resultat = compute_taux_par_famille(evaluations)

    assert resultat["regles_concurrentes"] == {
        "taux": 1 / 2,
        "reussis": 1,
        "total": 2,
        "partiels": 1,
    }


def test_compute_taux_par_famille_groupes_independants():
    """Chaque famille a son propre taux, indépendant des autres."""
    evaluations = [
        {"famille": "vocabulaire_source_opquast", "verdict": "PASS"},
        {"famille": "sans_reponse", "verdict": "FAIL"},
        {"famille": "sans_reponse", "verdict": "FAIL"},
    ]

    resultat = compute_taux_par_famille(evaluations)

    assert resultat["vocabulaire_source_opquast"]["taux"] == 1.0
    assert resultat["sans_reponse"]["taux"] == 0.0


def test_compute_taux_par_famille_uniquement_partiels_donne_zero():
    """Une famille entièrement composée de PARTIEL a un taux de 0.0 (pas de division par zéro)."""
    evaluations = [
        {"famille": "regles_concurrentes", "verdict": "PARTIEL"},
    ]

    resultat = compute_taux_par_famille(evaluations)

    assert resultat["regles_concurrentes"] == {
        "taux": 0.0,
        "reussis": 0,
        "total": 0,
        "partiels": 1,
    }


def test_is_acceptable_true_when_all_familles_above_seuil():
    """Le jeu est acceptable si toutes les familles atteignent le seuil."""
    taux_par_famille = {
        "vocabulaire_source_opquast": {"taux": 0.8, "reussis": 4, "total": 5, "partiels": 0},
        "regles_concurrentes": {"taux": 1.0, "reussis": 3, "total": 3, "partiels": 0},
    }

    assert is_acceptable(taux_par_famille, seuil=0.8) is True


def test_is_acceptable_false_when_one_famille_below_seuil():
    """Le jeu échoue si au moins une famille est sous le seuil."""
    taux_par_famille = {
        "vocabulaire_source_opquast": {"taux": 0.5, "reussis": 2, "total": 4, "partiels": 0},
        "regles_concurrentes": {"taux": 1.0, "reussis": 3, "total": 3, "partiels": 0},
    }

    assert is_acceptable(taux_par_famille, seuil=0.8) is False


def test_is_acceptable_ignores_sans_reponse_famille():
    """La famille sans_reponse n'entre jamais dans le calcul, même à 0%."""
    taux_par_famille = {
        "vocabulaire_source_opquast": {"taux": 1.0, "reussis": 4, "total": 4, "partiels": 0},
        "sans_reponse": {"taux": 0.0, "reussis": 0, "total": 2, "partiels": 0},
    }

    assert is_acceptable(taux_par_famille, seuil=0.8) is True


def test_format_dataset_versions_single_version():
    """Un jeu de données homogène tient sur une seule entrée."""
    summary = [{"prompt_version": 5, "llm_model": "kimi-k2.6", "nombre_regles": 245}]

    assert format_dataset_versions(summary) == "prompt_version=5 (kimi-k2.6): 245 règles"


def test_metriques_scores_top1_et_top15():
    """top1 = meilleur score, top15 = score du 15e candidat une fois trié."""
    candidats = [(i, 1.0 - i * 0.05) for i in range(20)]  # scores de 1.0 à 0.05

    resultat = metriques_scores(candidats)

    assert resultat["top1"] == 1.0
    assert resultat["top15"] == pytest.approx(1.0 - 14 * 0.05)
    assert resultat["ecart"] == pytest.approx(resultat["top1"] - resultat["top15"])


def test_metriques_scores_ignore_l_ordre_d_entree():
    """Le tri se fait par score, indépendamment de l'ordre de la liste passée."""
    candidats = [(1, 0.2), (2, 0.9), (3, 0.5)]

    resultat = metriques_scores(candidats)

    assert resultat["top1"] == 0.9


def test_metriques_scores_moins_de_15_candidats():
    """Avec moins de 15 candidats, top15 retombe sur le dernier (le plus faible)."""
    candidats = [(1, 0.8), (2, 0.3)]

    resultat = metriques_scores(candidats)

    assert resultat["top15"] == 0.3


def test_format_dataset_versions_mixed_versions():
    """Un jeu de données mélangé liste chaque combinaison séparément."""
    summary = [
        {"prompt_version": 5, "llm_model": "kimi-k2.6", "nombre_regles": 234},
        {"prompt_version": 6, "llm_model": "kimi-k2.6", "nombre_regles": 11},
    ]

    assert format_dataset_versions(summary) == (
        "prompt_version=5 (kimi-k2.6): 234 règles ; prompt_version=6 (kimi-k2.6): 11 règles"
    )


def test_rang_meilleure_cible_trouvee():
    """Retourne le rang (1-indexé) de la première cible rencontrée."""
    candidats_tries = [42, 139, 7, 200]

    assert rang_meilleure_cible(candidats_tries, [139]) == 2


def test_rang_meilleure_cible_la_plus_haute_gagne():
    """À cibles multiples, le rang retenu est celui de la mieux placée."""
    candidats_tries = [42, 139, 7, 200]

    assert rang_meilleure_cible(candidats_tries, [200, 139]) == 2


def test_rang_meilleure_cible_absente():
    """Aucune cible dans les candidats retourne None."""
    candidats_tries = [42, 7, 8]

    assert rang_meilleure_cible(candidats_tries, [139]) is None


def test_calculer_mrr_moyenne_des_inverses():
    """MRR = moyenne de 1/rang."""
    rangs = [1, 2, 4]

    assert calculer_mrr(rangs) == pytest.approx((1 / 1 + 1 / 2 + 1 / 4) / 3)


def test_calculer_mrr_cible_absente_contribue_zero():
    """Une cible absente (rang None) contribue 0 au MRR, pas une erreur."""
    rangs = [1, None]

    assert calculer_mrr(rangs) == pytest.approx((1 / 1 + 0.0) / 2)


def test_calculer_mrr_liste_vide():
    """Une liste vide retourne 0.0 (pas de division par zéro)."""
    assert calculer_mrr([]) == 0.0


def test_calculer_recall_a_k_cible_unique_trouvee():
    """Cible unique dans le top-k : recall = 1.0."""
    candidats_tries = [1, 2, 3, 4, 5]

    assert calculer_recall_a_k(candidats_tries, [3], k=5) == 1.0


def test_calculer_recall_a_k_cible_unique_hors_top_k():
    """Cible unique hors du top-k : recall = 0.0."""
    candidats_tries = [1, 2, 3, 4, 5]

    assert calculer_recall_a_k(candidats_tries, [5], k=3) == 0.0


def test_calculer_recall_a_k_cibles_multiples_fraction():
    """Cibles multiples : fraction retrouvée dans le top-k."""
    candidats_tries = [1, 2, 3, 4, 5]

    assert calculer_recall_a_k(candidats_tries, [1, 5], k=3) == pytest.approx(0.5)


def test_cosine_similarity_matrix_trie_par_score_decroissant():
    """Les règles sont triées par similarité cosinus décroissante."""
    vecteur_question = [1.0, 0.0]
    vecteurs_regles = {1: [1.0, 0.0], 2: [0.0, 1.0], 3: [0.5, 0.5]}

    resultat = cosine_similarity_matrix(vecteur_question, vecteurs_regles)

    numeros = [n for n, _ in resultat]
    assert numeros == [1, 3, 2]
    assert resultat[0] == (1, pytest.approx(1.0))
    assert resultat[2] == (2, pytest.approx(0.0, abs=1e-9))


def test_retrieve_variante_union_garde_le_meilleur_score():
    """Une règle trouvée par deux sous-questions garde le meilleur score."""
    vecteurs_regles = {5: [1.0, 0.5]}
    sous_questions_vecteurs = [[1.0, 0.0], [0.5, 1.0]]

    resultat = retrieve_variante(sous_questions_vecteurs, vecteurs_regles, top_n=15)

    assert resultat == [(5, pytest.approx(0.894427, abs=1e-5))]


def test_retrieve_variante_fusionne_deux_sous_questions():
    """Deux sous-questions ciblant des règles différentes ramènent les deux,
    dans l'ordre de première apparition."""
    vecteurs_regles = {10: [1.0, 0.0], 20: [0.0, 1.0]}
    sous_questions_vecteurs = [[1.0, 0.0], [0.6, 0.8]]

    resultat = retrieve_variante(sous_questions_vecteurs, vecteurs_regles, top_n=2)

    assert resultat == [(10, pytest.approx(1.0)), (20, pytest.approx(0.8))]


def test_mesurer_variante_cible_absente_exclut_le_cas_du_resume_mais_pas_du_csv():
    """Un cas dont aucune cible n'a été vectorisée (ex. règle sans tag pour
    la variante "tags") ne contribue aucune entrée MRR/recall pour sa
    famille, mais produit quand même ses lignes CSV par candidat."""
    vecteurs_regles = {1: [1.0, 0.0], 2: [0.0, 1.0]}
    cases = [{"question": "Q1", "famille": "fam_a", "numeros_regle_attendus": [99]}]
    sous_questions_vecteurs_par_cas = [[[1.0, 0.0]]]

    lignes_csv, lignes_resume = mesurer_variante(
        "variante_test",
        vecteurs_regles,
        cases,
        sous_questions_vecteurs_par_cas,
        top_n=2,
        recall_ks=[1],
    )

    assert lignes_resume == []
    assert len(lignes_csv) == 2
    for ligne in lignes_csv:
        assert ligne["numeros_attendus"] == "99"
        assert ligne["cibles_mesurees"] == ""
        assert ligne["est_cible"] == "non"


def test_mesurer_variante_cible_trouvee_alimente_le_resume():
    """Un cas dont la cible a été vectorisée et retrouvée alimente le MRR
    et le recall de sa famille, et cibles_mesurees reflète la cible
    effectivement mesurée."""
    vecteurs_regles = {1: [1.0, 0.0], 2: [0.0, 1.0]}
    cases = [{"question": "Q1", "famille": "fam_a", "numeros_regle_attendus": [1]}]
    sous_questions_vecteurs_par_cas = [[[1.0, 0.0]]]

    lignes_csv, lignes_resume = mesurer_variante(
        "variante_test",
        vecteurs_regles,
        cases,
        sous_questions_vecteurs_par_cas,
        top_n=2,
        recall_ks=[1, 2],
    )

    assert lignes_resume == [
        {
            "variante": "variante_test",
            "famille": "fam_a",
            "mrr": 1.0,
            "recall_1": 1.0,
            "recall_2": 1.0,
        }
    ]
    assert len(lignes_csv) == 2
    ligne_cible = next(ligne for ligne in lignes_csv if ligne["numero_retourne"] == 1)
    assert ligne_cible["est_cible"] == "oui"
    assert ligne_cible["cibles_mesurees"] == "1"
    assert ligne_cible["numeros_attendus"] == "1"


def test_construire_resume_markdown_structure_et_arrondi():
    """Le Markdown contient l'en-tête, une ligne par entrée, et des valeurs
    arrondies à 3 décimales."""
    lignes = [
        {
            "variante": "baseline",
            "famille": "fam_a",
            "mrr": 0.5,
            "recall_1": 0.1,
            "recall_3": 0.2,
            "recall_5": 0.3,
            "recall_10": 0.4,
            "recall_15": 0.5,
        },
        {
            "variante": "tags",
            "famille": "fam_b",
            "mrr": 1 / 3,
            "recall_1": 0.0,
            "recall_3": 0.0,
            "recall_5": 1.0,
            "recall_10": 1.0,
            "recall_15": 1.0,
        },
    ]
    horodatage = datetime(2026, 9, 11, 9, 47)

    resultat = construire_resume_markdown(lignes, horodatage)

    assert (
        "| Variante | Famille | MRR | recall@1 | recall@3 | recall@5 | recall@10 | recall@15 |"
        in resultat
    )
    assert "|---|---|---|---|---|---|---|---|" in resultat
    assert "| baseline | fam_a | 0.500 | 0.100 | 0.200 | 0.300 | 0.400 | 0.500 |" in resultat
    assert "| tags | fam_b | 0.333 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 |" in resultat
    lignes_tableau = [ligne for ligne in resultat.splitlines() if ligne.startswith("|")]
    assert len(lignes_tableau) == len(lignes) + 2  # en-tête + séparateur + une ligne par entrée


def _cases_deux_familles() -> list[dict]:
    return [
        {"question": f"Q{i}", "famille": "fam_a", "numeros_regle_attendus": [1]}
        for i in range(6)
    ] + [
        {"question": f"R{i}", "famille": "fam_b", "numeros_regle_attendus": [2]}
        for i in range(3)
    ]


def test_tirer_jeu_reserve_partition_complete_sans_chevauchement():
    """Chaque cas se retrouve dans exactement un des deux sous-ensembles."""
    cases = _cases_deux_familles()

    exploration, reserve = tirer_jeu_reserve(cases, proportion=1 / 3, seed=42)

    assert len(exploration) + len(reserve) == len(cases)
    questions_exploration = {c["question"] for c in exploration}
    questions_reserve = {c["question"] for c in reserve}
    assert questions_exploration.isdisjoint(questions_reserve)
    assert questions_exploration | questions_reserve == {c["question"] for c in cases}


def test_tirer_jeu_reserve_respecte_la_proportion_par_famille():
    """~1/3 de chaque famille est réservé, pas seulement 1/3 du total
    (une famille à 3 cas ne doit pas se retrouver à 0 cas réservés)."""
    cases = _cases_deux_familles()

    exploration, reserve = tirer_jeu_reserve(cases, proportion=1 / 3, seed=42)

    reserve_fam_a = [c for c in reserve if c["famille"] == "fam_a"]
    reserve_fam_b = [c for c in reserve if c["famille"] == "fam_b"]
    assert len(reserve_fam_a) == 2  # round(6 * 1/3)
    assert len(reserve_fam_b) == 1  # round(3 * 1/3)


def test_tirer_jeu_reserve_deterministe_pour_une_meme_seed():
    """Deux appels avec la même seed et le même ordre d'entrée donnent
    exactement le même partitionnement — condition pour que le jeu
    réservé soit reproductible."""
    cases = _cases_deux_familles()

    exploration_1, reserve_1 = tirer_jeu_reserve(cases, proportion=1 / 3, seed=7)
    exploration_2, reserve_2 = tirer_jeu_reserve(cases, proportion=1 / 3, seed=7)

    assert [c["question"] for c in reserve_1] == [c["question"] for c in reserve_2]
    assert [c["question"] for c in exploration_1] == [c["question"] for c in exploration_2]
