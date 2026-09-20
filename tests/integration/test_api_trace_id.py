from unittest.mock import patch

from fastapi.testclient import TestClient

from app.agent_us2.loop import ResultatAgent
from app.agent_us2.main import app

client = TestClient(app)


def test_poser_question_renvoie_un_trace_id():
    resultat = ResultatAgent(
        reponse="Reponse de test, regle 1.",
        regles_citees=[{"numero": 1, "intitule": "Test"}],
        nb_tours=1,
        duree_s=0.1,
        tokens_entree=10,
        tokens_sortie=5,
        cout_euros_estime=0.0001,
        trace_id="abcd1234abcd1234abcd1234abcd1234",
    )

    with patch("app.agent_us2.api.repondre", return_value=resultat):
        response = client.post("/questions", json={"question": "Question de test ?"})

    assert response.status_code == 200
    corps = response.json()
    assert corps["trace_id"] == "abcd1234abcd1234abcd1234abcd1234"
