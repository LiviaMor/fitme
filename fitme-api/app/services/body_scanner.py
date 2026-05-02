"""
Serviço de escaneamento corporal usando MediaPipe Pose Estimation.
Extrai landmarks do corpo e calcula medidas reais baseadas em referência.
"""

import math
from typing import Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np
from PIL import Image

from app.models.measurements import BodyMeasurements, BodyType


class BodyScanner:
    """Extrai medidas corporais a partir de uma imagem usando MediaPipe."""

    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            min_detection_confidence=0.5,
        )

    def _calculate_distance(
        self, p1: Tuple[float, float], p2: Tuple[float, float]
    ) -> float:
        """Calcula distância euclidiana entre dois pontos."""
        return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

    def _pixels_to_cm(
        self, pixel_distance: float, reference_cm: float, reference_pixels: float
    ) -> float:
        """Converte distância em pixels para centímetros usando referência."""
        if reference_pixels == 0:
            return 0.0
        return (pixel_distance / reference_pixels) * reference_cm

    def _estimate_body_type(self, measurements: BodyMeasurements) -> BodyType:
        """Estima o biotipo corporal baseado nas medidas."""
        shoulder = measurements.shoulder_width_cm
        bust = measurements.bust_cm or shoulder
        waist = measurements.waist_cm or shoulder * 0.7
        hip = measurements.hip_cm or shoulder

        # Lógica de classificação de biotipo
        if hip > shoulder * 1.05:
            return BodyType.TRIANGULO
        elif shoulder > hip * 1.05:
            return BodyType.TRIANGULO_INVERTIDO
        elif abs(bust - hip) < 5 and waist < bust * 0.75:
            return BodyType.AMPULHETA
        elif abs(shoulder - hip) < 5 and abs(waist - hip) < 10:
            return BodyType.RETANGULO
        else:
            return BodyType.OVAL

    def analyze(
        self, image: np.ndarray, reference_height_cm: Optional[float] = None
    ) -> Tuple[Optional[BodyMeasurements], int, float]:
        """
        Analisa a imagem e extrai medidas corporais.

        Args:
            image: Imagem em formato numpy array (BGR).
            reference_height_cm: Altura real do usuário para calibração (opcional).

        Returns:
            Tuple com (medidas, landmarks detectados, confiança).
        """
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, _ = image.shape
        results = self.pose.process(image_rgb)

        if not results.pose_landmarks:
            return None, 0, 0.0

        landmarks = results.pose_landmarks.landmark
        num_detected = sum(1 for lm in landmarks if lm.visibility > 0.5)

        # Pontos-chave do MediaPipe Pose
        left_shoulder = (landmarks[11].x * w, landmarks[11].y * h)
        right_shoulder = (landmarks[12].x * w, landmarks[12].y * h)
        left_hip = (landmarks[23].x * w, landmarks[23].y * h)
        right_hip = (landmarks[24].x * w, landmarks[24].y * h)
        left_ankle = (landmarks[27].x * w, landmarks[27].y * h)
        right_ankle = (landmarks[28].x * w, landmarks[28].y * h)
        nose = (landmarks[0].x * w, landmarks[0].y * h)

        # Distâncias em pixels
        shoulder_px = self._calculate_distance(left_shoulder, right_shoulder)
        hip_px = self._calculate_distance(left_hip, right_hip)

        # Altura em pixels (do topo da cabeça ao tornozelo)
        mid_ankle = (
            (left_ankle[0] + right_ankle[0]) / 2,
            (left_ankle[1] + right_ankle[1]) / 2,
        )
        height_px = self._calculate_distance(nose, mid_ankle) * 1.1  # Ajuste topo cabeça

        # Calibração: usar altura real ou estimar
        ref_height = reference_height_cm or 170.0  # Padrão 170cm
        scale = ref_height / height_px if height_px > 0 else 1.0

        # Converter para cm (com fator de correção para profundidade)
        shoulder_cm = shoulder_px * scale * 1.2  # Fator de correção 2D->3D
        hip_cm = hip_px * scale * 1.8  # Quadril tem mais profundidade

        # Estimativa do tórax baseada nos landmarks
        bust_cm = shoulder_cm * 2.3  # Proporção média busto/ombro
        waist_cm = hip_cm * 0.8  # Proporção média cintura/quadril

        # ===== FÓRMULAS DE MODELAGEM =====
        # Altura do gancho = (altura x 16) / 100
        inseam_cm = (ref_height * 16) / 100

        # Comprimento da calça = (altura x 61) / 100
        pants_length_cm = (ref_height * 61) / 100

        # Comprimento da camisa = (altura x 45) / 100
        shirt_length_cm = (ref_height * 45) / 100

        # Altura da cava = tórax / 4.4
        armhole_depth_cm = bust_cm / 4.4

        measurements = BodyMeasurements(
            shoulder_width_cm=round(shoulder_cm, 1),
            bust_cm=round(bust_cm, 1),
            waist_cm=round(waist_cm, 1),
            hip_cm=round(hip_cm, 1),
            inseam_cm=round(inseam_cm, 1),
            pants_length_cm=round(pants_length_cm, 1),
            shirt_length_cm=round(shirt_length_cm, 1),
            armhole_depth_cm=round(armhole_depth_cm, 1),
            height_cm=round(ref_height, 1),
        )

        confidence = min(num_detected / 33.0, 1.0)
        return measurements, num_detected, confidence

    def get_body_type(self, measurements: BodyMeasurements) -> BodyType:
        """Retorna o biotipo baseado nas medidas."""
        return self._estimate_body_type(measurements)
