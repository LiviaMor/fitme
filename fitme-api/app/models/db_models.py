"""
Modelos SQLAlchemy com pgvector para armazenamento de vetores corporais.

Vetores armazenados:
- landmarks_vector: 99 dims (33 landmarks × 3 coords x,y,z)
- measurements_vector: 12 dims (medidas normalizadas)
"""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class BodyProfile(Base):
    """Perfil corporal do cliente com vetores para busca por similaridade."""

    __tablename__ = "body_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Identificação (anônimo ou vinculado a e-commerce)
    external_user_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=True)

    # Medidas brutas
    height_cm = Column(Float, nullable=False)
    shoulder_width_cm = Column(Float)
    bust_circumference_cm = Column(Float)
    waist_circumference_cm = Column(Float)
    hip_circumference_cm = Column(Float)
    inseam_cm = Column(Float)
    pants_length_cm = Column(Float)
    shirt_length_cm = Column(Float)
    armhole_depth_cm = Column(Float)

    # Tom de pele
    skin_hex = Column(String(7))
    skin_undertone = Column(String(20))
    body_type = Column(String(30))

    # === VETORES (pgvector) ===
    # 33 landmarks × 3 (x, y, z) = 99 dimensões
    landmarks_vector = Column(Vector(99), nullable=True)

    # Medidas normalizadas para busca por similaridade
    # [shoulder, bust, waist, hip, inseam, height, bust/waist ratio,
    #  waist/hip ratio, shoulder/hip ratio, chest_depth, waist_depth, hip_depth]
    measurements_vector = Column(Vector(12), nullable=True)

    # Relacionamentos
    tryon_history = relationship("TryOnHistory", back_populates="profile")


class TryOnHistory(Base):
    """Histórico de try-ons para recomendação e analytics."""

    __tablename__ = "tryon_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile_id = Column(UUID(as_uuid=True), ForeignKey("body_profiles.id"), nullable=False)
    profile = relationship("BodyProfile", back_populates="tryon_history")

    # Peça
    garment_id = Column(String(255), nullable=False)
    garment_name = Column(String(500))
    garment_category = Column(String(50))
    garment_size = Column(String(10))
    garment_color = Column(String(100))
    garment_url = Column(Text, nullable=True)

    # Resultado
    fit_score = Column(Float)
    color_match_score = Column(Float)
    overall_score = Column(Float)
    recommended_size = Column(String(10))

    # Feedback do usuário (pós-compra)
    user_rating = Column(Integer, nullable=True)  # 1-5
    purchased = Column(Integer, nullable=True)     # 0 ou 1
    returned = Column(Integer, nullable=True)      # 0 ou 1


class GarmentVector(Base):
    """Vetores de peças para match com perfis corporais."""

    __tablename__ = "garment_vectors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    garment_id = Column(String(255), unique=True, nullable=False, index=True)
    garment_name = Column(String(500))
    category = Column(String(50))

    # Medidas da peça normalizadas (mesmo formato do measurements_vector)
    garment_vector = Column(Vector(12), nullable=True)

    # Vetor de "perfil ideal" - média dos perfis que deram fit_score > 8
    ideal_body_vector = Column(Vector(12), nullable=True)
