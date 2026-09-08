"""
Les deux domaines ont chacun leur base déclarative.

Sans cette séparation, l'autogenerate de chaque chaîne Alembic verrait les
tables de l'autre domaine et proposerait de les supprimer.
"""

import app.models.etat  # noqa: F401 — enregistre etat_donnees
import app.models.metier  # noqa: F401 — enregistre les tables métier
import app.models.referentiel  # noqa: F401 — enregistre les tables du référentiel
from app.models.base import BaseAudit, BaseReferentiel

TABLES_REFERENTIEL = {
    "theme",
    "regle",
    "objectif",
    "phase",
    "tag",
    "objectif_regle",
    "phase_regle",
    "regle_tag",
    "etat_donnees",
}

TABLES_AUDIT = {
    "utilisateur",
    "audit",
    "page",
    "audit_page",
    "audit_regle",
    "constat",
}


def test_le_referentiel_ne_declare_que_ses_tables():
    assert set(BaseReferentiel.metadata.tables) == TABLES_REFERENTIEL


def test_le_domaine_audit_ne_declare_que_ses_tables():
    assert set(BaseAudit.metadata.tables) == TABLES_AUDIT


def test_les_deux_metadata_sont_disjointes():
    communes = set(BaseReferentiel.metadata.tables) & set(BaseAudit.metadata.tables)
    assert communes == set(), f"tables déclarées deux fois : {communes}"


def test_audit_regle_reference_le_numero_sans_fk():
    """La frontière entre bases interdit une FK : on référence la clé métier."""
    table = BaseAudit.metadata.tables["audit_regle"]

    assert "regle_numero" in table.c
    assert "regle_id" not in table.c
    assert [fk.target_fullname for fk in table.foreign_keys] == ["audit.id"]
    assert [colonne.name for colonne in table.primary_key] == [
        "audit_id",
        "regle_numero",
    ]


def test_constat_reference_le_numero_sans_fk():
    table = BaseAudit.metadata.tables["constat"]

    assert "regle_numero" in table.c
    assert "regle_id" not in table.c
    assert sorted(fk.target_fullname for fk in table.foreign_keys) == [
        "audit.id",
        "page.id",
    ]
    assert [colonne.name for colonne in table.primary_key] == [
        "audit_id",
        "page_id",
        "regle_numero",
    ]
