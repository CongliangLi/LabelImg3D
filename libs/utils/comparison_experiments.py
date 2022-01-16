import os
import cv2
from scipy.spatial.transform import Rotation as R
import numpy as np
import pandas as pd
import math
import json
from libs.utils.utils import parse_yaml, get_rotation_acc, get_translation_acc, get_all_path, get_R_w2c, iou, \
    box_cxcywh_to_xyxy


def linemod_compare(scene_path, class_list, class_id_list):
    label_path = os.path.join(scene_path, "labels")
    anno_path = os.path.join(scene_path, "annotations")
    acc = {}
    # Calculate the acc of each picture
    for n, class_ in enumerate(class_list):
        acc[class_] = {}
        anno_all = get_all_path(os.path.join(anno_path, class_))
        labels_all = parse_yaml(os.path.join(os.path.join(label_path, class_), "gt.yml"))

        for i, path in enumerate(anno_all):
            with open(path, 'r') as load_f:
                anno = json.load(load_f)
            anno_T = anno["model"]["0"]["T_matrix_c2o"]
            # anno_R = np.linalg.inv(np.array(anno["model"]["0"]["R_matrix_c2o"]).reshape(3, 3))
            anno_R = np.array(anno["model"]["0"]["R_matrix_c2o"]).reshape(3, 3)
            # print(anno_R)
            # anno_R = R.from_matrix(anno_R).as_quat()
            anno_R = R.from_matrix(anno_R).as_euler("zxy", degrees=True)
            # anno_R = [360 + a for a in anno_R if a < 0]
            # anno_R = [math.fabs(anno) for anno in anno_R]
            anno_bbox = anno["model"]["0"]["2d_bbox"]

            class_id = class_id_list[n]
            labels = labels_all[i]
            label = None
            for l in labels:
                if l["obj_id"] == class_id:
                    label = l
                    break
            label_T = [l / 1000 for l in label["cam_t_m2c"]]
            label_R = np.array(label["cam_R_m2c"]).reshape(3, 3)
            # print(label_R)
            # label_R = R.from_matrix(label_R).as_quat()
            label_R = R.from_matrix(label_R).as_euler("zxy", degrees=True)
            label_bbox = label["obj_bb"]
            label_bbox[2] = label_bbox[0] + label_bbox[2]
            label_bbox[3] = label_bbox[1] + label_bbox[3]

            # label_R = [math.fabs(label) for label in label_R]

            img_name = anno["image_file"].split("\\")[-1].split(".")[0]
            acc_T = [get_translation_acc(label_T[i], anno_T[i]) for i in range(3)]
            acc_R = [get_rotation_acc(label_R[i], anno_R[i]) for i in range(3)]
            acc_R[0] = min(acc_R[0], math.fabs(180 - acc_R[0]))
            acc_R[1] = min(acc_R[1], math.fabs(90 - acc_R[1]))
            acc_R[2] = min(acc_R[2], math.fabs(180 - acc_R[2]))
            acc_R = [math.cos(math.radians(a)) for a in acc_R]
            # acc_R = [math.fabs(label_R[i] - anno_R[i]) for i in range(3)]

            iou_lm = iou(anno_bbox, label_bbox)
            acc[class_][img_name] = {}
            acc[class_][img_name]["acc_T"] = acc_T
            acc[class_][img_name]["acc_R"] = acc_R
            acc[class_][img_name]["iou"] = iou_lm

            # print("{}  {}   {}  {}".format(class_, acc_T, acc_R, iou_lm))

    return acc


def linemod_data_processing(acc, linemod_classes):
    for class_ in linemod_classes:
        acc_T, acc_R, iou_lm = [0, 0, 0], [0, 0, 0], 0
        for k in acc[class_].keys():
            acc_T = [acc_T[i] + acc[class_][k]["acc_T"][i] for i in range(3)]
            acc_R = [acc_R[i] + acc[class_][k]["acc_R"][i] for i in range(3)]
            iou_lm += acc[class_][k]["iou"]

        print("{}  {}  {}  {}".format(class_, [round(a / 10, 4) for a in acc_T], [round(a / 10, 4) for a in acc_R],
                                      round(iou_lm / 10, 4)))
        pass


