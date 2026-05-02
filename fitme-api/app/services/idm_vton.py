"""
IDM-VTON - Virtual Try-On de alta qualidade via Replicate.

Usa o modelo IDM-VTON que gera imagens realistas de uma pessoa
vestindo uma roupa, com caimento natural, dobras e sombras.

Input: foto da pessoa + foto da roupa (flat lay)
Output: foto gerada com a pessoa vestindo a roupa

Requer REPLICATE_API_TOKEN no .env
"""

import base64
import io
from typing import Optional

import httpx
import replicate
from PIL import Image

from app.config import settings


class IDMVtonService:
    """Virtual Try-On de alta qualidade usando IDM-VTON via Replicate."""

    # Modelo IDM-VTON no Replicate
    MODEL = "cuuupid/idm-vton:c871bb9b046c1b1f6e868a0afe94e2f3c46d5e67e3a0a3b3e6c5e4e5e6f7a8b9"

    async def fetch_image_bytes(self, url: str) -> Optional[bytes]:
        """Baixa imagem de uma URL e retorna bytes."""
        try:
            async with httpx.AsyncClient(
                timeout=15, follow_redirects=True
            ) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return response.content
        except Exception:
            pass
        return None

    def _image_to_data_uri(self, image_bytes: bytes) -> str:
        """Converte bytes de imagem para data URI."""
        img = Image.open(io.BytesIO(image_bytes))
        # Converter para JPEG se necessário
        if img.mode == "RGBA":
            img = img.convert("RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=90)
        b64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/jpeg;base64,{b64}"

    async def try_on(
        self,
        person_image_bytes: bytes,
        garment_image_bytes: bytes,
    ) -> Optional[bytes]:
        """
        Realiza try-on com IDM-VTON via Replicate.

        Args:
            person_image_bytes: Foto da pessoa (JPEG/PNG bytes).
            garment_image_bytes: Foto da roupa flat lay (JPEG/PNG bytes).

        Returns:
            Bytes da imagem resultado (PNG), ou None se falhar.
        """
        if not settings.replicate_api_token:
            return None

        try:
            person_uri = self._image_to_data_uri(person_image_bytes)
            garment_uri = self._image_to_data_uri(garment_image_bytes)

            # Chamar IDM-VTON via Replicate
            output = replicate.run(
                "cuuupid/idm-vton:c871bb9b046c1b1f6e868a0afe94e2f3c46d5e67e3a0a3b3e6c5e4e5e6f7a8b9",
                input={
                    "human_img": person_uri,
                    "garm_img": garment_uri,
                    "garment_des": "clothing item",
                    "category": "upper_body",
                    "seed": 42,
                    "steps": 30,
                },
            )

            # Output é uma URL da imagem gerada
            if output:
                result_url = str(output) if isinstance(output, str) else str(output[0]) if isinstance(output, list) else None
                if result_url:
                    async with httpx.AsyncClient(timeout=30) as client:
                        resp = await client.get(result_url)
                        if resp.status_code == 200:
                            return resp.content

        except Exception as e:
            print(f"IDM-VTON erro: {e}")

        return None

    async def try_on_from_url(
        self,
        person_image_bytes: bytes,
        garment_url: str,
    ) -> Optional[bytes]:
        """Try-on com URL da roupa."""
        garment_bytes = await self.fetch_image_bytes(garment_url)
        if garment_bytes is None:
            return None
        return await self.try_on(person_image_bytes, garment_bytes)
