import os
from libs.utils import roty, get_all_path
import numpy as np
import pandas as pd
import json
from kitti_util import Calibration


def KITTI_2_LabelImg3D(img_path, label_path, model_path, annotation_path, calib_path, c_distance):
    with open(model_path + "/models.json", 'r') as load_f:
        model_json_data = json.load(load_f)
    model_data = {"Tram": {}, "Car": {}, "Truck": {}, "Van": {}, "Pedestrian": {}}
    for d in model_data:
        for j_d in model_json_data:
            if model_json_data[j_d]["class_name"] == d:
                model_data[d]["path"] = "models\\" + j_d
                model_data[d]["index"] = model_json_data[j_d]["class_index"]
                model_data[d]["size"] = model_json_data[j_d]["size"]
                break

    calib = Calibration(calib_path)
    data = {}

    data["image_file"] = "\\".join(img_path.split("\\")[len(img_path.split("\\")) - 3:])

    data["model"] = {}
    data["model"]["num"] = 0
    num = 0

    # calib = pd.read_table(calib_path, sep=' ', header=None)
    # calib_velo2c0 = [[calib[4 * i + n][5] for n in range(1, 5)] for i in range(0, 3)]
    # calib_velo2c0 = np.row_stack([calib_velo2c0, np.array([0, 0, 0, 1])])
    #
    # calib_R0rect = [[calib[3 * i + n][4] for n in range(1, 4)] for i in range(0, 3)]
    # calib_R0rect = np.column_stack([calib_R0rect, np.array([0, 0, 0])])
    # calib_R0rect = np.row_stack([calib_R0rect, np.array([0, 0, 0, 1])])
    #
    # calib_velo2c = np.dot(calib_R0rect, calib_velo2c0)
    # R_velo2c = [[calib_velo2c[i][n] for n in range(0, 3)] for i in range(0, 3)]
    # T_velo2c = [calib_velo2c[i][3] for i in range(0, 3)]

    R_c02c = np.array([[0.9999758, -0.005267463, - 0.004552439],
                       [0.00251945, 0.9999804, - 0.003413835],
                       [0.004570332, 0.003389843, 0.9999838]])

    a = pd.read_table(label_path, sep=' ', header=None)
    for i in range(0, len(a)):
        obj_class = a[0][i]

        if obj_class == "Cyclist" or obj_class == "DontCare" or obj_class == "Misc":
            continue

        obj_position_c0 = np.array([[a[j][i] for j in range(11, 14)]])
        obj_position_c0 = np.array(obj_position_c0)

        # obj_position_c = np.matmul(R_rect_02, np.matmul(T_02, np.vstack((np.matmul(np.linalg.inv(R_rect_00), obj_position_c0[:3, :]), [1])))[:3, :])
        # obj_position_c = np.matmul(R_rect_02, obj_position_c0[:3, :])
        obj_position_c = calib.project_rect0_to_rect2(obj_position_c0)
        obj_position_c = obj_position_c.squeeze()
        # obj_position_c = [obj_position_c0[i] + T_c02c[i] for i in range(0, 3)]
        obj_position_w = np.array([obj_position_c[0], -obj_position_c[1], -(obj_position_c[2] - c_distance)])

        obj_alpha = a[3][i]
        R_oK2oL = [[0, 0, 1],
                   [0, 1, 0],
                   [-1, 0, 0]]

        obj_r_y = a[14][i]
        R_oK2c0 = roty(3.14 - obj_r_y)
        R_oK2c = np.dot(R_oK2c0, R_c02c)

        R_c2w_1 = [[0, -1, 0],
                   [1, 0, 0],
                   [0, 0, 1]]
        R_c2w_2 = [[1, 0, 0],
                   [0, -1, 0],
                   [0, 0, -1]]
        R_c2w = np.dot(R_c2w_1, R_c2w_2)
        # R_oL2w = np.dot(np.dot(R_oL2oK, R_oK2c), R_c2w)
        R_oL2w = np.dot(np.dot(R_oK2c, R_c2w), R_oK2oL)
        # R_oL2w = np.dot(R_oK2c, R_c2w)
        oL_2_w = np.column_stack([R_oL2w, obj_position_w])
        oL_2_w = np.row_stack([oL_2_w, np.array([0, 0, 0, 1])])

        for m_d in model_data:
            if m_d == obj_class:
                data["model"]["{}".format(num)] = {
                    "model_file": model_data[m_d]["path"],
                    "matrix": oL_2_w.reshape(1, 16).tolist()[0],
                    "class": model_data[m_d]["index"],
                    "class_name": m_d,
                    "size": model_data[m_d]["size"]
                }
                break
        num += 1
    data["model"]["num"] = num
    data["camera"] = {}
    data["camera"]["matrix"] = [1.0, 0.0, 0.0, 0.0,
                                0.0, 1.0, 0.0, 0.0,
                                0.0, 0.0, 1.0, 0.52,
                                0.0, 0.0, 0.0, 1.0
                                ]
    data["camera"]["position"] = [0.0, 0.0, 0.52]
    data["camera"]["focalPoint"] = [0.0, 0.0, 0.0]
    data["camera"]["fov"] = 88.8
    data["camera"]["viewup"] = [0.0, 1.0, 0.0]
    data["camera"]["distance"] = 0.52

    annotation_file = annotation_path + img_path.split("\\")[-1].split(".")[0] + ".json"
    if not os.path.exists(os.path.dirname(annotation_file)):
        os.makedirs(os.path.dirname(annotation_file))
    with open(annotation_file, 'w+') as f:
        json.dump(data, f, indent=4)


if __name__ == '__main__':

    scene_folder = "F:\\my_desktop\\PycharmFiles\\3D_detection\\labelimg3d\\KITTI_test"
    img_path = os.path.join(scene_folder, 'images')
    label_path = os.path.join(scene_folder, 'label')
    model_path = os.path.join(scene_folder, 'models')
    calib_path = os.path.join(scene_folder, 'calib')
    distance = 0.52
    if not os.path.exists(scene_folder) or not os.path.exists(img_path) or not os.path.exists(
            label_path) or not os.path.exists(model_path) or not os.path.exists(model_path) or not os.path.exists(
            calib_path):
        exit("The file path does not exist")

    annotation_path = "\\".join(model_path.split("\\")[:-1]) + "\\annotations\\" + img_path.split("\\")[-1] + "\\"
    img_path = get_all_path(img_path)
    label_path = get_all_path(label_path)
    calib_path = get_all_path(calib_path)

    for i in range(0, len(img_path)):
        img = img_path[i]
        label = label_path[i]
        calib = calib_path[i]
        if img.split("\\")[-1].split(".")[0] == label.split("\\")[-1].split(".")[0] == calib.split("\\")[-1].split(".")[
            0]:
            KITTI_2_LabelImg3D(img, label, model_path, annotation_path, calib, distance)
