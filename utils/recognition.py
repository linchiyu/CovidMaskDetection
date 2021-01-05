import cv2
import math
import threading
import numpy as np
import time
from multiprocessing import Process, Queue
#from threading import Thread as Process
#from queue import Queue
from .api_request import API
from . import distance as dst
import pandas as pd
from PIL import Image
from . import Facenet
import sys
#from keras.preprocessing import image
#import keras
from apscheduler.schedulers.background import BackgroundScheduler


def alignment_procedure(img, left_eye, right_eye):   
    #this function aligns given face in img based on left and right eye coordinates
    
    left_eye_x, left_eye_y = left_eye
    right_eye_x, right_eye_y = right_eye
    
    #-----------------------
    #find rotation direction
        
    if left_eye_y > right_eye_y:
        point_3rd = (right_eye_x, left_eye_y)
        direction = -1 #rotate same direction to clock
    else:
        point_3rd = (left_eye_x, right_eye_y)
        direction = 1 #rotate inverse direction of clock
    
    #-----------------------
    #find length of triangle edges
    
    a = dst.findEuclideanDistance(np.array(left_eye), np.array(point_3rd))
    b = dst.findEuclideanDistance(np.array(right_eye), np.array(point_3rd))
    c = dst.findEuclideanDistance(np.array(right_eye), np.array(left_eye))
    
    #-----------------------
    
    #apply cosine rule
            
    if b != 0 and c != 0: #this multiplication causes division by zero in cos_a calculation
        
        cos_a = (b*b + c*c - a*a)/(2*b*c)
        angle = np.arccos(cos_a) #angle in radian
        angle = (angle * 180) / math.pi #radian to degree
        
        #-----------------------
        #rotate base image
        
        if direction == -1:
            angle = 90 - angle
        
        img = Image.fromarray(img)
        img = np.array(img.rotate(direction * angle))
    
    #-----------------------
    
    return img #return img anyway


