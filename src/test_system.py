#!/usr/bin/env python3
"""
Aplicação de detecção de objetos em tempo real usando TensorFlow Lite com NPU
Adaptado do exemplo Torizon para usar apenas OpenCV
Versão para Verdin iMX8MP
"""

import sys
import numpy as np
from time import time
import os
import cv2

# Import tflite runtime
try:
    import tflite_runtime.interpreter as tf
    USING_TFLITE_RUNTIME = True
    print("✅ Usando tflite_runtime")
except ImportError:
    import tensorflow as tf_full
    tf = tf_full.lite
    USING_TFLITE_RUNTIME = False
    print("⚠️ Usando tensorflow.lite como fallback")

# Configurações via variáveis de ambiente
USE_HW_ACCELERATED_INFERENCE = True
if os.environ.get("USE_HW_ACCELERATED_INFERENCE") == "0":
    USE_HW_ACCELERATED_INFERENCE = False

MINIMUM_SCORE = float(os.environ.get("MINIMUM_SCORE", default=0.55))
CAPTURE_DEVICE = os.environ.get("CAPTURE_DEVICE", default="/dev/video0")
CAPTURE_RESOLUTION_X = int(os.environ.get("CAPTURE_RESOLUTION_X", default=640))
CAPTURE_RESOLUTION_Y = int(os.environ.get("CAPTURE_RESOLUTION_Y", default=480))
CAPTURE_FRAMERATE = int(os.environ.get("CAPTURE_FRAMERATE", default=30))

print(f"🔧 Configurações:")
print(f"   NPU Ativada: {USE_HW_ACCELERATED_INFERENCE}")
print(f"   Score Mínimo: {MINIMUM_SCORE}")
print(f"   Dispositivo: {CAPTURE_DEVICE}")
print(f"   Resolução: {CAPTURE_RESOLUTION_X}x{CAPTURE_RESOLUTION_Y}")
print(f"   Framerate: {CAPTURE_FRAMERATE}")

