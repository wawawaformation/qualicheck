"""
Tests unitaires pour app/ingestion/rag_acceptance.py

Logique pure (load_cases, evaluate_case, compute_taux_reussite,
is_acceptable) — aucun appel réseau ni BDD réelle. query_top_n_numeros
n'est pas testée ici (nécessite une base réellement vectorisée), validée
par exécution réelle via `make rag-acceptance`.
"""

from app.ingestion.rag_acceptance import (
    compute_taux_reussite,
    evaluate_case,
    is_acceptable,
    load_cases,
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


def test_evaluate_case_success_when_expected_in_results():
    """Un cas réussit si numero_regle_attendue figure dans les résultats."""
    case = {"question": "Q1", "numero_regle_attendue": 139}

    result = evaluate_case(case, numeros_retournes=[42, 139, 7])

    assert result["reussi"] is True
    assert result["numeros_retournes"] == [42, 139, 7]
    assert result["question"] == "Q1"
    assert result["numero_regle_attendue"] == 139


def test_evaluate_case_failure_when_expected_absent():
    """Un cas échoue si numero_regle_attendue est absent des résultats."""
    case = {"question": "Q1", "numero_regle_attendue": 139}

    result = evaluate_case(case, numeros_retournes=[42, 7, 8])

    assert result["reussi"] is False


def test_compute_taux_reussite_ratio():
    """Le taux de réussite est le ratio cas réussis / total."""
    evaluations = [
        {"reussi": True},
        {"reussi": True},
        {"reussi": False},
        {"reussi": True},
    ]

    assert compute_taux_reussite(evaluations) == 0.75


def test_is_acceptable_true_when_taux_above_seuil():
    """is_acceptable est vrai si le taux atteint ou dépasse le seuil."""
    assert is_acceptable(taux=0.8, seuil=0.8) is True


def test_is_acceptable_false_when_taux_below_seuil():
    """is_acceptable est faux si le taux est strictement sous le seuil."""
    assert is_acceptable(taux=0.7, seuil=0.8) is False
