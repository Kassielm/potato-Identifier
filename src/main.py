import cv2
import logging
import numpy as np
import os
import time
import threading

# Detectar se está rodando em ambiente headless
HEADLESS_MODE = os.environ.get('HEADLESS', 'false').lower() == 'true'

# Configuração do modo headless
wayland_display = os.getenv('WAYLAND_DISPLAY', '')
x11_display = os.getenv('DISPLAY', '')
gui_available_env = os.getenv('GUI_AVAILABLE', '1')
headless_env = os.getenv('HEADLESS', '0')

# Detectar se há interface gráfica disponível
# Priorizar variável de ambiente explícita, depois verificar displays disponíveis
HEADLESS_MODE = (
    headless_env == '1' or
    (gui_available_env == '0') or
    (not wayland_display and not x11_display and gui_available_env != '1')
)

GUI_AVAILABLE = gui_available_env == '1' and not HEADLESS_MODE

print(f"🖥️  Display status:")
print(f"   WAYLAND_DISPLAY: '{wayland_display}'")
print(f"   DISPLAY: '{x11_display}'")
print(f"   HEADLESS_MODE: {HEADLESS_MODE}")
print(f"   GUI_AVAILABLE: {GUI_AVAILABLE}")

NPU_AVAILABLE = os.getenv('NPU_AVAILABLE', '0') == '1'
DISABLE_DELEGATES = os.getenv('DISABLE_DELEGATES', '0') == '1'

print(f"🧠 NPU_AVAILABLE: {NPU_AVAILABLE}")
print(f"🚫 DISABLE_DELEGATES: {DISABLE_DELEGATES}")

# Tenta importar tflite_runtime primeiro, depois tensorflow.lite como fallback
try:
    import tflite_runtime.interpreter as tflite
    USING_TFLITE_RUNTIME = True
except ImportError:
    import tensorflow as tf_full
    tflite = tf_full.lite
    USING_TFLITE_RUNTIME = False

from plc import Plc

# --- Lógica de Caminhos Absolutos ---
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)

