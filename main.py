import cv2
import numpy as np
import torch
from PIL import Image
from io import BytesIO
import pandas as pd
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ultralytics import YOLO


app = FastAPI(title="Yolov11 Object Detection")
model = YOLO("yolo11n.pt")

@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    try:
        # Read image
        contents = await file.read()
        image = Image.open(BytesIO(contents)).convert("RGB")
        image_np = np.array(image)
        
        # Predict
        results = model(image_np)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # print(box)
                label_numbers = int(box.cls[0])
                conf = float(box.conf[0])
                bbox = box.xyxy[0].tolist()
    
                detections.append({
                    "class": model.names[label_numbers],
                    "confidence": conf,
                    "bounding_box": {
                        "x1": bbox[0], "y1": bbox[1], "x2": bbox[2], "y2": bbox[3]
                    }
                })
        return JSONResponse(content={'detections': detections, 'total_objects': len(detections)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/")
async def root():
    """
    Health check
    """
    return {"message": "Model is running"}