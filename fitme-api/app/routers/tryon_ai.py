"""
Router do Virtual Try-On com IA (IDM-VTON).

Try-on de alta qualidade usando modelo generativo.
Fallback para overlay básico se Replicate não estiver configurado.
"""

import base64

import cv2
import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import settings
from app.services.idm_vton import IDMVtonService
from app.services.virtual_tryon import VirtualTryOn
from app.services.image_utils import fix_orientation

router = APIRouter()
idm_service = IDMVtonService()
basic_tryon = VirtualTryOn()


@router.post("/tryon-ai/url")
async def tryon_ai_from_url(
    photo: UploadFile = File(..., description="Foto da pessoa (corpo inteiro)"),
    garment_url: str = Form(..., description="URL da imagem da roupa"),
    garment_type: str = Form("upper_body", description="upper_body | lower_body | full_body"),
):
    """
    Virtual Try-On com IA de alta qualidade (IDM-VTON).

    Gera uma imagem realista da pessoa vestindo a roupa,
    com caimento natural, dobras e sombras.

    Se REPLICATE_API_TOKEN não estiver configurado,
    usa fallback com overlay básico (MediaPipe).

    **Categorias:**
    - upper_body: camisetas, camisas, blazers, jaquetas
    - lower_body: calças, saias
    - full_body: vestidos, macacões
    """
    if photo.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Use JPEG, PNG ou WebP.")

    person_bytes = await photo.read()

    # Tentar IDM-VTON primeiro (alta qualidade)
    if settings.replicate_api_token:
        result_bytes = await idm_service.try_on_from_url(
            person_image_bytes=person_bytes,
            garment_url=garment_url,
        )

        if result_bytes:
            img_base64 = base64.b64encode(result_bytes).decode("utf-8")
            return {
                "image_base64": img_base64,
                "content_type": "image/png",
                "method": "idm-vton",
                "quality": "high",
                "garment_url": garment_url,
            }

    # Fallback: overlay básico com MediaPipe
    person_image = fix_orientation(person_bytes)
    if person_image is None:
        raise HTTPException(status_code=400, detail="Imagem inválida.")

    # Mapear categoria para tipo de peça
    type_map = {
        "upper_body": "camiseta",
        "lower_body": "calca",
        "full_body": "vestido",
    }
    basic_type = type_map.get(garment_type, "camiseta")

    result_image = await basic_tryon.try_on_from_url(
        person_image=person_image,
        garment_url=garment_url,
        garment_type=basic_type,
    )

    if result_image is None:
        raise HTTPException(
            status_code=422,
            detail="Corpo não detectado. Certifique-se de que ombros e tronco estão visíveis.",
        )

    _, buffer = cv2.imencode(".png", result_image)
    img_base64 = base64.b64encode(buffer.tobytes()).decode("utf-8")

    return {
        "image_base64": img_base64,
        "content_type": "image/png",
        "method": "overlay-basic",
        "quality": "standard",
        "garment_url": garment_url,
    }
