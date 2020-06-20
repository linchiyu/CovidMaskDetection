import cv2
import numpy as np

def resizeMaintainAspectRatio(img, ratio=1, width=False, height=False):
    #resize a img maintaining the aspect ratio
    #select one of the values to fill (ratio, width, height)
    #ratio: float value of the desired ratio
    #width: int value of the desired width, set false to ignore
    #height: int value of the desired heigh, set false to ignore
    if width:
        ratio = (width/img.shape[1])
        height = int(img.shape[0] * ratio)
    elif height:
        ratio = (height/img.shape[0])
        width = int(img.shape[1] * ratio)
    else:
        width = int(img.shape[1] * ratio)
        height = int(img.shape[0] * ratio)

    output = cv2.resize(img, (width, height))
    return output

def resizeBlackThumbnail(img, width, height):
    #resize a img maintaining the aspect ratio and fill blank with black
    width_ratio = (width/img.shape[1])
    height_ratio = (height/img.shape[0])
    if width_ratio > height_ratio:
        resized_image = resizeMaintainAspectRatio(img, height=height)
    else:
        resized_image = resizeMaintainAspectRatio(img, width=width)

    #Creating a dark square with NUMPY  
    output = np.zeros((height, width,3),np.uint8)

    #Pasting the 'image' in a start position
    output[0:resized_image.shape[0],0:resized_image.shape[1]] = resized_image

    return output

def createColorCanvas(width, height, rgb_color=(0, 0, 0)):
    """Create new image(numpy array) filled with certain color in RGB"""
    # Create black blank image
    image = np.zeros((height, width, 3), np.uint8)

    # Since OpenCV uses BGR, convert the color first
    color = tuple(reversed(rgb_color))
    # Fill image with color
    image[:] = color

    return image

'''
# Create new blank 300x300 red image
width, height = 300, 300

red = (255, 0, 0)
image = create_blank(width, height, rgb_color=red)
cv2.imwrite('red.jpg', image)
'''


def verticalConcat(image1, image2):
    """Create new image stacking image2 below image1"""
    shape1 = image1.shape
    shape2 = image2.shape
    if shape1[1] > shape2[1]:
        resizeMaintainAspectRatio(image2, width=shape1[1])
    elif shape2[1] > shape1[1]:
        resizeMaintainAspectRatio(image1, width=shape2[1])

    return np.hstack((image1, image2))

def horizontalConcat(image1, image2):
    """Create new image stacking image2 on the right of image1"""
    shape1 = image1.shape
    shape2 = image2.shape
    if shape1[0] > shape2[0]:
        resizeMaintainAspectRatio(image2, height=shape1[0])
    elif shape2[0] > shape1[0]:
        resizeMaintainAspectRatio(image1, height=shape2[0])

    return np.hstack((image1, image2))
