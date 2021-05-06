import cv2
from threading import Thread, Lock
from queue import Queue
import time
from apscheduler.schedulers.background import BackgroundScheduler
import os
from os import listdir
from os.path import isfile, join
import random
from settings import *

class Banner():
    """banner de propaganda
    shape = formato da propaganda
    pos = posição x, y inicial da propaganda"""
    def __init__(self, shape=(300,300), *args, **kwargs):
        #cv2.namedWindow('banner')
        #cv2.moveWindow('banner', pos[0], pos[1]);
        self.shape = shape
        self.q = Queue()
        self.generico = cv2.imread('data/generico.jpg')
        self.generico = cv2.resize(self.generico, shape)
        self.image = self.generico
        self.path = os.getcwd()
        self.lock = Lock()

        #super().__init__(*args, **kwargs)
        #self.daemon = True

        self.data = {}

        self.count = 0

        scheduler = BackgroundScheduler()
        job = scheduler.add_job(self.update, 'interval', args=[], seconds=TEMPO_REFRESH_BANNER)
        scheduler.start()

        self.stopped = False

    def run(self):
        while True:
            with self.lock:
                cv2.imshow('banner', self.image)
            k = cv2.waitKey(30)
            if k == ord('q') or self.stopped:
                break

    def loadImageList(self):
        path = self.path
        valid_images = [".jpg",".png"]
        onlyfiles = []
        if os.path.exists(path+"/propaganda"):
            for f in os.listdir(path+"/propaganda"):
                ext = os.path.splitext(f)[-1]
                if ext.lower() not in valid_images:
                    continue
                onlyfiles.append(f)
        return onlyfiles

    def getNewImage(self):
        path = self.path
        onlyfiles = self.loadImageList()
        if len(onlyfiles) <= 0:
            return self.generico
        img = cv2.imread(path+"/propaganda/"+onlyfiles[self.count%len(onlyfiles)])
        self.count = self.count + 1
        if self.count > 37203685775807:
            self.count = 0
        return img


    def update(self, elapse=20): #pass images here to fade between
        #print('updating banner')
        with self.lock:
            img1 = self.image
        img2 = self.getNewImage()
        img2 = cv2.resize(img2, self.shape)

        for i in range(0, elapse):
            fadein = i/float(elapse)
            with self.lock:
                self.image = cv2.addWeighted(img1, 1-fadein, img2, fadein, 0)
            time.sleep(0.1)
        with self.lock:
            self.image = img2

    def get(self):
        with self.lock:
            return self.image

    def stop(self):
        self.stopped = True

if __name__ == '__main__':
    x = Banner()
    '''x.start()
    image2 = cv2.imread('data/generico2.jpg')
    k = cv2.waitKey(1200)
    Thread(target=x.update, args=(image2,), daemon=True).start()
    k = cv2.waitKey(0)'''

    img = x.update()

    cv2.imshow('banner', x.image)
    cv2.waitKey(0)