import os
import utils
import json
import math
import numpy as np


def get_base_json(path):
    with open(path, 'r') as load_f:
        data = json.load(load_f)
    return data


def get_base_model(path):
    with open(path, 'r') as load_f:
        data = json.load(load_f)
        models = data["model"]
    return models


def get_image_name_list(path):
    name_list = []
    for file in os.listdir(path):
        name_list.append(os.path.splitext(file)[0])
    return name_list


def get_point_distance(point1, point2):
    _x = point1[0] - point2[0]
    _y = point1[1] - point2[1]
    _z = point1[2] - point2[2]
    return math.sqrt(math.pow(_x, 2) + math.pow(_y, 2) + math.pow(_z, 2))


def get_real_model_position(camera_3d_point, _image_points, _model_width):
    image_size = [960, 540]
    normalization_image_point1 = (_image_points[0] - 0.5 * image_size[0], -_image_points[1] + 0.5 * image_size[1], 0)
    normalization_image_point3 = (_image_points[2] - 0.5 * image_size[0], -_image_points[3] + 0.5 * image_size[1], 0)
    normalization_image_point1 = [p / image_size[0] for p in normalization_image_point1]
    normalization_image_point3 = [p / image_size[0] for p in normalization_image_point3]

    this_diatance = 0
    for i in np.arange(0, -600, -0.5):
        t = (i - camera_3d_point[2]) / (normalization_image_point1[2] - camera_3d_point[2])

        pre_distance = this_diatance
        this_diatance = math.fabs((t * (normalization_image_point1[1] - camera_3d_point[1]) + camera_3d_point[1]) -
                        (t * (normalization_image_point3[1] - camera_3d_point[1]) + camera_3d_point[1]))

        x1 = t * (normalization_image_point1[0] - camera_3d_point[0]) + camera_3d_point[0]
        y1 = t * (normalization_image_point1[1] - camera_3d_point[1]) + camera_3d_point[1]
        x2 = t * (normalization_image_point3[0] - camera_3d_point[0]) + camera_3d_point[0]
        y2 = t * (normalization_image_point3[1] - camera_3d_point[1]) + camera_3d_point[1]

        if _model_width - this_diatance < 0:
            x = (x1 + x2) / 2
            y = (y1 + y2) / 2
            return x, y, i


if __name__ == '__main__':
    fov = 60
    xml_path = "D:/TemporaryDocument/UA-DETRAC/DETRAC-Train-Annotations-XML/"
    image_path = "D:/TemporaryDocument/UA-DETRAC/Insight-MVT_Annotation_Train/"
    json_path = "D:/OtherFiles/PythonProject/labelimg3d/scenes/KITTI/annotations/"
    base_json_path = "D:/TemporaryDocument/UA-DETRAC/img00002.json"
    base_model_path = "D:/TemporaryDocument/UA-DETRAC/img00003.json"
    base_url = "images"

    for xml in os.listdir(xml_path):
        name = os.path.splitext(xml)[0]

        all_frames = utils.read_mot_file(os.path.join(xml_path, xml))
        base_json = get_base_json(base_json_path)
        models = get_base_model(base_model_path)
        image_name_list = get_image_name_list(os.path.join(image_path, name))
        distance = utils.get_distance(fov)

        camera_position_3d_point = [0, 0, distance]

        for i, frame in enumerate(all_frames):
            json_file_name = image_name_list[i] + ".json"
            image_name = image_name_list[i] + ".jpg"
            json_save_path = os.path.join(json_path, name)
            if not os.path.exists(json_save_path):
                os.makedirs(json_save_path)
            json_file = os.path.join(json_save_path, json_file_name)

            current_json = base_json
            current_json["image_file"] = os.path.join(base_url, name, image_name)
            model = current_json["model"]
            model["num"] = len(frame)

            print("{}，{}".format(name, image_name))
            for j, target in enumerate(frame):
                model[str(j)] = {}
                _id = target["id"]
                image_points = target["bbox_2d"]
                object_type = target["object_type"]

                for key, value in models[str(object_type)].copy().items():
                    # print(id(models[str(object_type)].copy()))
                    if key == "matrix":
                        model[str(j)][key] = value.copy()
                    else:
                        model[str(j)].update({key: value})

                model_width = model[str(j)]["size"][1]
                try:
                    x, y, z = get_real_model_position(camera_position_3d_point, image_points, model_width)
                    model[str(j)]["matrix"][3] = x
                    model[str(j)]["matrix"][7] = y
                    model[str(j)]["matrix"][11] = z
                except Exception as e:
                    print("{}，{}".format(name, image_name))


            current_json["model"] = model
            with open(json_file, 'w+') as f:
                json.dump(current_json, f, indent=4)
