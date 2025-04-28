import cv2
import numpy as np


class VehicleDetector:
    def __init__(self, model_path, config_path, classes_path, conf_threshold=0.5, nms_threshold=0.4, input_width=640, input_height=640):
        with open(classes_path, 'r') as f:
            self.classes = f.read().strip().split('\n')
        self.vehicle_classes = ['car', 'truck', 'bus', 'motorcycle', 'bicycle']
        self.vehicle_class_ids = [self.classes.index(cls) for cls in self.vehicle_classes if cls in self.classes]
        
        # Load YOLO model
        self.net = cv2.dnn.readNetFromDarknet(config_path, model_path)
        
        # Set preferred backend
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        self.input_width = input_width
        self.input_height = input_height
    
    def detect(self, frame):
        height, width = frame.shape[:2]
        
        # Create blob from image
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (self.input_width, self.input_height), swapRB=True, crop=False)
        
        # Set input
        self.net.setInput(blob)
        
        # Forward pass
        outputs = self.net.forward(self.output_layers)
        
        class_ids = []
        confidences = []
        boxes = []
        
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > self.conf_threshold and class_id in self.vehicle_class_ids:
                    #Scale bb into original image size
                    box_x = int(detection[0] * width)
                    box_y = int(detection[1] * height)
                    box_width = int(detection[2] * width)
                    box_height = int(detection[3] * height)
                    
                    # top-left coor
                    x = int(box_x - box_width / 2)
                    y = int(box_y - box_height / 2)
                    
                    boxes.append([x, y, box_width, box_height])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        
        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.conf_threshold, self.nms_threshold)
        
        # Result
        detections = []
        for i in indices:
            
            idx = int(i)
            box = boxes[idx]
            class_id = class_ids[idx]
            
            detections.append({
                'class_id': class_id,
                'class_name': self.classes[class_id],
                'confidence': confidences[idx],
                'bbox': box
            })
        return detections