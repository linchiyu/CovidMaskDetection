import cv2
import numpy as np
from utils import imgutil
from settings import *
#import imgutil

class Interface():
    """docstring for Interface"""
    def __init__(self, path='data/images/'):
        size = self.size = 900
        self.logo = cv2.imread(path+'logo.png', cv2.IMREAD_UNCHANGED)
        self.logo = imgutil.resizeMaintainAspectRatio(self.logo, height=int(size*100/1280))

        self.normal = cv2.imread(path+'background.jpg', cv2.IMREAD_UNCHANGED)
        self.normal = imgutil.resizeMaintainAspectRatio(self.normal, height=size)
        self.insertLogoBottom(self.normal)
        #self.insertText(self.normal)
        
        self.waitMessage = cv2.imread(path+'wait.png', cv2.IMREAD_UNCHANGED)
        self.waitMessage = imgutil.resizeMaintainAspectRatio(self.waitMessage, height=int(size*80/1280))
        self.stopMessage = cv2.imread(path+'stop.png', cv2.IMREAD_UNCHANGED)
        self.stopMessage = imgutil.resizeMaintainAspectRatio(self.stopMessage, height=int(size*80/1280))
        self.passMessage = cv2.imread(path+'pass.png', cv2.IMREAD_UNCHANGED)
        self.passMessage = imgutil.resizeMaintainAspectRatio(self.passMessage, height=int(size*80/1280))
        self.tempMessage = cv2.imread(path+'temperatura.png', cv2.IMREAD_UNCHANGED)
        self.tempMessage = imgutil.resizeMaintainAspectRatio(self.tempMessage, height=int(size*80/1280))
        self.mascMessage = cv2.imread(path+'mascara.png', cv2.IMREAD_UNCHANGED)
        self.mascMessage = imgutil.resizeMaintainAspectRatio(self.mascMessage, height=int(size*80/1280))
        self.alcoolMessage = cv2.imread(path+'alcool.png', cv2.IMREAD_UNCHANGED)
        self.alcoolMessage = imgutil.resizeMaintainAspectRatio(self.alcoolMessage, height=int(size*80/1280))
        self.cartaoMessage = cv2.imread(path+'cartao.png', cv2.IMREAD_UNCHANGED)
        self.cartaoMessage = imgutil.resizeMaintainAspectRatio(self.cartaoMessage, height=int(size*80/1280))
        self.catracaMessage = cv2.imread(path+'catraca.png', cv2.IMREAD_UNCHANGED)
        self.catracaMessage = imgutil.resizeMaintainAspectRatio(self.catracaMessage, height=int(size*80/1280))
        self.limiteMessage = cv2.imread(path+'limite.png', cv2.IMREAD_UNCHANGED)
        self.limiteMessage = imgutil.resizeMaintainAspectRatio(self.limiteMessage, height=int(size*80/1280))
        self.recogMessage = cv2.imread(path+'recog.png', cv2.IMREAD_UNCHANGED)
        self.recogMessage = imgutil.resizeMaintainAspectRatio(self.recogMessage, height=int(size*80/1280))
        self.blockMessage = cv2.imread(path+'block.png', cv2.IMREAD_UNCHANGED)
        self.blockMessage = imgutil.resizeMaintainAspectRatio(self.blockMessage, height=int(size*80/1280))


        self.clean_canvas = self.normal


    def mountImage(self, cam, message='wait'):
        image = self.clean_canvas.copy()

        if cam.shape[0] != int(self.size*930/1280) or cam.shape[1] != int(self.size*700/1280):
            cam = cv2.resize(cam, (int(self.size*700/1280), int(self.size*930/1280)))

        #insert camera image
        x_offset=int(image.shape[1]/2-cam.shape[1]/2)
        y_offset=int(image.shape[0]/2-cam.shape[0]/2)
        y1, y2 = y_offset, y_offset + cam.shape[0]
        x1, x2 = x_offset, x_offset + cam.shape[1]

        image[y1:y2, x1:x2] = cam[:, :]

        #insert text image
        image = self.insertMessage(image, message)


        if image.shape[0] != SCREEN_HEIGHT or image.shape[1] != SCREEN_WIDTH:
            image = cv2.resize(image, (SCREEN_WIDTH, SCREEN_HEIGHT))

        return image

    def insertMessage(self, image, message='wait'):
        if message == 'wait':
            message = self.waitMessage
        elif message == 'pass':
            message = self.passMessage
        elif message == 'stop':
            message = self.stopMessage
        elif message == 'temperatura':
            message = self.tempMessage
        elif message == 'mascara':
            message = self.mascMessage
        elif message == 'alcool':
            message = self.alcoolMessage
        elif message == 'cartao':
            message = self.cartaoMessage
        elif message == 'catraca':
            message = self.catracaMessage
        elif message == 'limite':
            message = self.limiteMessage
        elif message == 'recog':
            message = self.recogMessage
        elif message == 'block':
            message = self.blockMessage
        else: #message == 'wait'
            message = self.waitMessage

        x_offset=int(image.shape[1]/2-message.shape[1]/2)
        y_offset=int((image.shape[0]-message.shape[0])*0.88)
        y1, y2 = y_offset, y_offset + message.shape[0]
        x1, x2 = x_offset, x_offset + message.shape[1]

        alpha_s = message[:, :, 3] / 255.0
        alpha_l = 1.0 - alpha_s

        for c in range(0, 3):
            image[y1:y2, x1:x2, c] = (alpha_s * message[:, :, c] +
                                      alpha_l * image[y1:y2, x1:x2, c])

        return image

    def insertText(self, image, text=''):
        font = cv2.FONT_HERSHEY_TRIPLEX                                                                                 
        cv2.putText(image, text, (60,int(image.shape[0]*0.93)), font, 0.8, (0, 0, 0), 1, cv2.LINE_AA)

        return image



    def insertLogoTop(self, image):
        logo = self.logo
        x_offset=int(image.shape[1]-logo.shape[1]-25)
        y_offset=int(30)
        y1, y2 = y_offset, y_offset + logo.shape[0]
        x1, x2 = x_offset, x_offset + logo.shape[1]

        alpha_s = logo[:, :, 3] / 255.0
        alpha_l = 1.0 - alpha_s

        for c in range(0, 3):
            image[y1:y2, x1:x2, c] = (alpha_s * logo[:, :, c] +
                                      alpha_l * image[y1:y2, x1:x2, c])

        return image

    def insertLogoBottom(self, image):
        logo = self.logo
        x_offset=int(image.shape[1]-logo.shape[1]-40)
        y_offset=int(image.shape[0]-logo.shape[0]-25)
        y1, y2 = y_offset, y_offset + logo.shape[0]
        x1, x2 = x_offset, x_offset + logo.shape[1]

        alpha_s = logo[:, :, 3] / 255.0
        alpha_l = 1.0 - alpha_s

        for c in range(0, 3):
            image[y1:y2, x1:x2, c] = (alpha_s * logo[:, :, c] +
                                      alpha_l * image[y1:y2, x1:x2, c])

        return image


if __name__ == '__main__':
    x = Interface('./data/images/')
    cam = cv2.imread('camera.jpg')
    #cam = cv2.resize(cam, (640, 480))
    cam = cv2.resize(cam, (700, 930))
    frame = cv2.imread('background.jpg',
         cv2.IMREAD_UNCHANGED)
    #image = x.mountImage(cam, message='normal')
    image = x.mountImage(cam, message='positivo')
    x.insertText(image, 'Marlon Machado da Silva Sauro')

    image = imgutil.resizeMaintainAspectRatio(image, height=900)
    cv2.imshow('i', image)



    cv2.waitKey(0)