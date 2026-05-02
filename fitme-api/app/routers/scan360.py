"""
Router do Body Scanner 360°.

Recebe 2 fotos (frente + lado) e retorna medidas completas
incluindo circunferências reais de busto, cintura e quadril.
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from typing import Optional

import cv2
import numpy as np

from app.services.body_scanner_360 import BodyScanner360
from app.services.image_utils import fix_orientation

router = APIRouter()
scanner_360 = BodyScanner360()


class Scan360Response(BaseModel):
    """Resposta do escaneamento 360°."""

    # Medidas lineares
    height_cm: float = Field(..., description="Altura")
    shoulder_width_cm: float = Field(..., description="Largura dos ombros")
    inseam_cm: float = Field(..., description="Altura do gancho (altura×16/100)")
    pants_length_cm: float = Field(..., description="Comprimento calça (altura×61/100)")
    shirt_length_cm: float = Field(..., description="Comprimento camisa (altura×45/100)")
    armhole_depth_cm: float = Field(..., description="Altura da cava (tórax/4.4)")

    # Circunferências reais (calculadas com frente + lado)
    bust_circumference_cm: float = Field(..., description="Circunferência do busto")
    waist_circumference_cm: float = Field(..., description="Circunferência da cintura")
    hip_circumference_cm: float = Field(..., description="Circunferência do quadril")

    # Profundidades (do perfil)
    chest_depth_cm: float = Field(..., description="Profundidade do peito")
    waist_depth_cm: float = Field(..., description="Profundidade da cintura")
    hip_depth_cm: float = Field(..., description="Profundidade do quadril")

    # Metadados
    confidence_front: float = Field(..., description="Confiança da foto frontal")
    confidence_side: float = Field(..., description="Confiança da foto lateral")
    landmarks_front: int
    landmarks_side: int


@router.post("/scan360", response_model=Scan360Response)
async def scan_360(
    front_photo: UploadFile = File(..., description="Foto FRONTAL (de frente)"),
    side_photo: UploadFile = File(..., description="Foto LATERAL (de perfil)"),
    height_cm: float = Form(..., description="Altura real em cm (obrigatória)"),
):
    """
    Escaneamento corporal 360° com 2 fotos.

    Envia uma foto de frente e uma de perfil (lado).
    Retorna medidas completas incluindo circunferências reais.

    **Instruções:**
    1. **Foto frontal**: de frente para a câmera, braços levemente afastados
    2. **Foto lateral**: virado de lado (perfil), braços à frente ou cruzados
    3. Ambas: corpo inteiro visível, fundo claro, roupa justa

    **Circunferências calculadas:**
    - Usa a largura (foto frontal) + profundidade (foto lateral)
    - Aplica fórmula da elipse de Ramanujan para circunferência real
    - Precisão: ±2-3cm com boas fotos
    """
    # Validar formatos
    for photo, name in [(front_photo, "frontal"), (side_photo, "lateral")]:
        if photo.content_type not in ["image/jpeg", "image/png", "image/webp"]:
            raise HTTPException(
                status_code=400,
                detail=f"Foto {name}: use JPEG, PNG ou WebP.",
            )

    # Ler imagens
    front_bytes = await front_photo.read()
    front_image = fix_orientation(front_bytes)

    side_bytes = await side_photo.read()
    side_image = fix_orientation(side_bytes)

    if front_image is None:
        raise HTTPException(status_code=400, detail="Foto frontal inválida.")
    if side_image is None:
        raise HTTPException(status_code=400, detail="Foto lateral inválida.")

    # Escaneamento
    result = scanner_360.scan(
        front_image=front_image,
        side_image=side_image,
        height_cm=height_cm,
    )

    if result is None:
        raise HTTPException(
            status_code=422,
            detail="Não foi possível detectar o corpo em uma ou ambas as fotos. "
            "Certifique-se de que o corpo inteiro está visível, "
            "com fundo claro e boa iluminação.",
        )

    return Scan360Response(
        height_cm=result.height_cm,
        shoulder_width_cm=result.shoulder_width_cm,
        inseam_cm=result.inseam_cm,
        pants_length_cm=result.pants_length_cm,
        shirt_length_cm=result.shirt_length_cm,
        armhole_depth_cm=result.armhole_depth_cm,
        bust_circumference_cm=result.bust_circumference_cm,
        waist_circumference_cm=result.waist_circumference_cm,
        hip_circumference_cm=result.hip_circumference_cm,
        chest_depth_cm=result.chest_depth_cm,
        waist_depth_cm=result.waist_depth_cm,
        hip_depth_cm=result.hip_depth_cm,
        confidence_front=result.confidence_front,
        confidence_side=result.confidence_side,
        landmarks_front=result.landmarks_front,
        landmarks_side=result.landmarks_side,
    )
