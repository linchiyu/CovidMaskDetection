from apscheduler.schedulers.background import BackgroundScheduler
import cv2
import numpy as np
import urllib.request
import json
from json import JSONEncoder

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

def url_to_image(url):
    # download the image, convert it to a NumPy array, and then read
    # it into OpenCV format
    resp = urllib.request.urlopen(url)
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    # return the image
    return image

class Updater():
    def __init__(self, api_class, detector, recog, UPDATE_SERVER_FACES):
        self.UPDATE_SERVER_FACES = UPDATE_SERVER_FACES
        self.alive = False
        self.api_class = api_class
        self.detector = detector
        self.recog = recog

        scheduler = BackgroundScheduler()
        job = scheduler.add_job(self.update_all_faces, 'interval', args=[], 
            seconds=self.UPDATE_SERVER_FACES)
        scheduler.start()

    def update_all_faces(self):
        if self.alive:
            return

        self.alive = True

        #get all unprocessed persons from api
        persons = self.api_class.getProcessList()
        #print(persons)

        qtde_att = 0

        for p in persons:
            #download the person image
            try:
                image = url_to_image(p.get('foto'))
            except:
                print('erro na imagem ' + str(p.get('id')))
                self.api_class.updateProcessedFace(p.get('id'), json.dumps({"face": []}, cls=NumpyArrayEncoder), False)
                continue

            print('processando imagem')
            #find his face
            _, _, face_img = self.detector.get_face(image, color='bgr')

            encoding = self.recog.encode_face(face_img)

            #print(encoding)

            #upload back the result to the server
            if len(encoding) > 0:
                valida = True
            else:
                valida = False
            numpyData = {"face": encoding}
            #print(numpyData)
            encodedNumpyData = json.dumps(numpyData, cls=NumpyArrayEncoder)
            #print(encodedNumpyData)
            #print('atualizando imagem')
            self.api_class.updateProcessedFace(p.get('id'), encodedNumpyData, valida)
            qtde_att += 1

        if qtde_att > 0:
            self.recog.updateFaceList()

        self.alive = False

if __name__ == '__main__':
    image = url_to_image('http://localhost:8000/media/background_x9xJdgg.jpg')