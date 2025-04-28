import cv2
import numpy as np
import argparse
import yaml

from pipeline import TrafficMonitoringPipeline

def parse_args():
    parser = argparse.ArgumentParser(description="Traffic Monitoring System")
    parser.add_argument('-c', "-config", default="config/config.yaml", help="Config file path")
    parser.add_argument('-v', '--video', default=None, help='Video file path')
    
def main():
    args = parse_args()
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    pipeline = TrafficMonitoringPipeline(config_path=args.config)
    
    try:
        pipeline.start()
        
        if args.display():
            cv2.namedWindow('Traffic Monitoring', cv2.WINDOW_NORMAL)
            
            while True:
                pass
    except:
        pass