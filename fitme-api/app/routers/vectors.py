"""
Router de vetores corporais e busca por similaridade.

Endpoints para salvar perfis, buscar corpos similares
e obter recomendação de tamanho baseada em dados coletivos.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.vector_service import VectorService

router = APIRouter()
vector_service = VectorService()


class SaveProfileRequest(BaseModel):
    """Request para salvar perfil corporal."""
    height_cm: float = Field(..., description="Altura em cm")
    shoulder_width_cm: float = Field(0, description="Largura ombros")
    bust_circumference_cm: float = Field(0, description="Circunferência busto")
    waist_circumference_cm: float = Field(0, description="Circunferência cintura")
    hip_circumference_cm: float = Field(0, description="Circunferência quadril")
    inseam_cm: float = Field(0, description="Gancho")
    pants_length_cm: float = Field(0, description="Comprimento calça")
    shirt_length_cm: float = Field(0, description="Comprimento camisa")
    armhole_depth_cm: float = Field(0, description="Altura cava")
    chest_depth_cm: float = Field(0, description="Profundidade peito")
    waist_depth_cm: float = Field(0, description="Profundidade cintura")
    hip_depth_cm: float = Field(0, description="Profundidade quadril")
    skin_hex: str = Field("", description="Cor da pele HEX")
    skin_undertone: str = Field("", description="Subtom")
    body_type: str = Field("", description="Biotipo")
    external_user_id: Optional[str] = Field(None, description="ID do usuário no e-commerce")


class SaveProfileResponse(BaseModel):
    """Response após salvar perfil."""
    profile_id: str
    measurements_vector: List[float]
    message: str


class SimilarBodyResponse(BaseModel):
    profile_id: str
    height_cm: float
    shoulder_width_cm: Optional[float]
    bust_circumference_cm: Optional[float]
    waist_circumference_cm: Optional[float]
    hip_circumference_cm: Optional[float]
    body_type: Optional[str]
    skin_undertone: Optional[str]
    similarity: float


class SizeRecommendationResponse(BaseModel):
    recommended_size: str
    confidence: float
    based_on_profiles: int
    size_distribution: dict


@router.post("/profiles", response_model=SaveProfileResponse)
async def save_body_profile(
    request: SaveProfileRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Salva perfil corporal com vetor para busca por similaridade.

    O vetor de 12 dimensões é gerado automaticamente a partir das medidas.
    Usado para recomendação coletiva: "corpos parecidos compraram tamanho M".
    """
    measurements_vector = vector_service.measurements_to_vector(
        shoulder=request.shoulder_width_cm,
        bust=request.bust_circumference_cm,
        waist=request.waist_circumference_cm,
        hip=request.hip_circumference_cm,
        inseam=request.inseam_cm,
        height=request.height_cm,
        chest_depth=request.chest_depth_cm,
        waist_depth=request.waist_depth_cm,
        hip_depth=request.hip_depth_cm,
    )

    profile = await vector_service.save_profile(
        db=db,
        measurements_vector=measurements_vector,
        height_cm=request.height_cm,
        shoulder_width_cm=request.shoulder_width_cm,
        bust_circumference_cm=request.bust_circumference_cm,
        waist_circumference_cm=request.waist_circumference_cm,
        hip_circumference_cm=request.hip_circumference_cm,
        inseam_cm=request.inseam_cm,
        pants_length_cm=request.pants_length_cm,
        shirt_length_cm=request.shirt_length_cm,
        armhole_depth_cm=request.armhole_depth_cm,
        skin_hex=request.skin_hex,
        skin_undertone=request.skin_undertone,
        body_type=request.body_type,
        external_user_id=request.external_user_id,
    )

    return SaveProfileResponse(
        profile_id=str(profile.id),
        measurements_vector=measurements_vector,
        message="Perfil salvo com sucesso.",
    )


@router.post("/profiles/similar", response_model=List[SimilarBodyResponse])
async def find_similar_bodies(
    request: SaveProfileRequest,
    limit: int = Query(10, ge=1, le=50, description="Máximo de resultados"),
    db: AsyncSession = Depends(get_db),
):
    """
    Busca perfis com corpo similar usando distância coseno (pgvector).

    Envia as medidas e retorna os N perfis mais parecidos do banco.
    Útil para: "pessoas com corpo parecido compraram tamanho M nesta peça".
    """
    measurements_vector = vector_service.measurements_to_vector(
        shoulder=request.shoulder_width_cm,
        bust=request.bust_circumference_cm,
        waist=request.waist_circumference_cm,
        hip=request.hip_circumference_cm,
        inseam=request.inseam_cm,
        height=request.height_cm,
        chest_depth=request.chest_depth_cm,
        waist_depth=request.waist_depth_cm,
        hip_depth=request.hip_depth_cm,
    )

    results = await vector_service.find_similar_bodies(
        db=db,
        measurements_vector=measurements_vector,
        limit=limit,
    )

    return [SimilarBodyResponse(**r) for r in results]


@router.get(
    "/profiles/{garment_id}/recommend-size",
    response_model=SizeRecommendationResponse,
)
async def recommend_size(
    garment_id: str,
    height_cm: float = Query(...),
    shoulder_cm: float = Query(0),
    bust_cm: float = Query(0),
    waist_cm: float = Query(0),
    hip_cm: float = Query(0),
    inseam_cm: float = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """
    Recomenda tamanho baseado em dados coletivos.

    Busca corpos similares que já experimentaram esta peça
    e retorna o tamanho mais votado, ponderado por similaridade
    e feedback pós-compra (comprou e não devolveu = peso maior).
    """
    measurements_vector = vector_service.measurements_to_vector(
        shoulder=shoulder_cm,
        bust=bust_cm,
        waist=waist_cm,
        hip=hip_cm,
        inseam=inseam_cm,
        height=height_cm,
    )

    result = await vector_service.get_size_recommendation(
        db=db,
        measurements_vector=measurements_vector,
        garment_id=garment_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Sem dados suficientes para recomendar tamanho desta peça.",
        )

    return SizeRecommendationResponse(**result)
