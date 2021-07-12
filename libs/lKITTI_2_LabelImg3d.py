import os
from libs.utils import roty, get_all_path
import numpy as np
import pandas as pd
import json


def KITTI_2_LabelImg3D(img_path, label_path, model_path, annotation_path, c_distance):
    a = pd.read_table(label_path, sep=' ', header=None)
    with open(model_path + "/models.json", 'r') as load_f:
        model_json_data = json.load(load_f)
    model_data = {"Tram": {}, "Car": {}, "Track": {}, "Van": {}, "Pedestrian": {}}
    for d in model_data:
        for j_d in model_json_data:
            if model_json_data[j_d]["class_name"] == d:
                model_data[d]["path"] = "models\\" + j_d
                model_data[d]["index"] = model_json_data[j_d]["class_index"]
                model_data[d]["size"] = model_json_data[j_d]["size"]
                break
    data = {}

    data["image_file"] = "//".join(img_path.split("\\")[len(img_path.split("\\")) - 3:len(img_path.split("\\"))])

    data["model"] = {}
    data["model"]["num"] = 0
    num = 0
    for i in range(0, len(a)):
        obj_class = a[0][i]

        if obj_class == "Cyclist" or obj_class == "DontCare" or obj_class == "Misc":
            continue

        obj_position_c = [a[j][i] for j in range(11, 14)]
        obj_position_w = np.array([obj_position_c[0], -obj_position_c[1], -(obj_position_c[2] - c_distance)])

        obj_alpha = a[3][i]
        R_oL2oK = [[0, -1, 0],  # Rotate 90 degrees clockwise around the X axis
                   [1, 0, 0],
                   [0, 0, 1]]

        obj_r_y = a[14][i]
        R_oK2c = roty(obj_r_y)
        R_c2w_1 = [[0, -1, 0],
                   [1, 0, 0],
                   [0, 0, 1]]
        R_c2w_2 = [[1, 0, 0],
                   [0, -1, 0],
                   [0, 0, -1]]
        R_c2w = np.dot(R_c2w_1, R_c2w_2)
        R_oL2w = np.dot(np.dot(R_oL2oK, R_oK2c), R_c2w)

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
    img_path = "F:\\my_desktop\\PycharmFiles\\3D_detection\\labelimg3d\\KITTI_test\\images\\scene1"
    label_path = 'F:\\my_desktop\\PycharmFiles\\3D_detection\\labelimg3d\\KITTI_test\\label\\scene1'
    model_path = "F:\\my_desktop\\PycharmFiles\\3D_detection\\labelimg3d\\KITTI_test\\models"
    distance = 0.52

    annotation_path = "\\".join(model_path.split("\\")[:-1]) + "\\annotations\\" + img_path.split("\\")[-1] + "\\"
    img_path = get_all_path(img_path)
    label_path = get_all_path(label_path)

    for i in range(0, len(img_path)):
        img = img_path[i]
        label = label_path[i]
        if img.split("\\")[-1].split(".")[0] == label.split("\\")[-1].split(".")[0]:
            KITTI_2_LabelImg3D(img, label, model_path, annotation_path, distance)
