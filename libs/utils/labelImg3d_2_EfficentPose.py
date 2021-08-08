import json
import os
import shutil
from math import pow, sqrt
from PIL import Image
import yaml

from libs.utils.utils import get_all_path, get_camera_intrinsics, get_dirname, parse_yaml


# Convert labelimg3d model.json to EfficentPose models_info.yml
def model_trans(li3d_scene_path, ep_path):
    li3d_models_path = li3d_scene_path + "/models"
    li3d_annotation_path = li3d_scene_path + "/annotations"
    li3d_img_path = li3d_scene_path + "/images"

    ep_models_path = ep_path + "/models"
    ep_data_path = ep_path + "/data"

    with open(li3d_models_path + "/models.json", 'r') as load_f:
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

    if not os.path.exists(os.path.dirname(ep_models_path + "/models_info.yml")):
        os.makedirs(os.path.dirname(ep_models_path + "/models_info.yml"))
    with open(ep_models_path + "/models_info.yml", "w", encoding="utf-8") as f:
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

    annotations = get_all_path(li3d_annotation_path)

    for class_num in range(1, len(model_json_data) + 1):
        if not os.path.exists(os.path.dirname(ep_data_path + "/{}/rgb/".format("%02d" % class_num))):
            os.makedirs(os.path.dirname(ep_data_path + "/{}/rgb/".format("%02d" % class_num)))

        gt_yml = {}
        num = 0

        cam_R_m2c = [1, 0, 0,
                     0, 1, 0,
                     0, 0, 1]

        for annotation in annotations:
            with open(annotation, 'r') as load_f:
                # print(annotation)
                annotation_data = json.load(load_f)

            for i in range(0, annotation_data["model"]["num"]):
                if annotation_data["model"][str(i)]["class"] is not class_num:
                    continue

                ep_data_path + "/" + "%02d" % annotation_data["model"][str(i)]["class"]
                gt_yml[num] = {"cam_R_m2c": cam_R_m2c,
                               "cam_t_m2c": [0, 0, annotation_data["camera"]["distance"]],
                               "obj_bb": annotation_data["model"][str(i)]["2d_bbox"],
                               "obj_id": annotation_data["model"][str(i)]["class"]}

                this_img_path = os.path.join(li3d_scene_path, annotation_data["image_file"])
                copy_img_path = os.path.join(
                    ep_data_path + "/{}/rgb".format("%02d" % annotation_data["model"][str(i)]["class"]),
                    "{}.png".format("%04d" % num))
                shutil.copyfile(this_img_path, copy_img_path)
                # print(num)
                num += 1

        with open(ep_data_path + "/{}/gt.yml".format("%02d" % class_num), "w",
                  encoding="utf-8") as f:
            yaml.dump(gt_yml, f, allow_unicode=True)


# Convert labelimg3d json to EfficentPose info.yml
def camera_trans(li3d_scene_path, ep_path):
    li3d_models_path = li3d_scene_path + "/models"
    li3d_annotation_path = li3d_scene_path + "/annotations"
    li3d_img_path = li3d_scene_path + "/images"

    ep_models_path = ep_path + "/models"
    ep_data_path = ep_path + "/data"

    annotations = get_all_path(li3d_annotation_path)
    with open(annotations[0], 'r') as load_f:
        annotation_data = json.load(load_f)

    fov = annotation_data["camera"]["fov"]

    images = get_all_path(li3d_img_path)

    img_size = Image.open(images[0]).size

    cam_K = get_camera_intrinsics(fov, img_size)

    depth_scale = 1.0

    for path in get_dirname(ep_data_path):
        file_path = os.path.join(path, "rgb")
        info_yml = {}
        for i in range(len(get_all_path(file_path))):
            info_yml[i] = {"cam_K": cam_K,
                           "depth_scale": depth_scale}

        with open(os.path.join(path, "info.yml"), "w", encoding="utf-8") as f:
            yaml.dump(info_yml, f, allow_unicode=True)
        # yaml_file = parse_yaml(os.path.join(path, "info.yml"))


def train_test(ep_path):
    ep_data_path = ep_path + "/data"
    for path in get_dirname(ep_data_path):
        rgb_path = os.path.join(path, "rgb")
        img_path = get_all_path(rgb_path)
        train_txt = []
        test_txt = []
        for i in range(0, len(img_path)):
            if i < len(img_path) / 2:
                train_txt.append(img_path[i].split("\\")[-1].split(".")[0])
            else:
                test_txt.append(img_path[i].split("\\")[-1].split(".")[0])
        with open(os.path.join(path, "train.txt"), 'w') as f:
            for txt in train_txt:
                f.write(txt + '\n')

        with open(os.path.join(path, "test.txt"), 'w') as f:
            for txt in train_txt:
                f.write(txt + '\n')


def li3d_2_efficentpose(input_path, output_path):
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    model_trans(input_path, output_path)
    img_trans(input_path, output_path)
    camera_trans(input_path, output_path)
    train_test(output_path)


if __name__ == '__main__':
    scene_path = "F:/my_desktop/kitti"

    efficentPose_path = "F:/my_desktop/PycharmFiles/3D_detection/EfficientPose/kitti"
    li3d_2_efficentpose(scene_path, efficentPose_path)
