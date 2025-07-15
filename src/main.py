import os
import cv2
import logging
import asyncio
import time
import numpy as np
from pypylon import pylon
import tflite_runtime.interpreter as tf
from plc import Plc

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VisionSystem:
    def __init__(self, model_path: str = 'data/models/best_float32_edgetpu.tflite', label_path: str = 'data/labels.txt'):
        """
        Construtor da classe. É executado quando criamos uma instância de VisionSystem.
        """
        # Carrega o modelo TFLite a partir do caminho especificado e prepara o interpretador.
        self.interpreter = tf.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()

        # Obtém os detalhes de entrada e saída do modelo (como o tamanho da imagem que ele espera).
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.input_height = self.input_details[0]['shape'][1]
        self.input_width = self.input_details[0]['shape'][2]

        # Carrega as etiquetas (labels) do arquivo labels.txt.
        # O resultado será uma lista como ['OK', 'NOK', 'PEDRA'].
        with open(label_path, 'r') as f:
            self.labels = [line.strip() for line in f.readlines()]

        # Define cores para as caixas de detecção, prioridades e valores para o PLC.
        self.colors = {'OK': (0, 255, 0), 'NOK': (0, 0, 255), 'PEDRA': (255, 0, 0)}
        self.class_priority = {'PEDRA': 3, 'NOK': 2, 'OK': 1}
        self.class_values = {'OK': 0, 'NOK': 1, 'PEDRA': 2}
        
        # Inicializa outras variáveis importantes.
        self.window_name = 'Vision System'
        self.plc = Plc()
        self.camera = None
        self.converter = None
        self.last_screenshot_time = 0

    def init_camera(self) -> bool:
            """Inicializa a câmera usando a biblioteca pypylon."""
            try:
                # Encontra e inicializa a primeira câmera pylon disponível.
                self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
                self.camera.Open()
                logging.info("Câmera aberta com sucesso.")

                # Inicia a captura de imagens.
                self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
                
                # Converte o formato da imagem da câmera para um que o OpenCV entenda (BGR).
                self.converter = pylon.ImageFormatConverter()
                self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
                self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

                # Cria uma janela para exibir a imagem.
                cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
                cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                return True
            except Exception as e:
                logger.error(f"Erro ao inicializar a câmera: {e}")
                logger.error("Não foi possível encontrar um dispositivo disponível.")
                return False
            
    async def process_frame(self) -> None:
            """Processa o frame, realiza a inferência e envia o resultado para o PLC."""
            # Inicializa a conexão com o PLC.
            if not self.plc.init_plc():
                logger.error("Falha ao inicializar o PLC")
                return

            # Loop principal: continua enquanto a câmera estiver capturando.
            while self.camera.IsGrabbing():
                try:
                    # Captura o resultado da câmera.
                    grab_result = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                    if not grab_result.GrabSucceeded():
                        continue

                    # Converte a imagem para o formato do OpenCV.
                    image = self.converter.Convert(grab_result)
                    frame = image.GetArray()
                    
                    # Prepara a imagem para o modelo.
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    imH, imW, _ = frame.shape
                    input_data = cv2.resize(frame_rgb, (self.input_width, self.input_height))
                    input_data = np.expand_dims(input_data, axis=0)

                    # Realiza a inferência com o modelo TFLite.
                    self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
                    self.interpreter.invoke()

                    # Obtém os resultados da detecção.
                    boxes = self.interpreter.get_tensor(self.output_details[1]['index'])[0]      # Coordenadas das caixas
                    classes = self.interpreter.get_tensor(self.output_details[3]['index'])[0]    # Classes dos objetos
                    scores = self.interpreter.get_tensor(self.output_details[0]['index'])[0]     # Confiança da detecção

                    highest_priority_class = None
                    highest_priority = 0

                    # Itera sobre todas as detecções encontradas.
                    for i in range(len(scores)):
                        if scores[i] > 0.5: # Considera apenas detecções com mais de 50% de confiança.
                            # Extrai as coordenadas da caixa delimitadora.
                            ymin = int(max(1, boxes[i][0] * imH))
                            xmin = int(max(1, boxes[i][1] * imW))
                            ymax = int(min(imH, boxes[i][2] * imH))
                            xmax = int(min(imW, boxes[i][3] * imW))

                            # Obtém o nome da classe e desenha na tela.
                            object_name = self.labels[int(classes[i])]
                            color = self.colors.get(object_name, (0, 255, 0))
                            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
                            
                            # Verifica qual é a classe de maior prioridade no frame atual.
                            priority = self.class_priority.get(object_name, 0)
                            if priority > highest_priority:
                                highest_priority = priority
                                highest_priority_class = object_name
                    
                    # Se um objeto de alta prioridade foi detectado, envia o dado ao PLC.
                    if highest_priority_class:
                        plc_data = self.class_values[highest_priority_class]
                        self.plc.write_db(plc_data)

                    # Exibe o frame processado.
                    cv2.imshow(self.window_name, frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                except Exception as e:
                    logger.error(f"Erro ao processar o frame: {e}")
                    continue