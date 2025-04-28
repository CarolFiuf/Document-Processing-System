import cv2
import numpy as np
from queue import Queue
from threading import Thread

from modules.detection.yolo_detector import YoloDetector
from modules.video_capture.gstreamer_pipeline import GStreamerPipeline
class TrafficMonitoringPipeline:
    
    def processing_thread(self):
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=1)
                processed_frame, results = self.process_frame(frame)
                
                # Put result in output queue
                if processed_frame is not None and results is not None:
                    self.results_queue.put((processed_frame, results))
                    
                self.frame_queue.task_done()  
            except Exception as e:
                pass
    
    def start(self):
        if self.running:
            print("Pipeline is already running")
            return
        
        self.running = True
        
        if isinstance(self.video_source, GStreamerPipeline):
            self.video_source.start()
        
        self.capture_thread_odj = Thread(target=self.capture_thread)
        self.capture_thread_odj.deamon = True
        self.capture_thread_odj.start()
        
        for _ in range(self.num_processing_threads):
            thread = Thread(target=self.processing_thread)
            thread.deamon = True
            thread.start()
            self.processing_thread.append(thread)
        
        if self.record_data:
            self.start_recording
            