"""
Utilitários de imagem.
Corrige orientação EXIF de fotos de celular antes de processar.
"""

import cv2
import numpy as np
from PIL import Image
from io import BytesIO


def fix_orientation(image_bytes: bytes) -> np.ndarray:
    """
    Lê imagem corrigindo a orientação EXIF.

    Fotos de celular têm metadados EXIF que indicam rotação
    (90°, 180°, 270°). O OpenCV ignora esses metadados e lê
    a imagem "crua", resultando em fotos de ponta cabeça ou
    rotacionadas. O Pillow respeita o EXIF automaticamente.

    Args:
        image_bytes: Bytes da imagem (JPEG/PNG/WebP).

    Returns:
        Imagem BGR (numpy array) com orientação correta.
    """
    # Pillow aplica EXIF orientation automaticamente
    pil_image = Image.open(BytesIO(image_bytes))

    # Aplicar rotação EXIF
    from PIL import ImageOps
    pil_image = ImageOps.exif_transpose(pil_image)

    # Converter para RGB (Pillow usa RGB, OpenCV usa BGR)
    if pil_image.mode == "RGBA":
        # Manter alpha para imagens de roupa com transparência
        arr = np.array(pil_image)
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGRA)
    elif pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")

    arr = np.array(pil_image)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
