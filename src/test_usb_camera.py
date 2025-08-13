#!/usr/bin/env python3
"""
Script de teste para câmeras USB comuns
"""

import cv2
import logging
import sys
import os

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_usb_cameras():
    """Testa câmeras USB disponíveis"""
    logging.info("=== TESTE DE CÂMERAS USB ===")
    logging.info("")
    
    found_cameras = []
    
    # Testar índices de 0 a 9
    for camera_index in range(10):
        logging.info(f"Testando câmera índice {camera_index}...")
        
        cap = cv2.VideoCapture(camera_index)
        
        if cap.isOpened():
            # Tentar capturar um frame
            ret, frame = cap.read()
            
            if ret and frame is not None:
                height, width = frame.shape[:2]
                
                # Obter propriedades da câmera
                fps = cap.get(cv2.CAP_PROP_FPS)
                backend = cap.getBackendName()
                
                camera_info = {
                    'index': camera_index,
                    'resolution': f"{width}x{height}",
                    'fps': fps,
                    'backend': backend,
                    'working': True
                }
                
                found_cameras.append(camera_info)
                
                logging.info(f"✅ CÂMERA ENCONTRADA:")
                logging.info(f"   - Índice: {camera_index}")
                logging.info(f"   - Resolução: {width}x{height}")
                logging.info(f"   - FPS: {fps}")
                logging.info(f"   - Backend: {backend}")
                
                # Testar diferentes resoluções
                test_resolutions = [(640, 480), (1280, 720), (1920, 1080)]
                logging.info("   - Resoluções suportadas:")
                
                for test_width, test_height in test_resolutions:
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, test_width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, test_height)
                    
                    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    
                    if actual_width == test_width and actual_height == test_height:
                        logging.info(f"     ✅ {test_width}x{test_height}")
                    else:
                        logging.info(f"     ❌ {test_width}x{test_height} (obtido: {actual_width}x{actual_height})")
                
                logging.info("")
            else:
                logging.info(f"❌ Câmera {camera_index} não consegue capturar frames")
            
            cap.release()
        else:
            logging.info(f"❌ Não foi possível abrir câmera {camera_index}")
    
    logging.info("=== RESUMO ===")
    if found_cameras:
        logging.info(f"✅ {len(found_cameras)} câmera(s) USB encontrada(s):")
        for cam in found_cameras:
            logging.info(f"   - Índice {cam['index']}: {cam['resolution']} @ {cam['fps']}fps ({cam['backend']})")
        
        # Testar a primeira câmera encontrada
        test_camera_capture(found_cameras[0]['index'])
    else:
        logging.warning("❌ Nenhuma câmera USB encontrada")
        logging.info("")
        logging.info("💡 POSSÍVEIS SOLUÇÕES:")
        logging.info("1. Verifique se a câmera está conectada")
        logging.info("2. Se estiver no WSL2, configure usbipd:")
        logging.info("   - No Windows: usbipd list")
        logging.info("   - No Windows: usbipd bind --busid X-Y")
        logging.info("   - No Windows: usbipd attach --wsl --busid X-Y")
        logging.info("3. Verifique permissões:")
        logging.info("   - sudo usermod -a -G video $USER")
        logging.info("   - Reinicie o terminal")

def test_camera_capture(camera_index):
    """Testa captura contínua de uma câmera específica"""
    logging.info(f"=== TESTE DE CAPTURA CONTÍNUA - CÂMERA {camera_index} ===")
    
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        logging.error(f"Não foi possível abrir câmera {camera_index}")
        return
    
    # Configurar resolução padrão
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    logging.info("Capturando frames... (pressione Ctrl+C para parar)")
    
    frame_count = 0
    try:
        while frame_count < 10:  # Capturar apenas 10 frames para teste
            ret, frame = cap.read()
            
            if ret and frame is not None:
                frame_count += 1
                height, width = frame.shape[:2]
                logging.info(f"Frame {frame_count}: {width}x{height}")
                
                # Opcional: salvar primeiro frame como teste
                if frame_count == 1:
                    test_image_path = "/tmp/test_camera_frame.jpg"
                    cv2.imwrite(test_image_path, frame)
                    logging.info(f"Primeiro frame salvo em: {test_image_path}")
            else:
                logging.warning("Falha ao capturar frame")
                break
                
    except KeyboardInterrupt:
        logging.info("Teste interrompido pelo usuário")
    
    cap.release()
    logging.info("✅ Teste de captura concluído")

def check_opencv_info():
    """Mostra informações do OpenCV"""
    logging.info("=== INFORMAÇÕES DO OPENCV ===")
    logging.info(f"Versão do OpenCV: {cv2.__version__}")
    
    # Verificar backends disponíveis
    backends = []
    backend_names = [
        ('CAP_V4L2', cv2.CAP_V4L2),
        ('CAP_GSTREAMER', cv2.CAP_GSTREAMER),
        ('CAP_FFMPEG', cv2.CAP_FFMPEG),
        ('CAP_DSHOW', cv2.CAP_DSHOW if hasattr(cv2, 'CAP_DSHOW') else None),
    ]
    
    logging.info("Backends disponíveis:")
    for name, backend_id in backend_names:
        if backend_id is not None:
            logging.info(f"  - {name}: ✅")
        else:
            logging.info(f"  - {name}: ❌")
    
    logging.info("")

def main():
    """Função principal"""
    logging.info("=== DIAGNÓSTICO COMPLETO DE CÂMERAS USB ===")
    logging.info("")
    
    check_opencv_info()
    test_usb_cameras()
    
    logging.info("")
    logging.info("=== TESTE CONCLUÍDO ===")
    logging.info("Para usar na aplicação principal:")
    logging.info("  ./scripts/dev.sh run")

if __name__ == "__main__":
    main()
