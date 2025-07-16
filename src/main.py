import os
import cv2
import logging
import time
import numpy as np
from pypylon import pylon
import tflite_runtime.interpreter as tf
from plc import Plc

# --- Lógica de Caminhos Absolutos ---
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)

# --- Configuração do Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VisionSystem:
    def __init__(self, model_path: str = os.path.join(base_dir, 'data', 'models', 'best_float32_edgetpu.tflite'),
                 label_path: str = os.path.join(base_dir, 'data', 'models', 'labels.txt')):
        logger.info("Iniciando a inicialização do VisionSystem...")
        try:
            self.interpreter = tf.Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            self.input_height = self.input_details[0]['shape'][1]
            self.input_width = self.input_details[0]['shape'][2]
            with open(label_path, 'r') as f:
                self.labels = [line.strip() for line in f.readlines()]
            self.colors = {'OK': (0, 255, 0), 'NOK': (0, 0, 255), 'PEDRA': (255, 0, 0)}
            self.class_priority = {'PEDRA': 3, 'NOK': 2, 'OK': 1}
            self.class_values = {'OK': 0, 'NOK': 1, 'PEDRA': 2}
            self.window_name = 'Vision System'
            self.plc = Plc()
            self.camera = None
            self.converter = None
            logger.info("VisionSystem inicializado com sucesso.")
        except Exception as e:
            logger.error(f"Erro CRÍTICO na inicialização: {e}", exc_info=True)
            raise

    def init_camera(self) -> bool:
        logger.info("Tentando inicializar a câmera...")
        try:
            factory = pylon.TlFactory.GetInstance()
            if len(factory.EnumerateDevices()) == 0:
                logger.error("Nenhuma câmera Pylon encontrada!")
                return False
            
            self.camera = pylon.InstantCamera(factory.CreateFirstDevice())
            self.camera.Open()
            self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            self.converter = pylon.ImageFormatConverter()
            self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
            
            # Criando a janela com OpenCV
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            logger.info("Câmera e janela inicializadas com SUCESSO.")
            return True
        except Exception as e:
            logger.error(f"Falha CRÍTICA ao inicializar a câmera: {e}", exc_info=True)
            return False

    def run(self):
        if not self.init_camera() or not self.plc.init_plc():
            logger.error("Falha na inicialização da Câmera ou PLC. Encerrando.")
            return
            
        logger.info("Iniciando o loop principal de processamento...")
        while self.camera.IsGrabbing():
            try:
                grab_result = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if not grab_result.GrabSucceeded():
                    continue

                frame = self.converter.Convert(grab_result).GetArray()
                
                imH, imW, _ = frame.shape
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                input_data = cv2.resize(frame_rgb, (self.input_width, self.input_height))
                input_data_expanded = np.expand_dims(input_data, axis=0)
                input_data_final = np.float32(input_data_expanded) / 255.0

                self.interpreter.set_tensor(self.input_details[0]['index'], input_data_final)
                self.interpreter.invoke()

                boxes = self.interpreter.get_tensor(self.output_details[1]['index'])[0]
                classes = self.interpreter.get_tensor(self.output_details[3]['index'])[0]
                scores = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
                
                highest_priority_class = None
                highest_priority = 0

                for i in range(len(scores)):
                    if scores[i] > 0.5:
                        ymin = int(max(1, boxes[i][0] * imH))
                        xmin = int(max(1, boxes[i][1] * imW))
                        ymax = int(min(imH, boxes[i][2] * imH))
                        xmax = int(min(imW, boxes[i][3] * imW))
                        object_name = self.labels[int(classes[i])]
                        color = self.colors.get(object_name, (0, 255, 0))
                        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
                        
                        priority = self.class_priority.get(object_name, 0)
                        if priority > highest_priority:
                            highest_priority = priority
                            highest_priority_class = object_name
                
                if highest_priority_class:
                    self.plc.write_db(self.class_values[highest_priority_class])

                # Exibindo o frame
                cv2.imshow(self.window_name, frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("Tecla 'q' pressionada. Encerrando.")
                    break
            except Exception as e:
                logger.error(f"Erro no loop de processamento: {e}", exc_info=True)
                break
        
        logger.info("Loop de processamento encerrado.")

if __name__ == "__main__":
    logger.info("Iniciando Aplicação")
    try:
        vs = VisionSystem()
        vs.run()
    except Exception as e:
        logger.critical(f"Erro fatal na execução: {e}", exc_info=True)
    finally:
        cv2.destroyAllWindows()
        logger.info("Aplicação finalizada.")