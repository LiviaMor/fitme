"""
Router do Virtual Try-On.

Endpoints para prova virtual: recebe foto do cliente + imagem/URL da roupa
e retorna a imagem com a roupa sobreposta no corpo.
"""

import base64
from io import BytesIO

import cv2
import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from typing import Optional

from app.services.virtual_tryon import VirtualTryOn

router = APIRouter()
tryon_service = VirtualTryOn()


@router.post("/tryon/url", response_class=Response)
async def tryon_from_url(
    photo: UploadFile = File(..., description="Foto do cliente (corpo inteiro)"),
    garment_url: str = Form(..., description="URL da imagem da roupa"),
    garment_type: str = Form(
        "camiseta",
        description="Tipo: camiseta, camisa, vestido, calca, saia, blazer, jaqueta",
    ),
    opacity: float = Form(0.85, description="Opacidade da sobreposição (0-1)"),
):
    """
    Virtual Try-On a partir de URL.

    Recebe a foto do cliente e a URL da imagem da roupa no e-commerce.
    Retorna a imagem PNG com a roupa sobreposta no corpo.

    **Tipos de peça suportados:**
    - camiseta, camisa, blazer, jaqueta (ombro → quadril)
    - vestido, saia (ombro → tornozelo)
    - calca (quadril → tornozelo)
    """
    # Validar imagem do cliente
    if photo.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Use JPEG, PNG ou WebP.")

    contents = await photo.read()
    nparr = np.frombuffer(contents, np.uint8)
    person_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if person_image is None:
        raise HTTPException(status_code=400, detail="Imagem do cliente inválida.")

    # Realizar try-on
    result_image = await tryon_service.try_on_from_url(
        person_image=person_image,
        garment_url=garment_url,
        garment_type=garment_type,
        opacity=opacity,
    )

    if result_image is None:
        raise HTTPException(
            status_code=422,
            detail="Não foi possível realizar o try-on. "
            "Verifique se o corpo está visível e a URL da roupa é válida.",
        )

    # Encodar resultado como PNG
    _, buffer = cv2.imencode(".png", result_image)
    return Response(content=buffer.tobytes(), media_type="image/png")


@router.post("/tryon/upload", response_class=Response)
async def tryon_from_upload(
    photo: UploadFile = File(..., description="Foto do cliente (corpo inteiro)"),
    garment_photo: UploadFile = File(..., description="Imagem da roupa"),
    garment_type: str = Form(
        "camiseta",
        description="Tipo: camiseta, camisa, vestido, calca, saia, blazer, jaqueta",
    ),
    opacity: float = Form(0.85, description="Opacidade da sobreposição (0-1)"),
):
    """
    Virtual Try-On por upload de imagem.

    Recebe a foto do cliente e a imagem da roupa (upload direto).
    Retorna a imagem PNG com a roupa sobreposta no corpo.
    """
    # Validar imagem do cliente
    if photo.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Foto: use JPEG, PNG ou WebP.")

    if garment_photo.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Roupa: use JPEG, PNG ou WebP.")

    # Ler imagem do cliente
    person_bytes = await photo.read()
    person_arr = np.frombuffer(person_bytes, np.uint8)
    person_image = cv2.imdecode(person_arr, cv2.IMREAD_COLOR)

    if person_image is None:
        raise HTTPException(status_code=400, detail="Imagem do cliente inválida.")

    # Ler imagem da roupa
    garment_bytes = await garment_photo.read()
    garment_arr = np.frombuffer(garment_bytes, np.uint8)
    garment_image = cv2.imdecode(garment_arr, cv2.IMREAD_UNCHANGED)

    if garment_image is None:
        raise HTTPException(status_code=400, detail="Imagem da roupa inválida.")

    # Realizar try-on
    result_image = await tryon_service.try_on(
        person_image=person_image,
        garment_image=garment_image,
        garment_type=garment_type,
        opacity=opacity,
    )

    if result_image is None:
        raise HTTPException(
            status_code=422,
            detail="Não foi possível realizar o try-on. "
            "Verifique se o corpo está visível na foto.",
        )

    # Encodar resultado como PNG
    _, buffer = cv2.imencode(".png", result_image)
    return Response(content=buffer.tobytes(), media_type="image/png")


@router.post("/tryon/url/base64")
async def tryon_from_url_base64(
    photo: UploadFile = File(..., description="Foto do cliente (corpo inteiro)"),
    garment_url: str = Form(..., description="URL da imagem da roupa"),
    garment_type: str = Form("camiseta", description="Tipo da peça"),
    opacity: float = Form(0.85, description="Opacidade (0-1)"),
):
    """
    Virtual Try-On retornando base64 (útil para front-ends que não
    conseguem consumir binary response diretamente).
    """
    if photo.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Use JPEG, PNG ou WebP.")

    contents = await photo.read()
    nparr = np.frombuffer(contents, np.uint8)
    person_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if person_image is None:
        raise HTTPException(status_code=400, detail="Imagem inválida.")

    result_image = await tryon_service.try_on_from_url(
        person_image=person_image,
        garment_url=garment_url,
        garment_type=garment_type,
        opacity=opacity,
    )

    if result_image is None:
        raise HTTPException(
            status_code=422,
            detail="Try-on falhou. Corpo não detectado ou URL inválida.",
        )

    _, buffer = cv2.imencode(".png", result_image)
    img_base64 = base64.b64encode(buffer.tobytes()).decode("utf-8")

    return {
        "image_base64": img_base64,
        "content_type": "image/png",
        "garment_url": garment_url,
        "garment_type": garment_type,
    }
