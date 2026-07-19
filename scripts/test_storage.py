"""
Test insertion d'une règle sans passer par le LLM.
Vérifie que le schéma supporte les longs textes du scraping.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.referentiel import Regle, Theme, Objectif, ObjectifRegle

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

    # Crée un objectif avec du texte long (scraping simulé)
    long_objectif = "Éviter à des utilisateurs d'aides techniques d'être désorientés par l'ouverture d'une nouvelle fenêtre qui ne sera pas toujours aisément perceptible et qui perturbe notamment l'utilisation de l'historique de navigation ou qui masquera dans un lecteur d'écran la fenêtre principale."
    objectif = Objectif(objectif=long_objectif)
    session.add(objectif)
    session.flush()

    # Crée une règle de test avec du texte long
    regle = Regle(
        numero=999,
        theme_id=theme.id,
        intitule="Test rule with long text " * 30,  # ~750 chars
        solution="Recourir à des gestionnaires d'événements universels en cas d'interaction basée sur Javascript (par exemple,onclick pour un lien a ou pour un champ ou contrôle) permettra de déclencher les actions sans dépendre de la souris. On remplacera les gestionnaires d'événements spécifiques à la souris (onmouseover par exemple) par un second gestionnaire permettant l'accès clavier (onfocus par exemple) ou encore fournir un moyen d'accès alternatif." * 3,  # ~600+ chars
        controle="Cette vérification s'applique à l'ensemble des éléments interactifs : hyperliens, boutons, champs de formulaires, widgets Javascript, etc. Le mode de navigation doit faire l'objet d'une indication clairement perceptible: utilisation des touches de navigation au clavier (Tab, Maj+Tab, flèches), touches d'activation (Entrée, Espace), touches de positionnement (Home, End, Pg Up, Pg Down) dans les listes, touches de déplacement, touche d'échappement pour fermer ou sortir. Autant que possible dans ce cas, ces touches spécifiques devraient être indiquées à l'utilisateur." * 2,  # ~600+ chars
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
