from utils import face_class
import cv2

det = face_class.MaskDetector()

img = cv2.imread('masc.jpg')

output = det.inference(img, color='bgr')

img = det.draw(img)

cv2.imshow("img", img)

cv2.imwrite("result.jpg", img)

cv2.waitKey(0)
cv2.destroyAllWindows()