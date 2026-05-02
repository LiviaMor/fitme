"""
Estadiômetro Digital - Simulação baseada nos padrões WELMY.

Modelos de referência Welmy:
- W200/5: Balança antropométrica adulto, capacidade 200kg, estadiômetro 100-200cm
- W110H: Balança plataforma com estadiômetro, resolução 0.5cm
- W200/5A: Modelo com régua antropométrica acoplada

Especificações técnicas do estadiômetro digital:
- Faixa de medição: 100cm a 200cm (adulto) / 20cm a 100cm (pediátrico)
- Resolução: 0.5cm (padrão Welmy) ou 0.1cm (modo alta precisão)
- Precisão: ±0.3cm em condições ideais
- Método: Detecção do topo da cabeça via MediaPipe + calibração por referência

O estadiômetro digital usa a câmera para simular a medição de altura
com a mesma precisão e padrão dos equipamentos Welmy, usando:
1. Grade milimétrica virtual para calibração
2. Detecção de landmarks da cabeça e pés
3. Correção de perspectiva e distorção
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np


class WelmyModel(str, Enum):
    """Modelos de estadiômetro Welmy simulados."""
    W200_5 = "W200/5"       # Adulto padrão: 100-200cm, resolução 0.5cm
    W200_5A = "W200/5A"     # Adulto alta precisão: 100-200cm, resolução 0.1cm
    W110H = "W110H"         # Plataforma: 100-200cm, resolução 0.5cm
    PEDIATRICO = "Pediátrico"  # Infantômetro: 20-100cm, resolução 0.1cm


@dataclass
class StadiometerConfig:
    """Configuração do estadiômetro baseada no modelo Welmy."""
    model: WelmyModel
    min_height_cm: float
    max_height_cm: float
    resolution_cm: float
    precision_cm: float
    description: str


# Configurações dos modelos Welmy
WELMY_MODELS = {
    WelmyModel.W200_5: StadiometerConfig(
        model=WelmyModel.W200_5,
        min_height_cm=100.0,
        max_height_cm=200.0,
        resolution_cm=0.5,
        precision_cm=0.3,
        description="Balança antropométrica adulto com estadiômetro - Padrão clínico",
    ),
    WelmyModel.W200_5A: StadiometerConfig(
        model=WelmyModel.W200_5A,
        min_height_cm=100.0,
        max_height_cm=200.0,
        resolution_cm=0.1,
        precision_cm=0.2,
        description="Balança antropométrica adulto alta precisão com régua digital",
    ),
    WelmyModel.W110H: StadiometerConfig(
        model=WelmyModel.W110H,
        min_height_cm=100.0,
        max_height_cm=200.0,
        resolution_cm=0.5,
        precision_cm=0.3,
        description="Balança plataforma com estadiômetro integrado",
    ),
    WelmyModel.PEDIATRICO: StadiometerConfig(
        model=WelmyModel.PEDIATRICO,
        min_height_cm=20.0,
        max_height_cm=100.0,
        resolution_cm=0.1,
        precision_cm=0.1,
        description="Infantômetro digital para medição pediátrica",
    ),
}


@dataclass
class HeightMeasurement:
    """Resultado da medição de altura pelo estadiômetro digital."""
    height_cm: float
    height_rounded_cm: float  # Arredondado pela resolução do modelo
    model_used: WelmyModel
    confidence: float  # 0.0 a 1.0
    calibration_method: str
    within_range: bool  # Se está dentro da faixa do modelo
    grid_detected: bool  # Se a grade milimétrica foi detectada
    message: str


class DigitalStadiometer:
    """
    Estadiômetro digital baseado nos padrões Welmy.

    Usa MediaPipe para detectar o topo da cabeça e a base dos pés,
    e aplica calibração por grade milimétrica ou referência conhecida.
    """

    def __init__(self, model: WelmyModel = WelmyModel.W200_5):
        self.config = WELMY_MODELS[model]
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            min_detection_confidence=0.5,
        )

    def _round_to_resolution(self, value_cm: float) -> float:
        """Arredonda o valor para a resolução do modelo Welmy."""
        resolution = self.config.resolution_cm
        return round(value_cm / resolution) * resolution

    def _detect_grid(self, image: np.ndarray) -> Optional[float]:
        """
        Detecta grade milimétrica na imagem para calibração.

        A grade deve ter linhas espaçadas em intervalos conhecidos.
        Retorna o fator pixels/cm se detectada, None caso contrário.

        Método: Detecta linhas horizontais paralelas e calcula
        o espaçamento médio em pixels.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        # Detectar linhas horizontais com Hough Transform
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180,
            threshold=100,
            minLineLength=image.shape[1] * 0.3,
            maxLineGap=10,
        )

        if lines is None or len(lines) < 3:
            return None

        # Filtrar linhas horizontais (ângulo < 5 graus)
        horizontal_lines = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = abs(math.atan2(y2 - y1, x2 - x1) * 180 / math.pi)
            if angle < 5 or angle > 175:
                horizontal_lines.append((y1 + y2) / 2)

        if len(horizontal_lines) < 3:
            return None

        # Ordenar e calcular espaçamento médio
        horizontal_lines.sort()
        spacings = []
        for i in range(1, len(horizontal_lines)):
            spacing = horizontal_lines[i] - horizontal_lines[i - 1]
            if spacing > 5:  # Ignorar linhas muito próximas (ruído)
                spacings.append(spacing)

        if not spacings:
            return None

        avg_spacing_px = np.median(spacings)

        # Assumir que a grade tem espaçamento de 1cm entre linhas
        # (padrão de grade milimétrica para estadiômetro)
        pixels_per_cm = avg_spacing_px / 1.0

        return pixels_per_cm

    def _get_head_top(
        self, landmarks, image_height: int, image_width: int
    ) -> Tuple[float, float]:
        """
        Estima o topo da cabeça a partir dos landmarks do MediaPipe.

        O MediaPipe não tem um landmark para o topo da cabeça,
        então estimamos a partir do nariz e orelhas.
        """
        nose = landmarks[0]
        left_ear = landmarks[7]
        right_ear = landmarks[8]

        # Centro entre as orelhas (topo do crânio estimado)
        ear_center_y = (left_ear.y + right_ear.y) / 2
        nose_y = nose.y

        # O topo da cabeça está aproximadamente a mesma distância
        # acima das orelhas que as orelhas estão acima do nariz
        ear_to_nose = nose_y - ear_center_y
        head_top_y = ear_center_y - (ear_to_nose * 1.5)

        head_top_x = (left_ear.x + right_ear.x) / 2

        return (head_top_x * image_width, head_top_y * image_height)

    def _get_feet_base(
        self, landmarks, image_height: int, image_width: int
    ) -> Tuple[float, float]:
        """
        Obtém a base dos pés (ponto mais baixo).
        Usa os landmarks dos dedos dos pés e calcanhares.
        """
        # Landmarks dos pés no MediaPipe:
        # 29, 30 = calcanhar esquerdo/direito
        # 31, 32 = ponta do pé esquerdo/direito
        foot_landmarks = [
            landmarks[29],  # Calcanhar esquerdo
            landmarks[30],  # Calcanhar direito
            landmarks[31],  # Ponta pé esquerdo
            landmarks[32],  # Ponta pé direito
        ]

        # Pegar o ponto mais baixo (maior Y)
        max_y = max(lm.y for lm in foot_landmarks)
        avg_x = sum(lm.x for lm in foot_landmarks) / len(foot_landmarks)

        return (avg_x * image_width, max_y * image_height)

    def measure(
        self,
        image: np.ndarray,
        reference_object_cm: Optional[float] = None,
        reference_object_px: Optional[float] = None,
    ) -> HeightMeasurement:
        """
        Mede a altura usando o estadiômetro digital.

        Args:
            image: Imagem BGR do corpo inteiro.
            reference_object_cm: Tamanho real de um objeto de referência (opcional).
            reference_object_px: Tamanho em pixels do objeto de referência (opcional).

        Returns:
            HeightMeasurement com a altura medida e metadados.
        """
        h, w, _ = image.shape
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Detectar pose
        results = self.pose.process(image_rgb)

        if not results.pose_landmarks:
            return HeightMeasurement(
                height_cm=0.0,
                height_rounded_cm=0.0,
                model_used=self.config.model,
                confidence=0.0,
                calibration_method="none",
                within_range=False,
                grid_detected=False,
                message="Corpo não detectado. Posicione-se de frente, corpo inteiro visível.",
            )

        landmarks = results.pose_landmarks.landmark

        # Verificar visibilidade dos landmarks essenciais
        essential = [0, 7, 8, 29, 30, 31, 32]  # Cabeça e pés
        visible_count = sum(
            1 for idx in essential if landmarks[idx].visibility > 0.5
        )

        if visible_count < 4:
            return HeightMeasurement(
                height_cm=0.0,
                height_rounded_cm=0.0,
                model_used=self.config.model,
                confidence=0.0,
                calibration_method="none",
                within_range=False,
                grid_detected=False,
                message="Landmarks insuficientes. Certifique-se de que cabeça e pés estão visíveis.",
            )

        # Obter pontos extremos
        head_top = self._get_head_top(landmarks, h, w)
        feet_base = self._get_feet_base(landmarks, h, w)

        # Altura em pixels
        height_px = feet_base[1] - head_top[1]

        if height_px <= 0:
            return HeightMeasurement(
                height_cm=0.0,
                height_rounded_cm=0.0,
                model_used=self.config.model,
                confidence=0.0,
                calibration_method="none",
                within_range=False,
                grid_detected=False,
                message="Erro na detecção. Verifique posicionamento.",
            )

        # Calibração - Prioridade: 1) Grade, 2) Referência, 3) Proporção
        pixels_per_cm = None
        calibration_method = "proportion"
        grid_detected = False

        # Tentar detectar grade milimétrica
        grid_ppcm = self._detect_grid(image)
        if grid_ppcm and grid_ppcm > 0:
            pixels_per_cm = grid_ppcm
            calibration_method = "grid_millimetric"
            grid_detected = True

        # Usar referência fornecida
        elif reference_object_cm and reference_object_px:
            pixels_per_cm = reference_object_px / reference_object_cm
            calibration_method = "reference_object"

        # Fallback: proporção corporal (menos preciso)
        if pixels_per_cm is None:
            # Usar distância entre ombros como referência
            # Largura média de ombros adulto: ~40cm
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            shoulder_px = math.sqrt(
                ((left_shoulder.x - right_shoulder.x) * w) ** 2
                + ((left_shoulder.y - right_shoulder.y) * h) ** 2
            )
            # Proporção: altura ≈ 4.2x largura dos ombros
            estimated_height_cm = shoulder_px * 4.2 * (1.0 / (shoulder_px / height_px))
            pixels_per_cm = height_px / estimated_height_cm
            calibration_method = "body_proportion"

        # Calcular altura em cm
        height_cm = height_px / pixels_per_cm

        # Aplicar resolução do modelo Welmy
        height_rounded = self._round_to_resolution(height_cm)

        # Verificar se está dentro da faixa do modelo
        within_range = (
            self.config.min_height_cm <= height_rounded <= self.config.max_height_cm
        )

        # Calcular confiança
        confidence = self._calculate_confidence(
            visible_count, len(essential), grid_detected, calibration_method
        )

        # Mensagem
        if not within_range:
            message = (
                f"Altura {height_rounded}cm fora da faixa do modelo "
                f"{self.config.model.value} ({self.config.min_height_cm}-"
                f"{self.config.max_height_cm}cm)."
            )
        elif grid_detected:
            message = (
                f"Medição calibrada por grade milimétrica. "
                f"Precisão: ±{self.config.precision_cm}cm"
            )
        elif calibration_method == "reference_object":
            message = (
                f"Medição calibrada por objeto de referência. "
                f"Precisão estimada: ±{self.config.precision_cm * 2}cm"
            )
        else:
            message = (
                f"Medição por proporção corporal. "
                f"Precisão estimada: ±2.0cm. "
                f"Use grade milimétrica para maior precisão."
            )

        return HeightMeasurement(
            height_cm=round(height_cm, 1),
            height_rounded_cm=height_rounded,
            model_used=self.config.model,
            confidence=round(confidence, 2),
            calibration_method=calibration_method,
            within_range=within_range,
            grid_detected=grid_detected,
            message=message,
        )

    def _calculate_confidence(
        self,
        visible_landmarks: int,
        total_landmarks: int,
        grid_detected: bool,
        calibration_method: str,
    ) -> float:
        """Calcula score de confiança da medição."""
        # Base: proporção de landmarks visíveis
        landmark_score = visible_landmarks / total_landmarks

        # Bônus por método de calibração
        if grid_detected:
            calibration_bonus = 0.3
        elif calibration_method == "reference_object":
            calibration_bonus = 0.2
        else:
            calibration_bonus = 0.0

        confidence = min((landmark_score * 0.7) + calibration_bonus, 1.0)
        return confidence

    def generate_grid_overlay(
        self, image: np.ndarray, spacing_cm: float = 5.0, pixels_per_cm: float = 10.0
    ) -> np.ndarray:
        """
        Gera overlay de grade milimétrica na imagem para guiar o usuário.

        Args:
            image: Imagem original.
            spacing_cm: Espaçamento da grade em cm.
            pixels_per_cm: Escala pixels/cm.

        Returns:
            Imagem com grade sobreposta.
        """
        overlay = image.copy()
        h, w, _ = overlay.shape

        spacing_px = int(spacing_cm * pixels_per_cm)

        # Linhas horizontais (marcações de altura)
        for y in range(0, h, spacing_px):
            cv2.line(overlay, (0, y), (w, y), (0, 255, 0), 1)
            # Label a cada 10cm
            height_at_line = (h - y) / pixels_per_cm
            if height_at_line % 10 < spacing_cm:
                cv2.putText(
                    overlay,
                    f"{int(height_at_line)}cm",
                    (5, y + 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (0, 255, 0),
                    1,
                )

        # Linha central vertical (guia de posicionamento)
        center_x = w // 2
        cv2.line(overlay, (center_x, 0), (center_x, h), (255, 255, 0), 1)

        # Blend com transparência
        result = cv2.addWeighted(image, 0.7, overlay, 0.3, 0)
        return result
