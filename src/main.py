import cv2
import logging
import numpy as np
import os
import tflite_runtime.interpreter as tflite
# from plc import Plc # Supondo que seu arquivo plc.py está acessível

# --- Configuração do Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def detect_available_delegates():
    """
    Detecta delegates de aceleração disponíveis no sistema Verdin iMX8MP.
    
    Returns:
        tuple: (delegate_path, delegate_type) onde delegate_type pode ser:
               'imx_nn', 'ethos_u', 'vx_gpu', 'gpu_gl', 'cpu'
    """
    delegates_info = [
        ("/usr/lib/libvx_delegate.so", "vx_gpu", "VX GPU/VPU"),
        ("/usr/lib/aarch64-linux-gnu/libvx_delegate.so", "vx_gpu", "VX GPU/VPU (alt)"),
        ("/usr/lib/arm-linux-gnueabihf/libvx_delegate.so", "vx_gpu", "VX GPU/VPU (arm)"),
        # Delegates específicos (podem não estar presentes em todas as versões)
        ("/usr/lib/libimxnn_delegate.so", "imx_nn", "NPU específico iMX"),
        ("/usr/lib/libethosu_delegate.so", "ethos_u", "Ethos-U NPU"),
    ]
    
    for delegate_path, delegate_type, description in delegates_info:
        if os.path.exists(delegate_path):
            logger.info(f"Delegate encontrado: {description} em {delegate_path}")
            return delegate_path, delegate_type
    
    # Verificar se há bibliotecas GPU disponíveis para aceleração alternativa
    gpu_libs = [
        "/usr/lib/libGAL.so",
        "/usr/lib/aarch64-linux-gnu/libGAL.so", 
        "/usr/lib/libEGL.so",
        "/usr/lib/libGLESv2.so"
    ]
    
    gpu_available = False
    for lib in gpu_libs:
        if os.path.exists(lib):
            gpu_available = True
            logger.info(f"Biblioteca GPU encontrada: {lib}")
            break
    
    if gpu_available:
        logger.info("GPU disponível - TensorFlow Lite pode usar aceleração GPU interna")
        return None, "gpu_gl"
    
    logger.warning("Nenhum delegate ou GPU encontrados. Usando CPU.")
    return None, "cpu"

def supressao_nao_maxima(boxes, scores, iou_threshold):
    """Aplica Supressão Não-Máxima (NMS) para remover caixas sobrepostas."""
    if len(boxes) == 0:
        return []
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        intersection = w * h
        iou = intersection / (areas[i] + areas[order[1:]] - intersection)
        inds = np.where(iou <= iou_threshold)[0]
        order = order[inds + 1]
    return keep

