"""Change le mot de passe d'un gestionnaire déjà existant.

provisionner_tenant (voir src/catalogue/provisionnement.py) ne touche jamais
au mot de passe d'un compte déjà créé, volontairement : relancer seed.py ou
ajouter_tenant.py ne doit jamais écraser en silence un mot de passe déjà
changé côté client. Ce script est donc le seul chemin pour en changer un
après coup — en particulier les comptes de démonstration
(voir data/seed/README.md) avant d'ouvrir un déploiement à qui que ce soit.

Usage (depuis la racine du projet, avec DATABASE_URL renseigné dans .env) :
    uv run python data/seed/changer_mot_de_passe.py gestionnaire@etoile.com

Le nouveau mot de passe est saisi en masqué, jamais passé en argument de la
commande : il resterait sinon lisible dans l'historique du terminal.
"""
import argparse
import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.auth.hachage import hash_mot_de_passe
from src.db.models import Utilisateur


def main() -> None:
    email = _lire_arguments().email

    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL manquant : vérifie le fichier .env")

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as session:
        utilisateur = session.query(Utilisateur).filter_by(email=email).first()
        if utilisateur is None:
            raise SystemExit(f"Aucun gestionnaire avec l'email « {email} ».")

        utilisateur.mot_de_passe_hache = hash_mot_de_passe(_demander_nouveau_mot_de_passe())
        session.commit()

    print(f"Mot de passe changé pour « {email} ».")


def _demander_nouveau_mot_de_passe() -> str:
    """Saisie masquée, redemandée une fois pour écarter une faute de frappe silencieuse"""
    while True:
        premiere_saisie = getpass.getpass("Nouveau mot de passe : ")
        confirmation = getpass.getpass("Confirmer : ")
        if premiere_saisie and premiere_saisie == confirmation:
            return premiere_saisie
        print("Les deux saisies ne correspondent pas, ou sont vides. Recommence.")


def _lire_arguments() -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("email", help="Email du gestionnaire dont le mot de passe change")
    return analyseur.parse_args()


if __name__ == "__main__":
    main()
