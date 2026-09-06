"""Ouverture des sessions SQLAlchemy à partir de l'URL déclarée dans .env"""
import os
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session


@lru_cache(maxsize=1)
def _engine() -> Engine:
    """Construit le moteur de connexion une seule fois par processus.

    Streamlit réexécute le script à chaque interaction : sans ce cache, chaque
    rerun ouvrirait un pool de connexions supplémentaire.
    """
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL manquant : vérifie le fichier .env")
    return create_engine(url)


def ouvrir_session() -> Session:
    """Ouvre une session, que l'appelant referme (idéalement via un with)"""
    return Session(_engine())
