import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
import os
import time

# --- CONFIGURAÇÕES ---
MODEL_PATH = "data/models/best_int8.tflite"
LABELS_PATH = "data/models/labels.txt"
CAMERA_INDEX = 0  # 0 para a primeira webcam conectada
INPUT_WIDTH = 320 # O mesmo 'imgsz' que você usou no treino e exportação
INPUT_HEIGHT = 320
CONFIDENCE_THRESHOLD = 0.5 # Limiar de confiança para mostrar uma detecção (0.0 a 1.0)

class ObjectDetector:
    def __init__(self, model_path, labels_path):
        """Inicializa o detector, carrega o modelo e o delegate da NPU."""
        print("Inicializando o detector de objetos...")

        # Carrega os nomes das classes (labels)
        with open(labels_path, 'r') as f:
            self.labels = [line.strip() for line in f.readlines()]
        print(f"Classes carregadas: {self.labels}")

        # Verifica e carrega o delegate da NPU (a chave para a aceleração)
        vx_delegate_path = '/usr/lib/libvx_delegate.so'
        if os.path.exists(vx_delegate_path):
            experimental_delegates = [tflite.load_delegate(vx_delegate_path)]
            print(">>> Delegate da NPU encontrado e carregado! A inferência será acelerada. <<<")
        else:
            experimental_delegates = None
            print("AVISO: Delegate da NPU não encontrado. Rodando na CPU (será mais lento).")

        # Carrega o modelo TFLite no interpretador, usando o delegate se disponível
        self.interpreter = tflite.Interpreter(
            model_path=model_path,
            experimental_delegates=experimental_delegates
        )
        self.interpreter.allocate_tensors()

        # Obtém detalhes da entrada e saída do modelo
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # Verifica se o tipo de entrada é INT8 (esperado para modelos quantizados)
        if self.input_details[0]['dtype'] == np.int8:
            print("Modelo INT8 detectado. A quantização está correta para a NPU.")
        else:
            print("AVISO: Modelo não parece ser INT8. A performance na NPU pode não ser a ideal.")

    def preprocess_frame(self, frame):
        """Redimensiona e prepara o frame da câmera para o modelo."""
        # A imagem de entrada para o modelo é [1, 320, 320, 3]
        image_resized = cv2.resize(frame, (INPUT_WIDTH, INPUT_HEIGHT))
        input_data = np.expand_dims(image_resized, axis=0)
        return input_data

    def detect(self, frame):
        """Executa a detecção de objetos em um único frame."""
        # O modelo YOLOv8 TFLite retorna uma única saída com formato [1, num_classes + 4, num_boxes]
        # Exemplo: [1, 5, 8400] se tiver 1 classe. Onde 4 são as coordenadas (cx, cy, w, h)
        # e o restante são as confianças das classes.

        input_data = self.preprocess_frame(frame)
        
        # Define o tensor de entrada e executa a inferência
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()

        # Obtém o resultado
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        
        # Transpõe a matriz de saída para [8400, 5] para facilitar o processamento
        output_data = output_data.T 

        boxes = []
        scores = []
        class_ids = []

        # Processa cada detecção potencial
        for detection in output_data:
            confidence = detection[4:].max() # A confiança é o maior score entre as classes
            if confidence > CONFIDENCE_THRESHOLD:
                class_id = detection[4:].argmax()
                
                # Converte as coordenadas do centro (cx,cy,w,h) para (x1,y1,x2,y2)
                cx, cy, w, h = detection[:4]
                x1 = int((cx - w / 2))
                y1 = int((cy - h / 2))
                x2 = int((cx + w / 2))
                y2 = int((cy + h / 2))

                boxes.append([x1, y1, x2, y2])
                scores.append(float(confidence))
                class_ids.append(int(class_id))
        
        # Aplica Supressão Não-Máxima (NMS) para remover caixas sobrepostas
        # A saída do YOLO já é boa, mas o NMS do OpenCV pode refinar
        frame_height, frame_width, _ = frame.shape
        scaled_boxes = self.scale_boxes(boxes, (frame_width, frame_height))

        indices = cv2.dnn.NMSBoxes(scaled_boxes, scores, CONFIDENCE_THRESHOLD, 0.4)
        
        final_detections = []
        if len(indices) > 0:
            for i in indices.flatten():
                final_detections.append({
                    "box": scaled_boxes[i],
                    "label": self.labels[class_ids[i]],
                    "confidence": scores[i]
                })

        return final_detections

    def scale_boxes(self, boxes, frame_shape):
        """Converte as coordenadas da caixa do tamanho da entrada do modelo para o tamanho original do frame."""
        frame_w, frame_h = frame_shape
        scale_x = frame_w / INPUT_WIDTH
        scale_y = frame_h / INPUT_HEIGHT
        
        scaled_boxes = []
        for box in boxes:
            x1, y1, x2, y2 = box
            scaled_boxes.append([int(x1 * scale_x), int(y1 * scale_y), int(x2 * scale_x), int(y2 * scale_y)])
        return scaled_boxes

    def draw_detections(self, frame, detections):
        """Desenha as caixas e labels no frame."""
        for det in detections:
            box = det['box']
            label = det['label']
            confidence = det['confidence']
            
            x1, y1, x2, y2 = box
            
            # Desenha a caixa
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Prepara o texto
            text = f"{label}: {confidence:.2f}"
            
            # Desenha o fundo do texto
            (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x1, y1 - text_height - 10), (x1 + text_width, y1), (0, 255, 0), -1)
            
            # Desenha o texto
            cv2.putText(frame, text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        return frame

def main():
    """Função principal para rodar o sistema de visão."""
    # Inicializa o detector
    detector = ObjectDetector(MODEL_PATH, LABELS_PATH)

    # Abre a câmera
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"Erro: Não foi possível abrir a câmera no índice {CAMERA_INDEX}.")
        return

    print("Câmera aberta. Pressione 'q' para sair.")

    while True:
        start_time = time.time() # Início da contagem de tempo
        
        # Captura o frame
        ret, frame = cap.read()
        if not ret:
            print("Erro ao capturar frame.")
            break

        # Detecta os objetos
        detections = detector.detect(frame)
        
        # Desenha as detecções no frame
        output_frame = detector.draw_detections(frame, detections)
        
        # Calcula e mostra o FPS
        end_time = time.time()
        fps = 1 / (end_time - start_time)
        cv2.putText(output_frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Mostra o resultado
        cv2.imshow("Detector de Objetos - Toradex iMX8MP", output_frame)

        # Verifica se 'q' foi pressionado para sair
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    # Libera os recursos
    cap.release()
    cv2.destroyAllWindows()
    print("Sistema encerrado.")

if __name__ == '__main__':
    main()