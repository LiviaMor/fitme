"""
Router do Estadiômetro Digital - Padrão Welmy.

Endpoints para medição de altura com calibração por grade milimétrica,
simulando os modelos de estadiômetro da Welmy.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from typing import Optional, List
import cv2
import numpy as np

from app.models.stadiometer import (
    WelmyModelEnum,
    HeightMeasurementResponse,
    StadiometerInfoResponse,
)
from app.services.stadiometer import (
    DigitalStadiometer,
    WelmyModel,
    WELMY_MODELS,
)

router = APIRouter()


@router.get("/stadiometer/models", response_model=List[StadiometerInfoResponse])
async def list_welmy_models():
    """
    Lista todos os modelos de estadiômetro Welmy disponíveis
    com suas especificações técnicas.
    """
    models = []
    for config in WELMY_MODELS.values():
        models.append(
            StadiometerInfoResponse(
                model=config.model.value,
                min_height_cm=config.min_height_cm,
                max_height_cm=config.max_height_cm,
                resolution_cm=config.resolution_cm,
                precision_cm=config.precision_cm,
                description=config.description,
            )
        )
    return models


@router.post("/stadiometer/measure", response_model=HeightMeasurementResponse)
async def measure_height(
    photo: UploadFile = File(..., description="Foto de corpo inteiro"),
    model: WelmyModelEnum = Form(
        WelmyModelEnum.W200_5,
        description="Modelo Welmy a simular",
    ),
    reference_object_cm: Optional[float] = Form(
        None,
        description="Tamanho real de objeto de referência na foto (cm)",
    ),
    reference_object_px: Optional[float] = Form(
        None,
        description="Tamanho em pixels do objeto de referência na foto",
    ),
):
    """
    Mede a altura usando o estadiômetro digital (padrão Welmy).

    **Instruções para melhor precisão:**
    1. Posicione-se de frente, corpo inteiro visível
    2. Fundo branco ou claro
    3. Use grade milimétrica impressa ao lado (opcional, aumenta precisão)
    4. Pés juntos, postura ereta
    5. Iluminação uniforme

    **Modelos disponíveis:**
    - W200/5: Padrão clínico adulto (100-200cm, resolução 0.5cm)
    - W200/5A: Alta precisão adulto (100-200cm, resolução 0.1cm)
    - W110H: Plataforma com estadiômetro (100-200cm, resolução 0.5cm)
    - Pediátrico: Infantômetro (20-100cm, resolução 0.1cm)
    """
    # Validar imagem
    if photo.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(
            status_code=400,
            detail="Formato não suportado. Use JPEG, PNG ou WebP.",
        )

    contents = await photo.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Não foi possível ler a imagem.")

    # Mapear enum para modelo interno
    welmy_model = WelmyModel(model.value)

    # Criar estadiômetro e medir
    stadiometer = DigitalStadiometer(model=welmy_model)
    result = stadiometer.measure(
        image=image,
        reference_object_cm=reference_object_cm,
        reference_object_px=reference_object_px,
    )

    if result.confidence == 0:
        raise HTTPException(status_code=422, detail=result.message)

    # Calcular medidas derivadas usando fórmulas de modelagem
    height = result.height_rounded_cm
    crotch_height = round((height * 16) / 100, 1)
    pants_length = round((height * 61) / 100, 1)
    shirt_length = round((height * 45) / 100, 1)

    return HeightMeasurementResponse(
        height_cm=result.height_cm,
        height_rounded_cm=result.height_rounded_cm,
        model_used=result.model_used.value,
        confidence=result.confidence,
        calibration_method=result.calibration_method,
        within_range=result.within_range,
        grid_detected=result.grid_detected,
        message=result.message,
        crotch_height_cm=crotch_height,
        pants_length_cm=pants_length,
        shirt_length_cm=shirt_length,
    )


@router.get("/stadiometer/guide")
async def stadiometer_guide():
    """
    Retorna instruções de uso do estadiômetro digital
    e como imprimir a grade milimétrica de calibração.
    """
    return {
        "title": "Guia do Estadiômetro Digital FITME (Padrão Welmy)",
        "instructions": [
            "1. Imprima a grade milimétrica em folha A4 (link abaixo)",
            "2. Cole a grade na parede, com a base no chão",
            "3. Posicione-se ao lado da grade, de frente para a câmera",
            "4. Mantenha postura ereta, pés juntos, olhar para frente",
            "5. Certifique-se de que cabeça e pés estão visíveis na foto",
            "6. Use fundo branco ou claro para melhor detecção",
            "7. Iluminação uniforme (evite sombras fortes)",
        ],
        "grid_specs": {
            "spacing": "1cm entre linhas",
            "total_height": "Mínimo 180cm recomendado",
            "width": "20cm mínimo",
            "color": "Linhas pretas em fundo branco",
            "material": "Papel ou adesivo vinílico",
        },
        "models": {
            "W200/5": "Adulto padrão - resolução 0.5cm - uso clínico geral",
            "W200/5A": "Adulto precisão - resolução 0.1cm - pesquisa/nutrição",
            "W110H": "Plataforma - resolução 0.5cm - consultórios",
            "Pediátrico": "Infantômetro - resolução 0.1cm - pediatria",
        },
        "formulas": {
            "crotch_height": "altura × 16 / 100",
            "pants_length": "altura × 61 / 100",
            "shirt_length": "altura × 45 / 100",
            "armhole_depth": "tórax / 4.4",
        },
        "precision_tips": [
            "Com grade milimétrica: ±0.3cm (equivalente ao Welmy físico)",
            "Com objeto de referência: ±0.6cm",
            "Sem calibração (proporção): ±2.0cm",
        ],
    }
