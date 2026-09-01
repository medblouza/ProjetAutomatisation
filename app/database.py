"""
database.py — Connexion PostgreSQL + modèles CDC & DesignJSON + fonctions CRUD.

Tables créées automatiquement au démarrage via `init_db()` :
  - `cdc`         : cahiers des charges générés
  - `design_json` : JSON Design générés depuis un fichier CDC

La chaîne de connexion provient de la variable d'environnement DATABASE_URL.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    create_engine,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Session

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Connexion
# ─────────────────────────────────────────────────────────────

DATABASE_URL: str = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL n'est pas défini. "
        "Ajoutez-le dans app/.env : DATABASE_URL=postgresql://..."
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # vérifie la connexion avant usage
    echo=False,
)


# ─────────────────────────────────────────────────────────────
# ORM Base & Modèle
# ─────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


class CDCRecord(Base):
    """
    Représentation ORM de la table `cdc`.

    Colonnes :
      id           – identifiant auto-incrémenté
      company_name – nom de l'entreprise / code CodeSage
      content      – contenu Markdown complet du CDC
      created_at   – horodatage UTC de création
    """

    __tablename__ = "cdc"

    id: int            = Column(Integer, primary_key=True, index=True)
    company_name: str  = Column(String(255), nullable=False, index=True)
    content: str       = Column(Text, nullable=False)
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class DesignJsonRecord(Base):
    """
    Représentation ORM de la table `design_json`.

    Colonnes :
      id           – identifiant auto-incrémenté
      filename     – nom du fichier CDC source uploadé
      company_name – nom de l'entreprise extrait du DesignJSON
      content      – contenu JSON complet (stringifié)
      created_at   – horodatage UTC de création
    """

    __tablename__ = "design_json"

    id: int            = Column(Integer, primary_key=True, index=True)
    filename: str      = Column(String(255), nullable=False, index=True)
    company_name: str  = Column(String(255), nullable=False, index=True)
    content: str       = Column(Text, nullable=False)
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


# ─────────────────────────────────────────────────────────────
# Initialisation (CREATE TABLE IF NOT EXISTS)
# ─────────────────────────────────────────────────────────────

def init_db() -> None:
    """Crée la table `cdc` si elle n'existe pas encore."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("[DB] Table `cdc` prête (créée ou déjà existante).")
    except Exception as exc:
        logger.error(f"[DB] Échec d'init_db : {exc}", exc_info=True)
        raise


# ─────────────────────────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────────────────────────