def kitti_compare(scene_path, classes_name_list, classes_id_list):
    label_path_all = os.path.join(scene_path, "labels")
    annotations_all = os.path.join(scene_path, "annotations")
    img_path_all = os.path.join(scene_path, "images")
    acc = {}

    for n, class_ in enumerate(classes_name_list):
        this_img_path = get_all_path(os.path.join(img_path_all, class_))
        this_label_path = get_all_path(os.path.join(label_path_all, class_))
        this_annotation_path = get_all_path(os.path.join(annotations_all, class_))
        acc[class_] = {}
        for i in range(len(this_img_path)):
            img_path = this_img_path[i]
            label_path = this_label_path[i]
            annotation_path = this_annotation_path[i]

            with open(label_path, 'r') as load_f:
                label = json.load(load_f)
            with open(annotation_path, 'r') as load_f:
                anno = json.load(load_f)

            anno_T = anno["model"]["0"]["T_matrix_c2o"]
            anno_R = np.array(anno["model"]["0"]["R_matrix_c2o"]).reshape(3, 3)
            anno_R = R.from_matrix(anno_R).as_euler("xyz", degrees=True)
            anno_bbox = anno["model"]["0"]["2d_bbox"]

            label_T = label["model"]["0"]["T_matrix_c2o"]
            label_R = np.array(label["model"]["0"]["R_matrix_c2o"]).reshape(3, 3)
            label_R = R.from_matrix(label_R).as_euler("xyz", degrees=True)
            label_bbox = label["model"]["0"]["2d_bbox"]

            img_name = anno["image_file"].split("\\")[-1].split(".")[0]
            acc_T = [get_translation_acc(label_T[i], anno_T[i]) for i in range(3)]
            acc_R = [get_rotation_acc(label_R[i], anno_R[i]) for i in range(3)]

            acc_R[0] = min(acc_R[0], math.fabs(180 - acc_R[0]))
            acc_R[1] = min(acc_R[1], math.fabs(90 - acc_R[1]))
            acc_R[2] = min(acc_R[2], math.fabs(90 - acc_R[2]))
            acc_R = [round(math.cos(math.radians(a)), 4) for a in acc_R]

            iou_lm = iou(anno_bbox, label_bbox)
            acc[class_][img_name] = {}
            acc[class_][img_name]["acc_T"] = acc_T
            acc[class_][img_name]["acc_R"] = acc_R
            acc[class_][img_name]["iou"] = iou_lm

            # print("{}  {}   {}  {}".format(class_, acc_T, acc_R, iou_lm))

        # plot bbox 2d
        # img = cv2.imread(self.interactor.parent().image_path)
        # img = cv2.rectangle(img, (int(l), int(t)), (int(r), int(b)), [0, 0, 255], 3)
        # cv2.imshow("rect", img)
        # cv2.waitKey(0)
    return acc


def kitti_data_processing(acc, kitti_classes):
    for class_ in kitti_classes:
        acc_T, acc_R, iou_lm = [0, 0, 0], [0, 0, 0], 0
        for k in acc[class_].keys():
            acc_T = [acc_T[i] + acc[class_][k]["acc_T"][i] for i in range(3)]
            acc_R = [acc_R[i] + acc[class_][k]["acc_R"][i] for i in range(3)]
            iou_lm += acc[class_][k]["iou"]

        print("{}  {}  {}  {}".format(class_, [round(a / 10, 4) for a in acc_T], [round(a / 10, 4) for a in acc_R],
                                      round(iou_lm / 10, 4)))
        pass


if __name__ == "__main__":
    # linemod_path = "F:/my_desktop/linemod_test"
    # linemod_class_name_list = ["ape", "benchviseblue", "cat", "duck", "lamp"]
    # linemod_class_id_list = [1, 2, 6, 9, 14]
    # linemod_acc = linemod_compare(linemod_path, linemod_class_name_list, linemod_class_id_list)
    # linemod_data_processing(linemod_acc, linemod_class_name_list)
    kitti_path = "F:/my_desktop/kitti_test/test"
    kitti_classes_name_list = ["Tram", "Car", "Van", "Pedestrian"]
    kitti_classes_id_list = [1, 2, 3, 5]
    kitti_acc = kitti_compare(kitti_path, kitti_classes_name_list, kitti_classes_id_list)
    kitti_data_processing(kitti_acc, kitti_classes_name_list)

