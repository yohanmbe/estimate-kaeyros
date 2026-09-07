"""Fixtures partagées aux tests touchant la base de données ou l'extraction"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from src.db.models import Base
from src.db.session import _engine
from src.extraction.fabrique import FOURNISSEUR_MOCK

# Tables métier porteuses de tenant_id : toute lecture ou écriture doit les
# filtrer dessus. tenant et utilisateur en sont volontairement absents, parce
# que ce sont elles qui établissent le tenant : la connexion cherche un
# utilisateur par son email et le tenant par son slug, avant que le moindre
# tenant_id ne soit connu (voir src/auth/connexion.py et src/canaux/tenant.py).
TABLES_CLOISONNEES = frozenset(
    {"ressource", "modele_evenement", "prospect", "demande", "devis"}
)


class RequeteNonCloisonnee(AssertionError):
    """Une requête a touché une table métier sans filtrer sur tenant_id"""


def requete_non_cloisonnee(instruction: str) -> bool:
    """Dit si l'instruction SQL lit ou écrit une table métier sans tenant_id.

    Le filtre est cherché après le WHERE et non dans toute l'instruction : un
    SELECT sur une table métier ramène de toute façon sa colonne tenant_id dans
    la liste des colonnes lues, ce qui suffirait à faire passer pour cloisonnée
    une requête qui ne filtre rien.

    Les INSERT sont ignorés, ils portent tenant_id dans leurs valeurs et non
    dans un WHERE, ainsi que le DDL de création des bases de test.
    """
    normalisee = " ".join(instruction.lower().split())
    if not normalisee.startswith(("select", "update", "delete")):
        return False
    if not any(table in normalisee for table in TABLES_CLOISONNEES):
        return False
    _, _, filtre = normalisee.partition(" where ")
    return "tenant_id" not in filtre


@pytest.fixture()
def requetes_cloisonnees():
    """Fait échouer le test dès qu'une requête oublie de filtrer sur tenant_id.

    Branché sur toutes les connexions SQLAlchemy pendant le test, y compris
    celles que le code ouvre lui-même : c'est le seul filet qui attrape une
    requête ajoutée plus tard sans son filtre. L'erreur est levée au moment de
    l'exécution pour désigner l'appel fautif, pas en fin de test.

    Ce que ce filet ne garantit pas : il ne voit que les requêtes qu'un test
    exécute réellement, et un tenant_id présent dans une sous-requête seulement
    le satisferait à tort. Il rend l'oubli improbable, pas impossible.
    """

    def surveiller(connexion, curseur, instruction, parametres, contexte, executemany):
        if requete_non_cloisonnee(instruction):
            raise RequeteNonCloisonnee(
                "requête sans filtre tenant_id sur une table métier :\n" + instruction
            )

    event.listen(Engine, "before_cursor_execute", surveiller)
    yield
    event.remove(Engine, "before_cursor_execute", surveiller)


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
