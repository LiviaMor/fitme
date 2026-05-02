"""
Body Scanner 360° - Escaneamento corporal com múltiplas fotos.

Usa 2 fotos (frente + perfil/lado) para calcular circunferências reais.
Com apenas a foto frontal, só temos largura (eixo X).
Com a foto lateral, obtemos profundidade (eixo Z).
Combinando: circunferência ≈ formato elíptico (largura × profundidade).

Fórmula da elipse para circunferência:
C ≈ π × [3(a+b) - √((3a+b)(a+3b))]  (aproximação de Ramanujan)
onde a = semi-eixo maior, b = semi-eixo menor
"""

import math
from typing import Optional, Tuple
from dataclasses import dataclass

import cv2
import mediapipe as mp
import numpy as np


@dataclass
class CircumferenceMeasurements:
    """Medidas de circunferência calculadas com 2 fotos."""
    bust_circumference_cm: float
    waist_circumference_cm: float
    hip_circumference_cm: float
    shoulder_width_cm: float
    chest_depth_cm: float
    waist_depth_cm: float
    hip_depth_cm: float


@dataclass
class FullBodyScan:
    """Resultado completo do escaneamento 360°."""
    # Medidas lineares
    height_cm: float
    shoulder_width_cm: float
    inseam_cm: float
    pants_length_cm: float
    shirt_length_cm: float
    armhole_depth_cm: float

    # Circunferências (requerem foto lateral)
    bust_circumference_cm: float
    waist_circumference_cm: float
    hip_circumference_cm: float

    # Profundidades (do perfil)
    chest_depth_cm: float
    waist_depth_cm: float
    hip_depth_cm: float

    # Metadados
    confidence_front: float
    confidence_side: float
    landmarks_front: int
    landmarks_side: int


