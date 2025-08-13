import os
import cv2
import logging
import time
import numpy as np

# Detectar se está rodando em ambiente headless
HEADLESS_MODE = os.environ.get('HEADLESS', 'false').lower() == 'true'

# Tentar importar PyPylon (opcional para câmeras Basler)
try:
    from pypylon import pylon
    PYLON_AVAILABLE = True
    logging.info("PyPylon disponível para câmeras Basler")
except ImportError:
    PYLON_AVAILABLE = False
    logging.info("PyPylon não disponível - usando apenas câmeras USB/OpenCV")

# Tenta importar tflite_runtime primeiro, depois tensorflow.lite como fallback
try:
    import tflite_runtime.interpreter as tf
    USING_TFLITE_RUNTIME = True
except ImportError:
    import tensorflow as tf_full
    tf = tf_full.lite
    USING_TFLITE_RUNTIME = False
from plc import Plc

import cv2
import numpy as np
import logging
import time
import os

# Configuração do modo headless
HEADLESS_MODE = os.getenv('HEADLESS', '0') == '1' or os.getenv('DISPLAY') is None

# Importações condicionais para GUI
if not HEADLESS_MODE:
    try:
        import tkinter as tk
        from PIL import Image, ImageTk
    except ImportError as e:
        print(f"Aviso: Bibliotecas GUI não disponíveis: {e}")
        print("Executando em modo headless...")
        HEADLESS_MODE = True

# --- Lógica de Caminhos Absolutos ---
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)

