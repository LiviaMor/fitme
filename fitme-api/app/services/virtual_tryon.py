"""
Virtual Try-On Service.

Recebe a foto do cliente + imagem da roupa (via URL ou upload)
e gera uma sobreposição visual da peça no corpo do cliente
usando os landmarks do MediaPipe para posicionamento.

Fluxo:
1. Detecta landmarks do corpo (ombros, quadril, etc.)
2. Baixa/recebe imagem da roupa
3. Remove fundo da roupa (branco/claro -> transparente)
4. Redimensiona e posiciona a roupa nos landmarks
5. Faz blend (overlay) da roupa sobre o corpo
6. Retorna imagem final

Para MVP usa warp + overlay. Em produção, substituir por
modelos como IDM-VTON, OOTDiffusion ou similar.
"""

import math
from typing import Optional, Tuple

import cv2
import httpx
import mediapipe as mp
import numpy as np


class VirtualTryOn:
    """Serviço de prova virtual por sobreposição."""

    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            min_detection_confidence=0.5,
        )

    async def fetch_garment_image(self, url: str) -> Optional[np.ndarray]:
        """Baixa a imagem da roupa a partir de uma URL."""
        try:
            async with httpx.AsyncClient(
                timeout=15, follow_redirects=True
            ) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    nparr = np.frombuffer(response.content, np.uint8)
                    image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
                    return image
        except Exception:
            return None
        return None

    def _remove_background(self, garment_img: np.ndarray) -> np.ndarray:
        """
        Remove fundo branco/claro da imagem da roupa.
        Retorna imagem BGRA (com canal alpha para transparência).
        """
        if len(garment_img.shape) == 2:
            garment_img = cv2.cvtColor(garment_img, cv2.COLOR_GRAY2BGR)

        if garment_img.shape[2] == 4:
            return garment_img

        # Converter para HSV para detectar fundo claro
        hsv = cv2.cvtColor(garment_img, cv2.COLOR_BGR2HSV)

        # Máscara para fundo branco/claro (saturation baixa, value alto)
        lower_white = np.array([0, 0, 200], dtype=np.uint8)
        upper_white = np.array([180, 50, 255], dtype=np.uint8)
        white_mask = cv2.inRange(hsv, lower_white, upper_white)

        # Máscara para fundo cinza claro
        lower_gray = np.array([0, 0, 180], dtype=np.uint8)
        upper_gray = np.array([180, 30, 255], dtype=np.uint8)
        gray_mask = cv2.inRange(hsv, lower_gray, upper_gray)

        # Combinar máscaras de fundo
        bg_mask = cv2.bitwise_or(white_mask, gray_mask)

        # Dilatar para pegar bordas
        kernel = np.ones((3, 3), np.uint8)
        bg_mask = cv2.dilate(bg_mask, kernel, iterations=1)

        # Inverter: roupa = branco, fundo = preto
        fg_mask = cv2.bitwise_not(bg_mask)

        # Limpar ruído
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=1)

        # Criar BGRA
        bgra = cv2.cvtColor(garment_img, cv2.COLOR_BGR2BGRA)
        bgra[:, :, 3] = fg_mask

        return bgra

    def _get_body_region(
        self, landmarks, h: int, w: int, garment_type: str
    ) -> Tuple[int, int, int, int, float]:
        """
        Calcula a região do corpo onde a roupa deve ser posicionada.

        Returns:
            (x, y, width, height, angle) da região alvo.
        """
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        left_hip = landmarks[23]
        right_hip = landmarks[24]
        left_ankle = landmarks[27]
        right_ankle = landmarks[28]

        if garment_type in ("camiseta", "camisa", "blazer", "jaqueta"):
            # Região: além dos ombros (incluir mangas) até abaixo do quadril
            shoulder_width = abs(right_shoulder.x - left_shoulder.x) * w
            extra_w = int(shoulder_width * 0.35)  # Espaço para mangas
            x1 = int(min(left_shoulder.x, right_shoulder.x) * w) - extra_w
            y1 = int(min(left_shoulder.y, right_shoulder.y) * h) - 15
            x2 = int(max(left_shoulder.x, right_shoulder.x) * w) + extra_w
            y2 = int(max(left_hip.y, right_hip.y) * h) + 20

        elif garment_type in ("vestido", "saia"):
            # Região: ombros/cintura até tornozelos, com largura extra
            shoulder_width = abs(right_shoulder.x - left_shoulder.x) * w
            extra_w = int(shoulder_width * 0.3)
            x1 = int(min(left_shoulder.x, right_shoulder.x) * w) - extra_w
            y1 = int(min(left_shoulder.y, right_shoulder.y) * h) - 15
            x2 = int(max(left_hip.x, right_hip.x) * w) + extra_w
            y2 = int(max(left_ankle.y, right_ankle.y) * h)

        elif garment_type == "calca":
            # Região: quadril até tornozelos
            x1 = int(min(left_hip.x, right_hip.x) * w) - 15
            y1 = int(min(left_hip.y, right_hip.y) * h) - 10
            x2 = int(max(left_hip.x, right_hip.x) * w) + 15
            y2 = int(max(left_ankle.y, right_ankle.y) * h) + 5

        else:
            # Fallback: corpo inteiro
            x1 = int(min(left_shoulder.x, right_shoulder.x) * w) - 20
            y1 = int(min(left_shoulder.y, right_shoulder.y) * h) - 10
            x2 = int(max(left_hip.x, right_hip.x) * w) + 20
            y2 = int(max(left_ankle.y, right_ankle.y) * h)

        # Garantir limites
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)

        # Calcular ângulo dos ombros para rotação.
        # ATENÇÃO: No MediaPipe, landmark 11 = ombro esquerdo do usuário,
        # que aparece à DIREITA na imagem (coordenadas de câmera, não espelhadas).
        # Por isso usamos (left - right) para obter o ângulo correto sem inversão.
        angle = math.degrees(
            math.atan2(
                (left_shoulder.y - right_shoulder.y) * h,
                (left_shoulder.x - right_shoulder.x) * w,
            )
        )

        region_w = x2 - x1
        region_h = y2 - y1

        return x1, y1, region_w, region_h, angle

    def _overlay_transparent(
        self,
        background: np.ndarray,
        overlay: np.ndarray,
        x: int,
        y: int,
        overlay_width: int,
        overlay_height: int,
    ) -> np.ndarray:
        """
        Sobrepõe imagem com transparência (BGRA) sobre o fundo (BGR).
        """
        # Redimensionar overlay
        resized = cv2.resize(
            overlay, (overlay_width, overlay_height), interpolation=cv2.INTER_AREA
        )

        result = background.copy()
        bg_h, bg_w = result.shape[:2]

        # Calcular região de sobreposição válida
        y1 = max(0, y)
        y2 = min(bg_h, y + overlay_height)
        x1 = max(0, x)
        x2 = min(bg_w, x + overlay_width)

        # Offsets no overlay
        oy1 = y1 - y
        oy2 = oy1 + (y2 - y1)
        ox1 = x1 - x
        ox2 = ox1 + (x2 - x1)

        if y2 <= y1 or x2 <= x1:
            return result

        # Extrair canal alpha
        overlay_crop = resized[oy1:oy2, ox1:ox2]
        alpha = overlay_crop[:, :, 3].astype(float) / 255.0
        alpha_3ch = np.stack([alpha, alpha, alpha], axis=-1)

        # Blend
        bg_region = result[y1:y2, x1:x2].astype(float)
        fg_region = overlay_crop[:, :, :3].astype(float)

        blended = (fg_region * alpha_3ch + bg_region * (1 - alpha_3ch)).astype(
            np.uint8
        )
        result[y1:y2, x1:x2] = blended

        return result

    async def try_on(
        self,
        person_image: np.ndarray,
        garment_image: np.ndarray,
        garment_type: str = "camiseta",
        opacity: float = 0.85,
    ) -> Optional[np.ndarray]:
        """
        Realiza o try-on virtual: sobrepõe a roupa no corpo do cliente.

        Args:
            person_image: Foto do cliente (BGR).
            garment_image: Imagem da roupa (BGR ou BGRA).
            garment_type: Tipo da peça (camiseta, calca, vestido, etc).
            opacity: Opacidade da sobreposição (0-1).

        Returns:
            Imagem com a roupa sobreposta, ou None se falhar.
        """
        h, w, _ = person_image.shape
        person_rgb = cv2.cvtColor(person_image, cv2.COLOR_BGR2RGB)

        # Detectar pose
        results = self.pose.process(person_rgb)

        if not results.pose_landmarks:
            return None

        landmarks = results.pose_landmarks.landmark

        # Verificar landmarks mínimos (ombros são obrigatórios, resto é opcional)
        if landmarks[11].visibility < 0.2 or landmarks[12].visibility < 0.2:
            return None  # Precisa pelo menos dos ombros

        # Remover fundo da roupa
        garment_bgra = self._remove_background(garment_image)

        # Espelhar a roupa horizontalmente.
        # Imagens de e-commerce mostram a roupa "de frente" (como num cabide).
        # Quando sobreposta na foto da pessoa, fica invertida (frente nas costas).
        # O flip corrige isso.
        garment_bgra = cv2.flip(garment_bgra, 1)

        # Calcular região do corpo
        x, y, region_w, region_h, angle = self._get_body_region(
            landmarks, h, w, garment_type
        )

        if region_w < 10 or region_h < 10:
            return None

        # Pequeno padding vertical para naturalidade
        padding_y = int(region_h * 0.03)
        y = max(0, y - padding_y)
        region_h = min(h - y, region_h + padding_y * 2)

        # Rotacionar roupa se ombros não estão nivelados.
        # O sinal do ângulo já está corrigido em _get_body_region;
        # aplicamos diretamente (sem negar) para alinhar a roupa à inclinação real.
        if abs(angle) > 2:
            center = (garment_bgra.shape[1] // 2, garment_bgra.shape[0] // 2)
            matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            garment_bgra = cv2.warpAffine(
                garment_bgra,
                matrix,
                (garment_bgra.shape[1], garment_bgra.shape[0]),
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(0, 0, 0, 0),
            )

        # Ajustar opacidade
        if opacity < 1.0:
            garment_bgra[:, :, 3] = (
                garment_bgra[:, :, 3].astype(float) * opacity
            ).astype(np.uint8)

        # Sobrepor
        result = self._overlay_transparent(
            person_image, garment_bgra, x, y, region_w, region_h
        )

        return result

    async def try_on_from_url(
        self,
        person_image: np.ndarray,
        garment_url: str,
        garment_type: str = "camiseta",
        opacity: float = 0.85,
    ) -> Optional[np.ndarray]:
        """
        Try-on a partir de URL da roupa.

        Args:
            person_image: Foto do cliente (BGR).
            garment_url: URL da imagem da roupa no e-commerce.
            garment_type: Tipo da peça.
            opacity: Opacidade.

        Returns:
            Imagem com a roupa sobreposta.
        """
        garment_image = await self.fetch_garment_image(garment_url)
        if garment_image is None:
            return None

        return await self.try_on(person_image, garment_image, garment_type, opacity)
