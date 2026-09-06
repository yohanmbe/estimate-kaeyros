"""Fixtures partagées aux tests touchant la base de données"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.db.models import Base


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
