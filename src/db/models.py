"""Modèles SQLAlchemy — une classe par table, voir docs/DONNEES.md"""
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Integer, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def generate_uuid() -> str:
    """Génère un identifiant unique et non séquentiel"""
    return str(uuid.uuid4())


class Tenant(Base):
    """Une entreprise cliente du produit"""
    __tablename__ = "tenant"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    ville: Mapped[str | None] = mapped_column(String(100))
    coordonnees: Mapped[str | None] = mapped_column(Text)
    logo: Mapped[str | None] = mapped_column(String(500))
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    date_creation: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    utilisateurs: Mapped[list["Utilisateur"]] = relationship(back_populates="tenant")
    ressources: Mapped[list["Ressource"]] = relationship(back_populates="tenant")
    modeles_evenement: Mapped[list["ModeleEvenement"]] = relationship(back_populates="tenant")
    demandes: Mapped[list["Demande"]] = relationship(back_populates="tenant")
    devis: Mapped[list["Devis"]] = relationship(back_populates="tenant")


class Utilisateur(Base):
    """Un gestionnaire rattaché à un tenant, utilisateur du tableau de bord"""
    __tablename__ = "utilisateur"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    mot_de_passe_hache: Mapped[str] = mapped_column(String(255), nullable=False)
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    date_creation: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    derniere_connexion: Mapped[datetime | None] = mapped_column(DateTime)

    tenant: Mapped["Tenant"] = relationship(back_populates="utilisateurs")


class Ressource(Base):
    """Tout ce qu'un tenant peut facturer : salle, mobilier, prestation..."""
    __tablename__ = "ressource"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), nullable=False, index=True)
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    categorie: Mapped[str] = mapped_column(String(50), nullable=False)
    secteur: Mapped[str] = mapped_column(String(50), nullable=False, default="evenementiel")
    unite_facturation: Mapped[str] = mapped_column(String(20), nullable=False)
    prix_unitaire: Mapped[int] = mapped_column(Integer, nullable=False)
    attributs: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    date_creation: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    date_modification: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="ressources")


class ModeleEvenement(Base):
    """Le patron d'un type d'événement : catégories attendues et règles de quantité"""
    __tablename__ = "modele_evenement"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), nullable=False, index=True)
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    lignes_par_defaut: Mapped[dict] = mapped_column(JSON, nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="modeles_evenement")


class Demande(Base):
    """Une conversation avec un prospect, en cours ou terminée"""
    __tablename__ = "demande"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), nullable=False, index=True)
    canal: Mapped[str] = mapped_column(String(20), nullable=False)
    identifiant_prospect: Mapped[str | None] = mapped_column(String(255))
    etat: Mapped[str] = mapped_column(String(20), nullable=False, default="en_cours")
    besoin: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    date_creation: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    date_modification: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    tenant: Mapped["Tenant"] = relationship(back_populates="demandes")
    devis: Mapped[list["Devis"]] = relationship(back_populates="demande")


class Devis(Base):
    """Un devis émis, figé : ses lignes ne sont jamais recalculées après coup"""
    __tablename__ = "devis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenant.id"), nullable=False, index=True)
    demande_id: Mapped[str] = mapped_column(ForeignKey("demande.id"), nullable=False, index=True)
    lignes: Mapped[list] = mapped_column(JSON, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    devise: Mapped[str] = mapped_column(String(3), nullable=False, default="XAF")
    date_emission: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    date_validite: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    chemin_pdf: Mapped[str | None] = mapped_column(String(500))

    tenant: Mapped["Tenant"] = relationship(back_populates="devis")
    demande: Mapped["Demande"] = relationship(back_populates="devis")
