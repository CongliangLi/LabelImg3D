import os
import utils
import json
import math
import numpy as np
import pandas as pd
import cv2 as cv

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
    xml_path = "E:/UA-DETRAC/DETRAC-Train-Annotations-XML/"
    image_path = "E:/UA-DETRAC/Insight-MVT_Annotation_Train/"
    json_path = "E:/UA-DETRAC/model_json/"
    image_save_root_path = "E:/UA-DETRAC/changed_images"
    base_json_path = "E:/UA-DETRAC/img00002.json"
    base_model_path = "E:/UA-DETRAC/img00003.json"
    base_url = "images"

    for xml in os.listdir(xml_path):
        # Each xml represents a video and have one id_list
        name = os.path.splitext(xml)[0]

        all_frames = utils.read_mot_file(os.path.join(xml_path, xml))  # Get all frames of the video

        id_list = [value for i, value in all_frames[0]["track_id"].items()]

        models = get_base_model(base_model_path)
        image_name_list = get_image_name_list(os.path.join(image_path, name))
        distance = utils.get_distance(fov)

        camera_position_3d_point = [0, 0, distance]

        json_save_path = os.path.join(json_path, name)
        if not os.path.exists(json_save_path):
            os.makedirs(json_save_path)

        image_save_path = os.path.join(image_save_root_path, name)
        if not os.path.exists(image_save_path):
            os.makedirs(image_save_path)

        for frame_index, frame in enumerate(all_frames): ###########

            json_file_name = image_name_list[frame_index] + ".json"
            image_name = image_name_list[frame_index] + ".jpg"
            if image_name == "img00157.jpg":
                print(1)
            image = cv.imread(os.path.join(image_path, name, image_name))
            points = []

            json_file = os.path.join(json_save_path, json_file_name)

            current_json = get_base_json(base_json_path)
            current_json["image_file"] = os.path.join(base_url, name, image_name)
            model = current_json["model"]

            # print("{}，{}".format(name, image_name))

            # Plotting the model of the disappearing point
            if frame_index:
                current_id_list = [value for i, value in frame["track_id"].items()]
                previous_frame = all_frames[frame_index - 1]
                previous_image_name = image_name_list[frame_index - 1] + '.jpg'

                if previous_image_name == "img00157.jpg":
                    print(2)

                previous_image_path = os.path.join(image_save_root_path, name, previous_image_name)
                if not os.path.exists(previous_image_path):
                    previous_image = cv.imread(os.path.join(image_path, name, previous_image_name))
                else:
                    previous_image = cv.imread(os.path.join(image_save_root_path, name, previous_image_name))

                #  find the vanish point of current frame correspond to the previous frame
                previous_json_file_name = image_name_list[frame_index - 1] + ".json"
                previous_json_file = os.path.join(json_path, name, previous_json_file_name)
                if not os.path.exists(previous_json_file):
                    previous_json = get_base_json(base_json_path)
                    previous_json["image_file"] = os.path.join(base_url, name, previous_image_name)
                else:
                    previous_json = get_base_json(previous_json_file)


                previous_model = previous_json["model"]
                num = previous_model["num"]
                previous_points = []
                del_index = []
                for id, current_id_value in enumerate(id_list):
                    if current_id_value not in current_id_list:
                        del_index.append(current_id_value)
                        index = list(previous_frame["track_id"]).index(current_id_value)
                        # 1.draw 2d bounding box
                        image_points = previous_frame["bbox_2d"][index]
                        previous_points.append(image_points)

                        # 2.chang model position
                        previous_model[str(num)] = {}
                        object_type = previous_frame["object_type"][index]

                        for key, value in models[str(object_type)].copy().items():
                            # print(id(models[str(object_type)].copy()))
                            if key == "matrix":
                                previous_model[str(num)][key] = value.copy()
                            else:
                                previous_model[str(num)].update({key: value})

                        model_width = previous_model[str(num)]["size"][1]
                        try:
                            x, y, z = get_real_model_position(camera_position_3d_point, image_points, model_width)
                            previous_model[str(num)]["matrix"][3] = x
                            previous_model[str(num)]["matrix"][7] = y
                            previous_model[str(num)]["matrix"][11] = z
                        except Exception as e:
                            print("{}，{}".format(name, image_name))

                        previous_model["num"] += 1
                        num += 1
                if del_index:
                    for value in del_index:
                        index = id_list.index(value)
                        del id_list[index]
                if previous_points:
                    for point in previous_points:
                        previous_image = utils.draw_box(previous_image, point, (0, 0, 255))
                    cv.imwrite(os.path.join(image_save_root_path, name, previous_image_name), previous_image)
                    previous_json["model"] = previous_model
                    with open(previous_json_file, 'w+') as f:
                        json.dump(previous_json, f, indent=4)

            # Draw the model of the upcoming
            num = 0
            for index, id_value in frame["track_id"].items():  # Each item of one frame

                if id_value not in id_list:

                    id_list.append(id_value)
                    # we will do two things:
                    # 1.draw 2d bounding box
                    image_points = frame["bbox_2d"][index]

                    points.append(image_points)

                    # 2.chang model position
                    model[str(num)] = {}
                    object_type = frame["object_type"][index]

                    for key, value in models[str(object_type)].copy().items():
                        # print(id(models[str(object_type)].copy()))
                        if key == "matrix":
                            model[str(num)][key] = value.copy()
                        else:
                            model[str(num)].update({key: value})

                    model_width = model[str(num)]["size"][1]
                    try:
                        x, y, z = get_real_model_position(camera_position_3d_point, image_points, model_width)
                        model[str(num)]["matrix"][3] = x
                        model[str(num)]["matrix"][7] = y
                        model[str(num)]["matrix"][11] = z
                    except Exception as e:
                        print("{}，{}".format(name, image_name))

                    model["num"] += 1
                    num += 1


            if points:
                for point in points:
                    image = utils.draw_box(image, point, (0, 0, 255))
                cv.imwrite(os.path.join(image_save_path, image_name), image)
                current_json["model"] = model
                with open(json_file, 'w+') as f:
                    json.dump(current_json, f, indent=4)

