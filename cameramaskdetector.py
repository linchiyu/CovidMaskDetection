import cv2
from utils import cameraThread
from utils.interface import Interface
from utils.soundManager import SoundManager
import time
from settings import *
import uuid
import hashlib, binascii, os
import logging
import datetime
from utils import banco
from utils import usbcontroller
from utils.banner import Banner
from utils.iocontroller import IoManager
if TF_LITE:
    from utils.face_class import MaskDetectorLite as MaskDetector
else:
    from utils.face_class import MaskDetector

def get_id():
    # Extract serial from cpuinfo file
    cpuserial = "0000000000000000"
    try:
        if 'nt' in os.name: #windows
            cpuserial = uuid.UUID(int=uuid.getnode())
        else:
            f = open('/proc/cpuinfo','r')
            for line in f:
                if line[0:6]=='Serial':
                    cpuserial = line[10:26]
            f.close()
    except:
        cpuserial = "ERROR000000000"

    return cpuserial

def verify_key():
    """Verify a stored password against one provided by user"""
    provided_password = str(get_id())
    f = open("data/key", "r")
    stored_password = f.read()
    f.close()
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', 
                                  provided_password.encode('utf-8'), 
                                  salt.encode('ascii'), 
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password

def videoMain():
    GREEN = (85,201,0)
    RED = (2,1,211)
    YELLOW = (8,191,253)
    
    cam = cameraThread.iniciarCamera(camera=CAMERA, width=WIDTH, height=HEIGHT, rotation=ROTATION)
    sound = SoundManager()
    sound.run()
    detector = MaskDetector(CONFIDENCE)
    detector.run(cam)
    interface = Interface()
    iopin = IoManager()
    iopin.run()
    dbm = banco.DBManager()
    usbc = usbcontroller.USBDetector()

    if PROPAGANDA:
        banner = Banner(shape=(SCREEN_WIDTH, SCREEN_HEIGHT))

    if FULL_SCREEN:
        cv2.namedWindow('ArticfoxMaskDetection', cv2.WINDOW_FREERATIO)
        cv2.setWindowProperty('ArticfoxMaskDetection', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    message = 'wait'
    color = YELLOW
    last = message

    played_sound_time = 0
    cur_time = 0
    play = False
    reset = False

    usando_mascara = "nao"
    while True:
        image = cam.read()

        cur_time = time.time()

        if detector.new:
            detector.new = False
            if detector.largest_predict == None: #wait
                if last == 'wait':
                    message = 'wait'
                    color = YELLOW
                    reset = True
                last = 'wait'
            elif detector.largest_predict[0] == 0: #pass/com_mascara
                if last == 'pass':
                    message = 'pass'
                    color = GREEN
                    if (cur_time - played_sound_time) > SOUND_WAIT_TIME:
                        play = True
                    usando_mascara = "sim"
                elif last == 'stop':
                    reset = True
                last = 'pass'
            else: #stop/sem_mascara
                if last == 'stop':
                    message = 'stop'
                    color = RED
                    if (cur_time - played_sound_time) > SOUND_WAIT_TIME:
                        play = True
                    usando_mascara = "nao"
                elif last == 'pass':
                    reset = True
                last = 'stop'

        if not iopin.outputQ.empty():
            result = iopin.outputQ.get()
            now = time.time()
            if result == 'pass':
                #print('registrando temperatura regular, mascara:'+str(usando_mascara))
                dbm.threadInserir(data=datetime.datetime.now(), temperatura="regular", mascara=usando_mascara)
                #enviar para o banco:
                '''temp = 'normal'
                mascara = usando_mascara #true/false
                datahora = now()
                '''
            elif result == 'stop':
                #temperatura incorreta, tente novamente
                #print('registrando temperatura irregular')
                dbm.threadInserir(data=datetime.datetime.now(), temperatura="irregular", mascara=usando_mascara)

        if play:
            play = False
            played_sound_time = cur_time
            sound.soundQ.put(message)
        if reset:
            if (cur_time - played_sound_time) > SOUND_TIME:
                reset = False
                played_sound_time = 0
        
        if PROPAGANDA and banner.existePropaganda:
            image = banner.get()
        else:
            if SHOW_BB:
                image = detector.draw(image)
            image = cv2.copyMakeBorder(image,CANVAS_HEIGHT,CANVAS_HEIGHT,CANVAS_WIDTH,CANVAS_WIDTH,cv2.BORDER_CONSTANT,value=color)
            
            image = interface.insertMessage(image, message)
            image = interface.insertLogo(image)
            image = interface.insertLogo2(image)

        if SCREEN_ROTATION == 0:
            None
        elif SCREEN_ROTATION == 90:
            image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        elif SCREEN_ROTATION == 180:
            image = cv2.rotate(image, cv2.ROTATE_180)
        elif SCREEN_ROTATION == 270:
            image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

        image = cv2.resize(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        cv2.imshow('ArticfoxMaskDetection', image)
        
        k = cv2.waitKey(50) & 0xFF
        if k == ord("q") or k == ord("Q") or k == 27:
            break

    sound.soundQ.put('False')
    detector.stop()
    cam.stop()
    iopin.stop()
    if PROPAGANDA:
        banner.stop()
    cv2.destroyAllWindows()


def main():
    logger = logging.getLogger()
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
        filename='log.log',level=logging.ERROR,
        datefmt='%Y-%m-%d %H:%M:%S')
    try:
        if verify_key():
            videoMain()
        else:
            f = open("license_is_not_valid.txt", "a")
            f.write(str(time.time())+' - Tentativa de acesso fracassada, por favor entre em contato com a ARTICFOX TECNOLOGIA em contato@articfox.com.br\n')
            f.close()
            logger.log(logging.ERROR, "Licenca invalida. " + str(get_id()))
    except Exception:
        logger.exception("Fatal error in main loop")


if __name__ == '__main__':
    main()