# --- Configuração do Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VisionSystem:
    def __init__(self, root=None):
        self.root = root
        self.headless = HEADLESS_MODE or root is None
        
        if not self.headless:
            self.root.title("Vision System")
            # Cria um Canvas no Tkinter para exibir o vídeo
            self.canvas = tk.Canvas(root, width=640, height=480)
            self.canvas.pack()

        logger.info("Iniciando a inicialização do VisionSystem...")
        logger.info(f"Modo headless: {self.headless}")
        try:
            model_path = os.path.join(base_dir, 'data', 'models', 'best_float32_edgetpu.tflite')
            label_path = os.path.join(base_dir, 'data', 'models', 'labels.txt')

            logger.info(f"Carregando modelo de: {model_path}")
            # Verifica se o modelo EdgeTPU está disponível
            if os.path.exists(model_path):
                # Tenta carregar com EdgeTPU (NPU)
                try:
                    if USING_TFLITE_RUNTIME:
                        self.interpreter = tf.Interpreter(
                            model_path=model_path,
                            experimental_delegates=[tf.load_delegate('libedgetpu.so.1')]
                        )
                    else:
                        # Para TensorFlow completo, usa abordagem diferente
                        self.interpreter = tf.Interpreter(model_path=model_path)
                    logger.info("Modelo carregado com EdgeTPU (NPU) delegate." if USING_TFLITE_RUNTIME else "Modelo carregado (TensorFlow Lite).")
                except Exception as e:
                    logger.warning(f"Falha ao carregar EdgeTPU delegate: {e}")
                    logger.info("Carregando modelo sem EdgeTPU delegate...")
                    self.interpreter = tf.Interpreter(model_path=model_path)
            else:
                # Fallback para modelo sem EdgeTPU
                fallback_model = os.path.join(base_dir, 'data', 'models', 'best_float32.tflite')
                logger.warning(f"Modelo EdgeTPU não encontrado. Usando fallback: {fallback_model}")
                self.interpreter = tf.Interpreter(model_path=fallback_model)
            
            self.interpreter.allocate_tensors()
            logger.info("Modelo TFLite carregado.")

            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            self.input_height = self.input_details[0]['shape'][1]
            self.input_width = self.input_details[0]['shape'][2]

            # Debug: informações do modelo
            logger.info(f"Input shape: {self.input_details[0]['shape']}")
            logger.info(f"Número de outputs: {len(self.output_details)}")
            for i, output in enumerate(self.output_details):
                logger.info(f"Output {i}: shape={output['shape']}, dtype={output['dtype']}")

            logger.info(f"Carregando labels de: {label_path}")
            with open(label_path, 'r') as f:
                self.labels = [line.strip() for line in f.readlines()]
            logger.info(f"Labels carregadas: {self.labels}")

            self.colors = {'OK': (0, 255, 0), 'NOK': (0, 0, 255), 'PEDRA': (255, 0, 0)}
            self.class_priority = {'PEDRA': 3, 'NOK': 2, 'OK': 1}
            self.class_values = {'OK': 0, 'NOK': 1, 'PEDRA': 2}
            
            self.plc = Plc()
            self.camera = None
            self.camera_type = None
            self.converter = None
            logger.info("VisionSystem inicializado com sucesso.")
        except Exception as e:
            logger.error(f"Erro CRÍTICO na inicialização: {e}", exc_info=True)
            self.root.destroy()

    def init_camera(self) -> bool:
        """Inicializa câmera - tenta USB comum primeiro, depois Basler se disponível"""
        logger.info("Tentando inicializar a câmera...")
        
        # Primeiro tenta câmera USB comum (OpenCV)
        if self._init_usb_camera():
            logger.info("✅ Câmera USB comum inicializada com sucesso")
            return True
        
        # Se não encontrou USB comum e PyPylon está disponível, tenta Basler
        if PYLON_AVAILABLE and self._init_basler_camera():
            logger.info("✅ Câmera Basler inicializada com sucesso")
            return True
        
        logger.error("❌ Nenhuma câmera encontrada (USB comum ou Basler)")
        return False
    
    def _init_usb_camera(self) -> bool:
        """Inicializa câmera USB comum usando OpenCV"""
        try:
            logger.info("Procurando câmeras USB...")
            
            # Tenta diferentes índices de câmera (0, 1, 2...)
            for camera_index in range(5):
                logger.info(f"Testando câmera índice {camera_index}...")
                cap = cv2.VideoCapture(camera_index)
                
                if cap.isOpened():
                    # Testa se consegue capturar um frame
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        logger.info(f"✅ Câmera USB encontrada no índice {camera_index}")
                        
                        # Configurar resolução se possível
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        cap.set(cv2.CAP_PROP_FPS, 30)
                        
                        # Verificar configurações aplicadas
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        logger.info(f"Câmera configurada: {width}x{height} @ {fps}fps")
                        
                        self.camera = cap
                        self.camera_type = "USB"
                        return True
                    else:
                        cap.release()
                else:
                    cap.release()
            
            logger.warning("Nenhuma câmera USB funcional encontrada")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao inicializar câmera USB: {e}")
            return False
    
    def _init_basler_camera(self) -> bool:
        """Inicializa câmera Basler usando PyPylon"""
        try:
            factory = pylon.TlFactory.GetInstance()
            devices = factory.EnumerateDevices()
            if not devices:
                logger.warning("Nenhuma câmera Basler encontrada")
                return False
            
            logger.info(f"Encontradas {len(devices)} câmera(s) Basler")
            self.camera = pylon.InstantCamera(factory.CreateFirstDevice())
            self.camera.Open()
            
            # Configurações da câmera para melhor performance
            if self.camera.IsGrabbing():
                self.camera.StopGrabbing()
            
            # Configurar parâmetros da câmera se suportados
            try:
                if self.camera.PixelFormat.IsWritable():
                    self.camera.PixelFormat.SetValue("RGB8")
                if self.camera.Width.IsWritable():
                    self.camera.Width.SetValue(640)
                if self.camera.Height.IsWritable():
                    self.camera.Height.SetValue(480)
            except Exception as e:
                logger.warning(f"Não foi possível configurar alguns parâmetros da câmera: {e}")
            
            self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            self.converter = pylon.ImageFormatConverter()
            self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            self.converter = pylon.ImageFormatConverter()
            self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
            
            self.camera_type = "Basler"
            return True
            
        except Exception as e:
            logger.error(f"Erro ao inicializar câmera Basler: {e}")
            return False
            
            logger.info("Câmera inicializada com SUCESSO.")
            return True
        except Exception as e:
            logger.error(f"Falha CRÍTICA ao inicializar a câmera: {e}", exc_info=True)
            return False

    def capture_frame(self):
        """Captura frame da câmera (USB ou Basler)"""
        try:
            if self.camera_type == "USB":
                ret, frame = self.camera.read()
                if not ret or frame is None:
                    logger.warning("Falha ao capturar frame da câmera USB")
                    return None
                return frame
            
            elif self.camera_type == "Basler" and PYLON_AVAILABLE:
                if not self.camera.IsGrabbing():
                    logger.warning("Câmera Basler não está grabbing")
                    return None
                
                grab_result = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if not grab_result.GrabSucceeded():
                    logger.warning("Falha ao capturar frame da câmera Basler")
                    grab_result.Release()
                    return None

                image = self.converter.Convert(grab_result)
                frame = image.GetArray()
                grab_result.Release()
                return frame
            
            else:
                logger.error(f"Tipo de câmera desconhecido: {getattr(self, 'camera_type', 'indefinido')}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao capturar frame: {e}")
            return None

    def process_frame(self):
        try:
            # Verificar se câmera está inicializada
            if not hasattr(self, 'camera') or self.camera is None:
                logger.warning("Câmera não inicializada. Tentando reinicializar...")
                if not self.init_camera():
                    logger.error("Falha ao reinicializar câmera.")
                    self._schedule_next_frame(1000)
                    return

            # Capturar frame
            frame = self.capture_frame()
            if frame is None:
                logger.warning("Frame vazio recebido. Tentando novamente...")
                self._schedule_next_frame(10)
                return
                
            # --- Lógica de Inferência ---
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            imH, imW, _ = frame.shape
            input_data = cv2.resize(frame_rgb, (self.input_width, self.input_height))
            input_data = np.expand_dims(input_data, axis=0)
            input_data = np.float32(input_data) / 255.0

            # Executar inferência
            start_time = time.time()
            self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
            self.interpreter.invoke()
            inference_time = time.time() - start_time

            # Verificar outputs disponíveis e acessar com segurança
            if len(self.output_details) < 4:
                logger.warning(f"Modelo possui apenas {len(self.output_details)} outputs, esperado 4. Pulando frame.")
                self._schedule_next_frame(10)
                return

            # Acessar outputs com verificação de índice
            try:
                scores = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
                boxes = self.interpreter.get_tensor(self.output_details[1]['index'])[0]
                classes = self.interpreter.get_tensor(self.output_details[3]['index'])[0]
            except IndexError as e:
                logger.warning(f"Erro ao acessar outputs do modelo: {e}. Outputs disponíveis: {len(self.output_details)}")
                self._schedule_next_frame(10)
                return

            highest_priority_class = None
            highest_priority = 0
            detections_count = 0

            for i in range(len(scores)):
                if scores[i] > 0.5:
                    detections_count += 1
                    ymin = int(max(1, boxes[i][0] * imH))
                    xmin = int(max(1, boxes[i][1] * imW))
                    ymax = int(min(imH, boxes[i][2] * imH))
                    xmax = int(min(imW, boxes[i][3] * imW))
                    
                    object_name = self.labels[int(classes[i])]
                    color = self.colors.get(object_name, (0, 255, 0))
                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
                    
                    # Adicionar texto com confiança
                    confidence_text = f"{object_name}: {scores[i]:.2f}"
                    cv2.putText(frame, confidence_text, (xmin, ymin-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    
                    priority = self.class_priority.get(object_name, 0)
                    if priority > highest_priority:
                        highest_priority = priority
                        highest_priority_class = object_name

            # Adicionar informações de performance no frame
            perf_text = f"Inference: {inference_time*1000:.1f}ms | Detections: {detections_count}"
            cv2.putText(frame, perf_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Enviar dados para PLC apenas se houver detecção válida
            if highest_priority_class:
                plc_data = self.class_values[highest_priority_class]
                success = self.plc.write_db(plc_data)
                if success:
                    logger.debug(f"✅ Enviado para PLC: {highest_priority_class} ({plc_data})")
                else:
                    logger.debug(f"⚠️ PLC indisponível - valor não enviado: {highest_priority_class} ({plc_data})")
            
            # --- Lógica de Exibição com Tkinter (apenas em modo GUI) ---
            if not self.headless:
                # Converte a imagem do OpenCV (BGR) para o formato do Pillow (RGB)
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                # Redimensiona se necessário para caber na interface
                img = img.resize((640, 480), Image.Resampling.LANCZOS)
                # Converte para um formato que o Tkinter possa usar
                imgtk = ImageTk.PhotoImage(image=img)
                # Atualiza o canvas com a nova imagem
                self.canvas.delete("all")  # Limpar canvas anterior
                self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                self.canvas.imgtk = imgtk # Guarda uma referência para evitar que a imagem seja apagada

            # Agenda a próxima chamada deste método para criar o loop
            self._schedule_next_frame(10)

        except Exception as e:
            logger.error(f"Erro durante o processamento de um frame: {e}", exc_info=True)
            # Agenda a próxima chamada mesmo se houver erro
            self._schedule_next_frame(100)  # Espera um pouco mais em caso de erro

    def _schedule_next_frame(self, delay_ms=10):
        """Agenda a próxima execução do process_frame, com suporte para modo headless"""
        if self.headless:
            # Em modo headless, usa threading.Timer em vez de tkinter.after
            import threading
            timer = threading.Timer(delay_ms / 1000.0, self.process_frame)
            timer.daemon = True
            timer.start()
        else:
            # Em modo GUI, usa o tkinter.after
            self.root.after(delay_ms, self.process_frame)

    def start(self):
        if self.init_camera():
            # Tenta conectar ao PLC, mas não para a aplicação se falhar
            plc_status = self.plc.init_plc()
            if plc_status:
                logger.info("Sistema iniciado com câmera e PLC")
            else:
                logger.warning("Sistema iniciado apenas com câmera - PLC será reconectado automaticamente")
            
            logger.info("Iniciando o loop de processamento de frames.")
            self.process_frame()
            
            if self.headless:
                # Em modo headless, manter o programa rodando
                logger.info("Modo headless ativo - aplicação rodando em background")
                try:
                    while True:
                        import time
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Interrupção do usuário detectada - encerrando...")
                    self.on_closing()
        else:
            logger.error("Não foi possível iniciar a câmera. Encerrando.")
            if not self.headless:
                self.root.destroy()
            
    def on_closing(self):
        logger.info("Fechando a aplicação...")
        try:
            if hasattr(self, 'camera') and self.camera:
                if self.camera_type == "USB":
                    self.camera.release()
                    logger.info("Câmera USB liberada.")
                elif self.camera_type == "Basler" and PYLON_AVAILABLE:
                    if self.camera.IsOpen():
                        if self.camera.IsGrabbing():
                            self.camera.StopGrabbing()
                        self.camera.Close()
                    logger.info("Câmera Basler liberada.")
        except Exception as e:
            logger.error(f"Erro ao fechar câmera: {e}")
        
        try:
            if hasattr(self, 'plc') and self.plc:
                self.plc.disconnect()
                logger.info("Conexão PLC encerrada.")
        except Exception as e:
            logger.error(f"Erro ao desconectar PLC: {e}")
        
        if not self.headless:
            self.root.destroy()

# --- Ponto de Entrada Principal do Script ---
if __name__ == "__main__":
    logger.info("========================================")
    logger.info("      Iniciando Aplicação Potato ID     ")
    logger.info("========================================")
    
    try:
        if HEADLESS_MODE:
            logger.info("Modo HEADLESS detectado - iniciando sem interface gráfica")
            app = VisionSystem(root=None)
            app.start()
        else:
            logger.info("Modo GUI - iniciando com interface gráfica")
            root = tk.Tk()
            app = VisionSystem(root)
            root.protocol("WM_DELETE_WINDOW", app.on_closing)
            app.start()
            root.mainloop()
    except Exception as e:
        logger.critical(f"Erro fatal na execução principal: {e}", exc_info=True)
    finally:
        logger.info("Aplicação finalizada.")