import cv2
import logging

class VideoCapture:
    def __init__(self, source=0, width=1280, height=720, fps=30):
        """ Initialize video capture
        
        """
        self.source = source
        self.width = width
        self.height = height
        self.fps = 0
        self.cap = None
        
    
    def start(self):
        try:
            self.cap = cv2.VideoCapture(self.source)
            if isinstance(self.source, int):
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            return self.cap.isOpened()
        except:
            pass
        
    def read(self):
        """Read frame from video

        Returns:
            _type_: _description_
        """
        if self.cap is None:
            return False, None
        
        ret, frame = self.cap.read()
        
        if ret:
            self.last_frame = frame
        
        return ret, frame
    
    