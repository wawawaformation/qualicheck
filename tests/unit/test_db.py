"""Composition de l'URL de connexion PostgreSQL de l'étage données."""

from app import db


def test_url_composee_depuis_lenvironnement(monkeypatch):
    monkeypatch.setenv("POSTGRES_USER", "utilisateur")
    monkeypatch.setenv("POSTGRES_PASSWORD", "motdepasse")
    monkeypatch.setenv("POSTGRES_HOST", "serveur")
    monkeypatch.setenv("POSTGRES_PORT", "1234")
    monkeypatch.setenv("POSTGRES_DB", "base")

    assert db.build_database_url() == "postgresql://utilisateur:motdepasse@serveur:1234/base"


def test_hote_et_port_ont_des_valeurs_par_defaut(monkeypatch):
    monkeypatch.setenv("POSTGRES_USER", "utilisateur")
    monkeypatch.setenv("POSTGRES_PASSWORD", "motdepasse")
    monkeypatch.setenv("POSTGRES_DB", "base")
    monkeypatch.delenv("POSTGRES_HOST", raising=False)
    monkeypatch.delenv("POSTGRES_PORT", raising=False)

    assert db.build_database_url() == "postgresql://utilisateur:motdepasse@localhost:5432/base"
