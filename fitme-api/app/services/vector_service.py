"""
Serviço de vetorização e busca por similaridade com pgvector.

Converte medidas corporais e landmarks em vetores normalizados
para armazenamento e busca por similaridade no PostgreSQL.
"""

from typing import List, Optional
from uuid import UUID

import numpy as np
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import BodyProfile, TryOnHistory


class VectorService:
    """Operações com vetores corporais no pgvector."""

    @staticmethod
    def landmarks_to_vector(landmarks: list) -> List[float]:
        """
        Converte landmarks do MediaPipe (33 pontos) em vetor de 99 dims.
        Cada landmark tem (x, y, z).
        """
        vector = []
        for lm in landmarks:
            vector.extend([lm.x, lm.y, lm.z])
        return vector

    @staticmethod
    def measurements_to_vector(
        shoulder: float = 0,
        bust: float = 0,
        waist: float = 0,
        hip: float = 0,
        inseam: float = 0,
        height: float = 170,
        chest_depth: float = 0,
        waist_depth: float = 0,
        hip_depth: float = 0,
    ) -> List[float]:
        """
        Cria vetor normalizado de 12 dimensões a partir das medidas.
        Normaliza pela altura para tornar comparável entre pessoas.
        """
        h = height if height > 0 else 170

        # Ratios (invariantes ao tamanho)
        bust_waist_ratio = bust / waist if waist > 0 else 0
        waist_hip_ratio = waist / hip if hip > 0 else 0
        shoulder_hip_ratio = shoulder / hip if hip > 0 else 0

        return [
            shoulder / h,
            bust / h,
            waist / h,
            hip / h,
            inseam / h,
            1.0,  # height normalizado = 1
            bust_waist_ratio,
            waist_hip_ratio,
            shoulder_hip_ratio,
            chest_depth / h,
            waist_depth / h,
            hip_depth / h,
        ]

    @staticmethod
    async def save_profile(
        db: AsyncSession,
        measurements_vector: List[float],
        landmarks_vector: Optional[List[float]] = None,
        height_cm: float = 170,
        shoulder_width_cm: float = 0,
        bust_circumference_cm: float = 0,
        waist_circumference_cm: float = 0,
        hip_circumference_cm: float = 0,
        inseam_cm: float = 0,
        pants_length_cm: float = 0,
        shirt_length_cm: float = 0,
        armhole_depth_cm: float = 0,
        skin_hex: str = "",
        skin_undertone: str = "",
        body_type: str = "",
        external_user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> BodyProfile:
        """Salva perfil corporal com vetores no banco."""
        profile = BodyProfile(
            external_user_id=external_user_id,
            session_id=session_id,
            height_cm=height_cm,
            shoulder_width_cm=shoulder_width_cm,
            bust_circumference_cm=bust_circumference_cm,
            waist_circumference_cm=waist_circumference_cm,
            hip_circumference_cm=hip_circumference_cm,
            inseam_cm=inseam_cm,
            pants_length_cm=pants_length_cm,
            shirt_length_cm=shirt_length_cm,
            armhole_depth_cm=armhole_depth_cm,
            skin_hex=skin_hex,
            skin_undertone=skin_undertone,
            body_type=body_type,
            measurements_vector=measurements_vector,
            landmarks_vector=landmarks_vector,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        return profile

    @staticmethod
    async def find_similar_bodies(
        db: AsyncSession,
        measurements_vector: List[float],
        limit: int = 10,
    ) -> List[dict]:
        """
        Busca perfis com corpo similar usando distância coseno no pgvector.

        Retorna os N perfis mais parecidos com o vetor fornecido.
        Útil para: "pessoas com corpo parecido compraram tamanho M"
        """
        vector_str = "[" + ",".join(str(v) for v in measurements_vector) + "]"

        query = text("""
            SELECT
                id,
                height_cm,
                shoulder_width_cm,
                bust_circumference_cm,
                waist_circumference_cm,
                hip_circumference_cm,
                body_type,
                skin_undertone,
                1 - (measurements_vector <=> :vec::vector) AS similarity
            FROM body_profiles
            WHERE measurements_vector IS NOT NULL
            ORDER BY measurements_vector <=> :vec::vector
            LIMIT :lim
        """)

        result = await db.execute(query, {"vec": vector_str, "lim": limit})
        rows = result.fetchall()

        return [
            {
                "profile_id": str(row.id),
                "height_cm": row.height_cm,
                "shoulder_width_cm": row.shoulder_width_cm,
                "bust_circumference_cm": row.bust_circumference_cm,
                "waist_circumference_cm": row.waist_circumference_cm,
                "hip_circumference_cm": row.hip_circumference_cm,
                "body_type": row.body_type,
                "skin_undertone": row.skin_undertone,
                "similarity": round(float(row.similarity), 4),
            }
            for row in rows
        ]

    @staticmethod
    async def get_size_recommendation(
        db: AsyncSession,
        measurements_vector: List[float],
        garment_id: str,
        limit: int = 20,
    ) -> Optional[dict]:
        """
        Recomenda tamanho baseado no que corpos similares compraram.

        Busca os N perfis mais parecidos que já fizeram try-on
        desta peça e retorna o tamanho mais recomendado.
        """
        vector_str = "[" + ",".join(str(v) for v in measurements_vector) + "]"

        query = text("""
            SELECT
                th.recommended_size,
                th.fit_score,
                th.purchased,
                th.returned,
                1 - (bp.measurements_vector <=> :vec::vector) AS similarity
            FROM tryon_history th
            JOIN body_profiles bp ON bp.id = th.profile_id
            WHERE th.garment_id = :gid
              AND bp.measurements_vector IS NOT NULL
            ORDER BY bp.measurements_vector <=> :vec::vector
            LIMIT :lim
        """)

        result = await db.execute(
            query, {"vec": vector_str, "gid": garment_id, "lim": limit}
        )
        rows = result.fetchall()

        if not rows:
            return None

        # Contar votos por tamanho, ponderados pela similaridade
        size_scores: dict[str, float] = {}
        for row in rows:
            size = row.recommended_size
            weight = float(row.similarity)
            # Bônus se comprou e não devolveu
            if row.purchased == 1 and row.returned == 0:
                weight *= 1.5
            size_scores[size] = size_scores.get(size, 0) + weight

        best_size = max(size_scores, key=size_scores.get)

        return {
            "recommended_size": best_size,
            "confidence": round(size_scores[best_size] / sum(size_scores.values()), 2),
            "based_on_profiles": len(rows),
            "size_distribution": {
                k: round(v / sum(size_scores.values()), 2)
                for k, v in sorted(size_scores.items(), key=lambda x: -x[1])
            },
        }
