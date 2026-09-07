"""rend la date de validite du devis facultative

Revision ID: f4a1c9e27b03
Revises: d3bb338e15c7
Create Date: 2026-09-07 18:05:00.000000

Ecrite a la main : une seule colonne change de nullabilite, l'autogeneration
n'apporte rien et exigerait une connexion a la base de production.

Le produit s'arrete a l'estimation (D08). Une date de validite serait un
engagement commercial qu'il ne peut pas tenir, et la remplir d'office
reviendrait a inventer une donnee. La colonne reste declaree mais vide.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f4a1c9e27b03"
down_revision: Union[str, Sequence[str], None] = "d3bb338e15c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("devis", "date_validite", existing_type=sa.DateTime(), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Revenir en arriere exige une valeur pour les lignes deja emises sans
    # date : la date d'emission est la seule dont on soit sur.
    op.execute("UPDATE devis SET date_validite = date_emission WHERE date_validite IS NULL")
    op.alter_column("devis", "date_validite", existing_type=sa.DateTime(), nullable=False)
