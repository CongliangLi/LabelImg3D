import json
import yaml
import os, sys, shutil
from math import pow, sqrt
from libs.utils.utils import parse_yaml, get_all_path


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

    if not os.path.exists(os.path.dirname(model_path_output + "/models_info.yml")):
        os.makedirs(os.path.dirname(model_path_output + "/models_info.yml"))
    with open(model_path_output + "/models_info.yml", "w", encoding="utf-8") as f:
        yaml.dump(model_data, f, allow_unicode=True)

    # yaml_file = parse_yaml(model_path_output + "/models_info.yml")


# Convert labelimg3d json to EfficentPose gt.yml
def img_trans(li3d_scene_path, ep_path):
    li3d_models_path = li3d_scene_path + "/models"
    li3d_annotation_path = li3d_scene_path + "/annotations"
    li3d_img_path = li3d_scene_path + "/images"

    ep_models_path = ep_path + "/models"
    ep_data_path = ep_path + "/data"

    with open(li3d_models_path + "/models.json", 'r') as load_f:
        model_json_data = json.load(load_f)
    for i in range(1, len(model_json_data) + 1):
        if not os.path.exists(os.path.dirname(ep_data_path + "/{}/rgb/".format("%02d" % i))):
            os.makedirs(os.path.dirname(ep_data_path + "/{}/rgb/".format("%02d" % i)))

    gt_yml = {}
    num = 0

    annotations = get_all_path(li3d_annotation_path)
    for annotation in annotations:
        with open(annotation, 'r') as load_f:
            annotation_data = json.load(load_f)

        for i in range(0, annotation_data["model"]["num"]):
            ep_data_path + "/" + "%02d" % annotation_data["model"][str(i)]["class"]
            gt_yml[num] = {"cam_R_m2c": [1, 0, 0,
                                         0, 1, 0,
                                         0, 0, 1],
                           "cam_t_m2c": [0, 0, annotation_data["camera"]["distance"]],
                           "obj_bb": "",
                           "obj_id": annotation_data["model"][str(i)]["class"]}

            this_img_path = os.path.join(li3d_scene_path, annotation_data["image_file"])
            copy_img_path = os.path.join(
                ep_data_path + "/{}/rgb".format("%02d" % annotation_data["model"][str(i)]["class"]),
                "{}.png".format("%04d" % num))
            shutil.copyfile(this_img_path, copy_img_path)

            with open(ep_data_path + "/{}/gt.yml".format("%02d" % annotation_data["model"][str(i)]["class"]), "w+",
                      encoding="utf-8") as f:
                yaml.dump(gt_yml, f, allow_unicode=True)
            print(num)
            num += 1


    pass


# Convert labelimg3d json to EfficentPose info.yml
def camera_trans():
    pass


if __name__ == '__main__':
    scene_path = "F:/my_desktop/kitti"
    models_path = scene_path + "/models"
    annotation_path = scene_path + "/annotations"
    img_path = scene_path + "/images"

    efficentPose_path = "F:/my_desktop/PycharmFiles/3D_detection/EfficientPose/kitti"
    efficentPose_models_path = efficentPose_path + "/models"
    efficentPose_data_path = efficentPose_path + "/data"

    # model_trans(models_path, efficentPose_models_path)

    img_trans(scene_path, efficentPose_path)