# --- Configuração do Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    def __init__(self, root=None):
        self.root = root
        # Para OpenCV puro, não depender do parâmetro root para determinar GUI
        self.headless = HEADLESS_MODE
        self.use_opencv_gui = not self.headless and GUI_AVAILABLE
        
        # Variáveis para OpenCV GUI
        self.window_name = "Conecsa - Vision System"
        self.should_quit = False

        logger.info("Iniciando a inicialização do VisionSystem...")
        logger.info(f"Modo headless: {self.headless}")
        logger.info(f"Usar OpenCV GUI: {self.use_opencv_gui}")
        logger.info(f"GUI disponível: {GUI_AVAILABLE}")

        # --- Configurações de Detecção ---
        self.CONFIDENCE_THRESHOLD = 0.5
        self.IOU_THRESHOLD = 0.45
        self.CAMERA_INDEX = 2
        
        # --- Configurações do Sistema ---
        self.colors = {'OK': (0, 255, 0), 'NOK': (0, 0, 255), 'PEDRA': (255, 0, 0)}
        self.class_priority = {'PEDRA': 3, 'NOK': 2, 'OK': 1}
        self.class_values = {'OK': 0, 'NOK': 1, 'PEDRA': 2}
        
        # Inicializar recursos
        self.camera = None
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.input_height = 0
        self.input_width = 0
        self.labels = []
        
        # --- Inicializar PLC com resiliência ---
        try:
            self.plc = Plc()
            logger.info("✅ PLC inicializado")
        except Exception as e:
            logger.warning(f"Erro ao inicializar PLC - aplicação continuará sem PLC: {e}")
            self.plc = None

        # --- Inicializar Modelo ---
        self._initialize_model()

    def _test_delegate_safety(self):
        """Testa se o delegate VX é seguro para usar"""
        try:
            logger.info("🧪 Testando segurança do delegate VX...")
            
            # Criar um modelo dummy para testar
            import tempfile
            import struct
            
            # Criar um modelo TFLite minimal válido para teste
            with tempfile.NamedTemporaryFile(suffix='.tflite', delete=False) as temp_model:
                # Este é um modelo TFLite minimal válido (apenas para teste)
                minimal_model = bytes([0x54, 0x46, 0x4C, 0x33])  # Header TFL3
                temp_model.write(minimal_model)
                temp_model_path = temp_model.name
            
            try:
                # Tentar carregar delegate
                delegate = tflite.load_delegate('libvx_delegate.so')
                logger.info("✅ Delegate VX carregado para teste")
                
                # Cleanup
                os.unlink(temp_model_path)
                return True
                
            except Exception as e:
                logger.warning(f"⚠️ Delegate VX falhou no teste: {e}")
                os.unlink(temp_model_path)
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Erro no teste de segurança: {e}")
            return False
        
    def _initialize_model(self):
        """Inicializar modelo TensorFlow Lite"""
        logger.info("🧠 Carregando modelo TensorFlow Lite...")
        
        # Caminhos dos modelos
        
        int8_model_path = os.path.join(base_dir, 'data', 'models', 'lite-model_ssd_mobilenet_v1_1_metadata_2.tflite')
        edgetpu_model_path = os.path.join(base_dir, 'data', 'models', 'best_float32_edgetpu.tflite')
        fallback_model = os.path.join(base_dir, 'data', 'models', 'best_float32.tflite')
        label_path = os.path.join(base_dir, 'data', 'models', 'labelmap.txt')

        # Definir qual modelo usar - priorizar INT8 para performance
        if NPU_AVAILABLE and os.path.exists(int8_model_path):
            primary_model = int8_model_path
            logger.info("🧠 NPU disponível - usando modelo INT8 quantizado")
        elif os.path.exists(int8_model_path):
            primary_model = int8_model_path
            logger.info("📊 Modelo INT8 quantizado encontrado - melhor performance")
        elif os.path.exists(fallback_model):
            primary_model = fallback_model
            logger.info("💻 Modelo float32 encontrado")
        elif os.path.exists(edgetpu_model_path):
            primary_model = edgetpu_model_path
            logger.info("🔸 Modelo EdgeTPU encontrado")
        else:
            logger.error("❌ Nenhum modelo encontrado!")
            raise FileNotFoundError("Nenhum modelo válido encontrado")

        try:
            # Estratégia simplificada: testar disponibilidade do delegate primeiro
            use_delegate = False
            
            if NPU_AVAILABLE and not DISABLE_DELEGATES:
                logger.info("🚀 Verificando disponibilidade do delegate VX...")
                
                # Primeiro, verificar se conseguimos importar o delegate sem erro
                try:
                    # Teste mais simples e seguro
                    import ctypes
                    
                    # Tentar carregar a biblioteca diretamente
                    lib_path = 'libvx_delegate.so'
                    lib = ctypes.CDLL(lib_path)
                    logger.info("✅ Biblioteca VX delegate encontrada e carregável")
                    
                    # Se chegou até aqui, tentar usar o delegate
                    logger.info("🔧 Carregando modelo com delegate VX...")
                    delegate = tflite.load_delegate(lib_path)
                    self.interpreter = tflite.Interpreter(
                        model_path=primary_model,
                        experimental_delegates=[delegate]
                    )
                    use_delegate = True
                    logger.info("✅ Modelo configurado com delegate VX")
                    
                except Exception as delegate_error:
                    logger.warning(f"⚠️ Delegate VX não disponível: {delegate_error}")
                    use_delegate = False
            elif DISABLE_DELEGATES:
                logger.info("🚫 Delegates desabilitados via DISABLE_DELEGATES=1")
            
            # Se delegate não funcionou ou NPU não disponível, usar CPU
            if not use_delegate:
                logger.info("� Carregando modelo na CPU...")
                self.interpreter = tflite.Interpreter(model_path=primary_model)
            
            # Alocar tensors (para ambos os casos)
            logger.info("🧠 Alocando tensors...")
            self.interpreter.allocate_tensors()
            
            if use_delegate:
                logger.info("✅ Modelo carregado com sucesso usando delegate VX")
            else:
                logger.info("✅ Modelo carregado com sucesso na CPU")
                
        except Exception as e:
            logger.error(f"❌ Erro crítico ao carregar modelo: {e}")
            raise e

        # Obter detalhes do modelo
        self.input_details = self.interpreter.get_input_details()[0]
        self.output_details = self.interpreter.get_output_details()[0]
        self.input_height = self.input_details['shape'][1]
        self.input_width = self.input_details['shape'][2]
        
        logger.info(f"Tamanho de entrada do modelo: {self.input_width}x{self.input_height}")

        # Carregar labels
        if os.path.exists(label_path):
            with open(label_path, 'r') as f:
                self.labels = [line.strip() for line in f.readlines()]
            logger.info(f"Labels carregadas: {self.labels}")
        else:
            logger.warning("Arquivo de labels não encontrado, usando labels padrão")
            self.labels = ['OK', 'NOK', 'PEDRA']

    def init_camera(self) -> bool:
        """Inicializar câmera USB usando OpenCV."""
        logger.info("📷 Inicializando câmera...")
        
        # Lista de índices de câmera para tentar
        camera_indices = [2, 0, 1, 3, 4]
        
        for camera_index in camera_indices:
            try:
                logger.info(f"Testando câmera no índice {camera_index}...")
                cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
                
                if cap.isOpened():
                    # Configurar resolução e formato
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    # Tentar configurar formato MJPEG
                    try:
                        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
                    except:
                        logger.info("MJPEG não suportado, usando formato padrão")
                    
                    # Testar captura
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        logger.info(f"✅ Câmera USB inicializada no índice {camera_index}")
                        logger.info(f"Resolução: {frame.shape[1]}x{frame.shape[0]}")
                        self.camera = cap
                        self.CAMERA_INDEX = camera_index
                        
                        # Configurar janela se GUI disponível
                        if self.use_opencv_gui:
                            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
                            
                            # Verificar modo de exibição da janela
                            fullscreen_mode = os.getenv('FULLSCREEN_MODE', '1') == '1'
                            
                            if fullscreen_mode:
                                # Modo tela cheia
                                cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                                logger.info("🖥️  Janela configurada para TELA CHEIA")
                            else:
                                # Modo janela centralizada
                                cv2.resizeWindow(self.window_name, 1024, 768)
                                cv2.moveWindow(self.window_name, 100, 50)
                                logger.info("🖥️  Janela configurada para modo CENTRALIZADO (1024x768)")
                        
                        return True
                    else:
                        cap.release()
                        logger.warning(f"Câmera {camera_index} não conseguiu capturar frame")
                else:
                    logger.warning(f"Não foi possível abrir câmera no índice {camera_index}")
                    
            except Exception as e:
                logger.warning(f"Erro ao testar câmera {camera_index}: {e}")
                continue
        
        logger.error("❌ Nenhuma câmera USB funcional encontrada")
        return False

    def process_frame(self) -> None:
        """Loop principal de processamento com lógica robusta de PLC."""
        if not self.interpreter:
            logger.error("Modelo não inicializado. Saindo do processamento.")
            return
            
        # Tentar conectar ao PLC se disponível
        # if self.plc:
        #     plc_status = self.plc.init_plc()
        #     if plc_status:
        #         logger.info("Sistema iniciado com câmera e PLC")
        #     else:
        #         logger.warning("Sistema iniciado apenas com câmera - PLC indisponível")

        logger.info("Iniciando loop da câmera...")
        
        while self.camera and self.camera.isOpened() and not self.should_quit:
            try:
                ret, frame_original = self.camera.read()
                if not ret:
                    logger.warning('Falha ao capturar frame. Tentando novamente...')
                    continue
                
                frame_h, frame_w, _ = frame_original.shape
                frame_desenhado = frame_original.copy()

                # --- 1. Pré-processamento do Frame ---
                img_resized = cv2.resize(frame_original, (self.input_width, self.input_height))
                input_data = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
                
                # Normalizar dependendo do tipo do modelo
                if self.input_details['dtype'] == np.uint8:  # Para modelos quantizados (INT8)
                    input_data = np.expand_dims(input_data, axis=0)
                else:  # Para modelos float
                    input_data = np.expand_dims(input_data, axis=0).astype(np.float32) / 255.0

                # --- 2. Executar Inferência ---
                start_time = time.time()
                self.interpreter.set_tensor(self.input_details['index'], input_data)
                self.interpreter.invoke()
                inference_time = time.time() - start_time
                
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

                # --- 5. Processar e Desenhar Resultados ---
                highest_priority_class = None
                highest_priority = 0
                detections_count = len(indices_finais)

                for i in indices_finais:
                    box = boxes[i]
                    x1, y1, x2, y2 = box
                    label = self.labels[class_ids[i]] if class_ids[i] < len(self.labels) else f'Class_{class_ids[i]}'
                    score = scores[i]
                    color = self.colors.get(label, (255, 255, 255))
                    
                    cv2.rectangle(frame_desenhado, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame_desenhado, f'{label}: {score:.2f}', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                    priority = self.class_priority.get(label, 0)
                    if priority > highest_priority:
                        highest_priority = priority
                        highest_priority_class = label

                # Adicionar informações de performance
                perf_text = f"Inference: {inference_time*1000:.1f}ms | Detections: {detections_count}"
                cv2.putText(frame_desenhado, perf_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                # --- 6. Enviar para PLC com resiliência ---
                # if self.plc:
                #     if highest_priority_class:
                #         # Há detecção - enviar valor da classe detectada
                #         plc_data = self.class_values[highest_priority_class]
                #         success = self.plc.write_db(plc_data)
                #         if success:
                #             logger.debug(f"✅ Enviado para PLC: {highest_priority_class} ({plc_data})")
                #         else:
                #             logger.debug(f"⚠️ PLC indisponível - valor não enviado: {highest_priority_class} ({plc_data})")
                #     else:
                #         # Não há detecção - enviar "OK" (0)
                #         plc_data = self.class_values['OK']  # 0
                #         success = self.plc.write_db(plc_data)
                #         if success:
                #             logger.debug(f"✅ Enviado para PLC: OK (sem detecções) ({plc_data})")
                #         else:
                #             logger.debug(f"⚠️ PLC indisponível - valor OK não enviado ({plc_data})")
                # else:
                #     # PLC não disponível
                #     if highest_priority_class:
                #         plc_data = self.class_values[highest_priority_class]
                #         logger.debug(f"⚠️ PLC não inicializado - valor não enviado: {highest_priority_class} ({plc_data})")
                #     else:
                #         logger.debug(f"⚠️ PLC não inicializado - valor OK não enviado")

                # --- 7. Exibir Frame ---
                if self.use_opencv_gui and not self.headless:
                    cv2.imshow(self.window_name, frame_desenhado)
                    cv2.moveWindow(self.window_name, 0, 0)
                    
                    # Verificar se usuário quer sair
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q') or key == 27:  # 'q' ou ESC
                        logger.info("Usuário solicitou fechamento da aplicação")
                        self.should_quit = True
                        break
                # else:
                #     # Modo headless - pausa pequena para não sobrecarregar CPU
                #     # time.sleep(0.01)

            except Exception as e:
                logger.error(f"Erro no loop de processamento: {e}")
                continue

        logger.info("Loop da câmera finalizado")

    def start(self):
        """Iniciar aplicação"""
        logger.info("🚀 Iniciando aplicação...")
        
        if self.init_camera():
            logger.info("✅ Câmera inicializada com sucesso")
            
            # Iniciar loop principal
            self.process_frame()
            
        else:
            logger.error("Não foi possível iniciar a câmera. Encerrando.")
        
        # Cleanup final
        self.cleanup()

    def cleanup(self) -> None:
        """Libera os recursos da câmera, PLC e OpenCV com resiliência."""
        logger.info("🧹 Limpando recursos...")
        self.should_quit = True
        
        try:
            if self.camera and self.camera.isOpened():
                self.camera.release()
                logger.info("Câmera liberada com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao fechar câmera: {e}")
        
        # try:
        #     if hasattr(self, 'plc') and self.plc:
        #         self.plc.disconnect()
        #         logger.info("Conexão PLC encerrada.")
        # except Exception as e:
        #     logger.error(f"Erro ao desconectar PLC: {e}")
        
        try:
            cv2.destroyAllWindows()
            logger.info("Recursos de janela liberados com sucesso")
        except Exception as e:
            logger.error(f"Erro durante a limpeza de janelas: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

def main():
    """Função principal para rodar o sistema de visão."""
    logger.info("========================================")
    logger.info("      Iniciando Aplicação Potato ID     ")
    logger.info("========================================")
    
    try:
        if HEADLESS_MODE:
            logger.info("Modo HEADLESS detectado - iniciando sem interface gráfica")
        else:
            logger.info("Modo GUI detectado - iniciando com OpenCV GUI")
            
        with VisionSystem() as vision_system:
            vision_system.start()
            
    except Exception as e:
        logger.critical(f"Erro fatal na execução principal: {e}", exc_info=True)
    finally:
        logger.info("Aplicação finalizada.")

if __name__ == "__main__":
    main()