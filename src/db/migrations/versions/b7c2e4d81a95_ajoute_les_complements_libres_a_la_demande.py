"""ajoute les complements libres du prospect a la demande

Revision ID: b7c2e4d81a95
Revises: f4a1c9e27b03
Create Date: 2026-09-10

Deux colonnes de texte libre, alimentées par le prospect avant l'estimation :
ce dont il a besoin et que le catalogue ne propose pas, et un mot pour
l'entreprise. Elles vivent hors du JSON besoin, qui ne contient que ce que
l'extraction produit.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7c2e4d81a95"
down_revision: Union[str, Sequence[str], None] = "f4a1c9e27b03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("demande", sa.Column("besoins_hors_catalogue", sa.Text(), nullable=True))
    op.add_column("demande", sa.Column("commentaire", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("demande", "commentaire")
    op.drop_column("demande", "besoins_hors_catalogue")