def draw_bounding_boxes(img, labels, x1, x2, y1, y2, object_class, score):
    """Função auxiliar para desenhar bounding boxes"""
    # Cores para diferentes classes
    box_colors = [(254,153,143), (253,156,104), (253,157,13), (252,204,26),
                  (254,254,51), (178,215,50), (118,200,60), (30,71,87),
                  (1,48,178), (59,31,183), (109,1,142), (129,14,64)]

    text_colors = [(0,0,0), (0,0,0), (0,0,0), (0,0,0),
                   (0,0,0), (0,0,0), (0,0,0), (255,255,255),
                   (255,255,255), (255,255,255), (255,255,255), (255,255,255)]

    # Garantir que object_class seja válido
    if object_class >= len(labels):
        object_class = 0
    
    # Desenhar retângulo da detecção
    cv2.rectangle(img, (x1, y1), (x2, y2),
                  box_colors[object_class % len(box_colors)], 2)
    
    # Preparar texto com label e score
    label_text = f"{labels[object_class]} ({score:.2f})"
    text_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
    
    # Desenhar fundo do texto
    cv2.rectangle(img, (x1, y1 - text_size[1] - 5), (x1 + text_size[0], y1),
                  box_colors[object_class % len(box_colors)], -1)
    
    # Desenhar texto
    cv2.putText(img, label_text, (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                text_colors[object_class % len(text_colors)], 1, cv2.LINE_AA)

class ObjectDetector:
    def __init__(self):
        """Inicializar detector de objetos"""
        print("🚀 Inicializando detector de objetos...")
        
        # Caminhos dos arquivos
        self.model_path = self._find_model()
        self.labels_path = self._find_labels()
        
        # Carregar labels
        self.labels = self._load_labels()
        
        # Configurar delegate NPU
        self.delegates = self._setup_delegates()
        
        # Carregar modelo
        self.interpreter = self._load_model()
        
        # Obter detalhes de entrada e saída
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.input_size = self.input_details[0]['shape'][1]
        
        print(f"✅ Detector inicializado com input size: {self.input_size}")
        
    def _find_model(self):
        """Encontrar arquivo do modelo"""
        # Buscar modelo na estrutura de diretórios
        possible_paths = [
            "data/models/lite-model_ssd_mobilenet_v1_1_metadata_2.tflite",
            "../data/models/lite-model_ssd_mobilenet_v1_1_metadata_2.tflite",
            "lite-model_ssd_mobilenet_v1_1_metadata_2.tflite",
            "data/models/best_float32.tflite",
            "../data/models/best_float32.tflite",
            "best_float32.tflite"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"📁 Modelo encontrado em: {path}")
                return path
        
        raise FileNotFoundError("❌ Modelo não encontrado! Verifique os caminhos.")
    
    def _find_labels(self):
        """Encontrar arquivo de labels"""
        possible_paths = [
            "data/models/labelmap.txt",
            "../data/models/labelmap.txt", 
            "labelmap.txt",
            "data/models/labels.txt",
            "../data/models/labels.txt",
            "labels.txt"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"📁 Labels encontradas em: {path}")
                return path
        
        raise FileNotFoundError("❌ Arquivo de labels não encontrado!")
    
    def _load_labels(self):
        """Carregar labels do arquivo"""
        try:
            with open(self.labels_path, "r") as file:
                labels = file.read().splitlines()
            print(f"📋 Carregadas {len(labels)} classes: {labels}")
            return labels
        except Exception as e:
            print(f"❌ Erro ao carregar labels: {e}")
            return ["unknown"]
    
    def _setup_delegates(self):
        """Configurar delegates para NPU"""
        delegates = []
        
        if USE_HW_ACCELERATED_INFERENCE:
            try:
                # Tentar carregar VX Delegate (NPU)
                vx_delegate_path = "/usr/lib/libvx_delegate.so"
                if os.path.exists(vx_delegate_path):
                    print("🧠 Carregando VX Delegate (NPU)...")
                    delegates.append(tf.load_delegate(vx_delegate_path))
                    print("✅ VX Delegate carregado com sucesso!")
                else:
                    print(f"⚠️ VX Delegate não encontrado em {vx_delegate_path}")
                    
            except Exception as e:
                print(f"❌ Erro ao carregar delegate NPU: {e}")
                print("🔄 Continuando com CPU...")
        else:
            print("🔄 NPU desabilitada - usando CPU")
            
        return delegates
    
    def _load_model(self):
        """Carregar modelo TensorFlow Lite"""
        try:
            if self.delegates:
                print("🔄 Carregando modelo com delegate NPU...")
                interpreter = tf.Interpreter(
                    model_path=self.model_path,
                    experimental_delegates=self.delegates
                )
            else:
                print("🔄 Carregando modelo em CPU...")
                interpreter = tf.Interpreter(model_path=self.model_path)
            
            interpreter.allocate_tensors()
            print("✅ Modelo carregado com sucesso!")
            return interpreter
            
        except Exception as e:
            print(f"❌ Erro ao carregar modelo: {e}")
            # Fallback sem delegates
            if self.delegates:
                print("🔄 Tentando carregar sem delegates...")
                interpreter = tf.Interpreter(model_path=self.model_path)
                interpreter.allocate_tensors()
                print("✅ Modelo carregado em CPU como fallback!")
                return interpreter
            else:
                raise
    
    def preprocess_image(self, image_original):
        """Pré-processar imagem para inferência"""
        height1, width1 = image_original.shape[:2]
        
        # Redimensionar mantendo proporção
        image = cv2.resize(image_original,
                          (self.input_size, int(self.input_size * height1 / width1)),
                          interpolation=cv2.INTER_NEAREST)
        
        height2 = image.shape[0]
        scale = height1 / height2
        border_top = int((self.input_size - height2) / 2)
        
        # Adicionar padding
        image = cv2.copyMakeBorder(image,
                                  border_top,
                                  self.input_size - height2 - border_top,
                                  0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))
        
        # Converter para RGB e normalizar se necessário
        input_data = np.array([cv2.cvtColor(image, cv2.COLOR_BGR2RGB)], dtype=np.uint8)
        
        # Normalizar se modelo for float32
        if self.input_details[0]['dtype'] == np.float32:
            input_data = (np.float32(input_data) - 127.5) / 127.5
        
        return input_data, scale, border_top, width1
    
    def detect_objects(self, image_original):
        """Realizar detecção de objetos"""
        # Pré-processar imagem
        input_data, scale, border_top, width1 = self.preprocess_image(image_original)
        
        # Definir entrada
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        
        # Executar inferência
        start_time = time()
        self.interpreter.invoke()
        inference_time = time() - start_time
        
        # Verificar tipo de modelo (TF1 vs TF2)
        outname = self.output_details[0]['name']
        if 'StatefulPartitionedCall' in outname:  # TF2 model
            locations_idx, classes_idx, scores_idx, detections_idx = 1, 3, 0, 2
        else:  # TF1 model
            locations_idx, classes_idx, scores_idx, detections_idx = 0, 1, 2, 3
        
        # Obter resultados
        locations = (self.interpreter.get_tensor(self.output_details[locations_idx]['index'])[0] * width1).astype(int)
        locations[locations < 0] = 0
        locations[locations > width1] = width1
        
        classes = self.interpreter.get_tensor(self.output_details[classes_idx]['index'])[0].astype(int)
        scores = self.interpreter.get_tensor(self.output_details[scores_idx]['index'])[0]
        n_detections = self.interpreter.get_tensor(self.output_details[detections_idx]['index'])[0].astype(int)
        
        # Processar detecções
        detections = []
        for i in range(min(n_detections, len(scores))):
            if scores[i] > MINIMUM_SCORE:
                y1 = max(0, locations[i, 0] - int(border_top * scale))
                x1 = max(0, locations[i, 1])
                y2 = min(image_original.shape[0], locations[i, 2] - int(border_top * scale))
                x2 = min(image_original.shape[1], locations[i, 3])
                
                if x2 > x1 and y2 > y1:  # Validar bbox
                    detections.append({
                        'bbox': (x1, y1, x2, y2),
                        'class': classes[i],
                        'score': scores[i]
                    })
        
        return detections, inference_time

