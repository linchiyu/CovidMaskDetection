from settings import *
import cv2
import numpy as np
from utils import cameraThread
from utils.interface import Interface
from utils.soundManager import SoundManager
if TF_LITE:
    from utils.face_class import MaskDetectorLite
else:
    from utils.face_class import MaskDetector
from utils.iocontroller import IoManager
from utils import rfid
from utils.banner import Banner
from utils import usbcontroller
import time
import sys
import uuid
import hashlib, binascii, os
import logging
if SHARED_MEMORY:
    #from multiprocessing import shared_memory
    pass

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
    global RFID_ATIVO
    GREEN = (85,201,0)
    RED = (2,1,211)
    YELLOW = (8,191,253)
    GRAY = (105,105,105)
    
    cam = cameraThread.iniciarCamera(camera=CAMERA, width=WIDTH, height=HEIGHT, rotation=ROTATION)
    sound = SoundManager()
    sound.run()
    if TF_LITE:
        detector = MaskDetectorLite(CONFIDENCE)
    else:
        detector = MaskDetector(CONFIDENCE)
    detector.run(cam)
    interface = Interface()
    iopin = IoManager()
    iopin.run()

    if PROPAGANDA:
        banner = Banner(shape=(SCREEN_WIDTH, SCREEN_HEIGHT))
        usbc = usbcontroller.USBDetector()

    if FULL_SCREEN:
        cv2.namedWindow('ArticfoxMaskDetection', cv2.WINDOW_FREERATIO)
        cv2.setWindowProperty('ArticfoxMaskDetection', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    message = 'wait'
    color = GRAY
    last = message

    played_sound_time = 0
    cur_time = 0
    step_init_time = time.time()
    codigo_rfid = ''
    play = False
    reset = False
    somMascara = False

    #0 = Wait, 1 = temperatura, 2 = mascara, 3 = alcool, 4 = rfid, 5 = catraca
    step = 0
    lastStep = step
    reset_time = TIME_DEFAULT
    validacao = 0
    usr = None
    usuario = None

    if SHARED_MEMORY:
        nbytes = SCREEN_WIDTH*SCREEN_HEIGHT*3
        #shm = shared_memory.SharedMemory(name='cameraframe', create=True, size=nbytes)
        #sharedimg = np.ndarray((SCREEN_HEIGHT, SCREEN_WIDTH, 3), dtype=np.uint8, buffer=shm.buf)
        pass

    while True:
        image = cam.read()

        cur_time = time.time()

        if step == 0:
            #aguardar alguma pessoa passar pelo totem
            iopin.outputQ.queue.clear()
            iopin.outputAQ.queue.clear()
            reset_time = TIME_DEFAULT
            message = 'wait'
            if detector.largest_predict != None:
                step = 1
        elif step == 1:
            #verificar temperatura
            reset_time = TIME_TEMP
            message = 'temperatura'
            if not iopin.outputQ.empty():
                result = iopin.outputQ.get()
                if result == 'pass':
                    #temperatura normal
                    message = 'mascara'
                    step = 2
                elif result == 'stop':
                    #temperatura incorreta, tente novamente
                    step_init_time = cur_time
                    pass
        elif step == 2:
            #verificar mascara
            #message = 'mascara'
            reset_time = TIME_MASCARA
            if detector.new:
                detector.new = False
                if detector.largest_predict == None: #wait
                    validacao = 0
                    pass
                elif detector.largest_predict[0] == 0: #pass/com_mascara
                    validacao = validacao + 1
                    if validacao >= 2:
                        step = 3
                else: #stop/sem_mascara
                    step_init_time = cur_time
                    message = 'stop'
                    if somMascara == True:
                        somMascara = False
                        play = True
                    validacao = 0
        elif step == 3:
            #verificar alcool gel
            reset_time = TIME_ALCOOL
            message = 'alcool'
            if not iopin.outputAQ.empty():
                result = iopin.outputAQ.get()
                if result == 'pass':
                    #temperatura normal
                    usuario = None
                    if RFID_ATIVO:
                        step = 4
                    else:
                        step = 5
        elif step == 4:
            #verificar cartao do usuario
            reset_time = TIME_RFID
            if RFID_ATIVO:
                message = 'cartao'
                if usr != None:
                    #cartao PORTAL desativa RFID
                    if usr['numero'] == 6042777:
                        RFID_ATIVO = False
                    print(usr['nome'], usr['empresa'])
                    usuario = usr
                    step = 5
            else:
                step = 5
                continue
        elif step == 5:
            #catraca liberada
            message = 'catraca'
            reset_time = TIME_CATRACA

        if (cur_time - step_init_time) > reset_time and step != 0 and lastStep != 0:
            step = 0
            #print('reset')


        if play:
            play = False
            played_sound_time = cur_time
            sound.soundQ.queue.clear()
            sound.soundQ.put(message)
        if reset:
            if (cur_time - played_sound_time) > SOUND_TIME:
                reset = False
                played_sound_time = 0
                
        last = message
        if lastStep != step:
            #step changed
            iopin.step = step
            #iopin.outputQ.queue.clear()
            step_init_time = cur_time
            validacao = 0
            codigo_rfid = ''
            usr = None
            play = True
            somMascara = True
            if step == 5:
                iopin.liberar()
            lastStep = step

        if not PROPAGANDA:
            if SHOW_BB:
                image = detector.draw(image)
            image = cv2.copyMakeBorder(image,CANVAS_HEIGHT,CANVAS_HEIGHT,CANVAS_WIDTH,CANVAS_WIDTH,cv2.BORDER_CONSTANT,value=color)
            
            image = interface.insertMessage(image, message)
            image = interface.insertLogo(image)
            image = interface.insertLogo2(image)
        else:
            #banner
            if banner.existePropaganda:
                image = banner.get()
            else:
                if SHOW_BB:
                    image = detector.draw(image)
                image = cv2.copyMakeBorder(image,CANVAS_HEIGHT,CANVAS_HEIGHT,CANVAS_WIDTH,CANVAS_WIDTH,cv2.BORDER_CONSTANT,value=color)
                
                image = interface.insertMessage(image, message)
                image = interface.insertLogo(image)
                image = interface.insertLogo2(image)

        if step == 5:
            if usuario != None:
                registroPonto = time.strftime("%d/%m/%Y %H:%M:%S", time.gmtime()) + ' - ' + usuario['nome'] + '['+ usuario['empresa'] + ']'
                image = cv2.putText(image, registroPonto, (30, 30), cv2.FONT_HERSHEY_SIMPLEX,  
                       0.6, (255,255,255), 1, cv2.LINE_AA)

        if SCREEN_ROTATION == 0:
            None
        elif SCREEN_ROTATION == 90:
            image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        elif SCREEN_ROTATION == 180:
            image = cv2.rotate(image, cv2.ROTATE_180)
        elif SCREEN_ROTATION == 270:
            image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

        image = cv2.resize(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        if SHARED_MEMORY:
            #sharedimg[:] = image[:]
            pass
        cv2.imshow('ArticfoxMaskDetection', image)

        k = cv2.waitKey(10) & 0xFF
        if k == ord("q") or k == ord("Q") or k == 27:
            break
        elif k == ord("p"):
            step = step+1
        elif k == ord("a"):
            iopin.outputAQ.put('pass')
        elif k == 13 or k == 10:
            usr = rfid.verificarUsuario(codigo_rfid)
            #print(codigo_rfid)
            codigo_rfid = ''
        elif k != 255:
            codigo_rfid = codigo_rfid + chr(k)
        #print(k)

    sound.soundQ.put('False')
    iopin.stop()
    detector.stop()
    cam.stop()
    cv2.destroyAllWindows()
    if PROPAGANDA:
        banner.stop()
    if SHARED_MEMORY:
        #shm.close()
        #shm.unlink()
        pass


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
        raise
    finally:
        os._exit(1)
        sys.exit("Program main exit")


if __name__ == '__main__':
    main()
