import numpy as np
import cv2
import time
import sys
from pymba import Vimba, VimbaException


""" AVT Camera Interface using pymba """
class AVTCamera():
    def __init__(self, width=800, height=600):
        self.cams = None
        self.width = width
        self.height = height

    def init_cameras(self):
        # vimba object
        vimba = Vimba()
        # Start vimba system
        vimba.startup()
        vmFactory = vimba.camera_ids()
        # Get connected cameras
        self.cams  = [vimba.camera(id) for id in vmFactory]
        if len(self.cams) == 0:
            self.cams = None
            raise OSError("No camera present.")
        for idx, cam in enumerate(self.cams):
            print("Device {} ID: {}".format(idx, cam))
            try:
                cam.open()
                feature_h = cam.feature("Height")
                feature_h.value = self.height
                feature_w = cam.feature("Width")
                feature_w.value = self.width
                cam.arm('SingleFrame')
            except VimbaException as e:
                if e.error_code == VimbaException.ERR_TIMEOUT:
                    print(e)
                    cam.disarm()
                    cam.arm('SingleFrame')
                elif e.error_code == VimbaException.ERR_DEVICE_NOT_OPENED:
                    print(e)
                    cam.open()
                    cam.arm('SingleFrame')

    def startStreaming(self):
        print ("Starting to stream camera...")
        self.init_cameras()
        print(type(self.cams))
        print("len of cams {}" .format(len(self.cams)))

        #if self.cams:
        #    self.setROI(self.width, self.height)

    def convertFrame(self, frame):
        camera_frame_size = len(frame.buffer_data())
        frame_pixel_format = frame.pixel_format
        Width = self.width
        Height = self.height
        print("Frame size: %d,  Image Resolution: %dx%d,  pixel_format: %s " % (
        camera_frame_size, Width, Height, frame_pixel_format))
        data_bytes = frame.buffer_data()

        if (frame_pixel_format == "Mono8" or frame_pixel_format == "BayerRG8" or frame_pixel_format == "BayerGR8"):
            frame_8bits = np.ndarray(buffer=data_bytes, dtype=np.uint8, shape=(Height, Width))

        elif (frame_pixel_format == "BayerRG12" or frame_pixel_format == "Mono10" or frame_pixel_format == "Mono12" or frame_pixel_format == "Mono14"):
            data_bytes = np.frombuffer(data_bytes, dtype=np.uint8)
            pixel_even = data_bytes[0::2]
            pixel_odd = data_bytes[1::2]

            # Convert bayer16 to bayer8 / Convert Mono12/Mono14 to Mono8
            if (frame_pixel_format == "Mono14"):
                pixel_even = np.right_shift(pixel_even, 6)
                pixel_odd = np.left_shift(pixel_odd, 2)
            elif (frame_pixel_format == "Mono10"):
                pixel_even = np.right_shift(pixel_even, 2)
                pixel_odd = np.left_shift(pixel_odd, 6)
            else:
                pixel_even = np.right_shift(pixel_even, 4)
                pixel_odd = np.left_shift(pixel_odd, 4)
            frame_8bits = np.bitwise_or(pixel_even, pixel_odd).reshape(Height, Width)

        elif (frame_pixel_format == "BayerRG12Packed" or frame_pixel_format == "Mono12Packed" or frame_pixel_format == "BayerGR12Packed"):
            data_bytes = np.frombuffer(data_bytes, dtype=np.uint8)
            size = len(data_bytes)
            index = []
            for i in range(0, size, 3):
                index.append(i + 1)

            data_bytes = np.delete(data_bytes, index)
            frame_8bits = data_bytes.reshape(Height, Width)

        elif (frame_pixel_format == "RGB8Packed" or frame_pixel_format == "BGR8Packed"):
            frame_8bits = np.ndarray(buffer=frame.buffer_data(), dtype=np.uint8, shape=(Height, Width * 3))

        else:
            # Note: wait to do -- other format, such as YUV411Packed, YUV422Packed, YUV444Packed
            frame_8bits = np.ndarray(buffer=frame.buffer_data(), dtype=np.uint8, shape=(Height, Width))

        return frame_8bits

    def getFrame(self):
        raw_frame = self.cams[0].acquire_frame()
        frame = self.convertFrame(raw_frame)
        if self.cams:
            return frame
        else:
            print ("Failed to capture frame!")
            return None

    def isOpened(self):
        if self.cams:
            return True
        else:
            return False

    def setROI(self, width: int, height: int) -> None:
        for idx, cam in enumerate(self.cams):
            print("setROI: Device {} ID: {}".format(idx, cam))
            feature_h = cam.feature("Height")
            feature_h.value = height
            feature_w = cam.feature("Width")
            feature_w.value = width

    def __del__(self):
        if self.cams:
            for idx, cam in enumerate(self.cams):
                print("Del: Device {} ID: {}".format(idx, cam))
                cam.disarm()
                cam.close()
            Vimba().shutdown()
            self.cams = None
        print ("Cleanly exited AVTCamera")


