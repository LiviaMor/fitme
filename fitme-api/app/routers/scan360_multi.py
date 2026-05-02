"""
Router do Scanner 360° Multi-Frame.

O usuário gira em frente à câmera e o front-end captura
múltiplos frames automaticamente. A API detecta o ângulo
de cada frame e combina para medidas 3D completas.
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from typing import List

import cv2
import numpy as np

from app.services.scanner_360_multi import MultiFrameScanner360

router = APIRouter()
scanner = MultiFrameScanner360()


class Scan360MultiResponse(BaseModel):
    """Resposta do scan 360° multi-frame."""

    # Circunferências
    bust_circumference_cm: float = Field(..., description="Circunferência do busto")
    waist_circumference_cm: float = Field(..., description="Circunferência da cintura")
    hip_circumference_cm: float = Field(..., description="Circunferência do quadril")

    # Lineares
    height_cm: float
    shoulder_width_cm: float
    back_width_cm: float

    # Modelagem
    inseam_cm: float = Field(..., description="Altura do gancho")
    pants_length_cm: float = Field(..., description="Comprimento calça")
    shirt_length_cm: float = Field(..., description="Comprimento camisa")
    armhole_depth_cm: float = Field(..., description="Altura da cava")

    # Profundidades
    chest_depth_cm: float
    waist_depth_cm: float
    hip_depth_cm: float

    # Metadados
    frames_analyzed: int
    angles_captured: List[int]
    overall_confidence: float
    landmarks_vector: List[float] = Field(
        default=[], description="Vetor 99 dims para pgvector"
    )


@router.post("/scan360/multi", response_model=Scan360MultiResponse)
async def scan_360_multi(
    frames: List[UploadFile] = File(
        ..., description="Múltiplas fotos de diferentes ângulos (mín 2, ideal 4-8)"
    ),
    height_cm: float = Form(..., description="Altura real em cm"),
):
    """
    Scanner 360° com múltiplos frames.

    O front-end captura fotos enquanto o usuário gira lentamente.
    A API detecta automaticamente o ângulo de cada frame e combina
    para calcular circunferências reais.

    **Fluxo recomendado:**
    1. Usuário fica em pé, corpo inteiro visível
    2. Gira lentamente 360° (ou tira 4 fotos: frente, lado, costas, outro lado)
    3. Front-end captura 4-8 frames automaticamente
    4. API detecta ângulos e calcula medidas 3D

    **Mínimo:** 2 frames (frente + lado)
    **Ideal:** 4 frames (frente, lado direito, costas, lado esquerdo)
    **Máximo:** 8 frames (a cada 45°)
    """
    if len(frames) < 2:
        raise HTTPException(
            status_code=400,
            detail="Mínimo 2 fotos necessárias (frente + lado).",
        )

    if len(frames) > 12:
        raise HTTPException(
            status_code=400,
            detail="Máximo 12 fotos por scan.",
        )

    # Decodificar todas as imagens
    images = []
    for i, frame in enumerate(frames):
        if frame.content_type not in ["image/jpeg", "image/png", "image/webp"]:
            raise HTTPException(
                status_code=400,
                detail=f"Frame {i+1}: use JPEG, PNG ou WebP.",
            )

        contents = await frame.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(
                status_code=400,
                detail=f"Frame {i+1}: imagem inválida.",
            )
        images.append(img)

    # Processar scan 360°
    result = scanner.scan(frames=images, height_cm=height_cm)

    if result is None:
        raise HTTPException(
            status_code=422,
            detail="Não foi possível detectar o corpo nos frames. "
            "Certifique-se de que o corpo inteiro está visível em cada foto, "
            "com fundo claro e boa iluminação.",
        )

    return Scan360MultiResponse(
        bust_circumference_cm=result.bust_circumference_cm,
        waist_circumference_cm=result.waist_circumference_cm,
        hip_circumference_cm=result.hip_circumference_cm,
        height_cm=result.height_cm,
        shoulder_width_cm=result.shoulder_width_cm,
        back_width_cm=result.back_width_cm,
        inseam_cm=result.inseam_cm,
        pants_length_cm=result.pants_length_cm,
        shirt_length_cm=result.shirt_length_cm,
        armhole_depth_cm=result.armhole_depth_cm,
        chest_depth_cm=result.chest_depth_cm,
        waist_depth_cm=result.waist_depth_cm,
        hip_depth_cm=result.hip_depth_cm,
        frames_analyzed=result.frames_analyzed,
        angles_captured=result.angles_captured,
        overall_confidence=result.overall_confidence,
        landmarks_vector=result.landmarks_vector,
    )


@router.post("/scan360/video")
async def scan_360_from_video(
    video: UploadFile = File(..., description="Vídeo do usuário girando 360°"),
    height_cm: float = Form(..., description="Altura real em cm"),
    num_frames: int = Form(8, description="Número de frames a extrair (4-12)"),
):
    """
    Scanner 360° a partir de vídeo.

    O usuário grava um vídeo curto (5-10s) girando lentamente.
    A API extrai N frames espaçados uniformemente e processa.

    **Instruções:**
    1. Grave um vídeo de 5-10 segundos
    2. Gire lentamente 360° durante a gravação
    3. Mantenha corpo inteiro visível
    4. Fundo claro, iluminação uniforme
    """
    if video.content_type not in ["video/mp4", "video/webm", "video/quicktime"]:
        raise HTTPException(
            status_code=400,
            detail="Use MP4, WebM ou MOV.",
        )

    num_frames = max(4, min(12, num_frames))

    # Salvar vídeo temporariamente
    contents = await video.read()
    temp_path = "/tmp/scan360_video.mp4"
    with open(temp_path, "wb") as f:
        f.write(contents)

    # Extrair frames uniformemente espaçados
    cap = cv2.VideoCapture(temp_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames < num_frames:
        cap.release()
        raise HTTPException(
            status_code=400,
            detail="Vídeo muito curto. Grave pelo menos 3 segundos.",
        )

    # Índices dos frames a extrair
    indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)

    images = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            images.append(frame)

    cap.release()

    if len(images) < 2:
        raise HTTPException(
            status_code=422,
            detail="Não foi possível extrair frames do vídeo.",
        )

    # Processar
    result = scanner.scan(frames=images, height_cm=height_cm)

    if result is None:
        raise HTTPException(
            status_code=422,
            detail="Corpo não detectado nos frames do vídeo.",
        )

    return Scan360MultiResponse(
        bust_circumference_cm=result.bust_circumference_cm,
        waist_circumference_cm=result.waist_circumference_cm,
        hip_circumference_cm=result.hip_circumference_cm,
        height_cm=result.height_cm,
        shoulder_width_cm=result.shoulder_width_cm,
        back_width_cm=result.back_width_cm,
        inseam_cm=result.inseam_cm,
        pants_length_cm=result.pants_length_cm,
        shirt_length_cm=result.shirt_length_cm,
        armhole_depth_cm=result.armhole_depth_cm,
        chest_depth_cm=result.chest_depth_cm,
        waist_depth_cm=result.waist_depth_cm,
        hip_depth_cm=result.hip_depth_cm,
        frames_analyzed=result.frames_analyzed,
        angles_captured=result.angles_captured,
        overall_confidence=result.overall_confidence,
        landmarks_vector=result.landmarks_vector,
    )