def save_cdc(company_name: str, content: str) -> Optional[CDCRecord]:
    """
    Insère un nouveau CDC en base.

    Retourne l'objet CDCRecord créé, ou None en cas d'erreur
    (pour ne pas bloquer la réponse API en cas d'échec BDD).
    """
    try:
        with Session(engine) as session:
            record = CDCRecord(
                company_name=company_name.strip() or "Entreprise inconnue",
                content=content,
                created_at=datetime.now(timezone.utc),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            logger.info(
                f"[DB] CDC sauvegardé — id={record.id}, company='{record.company_name}'"
            )
            return record
    except Exception as exc:
        logger.error(f"[DB] Échec save_cdc : {exc}", exc_info=True)
        return None


def get_all_cdc() -> list[dict]:
    """
    Retourne la liste de tous les CDC (id, company_name, created_at)
    triés du plus récent au plus ancien.

    Le champ `content` est volontairement exclu pour garder la réponse légère.
    """
    try:
        with Session(engine) as session:
            records = (
                session.query(
                    CDCRecord.id,
                    CDCRecord.company_name,
                    CDCRecord.created_at,
                )
                .order_by(CDCRecord.created_at.desc())
                .all()
            )
            return [
                {
                    "id": r.id,
                    "company_name": r.company_name,
                    "created_at": r.created_at.isoformat(),
                }
                for r in records
            ]
    except Exception as exc:
        logger.error(f"[DB] Échec get_all_cdc : {exc}", exc_info=True)
        return []


def get_cdc_by_id(cdc_id: int) -> Optional[dict]:
    """
    Retourne le CDC complet (contenu inclus) pour un identifiant donné.
    Retourne None si non trouvé.
    """
    try:
        with Session(engine) as session:
            record = session.query(CDCRecord).filter(CDCRecord.id == cdc_id).first()
            if record is None:
                return None
            return {
                "id": record.id,
                "company_name": record.company_name,
                "content": record.content,
                "created_at": record.created_at.isoformat(),
            }
    except Exception as exc:
        logger.error(f"[DB] Échec get_cdc_by_id({cdc_id}) : {exc}", exc_info=True)
        return None


def update_cdc(cdc_id: int, company_name: str, content: str) -> Optional[dict]:
    """
    Met à jour un CDC existant en base.
    """
    try:
        with Session(engine) as session:
            record = session.query(CDCRecord).filter(CDCRecord.id == cdc_id).first()
            if record is None:
                return None
            record.company_name = company_name.strip() or record.company_name
            record.content = content
            session.commit()
            session.refresh(record)
            logger.info(f"[DB] CDC mis à jour — id={record.id}, company='{record.company_name}'")
            return {
                "id": record.id,
                "company_name": record.company_name,
                "content": record.content,
                "created_at": record.created_at.isoformat(),
            }
    except Exception as exc:
        logger.error(f"[DB] Échec update_cdc({cdc_id}) : {exc}", exc_info=True)
        return None


def delete_cdc(cdc_id: int) -> bool:
    """
    Supprime un CDC en base.
    """
    try:
        with Session(engine) as session:
            record = session.query(CDCRecord).filter(CDCRecord.id == cdc_id).first()
            if record is None:
                return False
            session.delete(record)
            session.commit()
            logger.info(f"[DB] CDC supprimé — id={cdc_id}")
            return True
    except Exception as exc:
        logger.error(f"[DB] Échec delete_cdc({cdc_id}) : {exc}", exc_info=True)
        return False


# ─────────────────────────────────────────────────────────────
# CRUD — DesignJSON
# ─────────────────────────────────────────────────────────────

def save_design_json(filename: str, company_name: str, content: str) -> Optional[DesignJsonRecord]:
    """
    Insère un nouveau DesignJSON en base.

    Retourne l'objet DesignJsonRecord créé, ou None en cas d'erreur.
    """
    try:
        with Session(engine) as session:
            record = DesignJsonRecord(
                filename=filename.strip() or "fichier_inconnu",
                company_name=company_name.strip() or "Entreprise inconnue",
                content=content,
                created_at=datetime.now(timezone.utc),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            logger.info(
                f"[DB] DesignJSON sauvegardé — id={record.id}, file='{record.filename}', company='{record.company_name}'"
            )
            return record
    except Exception as exc:
        logger.error(f"[DB] Échec save_design_json : {exc}", exc_info=True)
        return None


def get_all_design_jsons() -> list[dict]:
    """
    Retourne la liste de tous les DesignJSON (id, filename, company_name, created_at)
    triés du plus récent au plus ancien.

    Le champ `content` est exclu pour garder la réponse légère.
    """
    try:
        with Session(engine) as session:
            records = (
                session.query(
                    DesignJsonRecord.id,
                    DesignJsonRecord.filename,
                    DesignJsonRecord.company_name,
                    DesignJsonRecord.created_at,
                )
                .order_by(DesignJsonRecord.created_at.desc())
                .all()
            )
            return [
                {
                    "id": r.id,
                    "filename": r.filename,
                    "company_name": r.company_name,
                    "created_at": r.created_at.isoformat(),
                }
                for r in records
            ]
    except Exception as exc:
        logger.error(f"[DB] Échec get_all_design_jsons : {exc}", exc_info=True)
        return []


def get_design_json_by_id(record_id: int) -> Optional[dict]:
    """
    Retourne le DesignJSON complet (contenu JSON inclus) pour un identifiant donné.
    Retourne None si non trouvé.
    """
    try:
        with Session(engine) as session:
            record = session.query(DesignJsonRecord).filter(DesignJsonRecord.id == record_id).first()
            if record is None:
                return None
            return {
                "id": record.id,
                "filename": record.filename,
                "company_name": record.company_name,
                "content": record.content,
                "created_at": record.created_at.isoformat(),
            }
    except Exception as exc:
        logger.error(f"[DB] Échec get_design_json_by_id({record_id}) : {exc}", exc_info=True)
        return None


def update_design_json(record_id: int, filename: str, company_name: str, content: str) -> Optional[dict]:
    """
    Met à jour un DesignJSON existant en base.
    """
    try:
        with Session(engine) as session:
            record = session.query(DesignJsonRecord).filter(DesignJsonRecord.id == record_id).first()
            if record is None:
                return None
            record.filename = filename.strip() or record.filename
            record.company_name = company_name.strip() or record.company_name
            record.content = content
            session.commit()
            session.refresh(record)
            logger.info(f"[DB] DesignJSON mis à jour — id={record.id}, company='{record.company_name}'")
            return {
                "id": record.id,
                "filename": record.filename,
                "company_name": record.company_name,
                "content": record.content,
                "created_at": record.created_at.isoformat(),
            }
    except Exception as exc:
        logger.error(f"[DB] Échec update_design_json({record_id}) : {exc}", exc_info=True)
        return None


def delete_design_json(record_id: int) -> bool:
    """
    Supprime un DesignJSON en base.
    """
    try:
        with Session(engine) as session:
            record = session.query(DesignJsonRecord).filter(DesignJsonRecord.id == record_id).first()
            if record is None:
                return False
            session.delete(record)
            session.commit()
            logger.info(f"[DB] DesignJSON supprimé — id={record_id}")
            return True
    except Exception as exc:
        logger.error(f"[DB] Échec delete_design_json({record_id}) : {exc}", exc_info=True)
        return False
