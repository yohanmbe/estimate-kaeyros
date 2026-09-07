"""Provisionne un vrai client à partir d'un fichier JSON (voir D25).

Contrairement à seed.py (le tenant de démonstration, codé en dur), ce script
lit sa configuration dans un fichier tenu hors du dépôt (voir
data/clients/README.md et .gitignore) : chaque client a ses propres
ressources et prix, qui n'ont rien à faire dans le code source.

Usage (depuis la racine du projet, avec DATABASE_URL renseigné dans .env) :
    uv run python data/seed/ajouter_tenant.py data/clients/mon-client.json
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.catalogue.provisionnement import configuration_depuis_dict, provisionner_tenant


def main() -> None:
    arguments = _lire_arguments()
    donnees = json.loads(Path(arguments.chemin_config).read_text(encoding="utf-8"))
    configuration = configuration_depuis_dict(donnees)

    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL manquant : vérifie le fichier .env")

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as session:
        _, gestionnaire_cree = provisionner_tenant(session, configuration)
        session.commit()

    print(
        f"Tenant « {configuration.nom} » (slug={configuration.slug}) : "
        f"{len(configuration.ressources)} ressources, modèle Mariage à jour."
    )
    print(f"Chat accessible à l'adresse : ?slug={configuration.slug}")
    if configuration.logo:
        print(f"Logo attendu dans data/logos/{configuration.logo}")
    if gestionnaire_cree:
        print(
            f"Gestionnaire créé — email: {configuration.gestionnaire.email}  "
            f"mot de passe: {configuration.gestionnaire.mot_de_passe}"
        )
        print("À communiquer au client puis à retirer du fichier de configuration.")
    else:
        print(f"Gestionnaire déjà présent ({configuration.gestionnaire.email}), mot de passe inchangé.")


def _lire_arguments() -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument(
        "chemin_config", help="Chemin du fichier JSON décrivant le tenant (voir data/clients/exemple.json)"
    )
    return analyseur.parse_args()


if __name__ == "__main__":
    main()