class FaceRecog():
    """face recognition from face_recognition"""
    def __init__(self, api_class=API(), cameraClass=None, TOLERANCE=0.4, TAM_ROSTO=40, UPDATE_FACELIST_TIME = 180):
        self.api_class = api_class
        self.cameraClass = cameraClass

        #load detection
        self.face_detector = cv2.dnn.readNetFromCaffe(
            "./data/weights/deploy.prototxt", 
            "./data/weights/res10_300x300_ssd_iter_140000.caffemodel"
        )

        self.eye_detector = cv2.CascadeClassifier("./data/weights/haarcascade_eye.xml")

        self.ssd_labels = ["img_id", "is_face", "confidence", "left", "top", "right", "bottom"]
        self.target_size = (300, 300)

        img_raw = self.cameraClass.read()
        original_size = img_raw.shape
        self.aspect_ratio_x = (original_size[1] / self.target_size[1])
        self.aspect_ratio_y = (original_size[0] / self.target_size[0])


        #load recognition
        self.sess = Facenet.loadModel()

        self.input_shape = (160, 160)

        self.listaP = []
        self.listaFaceP = []

        self.TOLERANCE = TOLERANCE
        self.TAM_ROSTO = TAM_ROSTO
        self.UPDATE_FACELIST_TIME = UPDATE_FACELIST_TIME

        self.updateFaceList()
        scheduler = BackgroundScheduler()
        job = scheduler.add_job(self.updateFaceList, 'interval', args=[], seconds=self.UPDATE_FACELIST_TIME)
        scheduler.start()

        self.data = {}
        self.new = False
        self.alive = False

        self.stopped = False

        self.only_detection = True

        print('face_recog carregado')

    def generate_data(self, found=False, recog=False, idp=-1, name='', 
        coord=(0,0,0,0), encoding=[]):
        self.data = {
            'face_encontrada': found,
            'face_reconhecida': recog,
            'id': idp,
            'nome': name,
            'face_coordenadas': coord,
            'face_encoding': encoding
        }
        self.new = True
        return self.data

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

    def align_face(self, img):
        detected_face_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) #eye detector expects gray scale image
        eyes = self.eye_detector.detectMultiScale(detected_face_gray)
        
        if len(eyes) >= 2:
            #find the largest 2 eye
            base_eyes = eyes[:, 2]
            
            items = []
            for i in range(0, len(base_eyes)):
                item = (base_eyes[i], i)
                items.append(item)
            
            df = pd.DataFrame(items, columns = ["length", "idx"]).sort_values(by=['length'], ascending=False)
            
            eyes = eyes[df.idx.values[0:2]] #eyes variable stores the largest 2 eye
            
            #-----------------------
            #decide left and right eye
            
            eye_1 = eyes[0]; eye_2 = eyes[1]
            
            if eye_1[0] < eye_2[0]:
                left_eye = eye_1; right_eye = eye_2
            else:
                left_eye = eye_2; right_eye = eye_1
            
            #-----------------------
            #find center of eyes
            
            left_eye = (int(left_eye[0] + (left_eye[2] / 2)), int(left_eye[1] + (left_eye[3] / 2)))
            right_eye = (int(right_eye[0] + (right_eye[2]/2)), int(right_eye[1] + (right_eye[3]/2)))
            
            img = alignment_procedure(img, left_eye, right_eye)
            
        return img #return img anyway

    def camInference(self):
        self.alive = True
        print('iniciando reconhecimento')
        while not self.data.get('face_reconhecida', False) and not self.stopped:
            try:
                img_raw = self.cameraClass.read()
            except:
                continue
            faces = []
            
            img = cv2.resize(img_raw, self.target_size)

            img = cv2.dnn.blobFromImage(image = img)
            self.face_detector.setInput(img)
            detections = self.face_detector.forward()

            detections_df = pd.DataFrame(detections[0][0], columns = self.ssd_labels)
        
            detections_df = detections_df[detections_df['is_face'] == 1] #0: background, 1: face
            detections_df = detections_df[detections_df['confidence'] >= 0.90]
            
            detections_df['left'] = (detections_df['left'] * 300).astype(int)
            detections_df['bottom'] = (detections_df['bottom'] * 300).astype(int)
            detections_df['right'] = (detections_df['right'] * 300).astype(int)
            detections_df['top'] = (detections_df['top'] * 300).astype(int)

            if detections_df.shape[0] == 0:
                self.generate_data()
                #self.dataQ.put(self.generate_data())
                continue

            for instance in detections_df.iloc:
                x = int(instance["left"]*self.aspect_ratio_x)
                y = int(instance["top"]*self.aspect_ratio_y)
                w = int(instance["right"]*self.aspect_ratio_x)-x
                h = int(instance["bottom"]*self.aspect_ratio_y)-y

                faces.append((x,y,w,h))

            #ao menos uma face detectada, filtrar face principal (maior)
            face_size, face_location = self.extractLargestFace(faces)

            if face_size > self.TAM_ROSTO:
                if self.only_detection:
                    data = self.generate_data(found=True, recog=False, 
                            idp=-1, name='', coord=face_location)
                    #self.dataQ.put((data))
                    continue

                (x, y, w, h) = face_location
                face_bgr = img_raw[y:y+h, x:x+w]
                face_bgr = self.align_face(face_bgr)

                face_bgr = cv2.resize(face_bgr, self.input_shape)
                #img_pixels = image.img_to_array(face_bgr)
                img_pixels = np.asarray(face_bgr, dtype='float32')
                img_pixels = np.expand_dims(img_pixels, axis = 0)
                img_pixels /= 255

                softmax_tensor = self.sess.graph.get_tensor_by_name('import/Bottleneck_BatchNorm_2/cond/Merge:0')
                predictions = self.sess.run(softmax_tensor, {'import/input_1_2:0': img_pixels})
                face_encodings = predictions[0,:]

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
                    #self.dataQ.put((data))
                else:
                    #não há lista de pessoas registradas ou a pessoa é desconhecida
                    #fazer reconhecimento de genero e idade e retornar resultado
                    data = self.generate_data(found=True, recog=False, 
                        idp=-1, name='', coord=face_location,
                        encoding=face_encodings)
                    #self.dataQ.put((data))
        print('desligando reconhecimento')
        self.alive = False

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

    def runThreadRecog(self):
        threading.Thread(target=self.camInference,args=(),daemon=True).start()

    def stop(self):
        self.stopped = True
        '''self.stopQ.put(True)
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
            None'''


if __name__ == '__main__':
    import cameraThread