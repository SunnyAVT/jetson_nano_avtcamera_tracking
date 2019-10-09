import tensorflow as tf
import numpy as np
import cv2
import tensorflow.contrib.tensorrt as trt
import time
import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
from src.avt_camera import AVTCamera
from src.object_detector import ObjectDetection

""" Jetson Live Object Detector """
class JetsonLiveObjectDetection():
    def __init__(self, model, debug=False, fps = 10.):
        self.debug = debug
        #self.camera = AVTCamera(1280, 1024)
        self.camera = AVTCamera(640, 480)
        self.model = model
        self.rate = float(1. / fps)
        self.detector = ObjectDetection('./data/' + self.model)

    def _visualizeDetections(self, img, scores, boxes, classes, num_detections):
        cols = img.shape[1]
        rows = img.shape[0]
        detections = []

        for i in range(num_detections):
            bbox = [float(p) for p in boxes[i]]
            score = float(scores[i])
            classId = int(classes[i])
            if score > 0.5:
                x = int(bbox[1] * cols)
                y = int(bbox[0] * rows)
                right = int(bbox[3] * cols)
                bottom = int(bbox[2] * rows)
                thickness = int(4 * score)
                cv2.rectangle(img, (x, y), (right, bottom), (125,255, 21), thickness=thickness)
                detections.append(self.detector.labels[str(classId)])

        print("Debug: Found objects: " + str(' '.join(detections)) + ".")
        cv2.imshow('AVT Live Detection', img)

    def start(self):
        print ("Starting Live object detection, may take a few minutes to initialize...")
        self.camera.startStreaming()
        self.detector.initializeSession()

        if not self.camera.isOpened():
            print ("Camera has failed to open")
            exit(-1)
        elif self.debug:
            cv2.namedWindow("Jetson Live Detection", cv2.WINDOW_AUTOSIZE)
    
        while True:
            curr_time = time.time()

            frame_pixel_format, img = self.camera.getFrame()
            #input must be color, convert gray to color here -- Sunny notice
            if (frame_pixel_format == "Mono8" or frame_pixel_format == "Mono10" or frame_pixel_format == "Mono12" or frame_pixel_format == "Mono14"):
                colorImg = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            elif (frame_pixel_format == "BayerRG8" or frame_pixel_format == "BayerRG12" or frame_pixel_format == "BayerRG12Packed"):
                colorImg = cv2.cvtColor(img, cv2.COLOR_BAYER_RG2RGB )
            elif (frame_pixel_format == "BayerGR8" or frame_pixel_format == "BayerGR12" or frame_pixel_format == "BayerGR12Packed"):
                colorImg = cv2.cvtColor(img, cv2.COLOR_BAYER_GR2RGB )
            elif (frame_pixel_format == "RGB8Packed" or frame_pixel_format == "BGR8Packed"):
                RGBImg = img.reshape(Height, Width, 3)
                colorImg = cv2.cvtColor(RGBImg, cv2.COLOR_BGR2RGB)
            else:
                print("Not supported image format")
                exit(-1)

            #colorImg = cv2.resize(colorImg, (600, 400))
            #cv2.imshow("Cam", colorImg)
            #keyCode = cv2.waitKey(20)
            #time.sleep(2)
            scores, boxes, classes, num_detections = self.detector.detect(colorImg)
            #scores, boxes, classes, num_detections = self.detector.detect(colorImg)

            if self.debug:
                self._visualizeDetections(img, scores, boxes, classes, num_detections)
                print ("Debug: Running at: " + str(1.0/(time.time() - curr_time)) + " Hz.")

            if cv2.waitKey(1) == ord('q'):
                break

            # throttle to rate
            capture_duration = time.time() - curr_time
            sleep_time = self.rate - capture_duration
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        cv2.destroyAllWindows()
        self.camera.__del__()
        self.detector.__del__()
        print ("Exiting...")
        return



if __name__ == "__main__":
    debug = True
    model = 'ssd_mobilenet_v1_coco_trt_graph.pb'
    if len(sys.argv) > 2:
        debug = sys.argv[2]
        model = sys.argv[1]
    live_detection = JetsonLiveObjectDetection(model=model, debug=debug)
    live_detection.start()
    