def main():
    """Função principal"""
    print("🚀 Iniciando aplicação de detecção em tempo real...")
    
    try:
        # Inicializar detector
        detector = ObjectDetector()
        
        # Configurar câmera
        print(f"📷 Configurando câmera: {CAPTURE_DEVICE}")
        
        # Tentar diferentes métodos de captura
        cap = None
        
        # Método 1: GStreamer pipeline (recomendado para iMX8MP)
        # try:
        #     gst_pipeline = (
        #         f'v4l2src device={CAPTURE_DEVICE} '
        #         f'! video/x-raw,width={CAPTURE_RESOLUTION_X},height={CAPTURE_RESOLUTION_Y},framerate={CAPTURE_FRAMERATE}/1 '
        #         f'! videoconvert '
        #         f'! video/x-raw,format=BGR '
        #         f'! appsink drop=1'
        #     )
        #     cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        #     if cap.isOpened():
        #         print("✅ Câmera configurada com GStreamer")
        #     else:
        #         cap = None
        # except Exception as e:
        #     print(f"⚠️ GStreamer falhou: {e}")
        
        # Método 2: V4L2 direto
        if cap is None:
            try:
                device_id = int(CAPTURE_DEVICE.replace('/dev/video2', ''))
                cap = cv2.VideoCapture(device_id)
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_RESOLUTION_X)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_RESOLUTION_Y)
                    cap.set(cv2.CAP_PROP_FPS, CAPTURE_FRAMERATE)
                    print("✅ Câmera configurada com V4L2")
                else:
                    cap = None
            except Exception as e:
                print(f"⚠️ V4L2 falhou: {e}")
        
        # Método 3: Fallback para câmera padrão
        if cap is None:
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                print("✅ Usando câmera padrão (fallback)")
            else:
                raise RuntimeError("❌ Não foi possível abrir nenhuma câmera!")
        
        # Verificar se está rodando com interface gráfica
        # headless = os.environ.get('HEADLESS', 'false').lower() == 'true'
        
        # if not headless:
        cv2.namedWindow('Detecção de Objetos', cv2.WINDOW_AUTOSIZE)
        print("🖥️ Janela OpenCV criada. Pressione 'q' para sair.")
        # else:
            # print("🖥️ Modo headless ativado - sem interface gráfica")
        
        # Loop principal
        frame_count = 0
        fps_counter = time()
        
        print("🔄 Iniciando loop de detecção...")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Falha ao capturar frame")
                break
            
            # Realizar detecção
            detections, inference_time = detector.detect_objects(frame)
            
            # Desenhar detecções
            for detection in detections:
                x1, y1, x2, y2 = detection['bbox']
                class_id = detection['class']
                score = detection['score']
                
                draw_bounding_boxes(frame, detector.labels, x1, x2, y1, y2, class_id, score)
            
            # Desenhar informações de performance
            cv2.rectangle(frame, (0, 0), (300, 60), (0, 0, 0), -1)
            cv2.putText(frame, f"Tempo de inferencia: {inference_time*1000:.1f}ms", 
                       (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, f"Deteccoes: {len(detections)}", 
                       (5, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Calcular FPS a cada 30 frames
            frame_count += 1
            if frame_count % 30 == 0:
                fps = 30 / (time() - fps_counter)
                fps_counter = time()
                print(f"📊 FPS: {fps:.1f}, Inferência: {inference_time*1000:.1f}ms, Detecções: {len(detections)}")
            
            # if not headless:
                # Mostrar frame
            cv2.imshow('Detecção de Objetos', frame)
            
            # Verificar teclas
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # 'q' ou ESC
                break
            # else:
            #     # Em modo headless, parar após alguns frames para teste
            #     if frame_count > 100:  # Rode por 100 frames e pare
            #         print("🔄 Modo headless - parando após 100 frames")
            #         break
    
    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Limpeza
        if 'cap' in locals() and cap is not None:
            cap.release()
        # if not headless:
        cv2.destroyAllWindows()
        print("🧹 Recursos liberados")

if __name__ == "__main__":
    main()
