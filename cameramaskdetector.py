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
from utils.recognition import FaceRecog
from utils.iocontroller import IoManager
from utils import rfid_request
from utils.api_request import API
import time
import sys
import uuid
import hashlib, binascii, os
import logging


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
    if TF_LITE:
        detector = MaskDetectorLite(CONFIDENCE)
    else:
        detector = MaskDetector(CONFIDENCE)
    

    interface = Interface()
    iopin = IoManager()
    #iopin.run()

    api_class = API()

    #########FACE RECOG####
    recog = FaceRecog(api_class=api_class, cameraClass=cam, TOLERANCE=RECOG_TOLERANCE, TAM_ROSTO=TAM_ROSTO, UPDATE_FACELIST_TIME=UPDATE_FACELIST_TIME)
    #recog.run(cam)

    #run modules
    detector.run(cam)
    sound.run()
    ######

    if FULL_SCREEN:
        cv2.namedWindow('ArticfoxMaskDetection', cv2.WINDOW_FREERATIO)
        cv2.setWindowProperty('ArticfoxMaskDetection', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    message = 'wait'
    color = GRAY

    played_sound_time = 0
    cur_time = 0
    step_init_time = time.time()
    codigo_rfid = ''
    play = False
    reset = False
    somMascara = False

    #0 = Wait, 1 = temperatura, 2 = mascara, 3 = alcool, 4 = rfid, 5 = catraca
    step = 1
    lastStep = step
    reset_time = TIME_DEFAULT
    validacao = 0
    idxRfid = -1
    usuario = None

    finalizarProcesso = False
    pessoa = {
        'face_encontrada': False,
        'face_reconhecida': False,
        'id': -1,
        'nome': '',
        'encoding': []
    }
    
    reconhecimento = False
    step = 'wait'

    while True:
        image = cam.read()

        cur_time = time.time()

        #detectar pessoa
        if step == 'wait':
            iopin.stoptemp = True
            pessoa['face_encontrada'] = False
            pessoa['face_reconhecida'] = False
            pessoa['id'] = -1
            pessoa['nome'] = ''
            pessoa['encoding'] = []
            if RECOG_OBRIGATORIO:
                message = 'recog'
            else:
                message = 'wait'
            if detector.largest_predict != None:
                #pessoa detectada, realizar outros passos enquanto faz reconhecimento facial
                step = 'temperatura'
                message = 'temperatura'
                sound.soundQ.put('temperatura')
                recog.only_detection = False
                reconhecimento = True
                iopin.outputQ.queue.clear()
                iopin.stoptemp = False
                iopin.threadTemp()
                step_init_time = time.time()
                reset_time = TIME_TEMP
        #outros passos: alcool, temperatura, gel
        elif step == 'temperatura':
            if not iopin.outputQ.empty():
                result = iopin.outputQ.get()
                if result == 'pass':
                    #temperatura normal
                    message = 'mascara'
                    step = 'mascara'
                    detector.pause = False
                    sound.soundQ.put('mascara')
                    iopin.outputQ.queue.clear()
                    step_init_time = time.time()
                    reset_time = TIME_MASCARA
                else:
                    #pode salvar a informação de que a temperatura não foi aceita
                    pass
        elif step == 'mascara':
            if detector.new:
                detector.new = False
                if detector.largest_predict == None: #wait
                    validacao = 0
                    pass
                elif detector.largest_predict[0] == 0: #pass/com_mascara
                    validacao = validacao + 1
                    if validacao >= 2:
                        message = 'alcool'
                        step = 'alcool'
                        sound.soundQ.queue.clear()
                        sound.soundQ.put('alcool')
                        step_init_time = time.time()
                        reset_time = TIME_ALCOOL
                else: #stop/sem_mascara
                    #step_init_time = cur_time
                    message = 'stop'
                    if somMascara == True:
                        sound.soundQ.queue.clear()
                        sound.soundQ.put('stop')
                        step_init_time = time.time()
                    validacao = 0
        elif step == 'alcool':
            if not iopin.outputAQ.empty():
                result = iopin.outputAQ.get()
                if result == 'pass':
                    #temperatura normal
                    message = 'catraca'
                    step = 'catraca'

                    reconhecimento = False
                    recog.only_detection = True
                    #liberar catraca
                    if pessoa.get('face_reconhecida', False):
                        message = 'catraca'
                        sound.soundQ.put('catraca')
                        iopin.liberar()
                        #enviar informações de acesso pela API
                        api_class.threadCreateAcesso(idPessoa=pessoa.get('id', -1))
                    elif RECOG_OBRIGATORIO:
                        message = 'block'
                        sound.soundQ.put('block')
                    else:
                        iopin.liberar()
                        message = 'wait'
                        sound.soundQ.put('bemvindo')
                    step_init_time = time.time()
                    reset_time = TIME_CATRACA

        elif step == 'catraca':
            pass

        if SHOW_BB:
            image = detector.draw(image)
            image = recog.draw(image)

        image = interface.mountImage(image, message=message)

        if step != 'wait':
            if reconhecimento:
                if not recog.alive:
                    recog.runThreadRecog(detector)
                if recog.new:
                    if recog.data.get('face_reconhecida', False):
                        pessoa['face_encontrada'] = recog.data.get('face_encontrada', False)
                        pessoa['face_reconhecida'] = recog.data.get('face_reconhecida', False)
                        pessoa['id'] = recog.data.get('id', -1)
                        pessoa['nome'] = recog.data.get('nome', '')
                        pessoa['encoding'] = recog.data.get('encoding', [])
                        reconhecimento = False
                        recog.only_detection = True
                if RECOG_OBRIGATORIO:
                    interface.insertText(image, 'Identificando...')
            else:
                if pessoa.get('face_reconhecida', False):
                    interface.insertText(image, pessoa.get('nome', '...'))
                elif RECOG_OBRIGATORIO:
                    #apresentar tela não reconhecido
                    interface.insertText(image, 'Sem cadastro')

            if cur_time - step_init_time >= reset_time:
                step = 'wait'
                reconhecimento = False
                recog.only_detection = True

        #image = cv2.copyMakeBorder(image,CANVAS_HEIGHT,CANVAS_HEIGHT,CANVAS_WIDTH,CANVAS_WIDTH,
        #    cv2.BORDER_CONSTANT,value=color)
        
        if SCREEN_ROTATION == 0:
            None
        elif SCREEN_ROTATION == 90:
            image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        elif SCREEN_ROTATION == 180:
            image = cv2.rotate(image, cv2.ROTATE_180)
        elif SCREEN_ROTATION == 270:
            image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

        if image.shape[0] != SCREEN_HEIGHT or image.shape[1] != SCREEN_WIDTH:
            image = cv2.resize(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        cv2.imshow('ArticfoxMaskDetection', image)
        
        k = cv2.waitKey(50) & 0xFF
        if k == ord("q") or k == ord("Q") or k == 27:
            break
        elif k == ord("s"):
            if step == 'wait':
                step = 'temperatura'
            elif step == 'temperatura':
                step = 'mascara'
            elif step == 'mascara':
                step = 'alcool'
            elif step == 'alcool':
                step = 'catraca'
            elif step == 'catraca':
                step = 'wait'
        elif k == ord("a"):
            iopin.outputAQ.put('pass')
        elif k == ord("t"):
            iopin.outputQ.put('pass')
        elif k == ord("c"):
            iopin.contagem = iopin.contagem + 1
        elif k == ord("r"):
            recog.new = True
            recog.data = {
                'face_encontrada': True,
                'face_reconhecida': True,
                'id': 1,
                'nome': 'Lin Teste'
            }
        elif k == 13 or k == 10:
            #idxRfid = rfid_request.verificarUsuario(codigo_rfid, recog.listaRfid)
            #print(codigo_rfid)
            codigo_rfid = ''
        elif k != 255:
            codigo_rfid = codigo_rfid + chr(k)
        #print(k)

    sound.stop()
    iopin.stop()
    detector.stop()
    recog.stop()
    cam.stop()
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
    finally:
        os._exit(1)
        sys.exit("Program main exit")


if __name__ == '__main__':
    main()
