#!/usr/bin/env python3
"""
Teste com imagem simulada para demonstrar funcionamento da GUI
"""

import cv2
import numpy as np
import time

def create_test_image():
    """Cria uma imagem de teste"""
    # Criar imagem base
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Adicionar padrão de cores
    img[:160, :, 2] = 255  # Vermelho no topo
    img[160:320, :, 1] = 255  # Verde no meio
    img[320:, :, 0] = 255  # Azul embaixo
    
    # Adicionar texto
    cv2.putText(img, "POTATO IDENTIFIER TEST", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Adicionar timestamp
    timestamp = time.strftime("%H:%M:%S")
    cv2.putText(img, f"Time: {timestamp}", (50, 400), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Adicionar retângulo simulando detecção
    cv2.rectangle(img, (200, 150), (400, 350), (0, 255, 0), 3)
    cv2.putText(img, "POTATO: 0.95", (200, 140), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    
    return img

def test_opencv_display():
    """Testa display OpenCV com imagem simulada"""
    print("Iniciando teste de exibição OpenCV...")
    
    window_name = "Potato Identifier - Test"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 800, 600)
    
    print("Janela criada. Pressione 'q' ou ESC para sair...")
    
    frame_count = 0
    start_time = time.time()
    
    while True:
        # Criar frame de teste
        frame = create_test_image()
        
        # Adicionar contador de frames
        cv2.putText(frame, f"Frame: {frame_count}", (50, 450), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Exibir frame
        cv2.imshow(window_name, frame)
        
        # Verificar teclas
        key = cv2.waitKey(30) & 0xFF
        if key == ord('q') or key == 27:  # 'q' ou ESC
            break
        
        frame_count += 1
        
        # Limitar a 30 FPS
        time.sleep(1/30)
        
        # Parar após 10 segundos para teste automático
        if time.time() - start_time > 10:
            print("Teste automático finalizado após 10 segundos")
            break
    
    cv2.destroyAllWindows()
    print(f"Teste finalizado. Total de frames: {frame_count}")
    return True

if __name__ == "__main__":
    success = test_opencv_display()
    exit(0 if success else 1)
