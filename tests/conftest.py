"""Fixtures partagées aux tests touchant la base de données ou l'extraction"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.db.models import Base
from src.db.session import _engine
from src.extraction.fabrique import FOURNISSEUR_MOCK


@pytest.fixture(autouse=True)
def extraction_sans_reseau(monkeypatch):
    """Force le mock pour tous les tests, quel que soit le .env de la machine.

    Sans ce garde-fou, un poste configuré en LLM_PROVIDER=groq ferait appeler
    un vrai modèle par les tests de l'écran (voir CONVENTIONS.md : aucun test
    n'appelle un vrai LLM). Les tests d'intégration, eux, construisent leur
    extracteur explicitement et ne passent pas par cette variable.
    """
    monkeypatch.setenv("LLM_PROVIDER", FOURNISSEUR_MOCK)


@pytest.fixture()
def session():
    """Session SQLAlchemy sur une base SQLite en mémoire, neuve à chaque test.

    Jamais de vraie base Postgres dans les tests (voir CONVENTIONS.md) : le
    schéma déclaré dans src/db/models.py est créé à la volée sur une base
    jetable, propre à chaque test.
    """
    moteur = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(moteur)
    with Session(moteur) as session:
        yield session


@pytest.fixture()
def base_branchee(tmp_path, monkeypatch):
    """Base SQLite jetable branchée à la place de Postgres, pour tout le test.

    Sert aux tests qui exécutent du code appelant lui-même ouvrir_session(),
    l'écran Streamlit en particulier. load_dotenv n'écrase pas une variable
    déjà définie : DATABASE_URL pointe donc bien vers cette base.
    """
    url = f"sqlite:///{tmp_path / 'estimate_test.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    _engine.cache_clear()

    moteur = create_engine(url)
    Base.metadata.create_all(moteur)
    with Session(moteur) as session:
        yield session

    _engine.cache_clear()
