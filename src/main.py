import sys
import numpy as np
from time import time
import os
import cv2

## Import tflite runtime
import tflite_runtime.interpreter as tf #Tensorflow_Lite

## Read Environment Variables
USE_HW_ACCELERATED_INFERENCE = True

## The system returns the variables as Strings, so it's necessary to convert them where we need the numeric value

MINIMUM_SCORE = float(os.environ.get("MINIMUM_SCORE", default = 0.25))  # Lower threshold for YOLO

CAPTURE_DEVICE = os.environ.get("CAPTURE_DEVICE", default = "/dev/video2")

CAPTURE_RESOLUTION_X = int(os.environ.get("CAPTURE_RESOLUTION_X", default = 640))

CAPTURE_RESOLUTION_Y = int(os.environ.get("CAPTURE_RESOLUTION_Y", default = 480))

CAPTURE_FRAMERATE = int(os.environ.get("CAPTURE_FRAMERATE", default = 30))

## Helper function to draw bounding boxes
def draw_bounding_boxes(img, labels, x1, y1, x2, y2, object_class, score):
    # Define some colors to display bounding boxes
    box_colors=[(254,153,143),(253,156,104),(253,157,13),(252,204,26),
             (254,254,51),(178,215,50),(118,200,60),(30,71,87),
             (1,48,178),(59,31,183),(109,1,142),(129,14,64)]

    text_colors=[(0,0,0),(0,0,0),(0,0,0),(0,0,0),
             (0,0,0),(0,0,0),(0,0,0),(255,255,255),
            (255,255,255),(255,255,255),(255,255,255),(255,255,255)]

    cv2.rectangle(img,(x1,y1),(x2,y2),
                box_colors[object_class%len(box_colors)],2)
    
    # Create label with class name and confidence
    label = f"{labels[object_class]}: {score:.2f}"
    label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    
    cv2.rectangle(img,(x1, y1-label_size[1]-4),(x1+label_size[0], y1),
                box_colors[object_class%len(box_colors)],-1)
    cv2.putText(img,label,(x1,y1-2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                text_colors[(object_class)%len(text_colors)],1,cv2.LINE_AA)

class YOLOv8Detection:
    def __init__(self):
        # Try to load with hardware acceleration first, fall back to CPU if it fails
        self.interpreter = None
        
        if USE_HW_ACCELERATED_INFERENCE:
            try:
                print("Attempting to use hardware acceleration...")
                delegates = [tf.load_delegate("/usr/lib/libvx_delegate.so")]
                self.interpreter = tf.Interpreter(model_path="data/models/potato_model_quantized.tflite", experimental_delegates=delegates)
                # Try to allocate tensors to see if it really works
                self.interpreter.allocate_tensors()
                print("Hardware acceleration enabled successfully")
            except Exception as e:
                print(f"Failed to use hardware acceleration: {e}")
                print("Falling back to CPU...")
                self.interpreter = None
        
        # If hardware acceleration failed or not requested, use CPU
        # if self.interpreter is None:
        #     try:
        #         self.interpreter = tf.Interpreter(model_path="data/models/potato_model_quantized.tflite")
        #         self.interpreter.allocate_tensors()
        #         print("Using CPU for inference")
        #     except Exception as e:
        #         print(f"Failed to load model: {e}")
        #         raise

        # Get input and output tensors.
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        # Print model details for debugging
        print(f"Input shape: {self.input_details[0]['shape']}")
        print(f"Input dtype: {self.input_details[0]['dtype']}")
        print(f"Number of outputs: {len(self.output_details)}")
        for i, output in enumerate(self.output_details):
            print(f"Output {i} shape: {output['shape']}")
        
        self.input_size = self.input_details[0]['shape'][1]  # Assuming square input

        # Load labels - adjust path as needed
        try:
            with open("data/models/labels.txt", "r") as file:
                self.labels = file.read().splitlines()
        except:
            # Default COCO labels if file not found
            self.labels = ['OK', 'NOK', 'PEDRA']

        # Initialize video capture
        device_num = int(CAPTURE_DEVICE.split('video')[-1]) if 'video' in CAPTURE_DEVICE else 0
        
        self.cap = cv2.VideoCapture(device_num)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_RESOLUTION_X)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_RESOLUTION_Y)
        self.cap.set(cv2.CAP_PROP_FPS, CAPTURE_FRAMERATE)
        
        if not self.cap.isOpened():
            print(f"Error: Could not open video device {CAPTURE_DEVICE}")
            sys.exit(1)

    def process_yolov8_output(self, output, img_width, img_height):
        """Process YOLOv8 output format"""
        # YOLOv8 output is typically [1, num_predictions, 85] for COCO (80 classes + 5)
        # or [1, 85, num_predictions] depending on the export
        
        output = output[0]  # Remove batch dimension
        
        # Check if we need to transpose
        if output.shape[0] < output.shape[1]:
            output = output.T
        
        boxes = []
        for prediction in output:
            # YOLOv8 format: [x, y, w, h, confidence, class_scores...]
            x, y, w, h = prediction[:4]
            confidence = prediction[4]
            
            if confidence < MINIMUM_SCORE:
                continue
            
            # Get class scores
            class_scores = prediction[5:]
            class_id = np.argmax(class_scores)
            class_confidence = class_scores[class_id]
            
            # Combined confidence
            score = confidence * class_confidence
            
            if score < MINIMUM_SCORE:
                continue
            
            # Convert from normalized coordinates to pixel coordinates
            x1 = int((x - w/2) * img_width)
            y1 = int((y - h/2) * img_height)
            x2 = int((x + w/2) * img_width)
            y2 = int((y + h/2) * img_height)
            
            # Clip coordinates
            x1 = max(0, min(x1, img_width))
            y1 = max(0, min(y1, img_height))
            x2 = max(0, min(x2, img_width))
            y2 = max(0, min(y2, img_height))
            
            boxes.append([x1, y1, x2, y2, class_id, score])
        
        return boxes

    def process_frame(self, image_original):
        height_orig, width_orig = image_original.shape[:2]
        
        # Resize image to model input size
        image_resized = cv2.resize(image_original, (self.input_size, self.input_size))
        
        # Prepare input
        if self.input_details[0]['dtype'] == np.uint8:
            # For quantized models
            input_data = np.expand_dims(image_resized, axis=0).astype(np.uint8)
        else:
            # For float models
            input_data = np.expand_dims(image_resized, axis=0).astype(np.float32) / 255.0
        
        # Set input tensor
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        
        # Run inference
        t1 = time()
        self.interpreter.invoke()
        t2 = time()
        
        # Get output
        output = self.interpreter.get_tensor(self.output_details[0]['index'])
        
        # Process detections
        boxes = self.process_yolov8_output(output, width_orig, height_orig)
        
        # Draw results
        img = image_original.copy()
        for box in boxes:
            x1, y1, x2, y2, class_id, score = box
            if class_id < len(self.labels):
                draw_bounding_boxes(img, self.labels, x1, y1, x2, y2, int(class_id), score)
        
        # Draw inference time
        cv2.rectangle(img, (0, 0), (130, 20), (255, 0, 0), -1)
        cv2.putText(img, f"inf time: {(t2-t1):.3f}s", (0, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (255, 255, 255), 1, cv2.LINE_AA)
        
        return img

    def run(self):
        # Create window
        cv2.namedWindow('YOLOv8 Detection', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('YOLOv8 Detection', CAPTURE_RESOLUTION_X, CAPTURE_RESOLUTION_Y)
        
        print("Press 'q' to quit")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to capture frame")
                break
            
            # Apply flips if needed
            frame = cv2.flip(frame, 1)  # Horizontal flip
            frame = cv2.flip(frame, 0)  # Vertical flip
            
            # Process frame with object detection
            processed_frame = self.process_frame(frame)
            
            # Display the frame
            cv2.imshow('YOLOv8 Detection', processed_frame)
            
            # Check for 'q' key press to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # Cleanup
        self.cap.release()
        cv2.destroyAllWindows()

def main():
    # Force CPU usage to avoid the Vx Delegate error
    os.environ["USE_HW_ACCELERATED_INFERENCE"] = "0"
    
    try:
        detector = YOLOv8Detection()
        detector.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()