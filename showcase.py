import cv2
from utils import imgutil
from utils import cameraThread
from utils.interface import Interface
from utils.soundManager import SoundManager
from utils.face_class import MaskDetector

CAMERA = 1 #0, 1, 'pi'
ROTATION = 0 #0, 90, 180, 270

WIDTH = 640
HEIGHT = 480
CANVAS_WIDTH = 10
CANVAS_HEIGHT = 106

SOUND_TIME = 1 #tempo em segundos para reproduzir outro som
SOUND_WAIT_TIME = 7 #tempo em segundos para reproduzir o mesmo som
#assim que receber 2 waits zero o tempo para reproduzir o mesmo som


GREEN = (85,201,0)
RED = (2,1,211)
YELLOW = (8,191,253)

cam = cameraThread.iniciarCamera(camera=CAMERA, width=WIDTH, height=HEIGHT, rotation=ROTATION)
detector = MaskDetector()
detector.run(cam)

#cv2.namedWindow('ArticfoxMaskDetection', cv2.WND_PROP_FULLSCREEN)
#cv2.setWindowProperty('ArticfoxMaskDetection', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

interface = Interface()
sound = SoundManager()
message = 'wait'
color = YELLOW
last = message

while True:
	image = cam.read()

	if detector.new:
		detector.new = False
		last = message

	if detector.largest_predict == None:
		message = 'wait'
		color = YELLOW
	elif detector.largest_predict[0] == 0: #com_mascara
		message = 'pass'
		color = GREEN
	else:
		message = 'stop'
		color = RED

	image = detector.draw(image)
	image = cv2.copyMakeBorder(image,CANVAS_HEIGHT,CANVAS_HEIGHT,CANVAS_WIDTH,CANVAS_WIDTH,cv2.BORDER_CONSTANT,value=color)
	
	image = interface.insertMessage(image, message)
	image = interface.insertLogo(image)




	cv2.imshow('ArticfoxMaskDetection', image)
	
	k = cv2.waitKey(50) & 0xFF
	if k == ord("q") or k == ord("Q") or k == 27:
		break

detector.stop = True
cam.stop()
cv2.destroyAllWindows()