#https://www.hackster.io/news/benchmarking-tensorflow-and-tensorflow-lite-on-the-raspberry-pi-43f51b796796

import tensorflow as tf
import cv2
import numpy as np
from anchor_generator import generate_anchors
from anchor_decode import decode_bbox
from nms import single_class_non_max_suppression
import math

model = 'converted_model.tflite'
interpreter = tf.lite.Interpreter(model_path=model)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
height = input_details[0]['shape'][1]
width = input_details[0]['shape'][2]
floating_model = False
if input_details[0]['dtype'] == np.float32:
    floating_model = True

image = 'img.jpg'
picture = cv2.imread(image)
frame = cv2.resize(picture, (width, height))
frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
frame = frame / 255.0
input_data = np.expand_dims(frame, axis=0)
input_data = np.float32(input_data)

#interpreter.set_num_threads(4)
interpreter.set_tensor(input_details[0]['index'], input_data)
interpreter.invoke()

y_bboxes_output = interpreter.get_tensor(output_details[0]['index'])
y_cls_output = interpreter.get_tensor(output_details[1]['index'])





feature_map_sizes = [[33, 33], [17, 17], [9, 9], [5, 5], [3, 3]]
anchor_sizes = [[0.04, 0.056], [0.08, 0.11], [0.16, 0.22], [0.32, 0.45], [0.64, 0.72]]
anchor_ratios = [[1, 0.62, 0.42]] * 5

# generate anchors
anchors = generate_anchors(feature_map_sizes, anchor_sizes, anchor_ratios)
        

anchors_exp = np.expand_dims(anchors, axis=0)

y_bboxes = decode_bbox(anchors_exp, y_bboxes_output)[0]
y_cls = y_cls_output[0]
# To speed up, do single class NMS, not multiple classes NMS.
bbox_max_scores = np.max(y_cls, axis=1)
bbox_max_score_classes = np.argmax(y_cls, axis=1)

# keep_idx is the alive bounding box after nms.
keep_idxs = single_class_non_max_suppression(y_bboxes,
                                             bbox_max_scores,
                                             conf_thresh=0.5,
                                             iou_thresh=0.4,
                                             )
output_info = []
largest = None
largest_size = None
for idx in keep_idxs:
    conf = float(bbox_max_scores[idx])
    class_id = bbox_max_score_classes[idx]
    bbox = y_bboxes[idx]
    # clip the coordinate, avoid the value exceed the image boundary.
    xmin = max(0, int(bbox[0] * width))
    ymin = max(0, int(bbox[1] * height))
    xmax = min(int(bbox[2] * width), width)
    ymax = min(int(bbox[3] * height), height)

    output_info.append([class_id, conf, xmin, ymin, xmax, ymax])

    if largest == None:
        largest = (class_id, conf, xmin, ymin, xmax, ymax)
        largest_size = math.sqrt((xmax-xmin)^2 + (ymax-ymin)^2)
    else:
        size = math.sqrt((xmax-xmin)^2 + (ymax-ymin)^2)
        if largest_size < size:
            largest = (class_id, conf, xmin, ymin, xmax, ymax)
            largest_size = size

print(output_info)