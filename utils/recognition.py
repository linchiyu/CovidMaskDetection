import cv2
import math
import threading
import numpy as np
import time
from multiprocessing import Process, Queue
from .api_request import API
from . import Facenet
from . import distance as dst
import sys
import imutils
import imutils.face_utils
import dlib
from keras.preprocessing import image
import keras
from apscheduler.schedulers.background import BackgroundScheduler

class FaceRecog():
    """face recognition from face_recognition"""
    def __init__(self, api_class=API(), TOLERANCE=0.4, TAM_ROSTO=40, UPDATE_FACELIST_TIME = 180):
        self.api_class = api_class

        self.listaP = []
        self.listaFaceP = []

        self.TOLERANCE = TOLERANCE
        self.TAM_ROSTO = TAM_ROSTO
        self.UPDATE_FACELIST_TIME = UPDATE_FACELIST_TIME

        self.data = {}
        self.new = False

        self.dataQ = Queue()
        self.imageQ = Queue()
        self.stopQ = Queue()
        self.commandQ = Queue()
        self.stopped = False

        self.only_detection = True

        print('face_recog carregado')

    def generate_data(self, found=False, recog=False, idp=-1, name='', 
        coord=(0,0,0,0), encoding=[]):
        return {
            'face_encontrada': found,
            'face_reconhecida': recog,
            'id': idp,
            'nome': name,
            'face_coordenadas': coord,
            'face_encoding': encoding
        }

    def draw(self, image, text=False):
        if self.data.get('face_encontrada', False):
            x, y, w, h = self.data.get('face_coordenadas', (0,0,0,0))
            cv2.rectangle(image, (x, y), (x+w, y+h), (0, 0, 255), 2)
            if text:
                font = cv2.FONT_HERSHEY_DUPLEX
                if self.data.get('face_reconhecida', False):
                    cv2.putText(image, str(self.data.get('nome', '')), (x + 6, y+h - 6), font, 1.0, (255, 255, 255), 1)
                else:
                    cv2.putText(image, "Sem cadastro", (x + 6, y+h - 6), font, 1.0, (255, 255, 255), 1)

        return image

    def extractLargestFace(self, faces):
        largest = None
        largest_size = None
        for (x, y, w, h) in faces:
            if largest == None:
                largest = (x, y, w, h)
                largest_size = math.sqrt((w)**2 + (h)**2)
            else:
                size = math.sqrt((w)**2 + (h)**2)
                if largest_size < size:
                    largest = (x, y, w, h)
                    largest_size = size
        return largest_size, largest

    def camInference(self):
        face_detector = dlib.get_frontal_face_detector()
        sp = dlib.shape_predictor("./data/weights/shape_predictor_5_face_landmarks.dat")
        model = Facenet.loadModel()
        input_shape = model.layers[0].input_shape
        if type(input_shape) == list:
            input_shape = input_shape[0][1:3]
        else:
            input_shape = input_shape[1:3]

        self.updateFaceList()
        scheduler = BackgroundScheduler()
        job = scheduler.add_job(self.updateFaceList, 'interval', args=[], seconds=self.UPDATE_FACELIST_TIME)
        scheduler.start()
        print('iniciando reconhecimento')
        while self.stopQ.empty():
            if not self.commandQ.empty():
                command = self.commandQ.get()
                if command == 'only_detection':
                    self.only_detection = True
                else:
                    self.only_detection = False
            try:
                img_raw = self.imageQ.get(timeout=2)
            except:
                continue
            faces = []

            detections = face_detector(img_raw)
            if len(detections) == 0:
                #nenhuma face detectada
                self.dataQ.put(self.generate_data())
                continue

            for d in detections:
                faces.append(imutils.face_utils.rect_to_bb(d))

            #ao menos uma face detectada, filtrar face principal (maior)
            face_size, face_location = self.extractLargestFace(faces)

            if face_size > self.TAM_ROSTO:
                if self.only_detection:
                    data = self.generate_data(found=True, recog=False, 
                            idp=-1, name='', coord=face_location)
                    self.dataQ.put((data))
                    continue

                (x, y, w, h) = face_location
                img_shape = sp(img_raw, dlib.rectangle(x, y, x+w, y+h))
                face_bgr = dlib.get_face_chip(img_raw, img_shape, size = input_shape[0])
                face_bgr = cv2.resize(face_bgr, input_shape)

                img_pixels = image.img_to_array(face_bgr)
                img_pixels = np.expand_dims(img_pixels, axis = 0)
                img_pixels /= 255

                face_encodings = model.predict(img_pixels)[0,:]

                # See if the face is a match for the known face(s)
                #matches = face_recognition.compare_faces(self.listaFaceP, face_encoding)
                distance = float("inf")
                best_match_index = -1
                for idx, enc in enumerate(self.listaFaceP):
                    cur_distance = dst.findCosineDistance(face_encodings, enc)
                    if cur_distance < distance:
                        distance = cur_distance
                        best_match_index = idx

                if best_match_index >= 0 and distance <= self.TOLERANCE:
                    #pessoa identificada, retornar dados da pessoa
                    data = self.generate_data(found=True, recog=True, 
                        idp=self.listaP[best_match_index].get('id'), 
                        name=self.listaP[best_match_index].get('nome'), 
                        coord=face_location,
                        encoding=face_encodings)
                    self.dataQ.put((data))
                else:
                    #não há lista de pessoas registradas ou a pessoa é desconhecida
                    #fazer reconhecimento de genero e idade e retornar resultado
                    data = self.generate_data(found=True, recog=False, 
                        idp=-1, name='', coord=face_location,
                        encoding=face_encodings)
                    self.dataQ.put((data))
        print('desligando reconhecimento')
        self.stopQ.get()

    def collectData(self, cameraClass):
        #start = time.time()
        while not self.stopped:
            if self.imageQ.empty():
                #image = cameraClass.read()
                self.imageQ.put(cameraClass.read())
            if not self.dataQ.empty():
                self.data = self.dataQ.get()
                self.new = True


    def updateFaceList(self):
        listaP, listaFaceP = self.api_class.getFaceList()
        if listaP:
            self.listaP, self.listaFaceP = listaP, listaFaceP

    def run(self, cameraClass):
        #t = threading.Thread(target=self.camInference,args=(cameraClass,),daemon=True)
        p = Process(target=self.camInference,args=(),daemon=True)
        t = threading.Thread(target=self.collectData,args=(cameraClass,),daemon=True).start()
        p.start()

    def stop(self):
        self.stopped = True
        self.stopQ.put(True)
        time.sleep(5)
        try:
            self.dataQ.close()
        except:
            None
        try:
            self.imageQ.close()
        except:
            None
        try:
            self.stopQ.close()
        except:
            None


if __name__ == '__main__':
    import cameraThread