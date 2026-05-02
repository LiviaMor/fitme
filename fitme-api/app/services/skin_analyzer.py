"""
Serviço de análise de tom de pele usando OpenCV.
Extrai a cor média da pele e classifica o subtom.
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Tuple, Optional

from app.models.measurements import SkinAnalysis, SkinUndertone


class SkinAnalyzer:
    """Analisa o tom de pele a partir de uma imagem."""

    def __init__(self):
        self.mp_face = mp.solutions.face_detection
        self.face_detection = self.mp_face.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )

    def _rgb_to_hex(self, r: int, g: int, b: int) -> str:
        """Converte RGB para HEX."""
        return f"#{r:02x}{g:02x}{b:02x}"

    def _classify_undertone(self, r: int, g: int, b: int) -> SkinUndertone:
        """
        Classifica o subtom da pele baseado nos canais RGB.
        - Frio: mais azul/rosa
        - Quente: mais amarelo/dourado
        - Neutro: equilibrado
        """
        # Converter para HSV para melhor análise
        pixel = np.uint8([[[b, g, r]]])
        hsv = cv2.cvtColor(pixel, cv2.COLOR_BGR2HSV)
        h, s, v = hsv[0][0]

        # Hue entre 0-30 ou 150-180 tende a ser quente
        # Hue entre 90-150 tende a ser frio
        if h < 20 or h > 160:
            return SkinUndertone.QUENTE
        elif 20 <= h <= 40:
            # Verificar saturação para distinguir quente de neutro
            if s > 80:
                return SkinUndertone.QUENTE
            else:
                return SkinUndertone.NEUTRO
        else:
            return SkinUndertone.FRIO

    def _get_color_name(self, r: int, g: int, b: int) -> str:
        """Retorna um nome descritivo para o tom de pele."""
        brightness = (r + g + b) / 3

        if brightness > 200:
            return "Pele muito clara"
        elif brightness > 170:
            return "Pele clara"
        elif brightness > 140:
            return "Pele média clara"
        elif brightness > 110:
            return "Pele média"
        elif brightness > 80:
            return "Pele média escura"
        elif brightness > 50:
            return "Pele escura"
        else:
            return "Pele muito escura"

    def _extract_skin_region(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Extrai a região da pele usando detecção facial.
        Usa a região da testa/bochecha para melhor precisão.
        """
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, _ = image.shape
        results = self.face_detection.process(image_rgb)

        if not results.detections:
            # Fallback: usar região central da imagem
            center_y, center_x = h // 3, w // 2
            region_size = min(h, w) // 8
            region = image[
                center_y - region_size : center_y + region_size,
                center_x - region_size : center_x + region_size,
            ]
            return region

        # Usar a primeira face detectada
        detection = results.detections[0]
        bbox = detection.location_data.relative_bounding_box

        # Região da bochecha (mais representativa do tom de pele)
        face_x = int(bbox.xmin * w)
        face_y = int(bbox.ymin * h)
        face_w = int(bbox.width * w)
        face_h = int(bbox.height * h)

        # Pegar região da bochecha (centro-inferior do rosto)
        cheek_x = face_x + face_w // 4
        cheek_y = face_y + int(face_h * 0.5)
        cheek_w = face_w // 2
        cheek_h = face_h // 4

        # Garantir limites
        cheek_x = max(0, min(cheek_x, w - 1))
        cheek_y = max(0, min(cheek_y, h - 1))
        end_x = min(cheek_x + cheek_w, w)
        end_y = min(cheek_y + cheek_h, h)

        region = image[cheek_y:end_y, cheek_x:end_x]
        return region if region.size > 0 else None

    def analyze(self, image: np.ndarray) -> Optional[SkinAnalysis]:
        """
        Analisa o tom de pele da imagem.

        Args:
            image: Imagem em formato numpy array (BGR).

        Returns:
            SkinAnalysis com cor HEX, subtom e nome da cor.
        """
        skin_region = self._extract_skin_region(image)

        if skin_region is None or skin_region.size == 0:
            return None

        # Converter para RGB e calcular cor média
        skin_rgb = cv2.cvtColor(skin_region, cv2.COLOR_BGR2RGB)

        # Usar máscara de pele para filtrar pixels não-pele
        skin_hsv = cv2.cvtColor(skin_region, cv2.COLOR_BGR2HSV)
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([50, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(skin_hsv, lower_skin, upper_skin)

        # Aplicar máscara
        masked_rgb = cv2.bitwise_and(skin_rgb, skin_rgb, mask=mask)

        # Calcular cor média (ignorando pixels pretos da máscara)
        non_zero = masked_rgb[mask > 0]
        if len(non_zero) == 0:
            # Fallback sem máscara
            mean_color = skin_rgb.mean(axis=(0, 1))
        else:
            mean_color = non_zero.mean(axis=0)

        r, g, b = int(mean_color[0]), int(mean_color[1]), int(mean_color[2])

        hex_color = self._rgb_to_hex(r, g, b)
        undertone = self._classify_undertone(r, g, b)
        color_name = self._get_color_name(r, g, b)

        return SkinAnalysis(
            hex_color=hex_color,
            undertone=undertone,
            color_name=color_name,
        )
