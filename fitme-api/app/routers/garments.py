"""
Router de peças de roupa - catálogo de exemplo para o MVP.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.models.garments import (
    Garment,
    GarmentCategory,
    GarmentSize,
    GarmentMeasurements,
)

router = APIRouter()

# Catálogo de exemplo para o MVP
SAMPLE_CATALOG: List[Garment] = [
    Garment(
        id="vest-001",
        name="Vestido Midi Azul Marinho",
        category=GarmentCategory.VESTIDO,
        size=GarmentSize.M,
        color="Azul Marinho",
        color_hex="#1B2A4A",
        measurements=GarmentMeasurements(
            shoulder_cm=38.0,
            bust_cm=92.0,
            waist_cm=76.0,
            hip_cm=98.0,
            length_cm=110.0,
        ),
        brand="FITME Collection",
        price=189.90,
    ),
    Garment(
        id="cam-001",
        name="Camisa Social Branca Slim",
        category=GarmentCategory.CAMISA,
        size=GarmentSize.M,
        color="Branco",
        color_hex="#FFFFFF",
        measurements=GarmentMeasurements(
            shoulder_cm=42.0,
            bust_cm=100.0,
            waist_cm=90.0,
            length_cm=72.0,
        ),
        brand="FITME Collection",
        price=129.90,
    ),
    Garment(
        id="cal-001",
        name="Calça Skinny Preta",
        category=GarmentCategory.CALCA,
        size=GarmentSize.M,
        color="Preto",
        color_hex="#1A1A1A",
        measurements=GarmentMeasurements(
            waist_cm=78.0,
            hip_cm=96.0,
            length_cm=100.0,
        ),
        brand="FITME Collection",
        price=159.90,
    ),
    Garment(
        id="blz-001",
        name="Blazer Terracota Oversized",
        category=GarmentCategory.BLAZER,
        size=GarmentSize.G,
        color="Terracota",
        color_hex="#C75B39",
        measurements=GarmentMeasurements(
            shoulder_cm=46.0,
            bust_cm=108.0,
            waist_cm=100.0,
            length_cm=68.0,
        ),
        brand="FITME Collection",
        price=249.90,
    ),
    Garment(
        id="camt-001",
        name="Camiseta Básica Verde Oliva",
        category=GarmentCategory.CAMISETA,
        size=GarmentSize.P,
        color="Verde Oliva",
        color_hex="#556B2F",
        measurements=GarmentMeasurements(
            shoulder_cm=40.0,
            bust_cm=94.0,
            length_cm=65.0,
        ),
        brand="FITME Collection",
        price=69.90,
    ),
]


@router.get("/garments", response_model=List[Garment])
async def list_garments(
    category: Optional[GarmentCategory] = None,
    size: Optional[GarmentSize] = None,
):
    """Lista peças do catálogo com filtros opcionais."""
    results = SAMPLE_CATALOG

    if category:
        results = [g for g in results if g.category == category]
    if size:
        results = [g for g in results if g.size == size]

    return results


@router.get("/garments/{garment_id}", response_model=Garment)
async def get_garment(garment_id: str):
    """Retorna uma peça específica pelo ID."""
    for garment in SAMPLE_CATALOG:
        if garment.id == garment_id:
            return garment

    raise HTTPException(status_code=404, detail="Peça não encontrada.")
