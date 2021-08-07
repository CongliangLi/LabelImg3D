import json
import yaml
import os
from math import pow, sqrt
from libs.utils.utils import parse_yaml


# Convert labelimg3d model.json to EfficentPose models_info.yml
def model_trans(models_path_input, model_path_output):
    with open(models_path_input + "/models.json", 'r') as load_f:
        model_json_data = json.load(load_f)

    model_data = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}, 6: {}}
    for d in model_data:
        for j_d in model_json_data:
            if model_json_data[j_d]["class_index"] == int(d):
                model_data[d]["diameter"] = sqrt(pow(model_json_data[j_d]["size"][0], 2) +
                                                 pow(model_json_data[j_d]["size"][1], 2) +
                                                 pow(model_json_data[j_d]["size"][2], 2))

                model_data[d]["min_x"] = -model_json_data[j_d]["size"][0] / 2
                model_data[d]["min_y"] = -model_json_data[j_d]["size"][1] / 2
                model_data[d]["min_z"] = -model_json_data[j_d]["size"][2] / 2

                model_data[d]["size_x"] = model_json_data[j_d]["size"][0]
                model_data[d]["size_y"] = model_json_data[j_d]["size"][1]
                model_data[d]["size_z"] = model_json_data[j_d]["size"][2]
                break
    with open(model_path_output + "/models_info.yml", "w", encoding="utf-8") as f:
        yaml.dump(model_data, f, allow_unicode=True)

    # yaml_file = parse_yaml(model_path_output + "/models_info.yml")


# Convert labelimg3d json to EfficentPose info.yml
def camera_trans():
    pass


# Convert labelimg3d json to EfficentPose gt.yml
def img_trans():
    pass


if __name__ == '__main__':
    scene_path = "F:/my_desktop/PycharmFiles/3D_detection/labelimg3d/scenes/KITTI"
    models_path = scene_path + "/models"
    annotation_path = scene_path + "/annotations"

    efficentPose_path = "F:/my_desktop/PycharmFiles/3D_detection/EfficientPose/kitti"
    efficentPose_models_path = efficentPose_path + "/models"

    model_trans(models_path, efficentPose_models_path)