class VisionSystem:
    def __init__(self, model_path: str, labels_path: str, delegate_path: str = None):
        """
        Inicializa o sistema de visão.

        Args:
            model_path (str): Caminho para o modelo .tflite.
            labels_path (str): Caminho para o arquivo de labels.
            delegate_path (str, optional): Caminho para a biblioteca do delegate da NPU.
        """
        # --- Configurações de Detecção ---
        self.CONFIDENCE_THRESHOLD = 0.5
        self.IOU_THRESHOLD = 0.45

        # --- Configurações do Sistema ---
        self.CAMERA_INDEX = 2
        self.colors = {'OK': (0, 255, 0), 'NOK': (0, 0, 255), 'PEDRA': (255, 0, 0)}
        self.class_priority = {'PEDRA': 3, 'NOK': 2, 'OK': 1}
        self.class_values = {'OK': 0, 'NOK': 1, 'PEDRA': 2}
        self.window_name = 'Vision System'
        # self.plc = Plc()
        self.camera = None # Agora será um objeto cv2.VideoCapture

        # --- Inicialização do Modelo TFLite ---
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.input_height = 0
        self.input_width = 0
        self.labels = []
        self._initialize_model(model_path, labels_path, delegate_path)

    def _initialize_model(self, model_path, labels_path, delegate_path):
        """Carrega o modelo TFLite, os metadados e o delegate da NPU."""
        try:
            # Carrega os nomes das classes (labels)
            with open(labels_path, 'r') as f:
                self.labels = [line.strip() for line in f.readlines()]

            # Carrega o delegate da NPU, se o caminho for fornecido
            experimental_delegates = []
            delegate_loaded = False
            if delegate_path:
                try:
                    # Tentar carregar o delegate
                    delegate = tflite.load_delegate(delegate_path)
                    experimental_delegates.append(delegate)
                    
                    # Verificar se é um delegate VX/GPU/NPU específico
                    if "libethosu_delegate.so" in delegate_path:
                        logger.info(f"✅ Delegate Ethos-U NPU carregado: '{delegate_path}'")
                        delegate_loaded = True
                    elif "libvx_delegate.so" in delegate_path:
                        logger.info(f"✅ Delegate VX GPU/VPU carregado: '{delegate_path}'")
                        delegate_loaded = True
                    elif "libimxnn_delegate.so" in delegate_path:
                        logger.info(f"✅ Delegate iMX NN NPU carregado: '{delegate_path}'")
                        delegate_loaded = True
                    else:
                        logger.info(f"✅ Delegate carregado: '{delegate_path}'")
                        delegate_loaded = True
                        
                except Exception as e:
                    logger.error(f"❌ Erro ao carregar delegate '{delegate_path}': {e}")
                    logger.warning("⚠️  Tentando carregar o modelo sem delegate...")
                    experimental_delegates = []  # Limpar delegates com erro
            
            if not delegate_loaded and delegate_path:
                logger.warning("⚠️  Nenhum delegate pôde ser carregado. Usando CPU.")
            elif not delegate_path:
                logger.info("🖥️  Executando modelo na CPU (sem aceleração de hardware).")
            
            # Tentar usar GPU interna do TensorFlow Lite se disponível
            use_gpu = False
            if not delegate_loaded:
                try:
                    # Verifica se há suporte a GPU no TensorFlow Lite
                    import tflite_runtime.interpreter as tflite_gpu
                    if hasattr(tflite_gpu, 'experimental') and hasattr(tflite_gpu.experimental, 'get_gpu_delegates'):
                        gpu_delegates = tflite_gpu.experimental.get_gpu_delegates()
                        if gpu_delegates:
                            experimental_delegates.extend(gpu_delegates)
                            logger.info("🚀 Usando delegate GPU interno do TensorFlow Lite")
                            use_gpu = True
                except Exception as gpu_e:
                    logger.debug(f"GPU interna não disponível: {gpu_e}")
                    pass
            
            # Carrega o interpretador TFLite com o delegate (se houver)
            self.interpreter = tflite.Interpreter(
                model_path=model_path,
                experimental_delegates=experimental_delegates
            )
            self.interpreter.allocate_tensors()

            # Obtém detalhes de entrada e saída
            self.input_details = self.interpreter.get_input_details()[0]
            self.output_details = self.interpreter.get_output_details()[0]
            
            # Obtém o tamanho de entrada esperado pelo modelo (ex: 640x640)
            self.input_height = self.input_details['shape'][1]
            self.input_width = self.input_details['shape'][2]
            
            logger.info(f"📋 Modelo TFLite carregado: '{model_path}'")
            logger.info(f"📐 Tamanho de entrada: {self.input_width}x{self.input_height}")
            logger.info(f"🔧 Tipo de entrada: {self.input_details['dtype']}")
            logger.info(f"🎯 Classes disponíveis: {len(self.labels)}")
            
            # Teste rápido de inferência para verificar se o delegate está funcionando
            # self._test_inference_speed()

        except Exception as e:
            logger.error(f"Erro fatal ao inicializar o modelo TFLite: {e}")
            self.interpreter = None # Garante que o sistema não continue se o modelo falhar

    # def _test_inference_speed(self):
    #     """Testa a velocidade de inferência para verificar se o delegate está funcionando."""
    #     try:
    #         import time
    #         # Cria uma entrada de teste
    #         if self.input_details['dtype'] == np.uint8:
    #             test_input = np.random.randint(0, 255, 
    #                 (1, self.input_height, self.input_width, 3), dtype=np.uint8)
    #         else:
    #             test_input = np.random.random(
    #                 (1, self.input_height, self.input_width, 3)).astype(np.float32)
            
    #         # Executa algumas inferências de teste
    #         times = []
    #         for _ in range(3):
    #             start_time = time.time()
    #             self.interpreter.set_tensor(self.input_details['index'], test_input)
    #             self.interpreter.invoke()
    #             end_time = time.time()
    #             times.append((end_time - start_time) * 1000)  # em ms
            
    #         avg_time = np.mean(times)
    #         logger.info(f"⚡ Tempo médio de inferência: {avg_time:.1f}ms")
            
    #         if avg_time < 50:
    #             logger.info("🚀 Performance excelente - delegate de hardware funcionando!")
    #         elif avg_time < 100:
    #             logger.info("✅ Performance boa - possível aceleração de hardware")
    #         else:
    #             logger.warning("🐌 Performance lenta - verificar se delegate está funcionando")
                
    #     except Exception as e:
    #         logger.warning(f"Não foi possível testar performance: {e}")

    def init_camera(self) -> bool:
        """Inicializa a câmera USB usando OpenCV."""
        try:
            self.camera = cv2.VideoCapture(self.CAMERA_INDEX)
            if not self.camera.isOpened():
                raise IOError(f"Não foi possível abrir a câmera no índice {self.CAMERA_INDEX}")

            logger.info(f"Câmera no índice {self.CAMERA_INDEX} aberta com sucesso.")
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar camera: {e}")
            logger.error("Verifique a conexão da câmera e as permissões do dispositivo.")
            self.camera = None
            return False

    def process_frame(self) -> None:
        """Captura, processa o frame, exibe os resultados e escreve no PLC."""
        if not self.interpreter:
            logger.error("Modelo não inicializado. Saindo do processamento.")
            return
            
        # if not self.plc.init_plc():
        #     logger.error("Falha ao inicializar o PLC")

        while self.camera.isOpened():
            try:
                ret, frame_original = self.camera.read()
                if not ret:
                    logger.warning('Falha ao capturar frame. Fim do stream?')
                    break
                
                frame_h, frame_w, _ = frame_original.shape

                # --- 1. Pré-processamento do Frame ---
                img_resized = cv2.resize(frame_original, (self.input_width, self.input_height))
                input_data = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
                
                # Normaliza e expande a dimensão de acordo com o tipo de dado do modelo
                if self.input_details['dtype'] == np.uint8: # Para modelos quantizados (INT8)
                    input_data = np.expand_dims(input_data, axis=0)
                else: # Para modelos float
                    input_data = np.expand_dims(input_data, axis=0).astype(np.float32) / 255.0

                # --- 2. Executar Inferência ---
                self.interpreter.set_tensor(self.input_details['index'], input_data)
                self.interpreter.invoke()
                output = self.interpreter.get_tensor(self.output_details['index'])
                output_transposed = output.transpose(0, 2, 1)[0]

                # --- 3. Pós-processamento ---
                boxes, scores, class_ids = [], [], []
                for row in output_transposed:
                    confidence = np.max(row[4:])
                    if confidence > self.CONFIDENCE_THRESHOLD:
                        class_id = np.argmax(row[4:])
                        scores.append(confidence)
                        class_ids.append(class_id)
                        
                        cx, cy, w, h = row[:4]
                        x1 = int((cx - w / 2) * frame_w)
                        y1 = int((cy - h / 2) * frame_h)
                        x2 = int((cx + w / 2) * frame_w)
                        y2 = int((cy + h / 2) * frame_h)
                        boxes.append([x1, y1, x2, y2])
                
                # --- 4. Aplicar NMS ---
                indices_finais = supressao_nao_maxima(np.array(boxes), np.array(scores), self.IOU_THRESHOLD)

                # --- 5. Processar e Desenhar Resultados Finais ---
                highest_priority_class = None
                highest_priority = 0
                frame_desenhado = frame_original.copy()

                for i in indices_finais:
                    box = boxes[i]
                    x1, y1, x2, y2 = box
                    label = self.labels[class_ids[i]]
                    score = scores[i]
                    color = self.colors.get(label, (255, 255, 255))
                    
                    cv2.rectangle(frame_desenhado, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame_desenhado, f'{label}: {score:.2f}', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                    priority = self.class_priority.get(label, 0)
                    if priority > highest_priority:
                        highest_priority = priority
                        highest_priority_class = label

                # Escreve a classe de maior prioridade no PLC
                # if highest_priority_class:
                #     try:
                #         plc_data = self.class_values[highest_priority_class]
                #         self.plc.write_db(plc_data)
                #         logger.info(f"Escreveu a classe {highest_priority_class} (valor {plc_data}) para o PLC")
                #     except Exception as e:
                #         logger.error(f"Falha ao escrever no PLC: {e}")

                # Exibe o frame final
                cv2.imshow(self.window_name, frame_desenhado)
                cv2.moveWindow(self.window_name, 0, 0)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            except Exception as e:
                logger.error(f"Erro no loop de processamento: {e}")
                continue

    def cleanup(self) -> None:
        """Libera os recursos da câmera, PLC e OpenCV."""
        try:
            if self.camera and self.camera.isOpened():
                self.camera.release()
                logger.info("Câmera liberada com sucesso.")
            cv2.destroyAllWindows()
            logger.info("Recursos de janela liberados com sucesso")
        except Exception as e:
            logger.error(f"Erro durante a limpeza: {e}")

    def __enter__(self):
        self.init_camera()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

def main():
    """Função principal para rodar o sistema de visão."""
    
    # Detecta automaticamente o melhor delegate disponível
    delegate_path, delegate_type = detect_available_delegates()
    
    if delegate_type == "cpu":
        logger.info("🖥️  Usando processamento em CPU")
    elif delegate_type == "gpu_gl":
        logger.info("🎮 GPU disponível - TensorFlow Lite pode usar aceleração interna")
    else:
        logger.info(f"🚀 Usando aceleração de hardware: {delegate_type}")

    with VisionSystem(
        model_path='data/models/best_int8.tflite',
        labels_path='data/models/labels.txt',
        delegate_path=delegate_path
    ) as vision_system:
        if vision_system.camera and vision_system.camera.isOpened():
            vision_system.process_frame()
        else:
            print("Saindo do programa pois a câmera não pôde ser inicializada.")

if __name__ == "__main__":
    main()