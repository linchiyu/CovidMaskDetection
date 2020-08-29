# -*- coding:utf-8 -*-
import tensorflow as tf
import cv2
import math
import threading
import numpy as np
import face_recognition
import time
from multiprocessing import Process, Queue
#from keras.models import model_from_json
from utils.anchor_generator import generate_anchors
from utils.anchor_decode import decode_bbox
from utils.nms import single_class_non_max_suppression
from load_model.tensorflow_loader import load_tf_model, tf_inference
from utils.cameraThread import iniciarCamera

class MaskDetector():
    """Facial Mask detector"""
    def __init__(self, conf=0.5):
        self.conf = conf
        self.sess, self.graph = load_tf_model('data/bin')
        # anchor configuration
        feature_map_sizes = [[33, 33], [17, 17], [9, 9], [5, 5], [3, 3]]
        anchor_sizes = [[0.04, 0.056], [0.08, 0.11], [0.16, 0.22], [0.32, 0.45], [0.64, 0.72]]
        anchor_ratios = [[1, 0.62, 0.42]] * 5

        # generate anchors
        anchors = generate_anchors(feature_map_sizes, anchor_sizes, anchor_ratios)
        #print(anchors)
        # for inference , the batch size is 1, the model output shape is [1, N, 4],
        # so we expand dim for anchors to [1, anchor_num, 4]
        self.anchors_exp = np.expand_dims(anchors, axis=0)

        self.id2class = {0: 'ComMascara', 1: 'SemMascara'}

        self.predicts = None
        self.largest_predict = None
        self.stop = False
        self.new = True


    def inference(self, image,
                  conf_thresh=0.5,
                  iou_thresh=0.4,
                  target_shape=(160, 160),
                  color='rgb'
                  ):
        '''
        Main function of detection inference
        :param image: 3D numpy array of image
        :param conf_thresh: the min threshold of classification probabity.
        :param iou_thresh: the IOU threshold of NMS
        :param target_shape: the model input size.
        :param draw_result: whether to daw bounding box to the image.
        :param show_result: whether to display the image.
        :return:
        '''
        # image = np.copy(image)
        if color == 'bgr':
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        output_info = []
        height, width, _ = image.shape
        image_resized = cv2.resize(image, target_shape)
        image_np = image_resized / 255.0  # 归一化到0~1
        image_exp = np.expand_dims(image_np, axis=0)
        y_bboxes_output, y_cls_output = tf_inference(self.sess, self.graph, image_exp)

        # remove the batch dimension, for batch is always 1 for inference.
        y_bboxes = decode_bbox(self.anchors_exp, y_bboxes_output)[0]
        y_cls = y_cls_output[0]
        # To speed up, do single class NMS, not multiple classes NMS.
        bbox_max_scores = np.max(y_cls, axis=1)
        bbox_max_score_classes = np.argmax(y_cls, axis=1)

        # keep_idx is the alive bounding box after nms.
        keep_idxs = single_class_non_max_suppression(y_bboxes,
                                                     bbox_max_scores,
                                                     conf_thresh=conf_thresh,
                                                     iou_thresh=iou_thresh,
                                                     )

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
                largest_size = math.sqrt((xmax-xmin)**2 + (ymax-ymin)**2)
            else:
                size = math.sqrt((xmax-xmin)**2 + (ymax-ymin)**2)
                if largest_size < size:
                    largest = (class_id, conf, xmin, ymin, xmax, ymax)
                    largest_size = size

        self.predicts = output_info
        self.largest_predict = largest
        self.new = True

        return output_info

    def draw(self, image):
        #results is a vector with [class_id, conf, xmin, ymin, xmax, ymax]
        if self.predicts == None:
            return image
        for (class_id, conf, xmin, ymin, xmax, ymax) in self.predicts:
            if class_id == 0:
                color = (0, 255, 0)
            else:
                color = (0, 0, 255)
            cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, 2)
            #cv2.putText(image, "%s: %.2f" % (self.id2class[class_id], conf), (xmin + 2, ymin - 2),
            #            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color)
            cv2.putText(image, "%s" % (self.id2class[class_id]), (xmin + 2, ymin - 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color)
        return image

    def extractLargestPredict(self, results):
        largest = None
        largest_size = None
        for (class_id, conf, xmin, ymin, xmax, ymax) in results:
            if largest == None:
                largest = (class_id, conf, xmin, ymin, xmax, ymax)
                largest_size = math.sqrt((xmax-xmin)**2 + (ymax-ymin)**2)
            else:
                size = math.sqrt((xmax-xmin)**2 + (ymax-ymin)**2)
                if largest_size < size:
                    largest = (class_id, conf, xmin, ymin, xmax, ymax)
                    largest_size = size
        return largest

    def camInference(self, cameraClass):
        while not self.stop:
            img_raw = cameraClass.read()
            img_raw = cv2.cvtColor(img_raw, cv2.COLOR_BGR2RGB)
            self.inference(img_raw,
                      conf_thresh=self.conf,
                      iou_thresh=0.5,
                      target_shape=(260, 260)
                      )

    def run(self, cameraClass):
        t = threading.Thread(target=self.camInference,args=(cameraClass,),daemon=True)
        t.start()
      

class MaskDetectorLite():
    """Facial Mask detector"""
    def __init__(self, conf=0.5):
        self.conf = conf
        self.interpreter = tf.lite.Interpreter(model_path='data/binlt')
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # anchor configuration
        feature_map_sizes = [[33, 33], [17, 17], [9, 9], [5, 5], [3, 3]]
        anchor_sizes = [[0.04, 0.056], [0.08, 0.11], [0.16, 0.22], [0.32, 0.45], [0.64, 0.72]]
        anchor_ratios = [[1, 0.62, 0.42]] * 5

        # generate anchors
        anchors = generate_anchors(feature_map_sizes, anchor_sizes, anchor_ratios)
        #print(anchors)
        # for inference , the batch size is 1, the model output shape is [1, N, 4],
        # so we expand dim for anchors to [1, anchor_num, 4]
        self.anchors_exp = np.expand_dims(anchors, axis=0)

        self.id2class = {0: 'ComMascara', 1: 'SemMascara'}

        self.predicts = None
        self.largest_predict = None
        self.stop = False
        self.new = True


    def inference(self, image,
                  conf_thresh=0.5,
                  iou_thresh=0.4,
                  target_shape=(160, 160),
                  color='rgb'
                  ):
        '''
        Main function of detection inference
        :param image: 3D numpy array of image
        :param conf_thresh: the min threshold of classification probabity.
        :param iou_thresh: the IOU threshold of NMS
        :param target_shape: the model input size.
        :param draw_result: whether to daw bounding box to the image.
        :param show_result: whether to display the image.
        :return:
        '''
        # image = np.copy(image)
        if color == 'bgr':
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        output_info = []
        height, width, _ = image.shape
        image_resized = cv2.resize(image, target_shape)
        image_np = image_resized / 255.0  # 归一化到0~1
        image_exp = np.expand_dims(image_np, axis=0)
        image_exp = np.float32(image_exp)

        self.interpreter.set_tensor(self.input_details[0]['index'], image_exp)
        self.interpreter.invoke()

        y_bboxes_output = self.interpreter.get_tensor(self.output_details[0]['index'])
        y_cls_output = self.interpreter.get_tensor(self.output_details[1]['index'])

        # remove the batch dimension, for batch is always 1 for inference.
        y_bboxes = decode_bbox(self.anchors_exp, y_bboxes_output)[0]
        y_cls = y_cls_output[0]
        # To speed up, do single class NMS, not multiple classes NMS.
        bbox_max_scores = np.max(y_cls, axis=1)
        bbox_max_score_classes = np.argmax(y_cls, axis=1)

        # keep_idx is the alive bounding box after nms.
        keep_idxs = single_class_non_max_suppression(y_bboxes,
                                                     bbox_max_scores,
                                                     conf_thresh=conf_thresh,
                                                     iou_thresh=iou_thresh,
                                                     )

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
                largest_size = math.sqrt((xmax-xmin)**2 + (ymax-ymin)**2)
            else:
                size = math.sqrt((xmax-xmin)**2 + (ymax-ymin)**2)
                if largest_size < size:
                    largest = (class_id, conf, xmin, ymin, xmax, ymax)
                    largest_size = size

        self.predicts = output_info
        self.largest_predict = largest
        self.new = True

        return output_info

    def draw(self, image):
        #results is a vector with [class_id, conf, xmin, ymin, xmax, ymax]
        if self.predicts == None:
            return image
        for (class_id, conf, xmin, ymin, xmax, ymax) in self.predicts:
            if class_id == 0:
                color = (0, 255, 0)
            else:
                color = (0, 0, 255)
            cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, 2)
            #cv2.putText(image, "%s: %.2f" % (self.id2class[class_id], conf), (xmin + 2, ymin - 2),
            #            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color)
            cv2.putText(image, "%s" % (self.id2class[class_id]), (xmin + 2, ymin - 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color)
        return image

    def extractLargestPredict(self, results):
        largest = None
        largest_size = None
        for (class_id, conf, xmin, ymin, xmax, ymax) in results:
            if largest == None:
                largest = (class_id, conf, xmin, ymin, xmax, ymax)
                largest_size = math.sqrt((xmax-xmin)**2 + (ymax-ymin)**2)
            else:
                size = math.sqrt((xmax-xmin)**2 + (ymax-ymin)**2)
                if largest_size < size:
                    largest = (class_id, conf, xmin, ymin, xmax, ymax)
                    largest_size = size
        return largest

    def camInference(self, cameraClass):
        while not self.stop:
            img_raw = cameraClass.read()
            img_raw = cv2.cvtColor(img_raw, cv2.COLOR_BGR2RGB)
            self.inference(img_raw,
                      conf_thresh=self.conf,
                      iou_thresh=0.5,
                      target_shape=(260, 260)
                      )

    def run(self, cameraClass):
        t = threading.Thread(target=self.camInference,args=(cameraClass,),daemon=True)
        t.start()


class FaceRecog():
    """face recognition from face_recognition"""
    def __init__(self, listaId, listaNome, listaRfid, listaFaceP, TAM_ROSTO=60):
        self.listaId = listaId
        self.listaNome = listaNome
        self.listaRfid = listaRfid
        self.listaFaceP = listaFaceP

        self.TAM_ROSTO = TAM_ROSTO

        self.face_locations = []
        self.largestFace = None
        self.largestSize = 0

        self.id = None
        self.nome = None
        self.rfid = None
        self.face = None

        self.mascara = False
        self.temperatura = False
        self.alcool = False
        self.rfid = False

        self.dataQ = Queue()
        self.imageQ = Queue()
        self.stopQ = Queue()
        self.stop = False

    def draw(self, image):
        #results is a vector with [class_id, conf, xmin, ymin, xmax, ymax]
        if len(self.face_locations) == 0:
            return image
        if self.largestSize > self.TAM_ROSTO:
            for (top, right, bottom, left) in self.face_locations:
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a box around the face
                cv2.rectangle(image, (left, top), (right, bottom), (0, 0, 255), 2)

                # Draw a label with a name below the face
                cv2.rectangle(image, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(image, self.nome, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
        return image

    def extractLargestFace(self, faces):
        largest = None
        largest_size = None
        for (top, right, bottom, left) in faces:
            if largest == None:
                largest = (top, right, bottom, left)
                largest_size = math.sqrt((bottom-top)**2 + (right-left)**2)
            else:
                size = math.sqrt((bottom-top)**2 + (right-left)**2)
                if largest_size < size:
                    largest = (top, right, bottom, left)
                    largest_size = size
        self.face_locations = [largest]
        self.largestSize = largest_size

    def camInference(self):
        while self.stopQ.empty():
            img_raw = self.imageQ.get()
            small_frame = cv2.resize(img_raw, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = small_frame[:, :, ::-1]
            faces = face_recognition.face_locations(rgb_small_frame)
            if len(faces) > 0:
                self.extractLargestFace(faces)
                if self.largestSize > self.TAM_ROSTO:
                    face_encodings = face_recognition.face_encodings(rgb_small_frame, self.face_locations)
                    for face_encoding in face_encodings:
                        # See if the face is a match for the known face(s)
                        matches = face_recognition.compare_faces(self.listaFaceP, face_encoding)
                        
                        if True in matches:
                            first_match_index = matches.index(True)
                            data = (self.listaId[first_match_index], self.listaNome[first_match_index],
                                self.listaRfid[first_match_index], self.listaFaceP[first_match_index],
                                self.face_locations, self.largestSize)
                            print(data)
                            self.dataQ.put(data)
                            self.id = self.listaId[first_match_index]
                            self.nome = self.listaNome[first_match_index]
                            self.rfid = self.listaRfid[first_match_index]
                            self.face = self.listaFaceP[first_match_index]
                        else:
                            data = (0, 'desconhecido', '0', [], self.face_locations, self.largest_size)
                            self.dataQ.put(data)
                            self.id = 0
                            self.nome = 'desconhecido'
                            self.rfid = '0'
                            self.face = []

            time.sleep(0.2)

    def collectData(self, cameraClass):
        while not self.stop:
            if not self.dataQ.empty():
                data = self.dataQ.get()
                self.id, self.nome, self.rfid, self.face, self.face_locations, self.largestSize = data
            if self.imageQ.empty():
                self.imageQ.put(cameraClass.read())
            time.sleep(0.1)
        self.stopQ.put(True)


    def run(self, cameraClass):
        #t = threading.Thread(target=self.camInference,args=(cameraClass,),daemon=True)
        p = Process(target=self.camInference,args=(),daemon=True)
        t = threading.Thread(target=self.collectData,args=(cameraClass,),daemon=True).start()
        p.start()