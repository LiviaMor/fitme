"""
Router do Personal Stylist com IA.

Recebe medidas corporais e perfil do cliente,
retorna consultoria de estilo completa com peças,
cores e looks que CABEM no cliente.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from app.services.personal_stylist import PersonalStylist

router = APIRouter()
stylist = PersonalStylist()


class StylistRequest(BaseModel):
    height_cm: float = Field(..., description="Altura em cm")
    shoulder_cm: float = Field(0, description="Largura ombros cm")
    bust_cm: float = Field(0, description="Circunferência busto cm")
    waist_cm: float = Field(0, description="Circunferência cintura cm")
    hip_cm: float = Field(0, description="Circunferência quadril cm")
    pants_cm: float = Field(0, description="Comprimento calça cm")
    shirt_cm: float = Field(0, description="Comprimento camisa cm")
    armhole_cm: float = Field(0, description="Altura cava cm")
    body_type: str = Field("não identificado", description="Biotipo")
    skin_color: str = Field("não identificado", description="Tom de pele")
    skin_undertone: str = Field("não identificado", description="Subtom")
    gender: str = Field("não informado", description="Gênero")
    occasion: str = Field("casual", description="Ocasião: casual, trabalho, festa, etc")


class ColorRec(BaseModel):
    cor: str
    hex: Optional[str] = None
    motivo: str


class PieceRec(BaseModel):
    tipo: str
    descricao: str
    tamanho_sugerido: str
    medida_referencia: Optional[str] = None
    motivo: str


class LookRec(BaseModel):
    ocasiao: str
    pecas: List[str]
    descricao: str
    dica_extra: Optional[str] = None


class StylistResponse(BaseModel):
    perfil_resumo: str
    biotipo_analise: str
    cores_recomendadas: List[ColorRec]
    cores_evitar: List[ColorRec]
    pecas_recomendadas: List[PieceRec]
    look_completo: LookRec
    dicas_gerais: List[str]


@router.post("/stylist", response_model=StylistResponse)
async def personal_stylist(request: StylistRequest):
    """
    Personal Stylist com IA.

    Recebe as medidas corporais reais do cliente e retorna uma
    consultoria de estilo completa e personalizada:

    - **Cores** que combinam com o tom de pele
    - **Peças específicas** com tamanho e medidas de referência
    - **Look completo** montado para a ocasião
    - **Dicas de styling** personalizadas

    **Diferencial FITME:** as recomendações são baseadas em medidas
    REAIS extraídas por visão computacional — não é achismo.
    """
    if not request.height_cm or request.height_cm < 50:
        raise HTTPException(status_code=400, detail="Altura inválida.")

    result = await stylist.consult(
        height_cm=request.height_cm,
        shoulder_cm=request.shoulder_cm,
        bust_cm=request.bust_cm,
        waist_cm=request.waist_cm,
        hip_cm=request.hip_cm,
        pants_cm=request.pants_cm,
        shirt_cm=request.shirt_cm,
        armhole_cm=request.armhole_cm,
        body_type=request.body_type,
        skin_color=request.skin_color,
        skin_undertone=request.skin_undertone,
        gender=request.gender,
        occasion=request.occasion,
    )

    return StylistResponse(**result)
