import cv2
import numpy as np
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

class GStreamerPipeline:
    def __init__(self, camera_id=0, width=1280, height=720, fps=30, rtsp_url=None):
        """
        Initialize GStreamer pipeline for video capture
        
        Args:
            camera_id: Camera ID for local USB camera
            width: Frame width
            height: Frame height
            fps: Frames per second
            rtsp_url: RTSP URL for IP camera (takes precedence over camera_id if provided)
        """
        Gst.init(None)
        
        self.width = width
        self.height = height
        self.fps = fps
        self.frame = None
        self.running = False
        
        # Create GStreamer pipeline based on source type
        if rtsp_url:
            # RTSP camera source
            self.pipeline_str = (
                f'rtspsrc location={rtsp_url} latency=100 ! '
                f'rtph264depay ! h264parse ! avdec_h264 ! '
                f'videorate ! video/x-raw,framerate={fps}/1 ! '
                f'videoscale ! video/x-raw,width={width},height={height} ! '
                f'videoconvert ! appsink name=sink emit-signals=True max-buffers=1 drop=True'
            )
        else:
            # USB/local camera source
            self.pipeline_str = (
                f'v4l2src device=/dev/video{camera_id} ! '
                f'video/x-raw,width={width},height={height},framerate={fps}/1 ! '
                f'videoconvert ! video/x-raw,format=BGR ! '
                f'appsink name=sink emit-signals=True max-buffers=1 drop=True'
            )
        
        self.pipeline = Gst.parse_launch(self.pipeline_str)
        self.sink = self.pipeline.get_by_name('sink')
        
        # Connect signals
        self.sink.connect('new-sample', self.on_new_sample)
    
    def on_new_sample(self, sink):
        """Callback for new frame arrival"""
        sample = sink.emit('pull-sample')
        if sample:
            buf = sample.get_buffer()
            caps = sample.get_caps()
            
            # Get frame dimensions from caps
            caps_structure = caps.get_structure(0)
            width = caps_structure.get_value('width')
            height = caps_structure.get_value('height')
            
            # Convert Gst.Buffer to numpy array (frame)
            _, map_info = buf.map(Gst.MapFlags.READ)
            frame_data = map_info.data
            self.frame = np.ndarray(
                shape=(height, width, 3),
                buffer=frame_data,
                dtype=np.uint8
            )
            buf.unmap(map_info)
            
            return Gst.FlowReturn.OK
        
        return Gst.FlowReturn.ERROR
    
    def start(self):
        """Start the GStreamer pipeline"""
        self.pipeline.set_state(Gst.State.PLAYING)
        self.running = True
        print(f"Started GStreamer pipeline: {self.pipeline_str}")
    
    def stop(self):
        """Stop the GStreamer pipeline"""
        self.pipeline.set_state(Gst.State.NULL)
        self.running = False
        print("Stopped GStreamer pipeline")
    
    def get_frame(self):
        """Get the latest frame from the pipeline"""
        return self.frame.copy() if self.frame is not None else None


# Example usage
if __name__ == "__main__":
    import time
    
    # Example with USB camera
    # pipeline = GStreamerPipeline(camera_id=0, width=1280, height=720, fps=30)
    
    # Example with RTSP camera
    pipeline = GStreamerPipeline(rtsp_url="rtsp://181.57.169.89:8080//axis-media/media.amp?adjustablelivestream=1")
    
    pipeline.start()
    
    try:
        # Display video for 30 seconds
        start_time = time.time()
        while time.time() - start_time < 30:
            frame = pipeline.get_frame()
            if frame is not None:
                cv2.imshow("GStreamer Stream", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                time.sleep(0.01)  # Small delay if no frame is available
    finally:
        pipeline.stop()
        cv2.destroyAllWindows()