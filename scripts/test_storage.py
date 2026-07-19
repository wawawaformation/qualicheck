"""
Test insertion d'une règle sans passer par le LLM.
Vérifie que le schéma supporte les longs textes du scraping.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.referentiel import Objectif, ObjectifRegle, Regle, Theme

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
host = os.getenv("POSTGRES_HOST", "localhost")
port = os.getenv("POSTGRES_PORT", "5432")
db = os.getenv("POSTGRES_DB")

if not all([user, password, host, db]):
    raise ValueError("PostgreSQL config incomplete in .env")

DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db}"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Crée un thème de test
    theme = Theme(theme="Test")
    session.add(theme)
    session.flush()

    # Crée un objectif avec du texte long (scraping simulé, ~280 chars)
    long_objectif = "Éviter la désorientation des utilisateurs d'aides techniques. " * 5
    objectif = Objectif(objectif=long_objectif)
    session.add(objectif)
    session.flush()

    # Crée une règle de test avec du texte long (multiplication = texte volumineux)
    regle = Regle(
        numero=999,
        theme_id=theme.id,
        intitule="Test rule with long text " * 30,  # ~750 chars
        solution="Recourir à des gestionnaires d'événements universels. " * 12,  # ~640 chars
        controle="Vérification appliquée à l'ensemble des éléments interactifs. " * 12,  # long
        strategie_analyse="test",
        strategie_source="test",
        guide_analyse="Test guide",
    )
    session.add(regle)
    session.flush()

    # Crée l'association
    session.add(ObjectifRegle(regle_id=regle.id, objectif_id=objectif.id))
    session.commit()

    print("✓ Test insertion réussi")
    print(f"  Règle {regle.numero} créée")
    print(f"  Intitule: {len(regle.intitule)} chars")
    print(f"  Solution: {len(regle.solution)} chars")
    print(f"  Controle: {len(regle.controle)} chars")
    print(f"  Objectif: {len(objectif.objectif)} chars")

except Exception as e:
    session.rollback()
    print(f"✗ Erreur: {e}")
    raise
finally:
    session.close()
