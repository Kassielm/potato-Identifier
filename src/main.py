import os
import cv2
import logging
import time
import numpy as np
from pypylon import pylon
import tflite_runtime.interpreter as tf
from plc import Plc
import tkinter as tk
from PIL import Image, ImageTk

# --- Lógica de Caminhos Absolutos ---
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)

# --- Configuração do Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VisionSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Vision System")
        
        # Cria um Canvas no Tkinter para exibir o vídeo
        self.canvas = tk.Canvas(root, width=640, height=480)
        self.canvas.pack()

        logger.info("Iniciando a inicialização do VisionSystem...")
        try:
            model_path = os.path.join(base_dir, 'data', 'models', 'best_float32_edgetpu.tflite')
            label_path = os.path.join(base_dir, 'data', 'models', 'labels.txt')

            logger.info(f"Carregando modelo de: {model_path}")
            self.interpreter = tf.Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()
            logger.info("Modelo TFLite carregado.")

            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            self.input_height = self.input_details[0]['shape'][1]
            self.input_width = self.input_details[0]['shape'][2]

            logger.info(f"Carregando labels de: {label_path}")
            with open(label_path, 'r') as f:
                self.labels = [line.strip() for line in f.readlines()]
            logger.info(f"Labels carregadas: {self.labels}")

            self.colors = {'OK': (0, 255, 0), 'NOK': (0, 0, 255), 'PEDRA': (255, 0, 0)}
            self.class_priority = {'PEDRA': 3, 'NOK': 2, 'OK': 1}
            self.class_values = {'OK': 0, 'NOK': 1, 'PEDRA': 2}
            
            self.plc = Plc()
            self.camera = None
            self.converter = None
            logger.info("VisionSystem inicializado com sucesso.")
        except Exception as e:
            logger.error(f"Erro CRÍTICO na inicialização: {e}", exc_info=True)
            self.root.destroy()

    def init_camera(self) -> bool:
        logger.info("Tentando inicializar a câmera...")
        try:
            factory = pylon.TlFactory.GetInstance()
            devices = factory.EnumerateDevices()
            if not devices:
                logger.error("Nenhuma câmera Pylon encontrada!")
                return False
            
            self.camera = pylon.InstantCamera(factory.CreateFirstDevice())
            self.camera.Open()
            self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            
            self.converter = pylon.ImageFormatConverter()
            self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
            
            logger.info("Câmera inicializada com SUCESSO.")
            return True
        except Exception as e:
            logger.error(f"Falha CRÍTICA ao inicializar a câmera: {e}", exc_info=True)
            return False

    def process_frame(self):
        try:
            if self.camera and self.camera.IsGrabbing():
                grab_result = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if not grab_result.GrabSucceeded():
                    # Tenta novamente no próximo ciclo
                    self.root.after(10, self.process_frame)
                    return

                image = self.converter.Convert(grab_result)
                frame = image.GetArray()
                
                # --- Lógica de Inferência (sem alterações) ---
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                imH, imW, _ = frame.shape
                input_data = cv2.resize(frame_rgb, (self.input_width, self.input_height))
                input_data = np.expand_dims(input_data, axis=0)
                input_data = np.float32(input_data) / 255.0

                self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
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
                    plc_data = self.class_values[highest_priority_class]
                    self.plc.write_db(plc_data)
                
                # --- Lógica de Exibição com Tkinter ---
                # Converte a imagem do OpenCV (BGR) para o formato do Pillow (RGB)
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                # Converte para um formato que o Tkinter possa usar
                imgtk = ImageTk.PhotoImage(image=img)
                # Atualiza o canvas com a nova imagem
                self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                self.canvas.imgtk = imgtk # Guarda uma referência para evitar que a imagem seja apagada

            # Agenda a próxima chamada deste método para criar o loop
            self.root.after(10, self.process_frame)

        except Exception as e:
            logger.error(f"Erro durante o processamento de um frame: {e}", exc_info=True)
            # Agenda a próxima chamada mesmo se houver erro
            self.root.after(10, self.process_frame)

    def start(self):
        if self.init_camera():
            if self.plc.init_plc():
                logger.info("Iniciando o loop de processamento de frames.")
                self.process_frame()
            else:
                logger.error("Não foi possível iniciar o PLC. Encerrando.")
                self.root.destroy()
        else:
            logger.error("Não foi possível iniciar a câmera. Encerrando.")
            self.root.destroy()
            
    def on_closing(self):
        logger.info("Fechando a aplicação...")
        if self.camera and self.camera.IsOpen():
            self.camera.Close()
            logger.info("Recurso da câmera liberado.")
        self.root.destroy()

# --- Ponto de Entrada Principal do Script ---
if __name__ == "__main__":
    logger.info("========================================")
    logger.info("      Iniciando Aplicação Potato ID     ")
    logger.info("========================================")
    
    try:
        root = tk.Tk()
        app = VisionSystem(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.start()
        root.mainloop()
    except Exception as e:
        logger.critical(f"Erro fatal na execução principal: {e}", exc_info=True)
    finally:
        logger.info("Aplicação finalizada.")