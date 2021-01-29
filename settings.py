TEST = False

PI = False
CAMERA = 0 #0, 1, 'pi'
#default 270
ROTATION = 0 #0, 90, 180, 270

WIDTH = 640
HEIGHT = 480
CAMERA_OUTPUT_WIDTH = 700
CAMERA_OUTPUT_HEIGHT = 930
CANVAS_WIDTH = 10
CANVAS_HEIGHT = 125

#resolution 1280x720
FULL_SCREEN = False
SCREEN_WIDTH = 720
SCREEN_HEIGHT = 1280

SCREEN_WIDTH = 506
SCREEN_HEIGHT = 900

#default 270
SCREEN_ROTATION = 0 #0, 90, 180, 270

SOUND_TIME = 4 #tempo em segundos para reproduzir outro som
SOUND_WAIT_TIME = 13 #tempo em segundos para reproduzir o mesmo som
CATRACA_TIME = 5 #tempo em segudos para liberar acesso da catrata

TF_LITE = False
SHOW_BB = True #marca cada deteccao realizada com sucesso
CONFIDENCE = 0.70

#tempo entre detecções
TIME_DEFAULT = 15
TIME_TEMP = TIME_DEFAULT
TIME_MASCARA = TIME_DEFAULT #15
TIME_ALCOOL = TIME_DEFAULT
TIME_RFID = TIME_DEFAULT
TIME_CATRACA = 5

CAPACIDADE_PESSOAS = 100

RFID_ATIVO = True

if PI:
    CAMERA = 'pi'
    ROTATION = 270
    FULL_SCREEN = True
    SCREEN_ROTATION = 270

#face_recognition
LIGAR_RECOG = True
RECOG_OBRIGATORIO = True
TAM_ROSTO = 55
RECOG_TOLERANCE = 0.4
UPDATE_FACELIST_TIME = 180
UPDATE_SERVER_FACES = 20

###api server
URL = 'http://localhost:8000'
USUARIO = 'api_client'
SENHA = 'api_client_secret_key2020'
