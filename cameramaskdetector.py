from settings import *
import cv2
import numpy as np
import face_recognition
from utils import cameraThread
from utils.interface import Interface
from utils.soundManager import SoundManager
if TF_LITE:
    from utils.face_class import MaskDetectorLite
else:
    from utils.face_class import MaskDetector
from utils.recognition import FaceRecog, Person
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
    sound.run()
    if TF_LITE:
        detector = MaskDetectorLite(CONFIDENCE)
    else:
        detector = MaskDetector(CONFIDENCE)
    detector.run(cam)
    interface = Interface()
    iopin = IoManager()
    iopin.run()
    api_class = API()

    #########FACE RECOG####
    ####TEST DATA### change to  API request
    if TEST:
        biden_image = face_recognition.load_image_file("f1.jpg")
        biden_face_encoding = face_recognition.face_encodings(biden_image)[0]
        # Create arrays of known face encodings and their names
        known_face_encodings = [biden_face_encoding]
        known_face_names = ["lin"]
        ids = [1]
        rfid_l = ['1']
        #END TEST DATA###
    else:
        ids, known_face_names, rfid_l, known_face_encodings = api_class.getFaceList()

    recog = FaceRecog(ids, known_face_names, rfid_l, known_face_encodings, api_class, TAM_ROSTO)
    recog.run(cam)

    ######

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
    step = 1
    lastStep = step
    reset_time = TIME_DEFAULT
    validacao = 0
    idxRfid = -1
    usuario = None

    finalizarProcesso = False
    person = Person()

    while True:
        image = cam.read()

        cur_time = time.time()

        #detectar pessoa
        if not finalizarProcesso:
            message = 'recog'
            #aguardar pessoa se aproximar da tela e ser detectada
            idP, nome, rfid, face, location = recog.getPerson()
            if idP == None or idP == -1:
                #do nothing
                person.update(-1, '', '', '', [])
                pass
            else:
                #show person and start other detections
                #recog.getPerson()
                person.update(idP, nome, rfid, face, location)
                #iopin.verifyData = True
                finalizarProcesso = True
            if RFID_ATIVO:
                #verificar cartao do usuario
                #message = 'cartao'
                if idxRfid != -1:
                    #cartao PORTAL desativa RFID
                    person.update(recog.listaId[idxRfid], recog.listaNome[idxRfid], 
                        recog.listaRfid[idxRfid], recog.listaFaceP[idxRfid], [])
                    finalizarProcesso = True
        else:
            #pessoa já foi identificada, agora deve fazer os passos para liberar catraca
            if step == 0:
                #aguardar alguma pessoa passar pelo totem
                step = 1
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
                        #step_init_time = cur_time
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
                        step = 5
                '''elif step == 4:
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
                    continue'''
            elif step == 5:
                #catraca liberada
                message = 'catraca'
                reset_time = TIME_CATRACA

            if (cur_time - step_init_time) > reset_time and step != 0 and lastStep != 0:
                if step == 5:
                    #registrar ponto
                    if TEST:
                        pass
                    else:
                        api_class.loopCreateAcesso(idPessoa=person.id)
                finalizarProcesso = False
                idxRfid = -1
                step = 1

            if iopin.contagem >= CAPACIDADE_PESSOAS:
                step = 1
                message = 'limite'

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
                iopin.outputQ.queue.clear()
                iopin.outputAQ.queue.clear()
                step_init_time = cur_time
                validacao = 0
                codigo_rfid = ''
                usr = None
                play = True
                somMascara = True
                if step == 5:
                    iopin.liberar()
                lastStep = step
            
        if SHOW_BB:
            image = detector.draw(image)
            image = recog.draw(image)
        image = cv2.copyMakeBorder(image,CANVAS_HEIGHT,CANVAS_HEIGHT,CANVAS_WIDTH,CANVAS_WIDTH,cv2.BORDER_CONSTANT,value=color)
        
        image = interface.insertMessage(image, message, person.nome)
        image = interface.insertLogo(image)
        image = interface.insertLogo2(image)
        
        if step == 5:
            if usuario != None:
                #registroPonto = time.strftime("%d/%m/%Y %H:%M:%S", time.gmtime()) + ' - ' + usuario['nome'] + '['+ usuario['empresa'] + ']'
                #image = cv2.putText(image, registroPonto, (30, 30), cv2.FONT_HERSHEY_SIMPLEX,  
                #       0.6, (255,255,255), 1, cv2.LINE_AA)
                pass


        if SCREEN_ROTATION == 0:
            None
        elif SCREEN_ROTATION == 90:
            image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        elif SCREEN_ROTATION == 180:
            image = cv2.rotate(image, cv2.ROTATE_180)
        elif SCREEN_ROTATION == 270:
            image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)

        cv2.resize(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        cv2.imshow('ArticfoxMaskDetection', image)
        
        k = cv2.waitKey(50) & 0xFF
        if k == ord("q") or k == ord("Q") or k == 27:
            break
        elif k == ord("p"):
            step = step + 1
        elif k == ord("c"):
            iopin.contagem = iopin.contagem + 1
        elif k == 13 or k == 10:
            idxRfid = rfid_request.verificarUsuario(codigo_rfid, recog.listaRfid)
            #print(codigo_rfid)
            codigo_rfid = ''
        elif k != 255:
            codigo_rfid = codigo_rfid + chr(k)
        #print(k)

    sound.soundQ.put('False')
    iopin.stop = True
    detector.stop = True
    recog.stop = True
    recog.stopQ.put(True)
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
