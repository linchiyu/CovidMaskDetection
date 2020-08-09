import cv2
import numpy as np
from utils import imgutil

class Interface():
    """docstring for Interface"""
    def __init__(self, path='data/images/'):
        self.waitMessage = cv2.imread(path+'wait.png', cv2.IMREAD_UNCHANGED)
        self.waitMessage = imgutil.resizeMaintainAspectRatio(self.waitMessage, height=60)
        self.stopMessage = cv2.imread(path+'stop.png', cv2.IMREAD_UNCHANGED)
        self.stopMessage = imgutil.resizeMaintainAspectRatio(self.stopMessage, height=60)
        self.passMessage = cv2.imread(path+'pass.png', cv2.IMREAD_UNCHANGED)
        self.passMessage = imgutil.resizeMaintainAspectRatio(self.passMessage, height=60)
        self.tempMessage = cv2.imread(path+'temp.png', cv2.IMREAD_UNCHANGED)
        self.tempMessage = imgutil.resizeMaintainAspectRatio(self.tempMessage, height=60)
        self.fimMessage = cv2.imread(path+'fim.png', cv2.IMREAD_UNCHANGED)
        self.fimMessage = imgutil.resizeMaintainAspectRatio(self.fimMessage, height=60)

        self.logo = cv2.imread(path+'logo.png', cv2.IMREAD_UNCHANGED)
        self.logo = imgutil.resizeMaintainAspectRatio(self.logo, height=80)
        self.logo2 = cv2.imread(path+'logo2.png', cv2.IMREAD_UNCHANGED)
        self.logo2 = imgutil.resizeMaintainAspectRatio(self.logo2, height=80)

        
    def insertMessage(self, image, message):
        if message == 'pass':
            message = self.passMessage
        elif message == 'stop':
            message = self.stopMessage
        elif message == 'temperatura':
            message = self.tempMessage
        elif message == 'catraca':
            message = self.fimMessage
        else: #message == 'wait'
            message = self.waitMessage

        x_offset=int(image.shape[1]/2-message.shape[1]/2)
        y_offset=int(image.shape[0]-message.shape[0]-70)
        y1, y2 = y_offset, y_offset + message.shape[0]
        x1, x2 = x_offset, x_offset + message.shape[1]

        alpha_s = message[:, :, 3] / 255.0
        alpha_l = 1.0 - alpha_s

        for c in range(0, 3):
            image[y1:y2, x1:x2, c] = (alpha_s * message[:, :, c] +
                                      alpha_l * image[y1:y2, x1:x2, c])

        return image

    def insertLogo(self, image):
        logo = self.logo
        x_offset=int(image.shape[1]-logo.shape[1]-5)
        y_offset=int(image.shape[0]-logo.shape[0]-5)
        y1, y2 = y_offset, y_offset + logo.shape[0]
        x1, x2 = x_offset, x_offset + logo.shape[1]

        alpha_s = logo[:, :, 3] / 255.0
        alpha_l = 1.0 - alpha_s

        for c in range(0, 3):
            image[y1:y2, x1:x2, c] = (alpha_s * logo[:, :, c] +
                                      alpha_l * image[y1:y2, x1:x2, c])

        return image

    def insertLogo2(self, image):
        logo = self.logo2
        x_offset=int(5)
        y_offset=int(image.shape[0]-logo.shape[0]-5)
        y1, y2 = y_offset, y_offset + logo.shape[0]
        x1, x2 = x_offset, x_offset + logo.shape[1]

        alpha_s = logo[:, :, 3] / 255.0
        alpha_l = 1.0 - alpha_s

        for c in range(0, 3):
            image[y1:y2, x1:x2, c] = (alpha_s * logo[:, :, c] +
                                      alpha_l * image[y1:y2, x1:x2, c])

        return image


if __name__ == '__main__':

    image = imgutil.createColorCanvas(640,480,(0,0,0))

    CANVAS_WIDTH = 100
    CANVAS_HEIGHT = 10
    image = cv2.copyMakeBorder(image,CANVAS_HEIGHT,CANVAS_HEIGHT,CANVAS_WIDTH,CANVAS_WIDTH,
        cv2.BORDER_CONSTANT,value=(85,201,0))

    i = Interface(path='./data/images/')

    image = i.insertMessage(image, 'pass')

    image = i.insertLogo(image)
    image = i.insertLogo2(image)

    image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

    cv2.imshow('image', image)

    cv2.waitKey(0)