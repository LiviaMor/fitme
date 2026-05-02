from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class GarmentSize(str, Enum):
    PP = "PP"
    P = "P"
    M = "M"
    G = "G"
    GG = "GG"
    XG = "XG"


class GarmentCategory(str, Enum):
    CAMISETA = "camiseta"
    CAMISA = "camisa"
    VESTIDO = "vestido"
    CALCA = "calca"
    SAIA = "saia"
    BLAZER = "blazer"
    JAQUETA = "jaqueta"


class GarmentMeasurements(BaseModel):
    """Medidas técnicas da peça de roupa."""
    shoulder_cm: Optional[float] = Field(None, description="Ombro da peça em cm")
    bust_cm: Optional[float] = Field(None, description="Busto da peça em cm")
    waist_cm: Optional[float] = Field(None, description="Cintura da peça em cm")
    hip_cm: Optional[float] = Field(None, description="Quadril da peça em cm")
    length_cm: Optional[float] = Field(None, description="Comprimento da peça em cm")


class Garment(BaseModel):
    """Peça de roupa do catálogo."""
    id: str = Field(..., description="ID único da peça")
    name: str = Field(..., description="Nome da peça")
    category: GarmentCategory
    size: GarmentSize
    color: str = Field(..., description="Cor principal da peça")
    color_hex: str = Field(..., description="Cor em HEX")
    measurements: GarmentMeasurements
    image_url: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[float] = None


class FitResult(BaseModel):
    """Resultado da análise de caimento."""
    garment_id: str
    fit_score: float = Field(..., ge=0, le=10, description="Nota de caimento 0-10")
    color_match_score: float = Field(..., ge=0, le=10, description="Nota de combinação de cor")
    overall_score: float = Field(..., ge=0, le=10, description="Nota geral")
    fit_description: str = Field(..., description="Descrição do caimento")
    style_advice: str = Field(..., description="Consultoria de estilo")
    recommended_size: GarmentSize
