"""
Scanner 360° Multi-Frame.

O usuário gira lentamente em frente à câmera.
O sistema captura 4-8 frames em ângulos diferentes e combina
os landmarks de cada ângulo para reconstruir medidas 3D completas.

Ângulos capturados:
- 0° (frente): largura ombros, largura quadril
- 90° (lado direito): profundidade peito, profundidade quadril
- 180° (costas): largura costas, confirmação ombros
- 270° (lado esquerdo): confirmação profundidades

Com 4 frames, calcula circunferências reais usando elipse.
Com 8 frames (45° cada), usa interpolação para maior precisão.
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np


@dataclass
class FrameAnalysis:
    """Análise de um frame individual."""
    angle_degrees: int
    shoulder_width_px: float
    torso_width_px: float
    hip_width_px: float
    height_px: float
    landmarks_detected: int
    confidence: float


@dataclass
class Scan360Result:
    """Resultado completo do scan 360°."""
    # Circunferências reais
    bust_circumference_cm: float
    waist_circumference_cm: float
    hip_circumference_cm: float

    # Medidas lineares
    height_cm: float
    shoulder_width_cm: float
    back_width_cm: float

    # Fórmulas de modelagem
    inseam_cm: float          # altura × 16 / 100
    pants_length_cm: float    # altura × 61 / 100
    shirt_length_cm: float    # altura × 45 / 100
    armhole_depth_cm: float   # busto / 4.4

    # Profundidades
    chest_depth_cm: float
    waist_depth_cm: float
    hip_depth_cm: float

    # Metadados
    frames_analyzed: int
    angles_captured: List[int]
    overall_confidence: float
    landmarks_vector: List[float] = field(default_factory=list)


class MultiFrameScanner360:
    """
    Scanner 360° que processa múltiplos frames de diferentes ângulos.
    """

    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            min_detection_confidence=0.5,
        )

    def _analyze_frame(self, image: np.ndarray) -> Optional[FrameAnalysis]:
        """Analisa um frame individual e extrai medidas em pixels."""
        h, w, _ = image.shape
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)

        if not results.pose_landmarks:
            return None

        lm = results.pose_landmarks.landmark
        num_detected = sum(1 for l in lm if l.visibility > 0.5)

        if num_detected < 15:
            return None

        # Largura dos ombros
        ls, rs = lm[11], lm[12]
        shoulder_w = math.sqrt(
            ((rs.x - ls.x) * w) ** 2 + ((rs.y - ls.y) * h) ** 2
        )

        # Largura do torso (meio entre ombros e quadril)
        lh, rh = lm[23], lm[24]
        hip_w = math.sqrt(
            ((rh.x - lh.x) * w) ** 2 + ((rh.y - lh.y) * h) ** 2
        )
        torso_w = (shoulder_w + hip_w) / 2

        # Altura
        nose = lm[0]
        la, ra = lm[27], lm[28]
        mid_ankle_y = (la.y + ra.y) / 2
        height_px = (mid_ankle_y - nose.y) * h * 1.1

        confidence = min(num_detected / 33.0, 1.0)

        return FrameAnalysis(
            angle_degrees=0,  # Será definido externamente
            shoulder_width_px=shoulder_w,
            torso_width_px=torso_w,
            hip_width_px=hip_w,
            height_px=height_px,
            landmarks_detected=num_detected,
            confidence=confidence,
        )

    def _detect_rotation_angle(
        self, landmarks, w: int, h: int
    ) -> int:
        """
        Estima o ângulo de rotação do corpo baseado na posição dos ombros.

        - Ombros com mesma X e distância grande = frontal (0°) ou costas (180°)
        - Ombros sobrepostos (distância pequena) = lateral (90° ou 270°)
        - Intermediário = 45°, 135°, etc.
        """
        ls, rs = landmarks[11], landmarks[12]
        shoulder_dist_x = abs(rs.x - ls.x) * w
        shoulder_dist_y = abs(rs.y - ls.y) * h

        # Distância horizontal normalizada pela largura da imagem
        norm_dist = shoulder_dist_x / w

        if norm_dist > 0.15:
            # Ombros bem separados = frontal ou costas
            # Diferenciar: se nariz está entre os ombros = frontal
            nose_x = landmarks[0].x
            mid_shoulder_x = (ls.x + rs.x) / 2
            if abs(nose_x - mid_shoulder_x) < 0.1:
                return 0  # Frontal
            else:
                return 180  # Costas
        elif norm_dist > 0.08:
            # Parcialmente virado = 45° ou 135°
            nose_x = landmarks[0].x
            mid_shoulder_x = (ls.x + rs.x) / 2
            if nose_x < mid_shoulder_x:
                return 315  # 45° para esquerda
            else:
                return 45
        else:
            # Ombros sobrepostos = lateral
            # Diferenciar lado: posição do nariz relativa aos ombros
            nose_x = landmarks[0].x
            mid_shoulder_x = (ls.x + rs.x) / 2
            if nose_x < mid_shoulder_x:
                return 270  # Lado esquerdo visível
            else:
                return 90  # Lado direito visível

    def _ellipse_circumference(self, a: float, b: float) -> float:
        """Circunferência da elipse (Ramanujan)."""
        if a <= 0 or b <= 0:
            return 0
        h = ((a - b) ** 2) / ((a + b) ** 2)
        return math.pi * (a + b) * (1 + (3 * h) / (10 + math.sqrt(4 - 3 * h)))

    def scan(
        self,
        frames: List[np.ndarray],
        height_cm: float = 170.0,
    ) -> Optional[Scan360Result]:
        """
        Processa múltiplos frames e calcula medidas 360°.

        Args:
            frames: Lista de imagens (BGR) de diferentes ângulos.
            height_cm: Altura real do usuário.

        Returns:
            Scan360Result com medidas completas.
        """
        if not frames:
            return None

        analyses: List[FrameAnalysis] = []
        angles_data: dict = {}  # angle -> FrameAnalysis
        all_landmarks_flat: List[float] = []

        for frame in frames:
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb)

            if not results.pose_landmarks:
                continue

            lm = results.pose_landmarks.landmark

            # Detectar ângulo automaticamente
            angle = self._detect_rotation_angle(lm, w, h)

            # Analisar frame
            analysis = self._analyze_frame(frame)
            if analysis is None:
                continue

            analysis.angle_degrees = angle
            analyses.append(analysis)

            # Guardar por ângulo (manter o de maior confiança)
            if angle not in angles_data or analysis.confidence > angles_data[angle].confidence:
                angles_data[angle] = analysis

            # Acumular landmarks para vetor (usar primeiro frame bom)
            if not all_landmarks_flat:
                for l in lm:
                    all_landmarks_flat.extend([l.x, l.y, l.z])

        if not analyses:
            return None

        # Calcular escala usando a melhor estimativa de altura
        best_height_px = max(a.height_px for a in analyses if a.height_px > 0)
        if best_height_px <= 0:
            return None

        scale = height_cm / best_height_px  # cm/pixel

        # === EXTRAIR MEDIDAS POR ÂNGULO ===

        # Frontal (0°): larguras reais
        front = angles_data.get(0) or angles_data.get(
            min(angles_data.keys(), key=lambda a: min(a, 360 - a))
        )

        # Lateral (90° ou 270°): profundidades
        side = angles_data.get(90) or angles_data.get(270)

        # Costas (180°): largura das costas
        back = angles_data.get(180)

        # Larguras (da vista frontal)
        shoulder_width_cm = front.shoulder_width_px * scale if front else 0
        hip_width_cm = front.hip_width_px * scale if front else 0
        bust_width_cm = front.torso_width_px * scale if front else shoulder_width_cm * 0.95

        # Profundidades (da vista lateral)
        if side:
            # Na vista lateral, a "largura" dos ombros = profundidade do peito
            chest_depth_cm = side.shoulder_width_px * scale * 0.6
            waist_depth_cm = side.torso_width_px * scale * 0.5
            hip_depth_cm = side.hip_width_px * scale * 0.55
        else:
            # Estimativa sem foto lateral (menos preciso)
            chest_depth_cm = bust_width_cm * 0.6
            waist_depth_cm = bust_width_cm * 0.45
            hip_depth_cm = hip_width_cm * 0.55

        # Largura das costas
        back_width_cm = back.shoulder_width_px * scale if back else shoulder_width_cm * 0.95

        # === CIRCUNFERÊNCIAS (elipse) ===
        bust_circ = self._ellipse_circumference(bust_width_cm / 2, chest_depth_cm / 2)
        waist_circ = self._ellipse_circumference(hip_width_cm * 0.4, waist_depth_cm / 2)
        hip_circ = self._ellipse_circumference(hip_width_cm / 2, hip_depth_cm / 2)

        # === FÓRMULAS DE MODELAGEM ===
        inseam = (height_cm * 16) / 100
        pants_length = (height_cm * 61) / 100
        shirt_length = (height_cm * 45) / 100
        armhole_depth = bust_circ / 4.4

        # Confiança geral
        overall_confidence = sum(a.confidence for a in analyses) / len(analyses)
        # Bônus por ter múltiplos ângulos
        angle_bonus = min(len(angles_data) / 4.0, 1.0) * 0.2
        overall_confidence = min(overall_confidence + angle_bonus, 1.0)

        return Scan360Result(
            bust_circumference_cm=round(bust_circ, 1),
            waist_circumference_cm=round(waist_circ, 1),
            hip_circumference_cm=round(hip_circ, 1),
            height_cm=round(height_cm, 1),
            shoulder_width_cm=round(shoulder_width_cm, 1),
            back_width_cm=round(back_width_cm, 1),
            inseam_cm=round(inseam, 1),
            pants_length_cm=round(pants_length, 1),
            shirt_length_cm=round(shirt_length, 1),
            armhole_depth_cm=round(armhole_depth, 1),
            chest_depth_cm=round(chest_depth_cm, 1),
            waist_depth_cm=round(waist_depth_cm, 1),
            hip_depth_cm=round(hip_depth_cm, 1),
            frames_analyzed=len(analyses),
            angles_captured=sorted(angles_data.keys()),
            overall_confidence=round(overall_confidence, 2),
            landmarks_vector=all_landmarks_flat[:99],  # Primeiros 99 (33×3)
        )
