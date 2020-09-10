import cv2
import math
import threading
import numpy as np
import face_recognition
import time
from multiprocessing import Process, Queue

class Person():
    def __init__(self):
        self.id = None
        self.nome = None
        self.rfid = None
        self.face = None
        self.location = []

        self.mascara = False
        self.temperatura = False
        self.alcool = False
        self.rfid = False

        self.timeIni = time.time()

    def update(self, idP, nome, rfid, face, location):
        if idP == None or idP == 0:
            return
        if idP == self.id:
            self.timeIni = time.time()
        else:
            self.timeIni = time.time()
            self.id = idP
            self.nome = nome
            self.rfid = rfid
            self.face = face
            self.location = location

            self.mascara = False
            self.temperatura = False
            self.alcool = False
            self.rfid = False

    def draw(self, image):
        #results is a vector with [class_id, conf, xmin, ymin, xmax, ymax]
        if len(self.location) == 0:
            return image
        for (top, right, bottom, left) in self.location:
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a box around the face
            cv2.rectangle(image, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(image, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(image, self.nome, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
        return image



class FaceRecog():
    """face recognition from face_recognition"""
    def __init__(self, listaId, listaNome, listaRfid, listaFaceP, api_class, TAM_ROSTO=60):
        self.listaId = listaId
        self.listaNome = listaNome
        self.listaRfid = listaRfid
        self.listaFaceP = listaFaceP

        self.TAM_ROSTO = TAM_ROSTO

        self.api_class = api_class

        self.face_locations = []
        self.largestFace = None
        self.largestSize = 0

        self.id = -1
        self.nome = None
        self.rfid = None
        self.face = None

        self.dataQ = Queue()
        self.imageQ = Queue()
        self.stopQ = Queue()
        self.stop = False

    def getPerson(self):
        (idP, nome, rfid, face, location) = (self.id, self.nome, self.rfid, self.face, self.face_locations)
        self.id = None
        self.nome = None
        self.rfid = None
        self.face = None
        self.location = None
        return idP, nome, rfid, face, location

    def draw(self, image):
        #results is a vector with [class_id, conf, xmin, ymin, xmax, ymax]
        if len(self.face_locations) == 0:
            return image
        for (top, right, bottom, left) in self.face_locations:
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a box around the face
            cv2.rectangle(image, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(image, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(image, self.nome, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
        return image

    def extractLargestFace(self, faces):
        largest = None
        largest_size = None
        for (top, right, bottom, left) in faces:
            if largest == None:
                largest = (top, right, bottom, left)
                largest_size = math.sqrt((bottom-top)**2 + (right-left)**2)
            else:
                size = math.sqrt((bottom-top)**2 + (right-left)**2)
                if largest_size < size:
                    largest = (top, right, bottom, left)
                    largest_size = size
        self.face_locations = [largest]
        self.largestSize = largest_size

    def camInference(self):
        start = time.time()
        while self.stopQ.empty():
            if len(self.listaId) <= 0:
                if time.time() - start > 10:
                    self.listaId, self.listaNome, self.listaRfid, self.listaFaceP = self.api_class.getFaceList()
                    start = time.time()
                continue
            img_raw = self.imageQ.get()
            small_frame = cv2.resize(img_raw, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = small_frame[:, :, ::-1]
            faces = face_recognition.face_locations(rgb_small_frame)
            if len(faces) > 0:
                self.extractLargestFace(faces)
                if self.largestSize > self.TAM_ROSTO:
                    face_encodings = face_recognition.face_encodings(rgb_small_frame, self.face_locations)
                    for face_encoding in face_encodings:
                        # See if the face is a match for the known face(s)
                        matches = face_recognition.compare_faces(self.listaFaceP, face_encoding)

                        face_distances = face_recognition.face_distance(self.listaFaceP, face_encoding)
                        try:
                            best_match_index = np.argmin(face_distances)
                        except:
                            best_match_index = 0
                        if matches[best_match_index]:
                            first_match_index = best_match_index
                            data = (self.listaId[first_match_index], self.listaNome[first_match_index],
                                self.listaRfid[first_match_index], self.listaFaceP[first_match_index],
                                self.face_locations, self.largestSize)
                            try:
                                self.dataQ.get_nowait()
                            except:
                                None
                            self.dataQ.put(data)
                            self.id = self.listaId[first_match_index]
                            self.nome = self.listaNome[first_match_index]
                            self.rfid = self.listaRfid[first_match_index]
                            self.face = self.listaFaceP[first_match_index]
                        else:
                            data = (-1, 'Não identificado', '0', [], self.face_locations, self.largestSize)
                            try:
                                self.dataQ.get_nowait()
                            except:
                                None
                            self.dataQ.put(data)
                            self.id = 0
                            self.nome = 'desconhecido'
                            self.rfid = '0'
                            self.face = []
            else:
                data = (-1, 'Não identificado', '0', [], self.face_locations, self.largestSize)
                try:
                    self.dataQ.get_nowait()
                except:
                    None
                self.dataQ.put(data)
                self.id = 0
                self.nome = 'desconhecido'
                self.rfid = '0'
                self.face = []

            time.sleep(0.2)
            if time.time() - start > 30:
                self.listaId, self.listaNome, self.listaRfid, self.listaFaceP = self.api_class.getFaceList()
                start = time.time()

    def collectData(self, cameraClass):
        start = time.time()
        while not self.stop:
            if not self.dataQ.empty():
                data = self.dataQ.get()
                self.id, self.nome, self.rfid, self.face, self.face_locations, self.largestSize = data

            if self.imageQ.empty():
                self.imageQ.put(cameraClass.read())
            time.sleep(0.1)
            if time.time() - start > 30:
                self.listaId, self.listaNome, self.listaRfid, self.listaFaceP = self.api_class.getFaceList()
                start = time.time()
        self.stopQ.put(True)


    def run(self, cameraClass):
        #t = threading.Thread(target=self.camInference,args=(cameraClass,),daemon=True)
        p = Process(target=self.camInference,args=(),daemon=True)
        t = threading.Thread(target=self.collectData,args=(cameraClass,),daemon=True).start()
        p.start()