class BodyScanner360:
    """
    Escaneamento corporal 360° usando 2 fotos:
    - Foto 1: Frente (larguras)
    - Foto 2: Perfil/Lado (profundidades)

    Combina ambas para calcular circunferências reais.
    """

    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            min_detection_confidence=0.5,
        )

    def _ellipse_circumference(self, a: float, b: float) -> float:
        """
        Calcula circunferência de uma elipse (aproximação de Ramanujan).
        a = semi-eixo maior, b = semi-eixo menor.
        """
        h = ((a - b) ** 2) / ((a + b) ** 2)
        return math.pi * (a + b) * (1 + (3 * h) / (10 + math.sqrt(4 - 3 * h)))

    def _distance_px(self, p1, p2, w: int, h: int) -> float:
        """Distância em pixels entre dois landmarks."""
        x1, y1 = p1.x * w, p1.y * h
        x2, y2 = p2.x * w, p2.y * h
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def _extract_widths(
        self, image: np.ndarray, height_cm: float
    ) -> Optional[Tuple[dict, float, int]]:
        """
        Extrai larguras (frente) da imagem.
        Retorna dict com larguras em cm, scale, e landmarks detectados.
        """
        h, w, _ = image.shape
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)

        if not results.pose_landmarks:
            return None

        lm = results.pose_landmarks.landmark
        num_detected = sum(1 for l in lm if l.visibility > 0.5)

        # Calcular escala (pixels -> cm) usando altura
        nose = lm[0]
        left_ankle = lm[27]
        right_ankle = lm[28]
        mid_ankle_y = (left_ankle.y + right_ankle.y) / 2
        height_px = (mid_ankle_y - nose.y) * h * 1.1  # Ajuste topo cabeça

        if height_px <= 0:
            return None

        scale = height_cm / height_px  # cm por pixel

        # Larguras frontais
        shoulder_width_px = self._distance_px(lm[11], lm[12], w, h)

        # Para busto/cintura/quadril na vista frontal, usamos a silhueta
        # Estimativa: distância entre os pontos laterais do torso
        bust_width_px = shoulder_width_px * 0.95  # Busto ≈ 95% dos ombros
        waist_width_px = self._distance_px(lm[23], lm[24], w, h) * 0.85
        hip_width_px = self._distance_px(lm[23], lm[24], w, h)

        # Medidas lineares
        inseam_px = (mid_ankle_y * h) - ((lm[23].y + lm[24].y) / 2 * h)

        widths = {
            "shoulder_width_cm": shoulder_width_px * scale,
            "bust_width_cm": bust_width_px * scale,
            "waist_width_cm": waist_width_px * scale,
            "hip_width_cm": hip_width_px * scale,
            "inseam_cm": inseam_px * scale,
            "height_px": height_px,
        }

        return widths, scale, num_detected

    def _extract_depths(
        self, image: np.ndarray, scale: float
    ) -> Optional[Tuple[dict, int]]:
        """
        Extrai profundidades (perfil/lado) da imagem.
        Retorna dict com profundidades em cm e landmarks detectados.
        """
        h, w, _ = image.shape
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)

        if not results.pose_landmarks:
            return None

        lm = results.pose_landmarks.landmark
        num_detected = sum(1 for l in lm if l.visibility > 0.5)

        # Na vista lateral, a "largura" visível é a profundidade do corpo
        # Usamos a distância horizontal entre frente e costas do torso

        # Busto: distância entre o ponto mais anterior e posterior do peito
        # No perfil, landmarks 11/12 (ombros) dão a profundidade do tronco
        left_shoulder = lm[11]
        right_shoulder = lm[12]
        left_hip = lm[23]
        right_hip = lm[24]

        # No perfil, a distância horizontal entre ombros = profundidade do peito
        chest_depth_px = abs(left_shoulder.x - right_shoulder.x) * w
        if chest_depth_px < 10:
            # Se os ombros estão sobrepostos, usar largura da silhueta
            # Estimar pela distância entre nariz e ponto mais posterior
            chest_depth_px = abs(lm[0].x * w - ((left_shoulder.x + right_shoulder.x) / 2) * w) * 2.5

        waist_depth_px = abs(left_hip.x - right_hip.x) * w
        if waist_depth_px < 10:
            waist_depth_px = chest_depth_px * 0.7

        hip_depth_px = waist_depth_px * 1.1  # Quadril geralmente mais profundo

        depths = {
            "chest_depth_cm": chest_depth_px * scale,
            "waist_depth_cm": waist_depth_px * scale,
            "hip_depth_cm": hip_depth_px * scale,
        }

        return depths, num_detected

    def scan(
        self,
        front_image: np.ndarray,
        side_image: np.ndarray,
        height_cm: float = 170.0,
    ) -> Optional[FullBodyScan]:
        """
        Escaneamento 360° completo com 2 fotos.

        Args:
            front_image: Foto frontal (BGR).
            side_image: Foto de perfil/lado (BGR).
            height_cm: Altura real do usuário em cm.

        Returns:
            FullBodyScan com todas as medidas incluindo circunferências.
        """
        # Extrair larguras da foto frontal
        front_result = self._extract_widths(front_image, height_cm)
        if front_result is None:
            return None

        widths, scale, landmarks_front = front_result

        # Extrair profundidades da foto lateral
        side_result = self._extract_depths(side_image, scale)
        if side_result is None:
            return None

        depths, landmarks_side = side_result

        # Calcular circunferências usando fórmula da elipse
        # Semi-eixos: largura/2 (frente) e profundidade/2 (lado)
        bust_a = widths["bust_width_cm"] / 2
        bust_b = depths["chest_depth_cm"] / 2
        bust_circ = self._ellipse_circumference(bust_a, bust_b)

        waist_a = widths["waist_width_cm"] / 2
        waist_b = depths["waist_depth_cm"] / 2
        waist_circ = self._ellipse_circumference(waist_a, waist_b)

        hip_a = widths["hip_width_cm"] / 2
        hip_b = depths["hip_depth_cm"] / 2
        hip_circ = self._ellipse_circumference(hip_a, hip_b)

        # Medidas derivadas (fórmulas de modelagem)
        pants_length = (height_cm * 61) / 100
        shirt_length = (height_cm * 45) / 100
        inseam = (height_cm * 16) / 100
        armhole_depth = bust_circ / 4.4

        # Confiança
        confidence_front = min(landmarks_front / 33.0, 1.0)
        confidence_side = min(landmarks_side / 33.0, 1.0)

        return FullBodyScan(
            height_cm=round(height_cm, 1),
            shoulder_width_cm=round(widths["shoulder_width_cm"], 1),
            inseam_cm=round(inseam, 1),
            pants_length_cm=round(pants_length, 1),
            shirt_length_cm=round(shirt_length, 1),
            armhole_depth_cm=round(armhole_depth, 1),
            bust_circumference_cm=round(bust_circ, 1),
            waist_circumference_cm=round(waist_circ, 1),
            hip_circumference_cm=round(hip_circ, 1),
            chest_depth_cm=round(depths["chest_depth_cm"], 1),
            waist_depth_cm=round(depths["waist_depth_cm"], 1),
            hip_depth_cm=round(depths["hip_depth_cm"], 1),
            confidence_front=round(confidence_front, 2),
            confidence_side=round(confidence_side, 2),
            landmarks_front=landmarks_front,
            landmarks_side=landmarks_side,
        )
