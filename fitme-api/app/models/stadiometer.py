"""Modelos para o estadiômetro digital Welmy."""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class WelmyModelEnum(str, Enum):
    """Modelos de estadiômetro Welmy disponíveis."""
    W200_5 = "W200/5"
    W200_5A = "W200/5A"
    W110H = "W110H"
    PEDIATRICO = "Pediátrico"


class HeightMeasurementResponse(BaseModel):
    """Resposta da medição de altura pelo estadiômetro digital."""

    model_config = {"protected_namespaces": ()}

    height_cm: float = Field(..., description="Altura medida em cm (valor bruto)")
    height_rounded_cm: float = Field(
        ..., description="Altura arredondada pela resolução do modelo Welmy"
    )
    model_used: str = Field(..., description="Modelo Welmy utilizado")
    confidence: float = Field(
        ..., ge=0, le=1, description="Confiança da medição (0-1)"
    )
    calibration_method: str = Field(
        ..., description="Método de calibração usado"
    )
    within_range: bool = Field(
        ..., description="Se a medida está dentro da faixa do modelo"
    )
    grid_detected: bool = Field(
        ..., description="Se a grade milimétrica foi detectada"
    )
    message: str = Field(..., description="Mensagem sobre a medição")

    # Medidas derivadas (fórmulas de modelagem)
    crotch_height_cm: Optional[float] = Field(
        None, description="Altura do gancho (altura x 16 / 100)"
    )
    pants_length_cm: Optional[float] = Field(
        None, description="Comprimento da calça (altura x 61 / 100)"
    )
    shirt_length_cm: Optional[float] = Field(
        None, description="Comprimento da camisa (altura x 45 / 100)"
    )


class StadiometerInfoResponse(BaseModel):
    """Informações sobre um modelo de estadiômetro Welmy."""
    model: str
    min_height_cm: float
    max_height_cm: float
    resolution_cm: float
    precision_cm: float
    description: str
