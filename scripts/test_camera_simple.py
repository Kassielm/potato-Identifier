#!/usr/bin/env python3
"""
Teste simples da câmera para debug
"""

import cv2
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_camera():
    """Teste básico da câmera"""
    logger.info("Iniciando teste da câmera...")
    
    # Verificar dispositivos de vídeo
    video_devices = []
    for i in range(10):
        device = f"/dev/video{i}"
        if os.path.exists(device):
            video_devices.append(device)
    
    logger.info(f"Dispositivos de vídeo encontrados: {video_devices}")
    
    # Testar câmeras
    for camera_index in range(4):
        logger.info(f"Testando câmera no índice {camera_index}...")
        
        cap = cv2.VideoCapture(camera_index)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                logger.info(f"✅ Câmera {camera_index} funcional - frame shape: {frame.shape}")
                
                # Criar janela e mostrar frame
                window_name = f"Camera Test {camera_index}"
                cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                cv2.resizeWindow(window_name, 640, 480)
                
                logger.info("Exibindo frame de teste...")
                cv2.imshow(window_name, frame)
                cv2.waitKey(5000)  # Mostrar por 5 segundos
                cv2.destroyAllWindows()
                
                cap.release()
                return True
            else:
                logger.warning(f"❌ Câmera {camera_index} não retornou frame válido")
                cap.release()
        else:
            logger.warning(f"❌ Não foi possível abrir câmera {camera_index}")
            cap.release()
    
    logger.error("Nenhuma câmera funcional encontrada")
    return False

if __name__ == "__main__":
    success = test_camera()
    if success:
        print("✅ Teste da câmera passou!")
    else:
        print("❌ Teste da câmera falhou!")
    exit(0 if success else 1)
