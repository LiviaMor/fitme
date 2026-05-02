from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class BodyType(str, Enum):
    TRIANGULO = "triangulo"
    TRIANGULO_INVERTIDO = "triangulo_invertido"
    RETANGULO = "retangulo"
    AMPULHETA = "ampulheta"
    OVAL = "oval"


class SkinUndertone(str, Enum):
    FRIO = "frio"
    QUENTE = "quente"
    NEUTRO = "neutro"


class BodyMeasurements(BaseModel):
    """Medidas corporais extraídas pela visão computacional."""
    shoulder_width_cm: float = Field(..., description="Largura dos ombros em cm")
    bust_cm: Optional[float] = Field(None, description="Medida do busto/tórax em cm")
    waist_cm: Optional[float] = Field(None, description="Medida da cintura em cm")
    hip_cm: Optional[float] = Field(None, description="Medida do quadril em cm")
    inseam_cm: Optional[float] = Field(None, description="Altura do gancho em cm (altura x 16 / 100)")
    pants_length_cm: Optional[float] = Field(None, description="Comprimento da calça em cm (altura x 61 / 100)")
    shirt_length_cm: Optional[float] = Field(None, description="Comprimento da camisa em cm (altura x 45 / 100)")
    armhole_depth_cm: Optional[float] = Field(None, description="Altura da cava em cm (tórax / 4.4)")
    height_cm: Optional[float] = Field(None, description="Altura estimada em cm")


class SkinAnalysis(BaseModel):
    """Análise do tom de pele."""
    hex_color: str = Field(..., description="Cor média da pele em HEX")
    undertone: SkinUndertone = Field(..., description="Subtom da pele")
    color_name: str = Field(..., description="Nome descritivo da cor")


class BodyAnalysisResult(BaseModel):
    """Resultado completo da análise corporal."""
    measurements: BodyMeasurements
    skin_analysis: SkinAnalysis
    body_type: BodyType
    confidence_score: float = Field(..., ge=0, le=1, description="Confiança da análise")
    landmarks_detected: int = Field(..., description="Pontos de referência detectados")
