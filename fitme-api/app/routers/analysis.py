"""
Router principal: análise corporal completa.
Recebe foto, extrai medidas, analisa pele e retorna consultoria.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import cv2
import numpy as np

from app.models.measurements import BodyAnalysisResult
from app.models.garments import Garment, FitResult
from app.services.body_scanner import BodyScanner
from app.services.skin_analyzer import SkinAnalyzer
from app.services.style_consultant import StyleConsultant
from app.services.image_utils import fix_orientation

router = APIRouter()

# Instâncias dos serviços
body_scanner = BodyScanner()
skin_analyzer = SkinAnalyzer()
style_consultant = StyleConsultant()


@router.post("/analyze/body", response_model=BodyAnalysisResult)
async def analyze_body(
    photo: UploadFile = File(..., description="Foto do corpo inteiro"),
    height_cm: Optional[float] = Form(None, description="Altura real em cm"),
):
    """
    Analisa a foto do usuário e extrai medidas corporais + tom de pele.

    O usuário deve estar de frente, em local claro com fundo branco.
    Opcionalmente, informar a altura real para calibração precisa.
    """
    # Validar tipo de arquivo
    if photo.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(
            status_code=400,
            detail="Formato de imagem não suportado. Use JPEG, PNG ou WebP.",
        )

    # Ler imagem
    contents = await photo.read()
    image = fix_orientation(contents)

    if image is None:
        raise HTTPException(status_code=400, detail="Não foi possível ler a imagem.")

    # Análise corporal
    measurements, landmarks, confidence = body_scanner.analyze(image, height_cm)

    if measurements is None:
        raise HTTPException(
            status_code=422,
            detail="Não foi possível detectar o corpo na imagem. "
            "Certifique-se de estar de corpo inteiro, em local claro e fundo branco.",
        )

    # Análise de pele
    skin_analysis = skin_analyzer.analyze(image)

    if skin_analysis is None:
        raise HTTPException(
            status_code=422,
            detail="Não foi possível analisar o tom de pele. "
            "Certifique-se de que o rosto está visível na foto.",
        )

    # Determinar biotipo
    body_type = body_scanner.get_body_type(measurements)

    return BodyAnalysisResult(
        measurements=measurements,
        skin_analysis=skin_analysis,
        body_type=body_type,
        confidence_score=round(confidence, 2),
        landmarks_detected=landmarks,
    )


@router.post("/analyze/fit", response_model=FitResult)
async def analyze_fit(
    photo: UploadFile = File(..., description="Foto do corpo inteiro"),
    garment_json: str = Form(..., description="JSON da peça de roupa"),
    height_cm: Optional[float] = Form(None, description="Altura real em cm"),
):
    """
    Análise completa: extrai medidas da foto e analisa o caimento
    de uma peça específica usando IA generativa.
    """
    import json

    # Validar peça
    try:
        garment_data = json.loads(garment_json)
        garment = Garment(**garment_data)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=400,
            detail=f"JSON da peça inválido: {str(e)}",
        )

    # Validar imagem
    if photo.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(
            status_code=400,
            detail="Formato de imagem não suportado. Use JPEG, PNG ou WebP.",
        )

    contents = await photo.read()
    image = fix_orientation(contents)

    if image is None:
        raise HTTPException(status_code=400, detail="Não foi possível ler a imagem.")

    # Análise corporal
    measurements, landmarks, confidence = body_scanner.analyze(image, height_cm)

    if measurements is None:
        raise HTTPException(
            status_code=422,
            detail="Não foi possível detectar o corpo na imagem.",
        )

    # Análise de pele
    skin_analysis = skin_analyzer.analyze(image)

    if skin_analysis is None:
        raise HTTPException(
            status_code=422,
            detail="Não foi possível analisar o tom de pele.",
        )

    body_type = body_scanner.get_body_type(measurements)

    # Consultoria com LLM
    fit_result = await style_consultant.analyze_fit(
        measurements=measurements,
        skin_analysis=skin_analysis,
        body_type=body_type,
        garment=garment,
    )

    return fit_result
