import os
import utils
import json
import math
import numpy as np
import pandas as pd
import cv2 as cv

class DrawModel:
    def __init__(self, xml_path=None, image_path=None, save_path=None, fov = 60):
        self.xml_path = xml_path
        self.save_path = save_path
        self.image_path = image_path
        self.fov = fov
        distance = utils.get_distance(fov)
        self.camera_position_3d_point = [0, 0, distance]
        self.save_json_path = os.path.join(self.save_path, "annotations")
        self.save_image_path = os.path.join(self.save_path, "images")
        self.all_xml = [xml for xml in os.listdir(xml_path)]
        # self.models = self.read_model("E:/UA-DETRAC/img00003.json")
        self.base_url = "images"

    def read_xml(self):
        pass

    def read_json(self, path):
        with open(path, 'r') as load_f:
            data = json.load(load_f)
        return data

    def read_model(self, path):
        with open(path, 'r') as load_f:
            data = json.load(load_f)
            models = data["model"]
        return models

    def get_image_name_list(self, path):
        name_list = []
        for file in os.listdir(path):
            name_list.append(os.path.splitext(file)[0])
        return name_list

    def get_one_frame_data(self, path):
        dict = {}
        all_frames = utils.read_mot_file(path)
        for frame_index, frames in enumerate(all_frames):
            for index, track_id in frames["track_id"].items():
                list = [frames[value][index] for value in frames]
                if track_id not in dict:
                    dict[track_id] = []
                    dict[track_id].append(list)
                else:
                    dict[track_id].append(list)
        return dict

    def draw(self):
        for xml in self.all_xml:
            xml_name = os.path.splitext(xml)[0]
            dict = self.get_one_frame_data(os.path.join(self.xml_path, xml))  # Get all id data
            image_name_list = self.get_image_name_list(os.path.join(self.image_path, xml_name))
            image_name_list = sorted(image_name_list)
            for id, value in dict.items():
                polar_value = self.find_value(value)
                for data_list in polar_value:
                    self.rw_json(xml_name, data_list, image_name_list)
                    # print(polar_value)

    def rw_json(self, xml_name, data_list, image_name_list):
        image_name = image_name_list[data_list[0] - 1]
        json_name = image_name + ".json"
        image_name = image_name + ".jpg"
        json_dir_path = os.path.join(self.save_json_path, xml_name)
        if not os.path.exists(json_dir_path):
            os.makedirs(json_dir_path)

        json_path = os.path.join(json_dir_path, json_name)
        if not os.path.exists(json_path):
            current_json = self.read_json("E:/UA-DETRAC/img00002.json")
            current_json["image_file"] = os.path.join(self.base_url, xml_name, image_name)
        else:
            current_json = self.read_json(json_path)
        num = current_json["model"]["num"]

        object_type = data_list[4]
        current_json["model"][str(num)] = self.read_model("E:/UA-DETRAC/img00003.json")[str(object_type)]
        current_json["model"][str(num)]["actor_id"] = int(data_list[1])
        model_width = current_json["model"][str(num)]["size"][1]
        try:
            x, y, z = self.get_real_model_position(self.camera_position_3d_point, data_list[2], model_width)
        except:
            print(xml_name, image_name, data_list)
            return -1
        current_json["model"][str(num)]["matrix"][3] = x
        current_json["model"][str(num)]["matrix"][7] = y
        current_json["model"][str(num)]["matrix"][11] = z

        current_json["model"]["num"] += 1

        with open(json_path, 'w+') as f:
            json.dump(current_json, f, indent=4)

        self.draw_rectangle(xml_name, data_list[2], image_name)

    def draw_rectangle(self, xml_name, point, image_name):
        image_save_dir_path = os.path.join(self.save_image_path, xml_name)
        if not os.path.exists(image_save_dir_path):
            os.makedirs(image_save_dir_path)
        image_save_path = os.path.join(image_save_dir_path, image_name)

        if not os.path.exists(image_save_path):
            image = cv.imread(os.path.join(self.image_path, xml_name, image_name))
        else:
            image = cv.imread(image_save_path)
        image = utils.draw_box(image, point, (0, 0, 255))
        cv.imwrite(image_save_path, image)

    def find_value(self, value_list):
        # polar_value = [value_list[0], value_list[-1]]
        polar_value = []
        for value in value_list:
            if value[3] <= 0.3:  # The value of overlap_ratio
                polar_value.append(value)
                break

        polar_value.append(value_list[int(len(value_list) / 2) - 1])

        for value in reversed(value_list):
            if value[3] <=0.3:  # The value of overlap_ratio
                polar_value.append(value)
                break
        return polar_value

    def get_real_model_position(self, camera_3d_point, _image_points, _model_width):
        image_size = [960, 540]
        normalization_image_point1 = (
            _image_points[0] - 0.5 * image_size[0], -_image_points[1] + 0.5 * image_size[1], 0)
        normalization_image_point3 = (
            _image_points[2] - 0.5 * image_size[0], -_image_points[3] + 0.5 * image_size[1], 0)
        normalization_image_point1 = [p / image_size[0] for p in normalization_image_point1]
        normalization_image_point3 = [p / image_size[0] for p in normalization_image_point3]

        this_diatance = 0
        for i in np.arange(0, -10000, -0.5):
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
    xml_path = "E:/UA-DETRAC/DETRAC-Train-Annotations-XML"
    image_path = "E:/UA-DETRAC/Insight-MVT_Annotation_Train"
    save_path = "E:/UA-DETRAC/dataset"
    draw_model = DrawModel(xml_path, image_path, save_path)
    draw_model.draw()
