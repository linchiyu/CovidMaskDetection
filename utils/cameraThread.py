from threading import Thread
from threading import Lock
import cv2
import numpy as np
import sys
import time

class PiVideoStream:
    """
    Pi Camera initialize then stream and read the first video frame from stream
    """
    def __init__(self, resolution=(640, 480),
                 framerate=32, rotation=0,
                 hflip=True, vflip=False):
        try:
            from picamera.array import PiRGBArray
            from picamera import PiCamera
            self.camera = PiCamera()
        except:
            self.stop()
            raise RuntimeError('picamera start failed.')
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.camera.awb_mode = 'fluorescent'
        self.rotation = rotation
        self.camera.hflip = hflip
        self.camera.vflip = vflip
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture,
                                                     format="bgr",
                                                     use_video_port=True)
        self.read_lock = Lock()
        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.stopped = False

    def start(self):
        """ start the thread to read frames from the video stream """
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        """ keep looping infinitely until the thread is stopped """
        for f in self.stream:
            # if the thread indicator variable is set, stop the thread
            # and release camera resources
            if self.stopped:
                self.stream.close()
                self.rawCapture.close()
                self.camera.close()
                return
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            frame = f.array
            self.rawCapture.truncate(0)
            if self.rotation == 0:
                None
            elif self.rotation == 90:
                frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            elif self.rotation == 180:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            elif self.rotation == 270:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
            with self.read_lock:
                self.frame = frame
        self.stop()

    def read(self):
        """ return the frame most recently read """
        if self.stopped:
            raise RuntimeError('Failed to read from camera. Camera stopped.')
        with self.read_lock:
            frame = self.frame.copy()
        return frame

    def stop(self):
        """ indicate that the thread should be stopped """
        self.stopped = True
        time.sleep(3)

#------------------------------------------------------------------------------
class WebcamVideoStream:
    """
    WebCam initialize then stream and read the first video frame from stream
    """
    def __init__(self, cam_src=0, cam_width=640,
                 cam_height=480, rotation=0):
        try:
            self.webcam = cv2.VideoCapture(cam_src)
        except:
            self.stop()
            print ("Erro na camera! Verifique se a camera", cam_src, "está instalada!")
            raise RuntimeError("Erro na leitura da camera! Verifique se a camera", cam_src, "está instalada!")
        self.webcam.set(3, cam_width)
        self.webcam.set(4, cam_height)
        self.rotation = rotation
        (self.grabbed, self.frame) = self.webcam.read()
        if not self.grabbed:
            self.frame = np.zeros((cam_height, cam_width, 3))
        self.read_lock = Lock()
        # initialize the variable used to indicate if the thread should
        # be stopped
        self.stopped = False

    def start(self):
        """ start the thread to read frames from the video stream """
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        """ keep looping infinitely until the thread is stopped """
        erro = 0
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                self.webcam.release()
                return
            # otherwise, read the next frame from the webcam stream
            grabbed, frame = self.webcam.read()
            if grabbed:
                erro = 0
                if self.rotation == 0:
                    None
                elif self.rotation == 90:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                elif self.rotation == 180:
                    frame = cv2.rotate(frame, cv2.ROTATE_180)
                elif self.rotation == 270:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

                #mirror the image
                frame = cv2.flip(frame, 1)

                with self.read_lock:
                    self.grabbed = grabbed
                    self.frame = frame
            else:
                erro = erro + 1
                if erro >= 10:
                    self.stop()
                    raise RuntimeError('Failed to read from camera')
                time.sleep(0.5)
            
    def read(self):
        """ return the frame most recently read """
        if self.stopped:
            raise RuntimeError('Failed to read from camera. Camera stopped.')
        with self.read_lock:
            frame = self.frame.copy()
        return frame

    def stop(self):
        """ indicate that the thread should be stopped """
        self.stopped = True
        time.sleep(1)

def iniciarCamera(camera=0, width=640, height=480, rotation=0):
    try:
        if camera == 'PI' or camera == 'pi':
            print("Iniciando Pi Camera ....")
            cap = PiVideoStream(resolution=(width, height), rotation=rotation).start()
            time.sleep(2.0)  # Allow PiCamera time to initialize
        else:
            print("Iniciando Camera USB: ", str(camera))
            cap = WebcamVideoStream(cam_src=camera, 
                cam_width=width, cam_height=height, 
                rotation=rotation).start()
            time.sleep(2.0) # Allow WebCam time to initialize
        return cap
    except Exception:
        print("Erro na abertura da camera")
        raise

if __name__ == '__main__':
    cam = iniciarCamera(camera=1, width=640, height=480, rotation=0)
    #cam = cv2.VideoCapture(1)
    while True:
        image = cam.read()
        cv2.imshow('image', image)
        k = cv2.waitKey(50) & 0xFF
        if k == ord("q") or k == ord("Q") or k == 27:
            break
    cam.stop()
    cv2.destroyAllWindows()