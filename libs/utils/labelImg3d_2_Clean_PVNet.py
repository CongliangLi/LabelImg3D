import json
import os
import shutil
from math import pow, sqrt
from PIL import Image
import yaml
from cv2 import imread, line, imshow, waitKey, imwrite
from libs.utils.utils import get_all_path, get_camera_intrinsics, get_dirname, parse_yaml, \
    get_R_obj2c, get_T_obj2c, load_model_ply, axis_angle_to_rotation_mat, \
    rotation_mat_to_axis_angle, draw_box, get_mask_img, get_fps_points, trans_3d_2_2d
import numpy as np
import cv2


# get diameter from ply files
def model_trans(type_path):
    model_path = os.path.join(type_path, "model.ply")
    diameter_path = os.path.join(type_path, "diameter.txt")

    model = load_model_ply(model_path).T
    model_diameter = pow(sqrt(model[0].max() - model[0].min()) + sqrt(model[0].max() - model[0].min()) + \
                         sqrt(model[0].max() - model[0].min()), 0.5)
    with open(diameter_path, 'w') as f:
        f.write(str(model_diameter))

    # Convert labelimg3d json to EfficentPose gt.yml


# get camera intrinsics from annotations
def camera_trans(li3d_scene_path, type_path):
    li3d_annotation_path = li3d_scene_path + "/annotations"
    li3d_img_path = li3d_scene_path + "/images"
    camera_path = os.path.join(type_path, "camera.txt")

    annotations = get_all_path(li3d_annotation_path)
    with open(annotations[0], 'r') as load_f:
        annotation_data = json.load(load_f)

    fov = annotation_data["camera"]["fov"]

    img_size = Image.open(get_all_path(li3d_img_path)[1]).size
    cam_K = np.array([get_camera_intrinsics(fov, img_size)]).reshape(3, 3)
    np.savetxt(camera_path, cam_K, fmt="%f", delimiter=" ")


def img_trans(li3d_scene_path, type_path, fps_num=8):
    this_class = type_path.split("\\")[-1]

    li3d_annotation_path = li3d_scene_path + "/annotations"
    li3d_img_path = li3d_scene_path + "/images"

    mask_path = os.path.join(type_path, "mask")
    rgb_path = os.path.join(type_path, "rgb")
    pose_path = os.path.join(type_path, "pose")
    fps_path = os.path.join(type_path, "fps.txt")
    train_json_path = os.path.join(type_path, "train.json")

    if not os.path.exists(mask_path):
        os.makedirs(mask_path)
    if not os.path.exists(rgb_path):
        os.makedirs(rgb_path)
    if not os.path.exists(pose_path):
        os.makedirs(pose_path)

    if not os.path.exists(os.path.dirname(train_json_path)):
        os.makedirs(os.path.dirname(train_json_path))

    model_3d_points = load_model_ply(os.path.join(type_path, "model.ply"))

    annotations = get_all_path(li3d_annotation_path)

    # get fps points
    model_center_3d = [0, 0, (model_3d_points.T[2].max() - model_3d_points.T[2].min()) / 2]
    fps_points = get_fps_points(model_3d_points, model_center_3d, fps_num)
    np.savetxt(fps_path, fps_points, fmt="%f", delimiter=" ")

    # get model 3d corner
    min_x = model_3d_points.T[0].min()
    min_y = model_3d_points.T[1].min()
    min_z = model_3d_points.T[2].min()
    max_x = model_3d_points.T[0].max()
    max_y = model_3d_points.T[1].max()
    max_z = model_3d_points.T[2].max()

    model_corner_3d = [[min_x, min_y, min_z], [min_x, min_y, max_z],
                       [min_x, max_y, min_z], [min_x, max_y, max_z],
                       [max_x, min_y, min_z], [max_x, min_y, max_z],
                       [max_x, max_y, min_z], [max_x, max_y, max_z]]

    train_json = {"images": [], "annotations": [], "categories": []}

    index = 0
    for annotation in annotations:
        with open(annotation, 'r') as load_f:
            annotation_data = json.load(load_f)

        for i in range(0, annotation_data["model"]["num"]):
            if annotation_data["model"][str(i)]["class_name"].strip() != this_class.strip():
                continue
            this_class_num = annotation_data["model"][str(i)]["class"]
            if this_class_num == 6:
                this_class_num = 5

            R_obj2c = get_R_obj2c(np.array(annotation_data["model"][str(i)]["matrix"])).T

            T_obj2c = get_T_obj2c(np.array(annotation_data["model"][str(i)]["matrix"]),
                                  annotation_data["camera"]["fov"])
            T_obj2c = [-T_obj2c[0], T_obj2c[1], -T_obj2c[2]]

            fov = annotation_data["camera"]["fov"]

            img_size = Image.open(get_all_path(li3d_img_path)[1]).size
            cam_K = np.array([get_camera_intrinsics(fov, img_size)]).reshape(3, 3)

            this_img_path = os.path.join(li3d_scene_path, annotation_data["image_file"])

            mask_img = get_mask_img(img_size, model_3d_points, R_obj2c, T_obj2c, cam_K)

            model_pose = np.column_stack([R_obj2c, T_obj2c])

            # save img, mask_img, pose
            shutil.copyfile(this_img_path, os.path.join(rgb_path, "{}.png".format(index)))
            cv2.imwrite(os.path.join(mask_path, "{}.png".format(index)), mask_img)
            np.save(os.path.join(pose_path, "pose{}.npy".format(index)), model_pose)

            image_json = {"file_name": "data/{}/rgb/{}.jpg".format(this_class, index), "height": img_size[1],
                          "width": img_size[0], "id": index}
            annotation_json = {'mask_path': "data/{}/mask/{}.jpg".format(this_class, index),
                               'image_id': index + 1,
                               'category_id': this_class_num,
                               'id': index,
                               'corner_3d': np.array(model_corner_3d).tolist(),
                               'corner_2d': annotation_data["model"][str(i)]["3d_bbox"],
                               'center_3d': model_center_3d,
                               'center_2d': trans_3d_2_2d([model_center_3d], R_obj2c, T_obj2c, cam_K).tolist(),
                               'fps_3d': fps_points.tolist(),
                               'fps_2d': trans_3d_2_2d(fps_points, R_obj2c, T_obj2c, cam_K).tolist(),
                               'K': cam_K.astype(np.float64).tolist(),
                               'pose': model_pose.tolist(),
                               'data_root': 'data/{}/rgb'.format(this_class),
                               'type': "real",
                               'cls': this_class
                               }

            category_json = [{'supercategory': 'none', 'id': this_class_num, 'name': this_class}]

            train_json["images"].append(image_json)
            train_json["annotations"].append(annotation_json)
            train_json["categories"] = category_json

            index += 1
            print(index)

    with open(train_json_path, 'w+') as f:
        json.dump(train_json, f, indent=4)


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


def li3d_2_PVNet(input_path, input_type, output_path):
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    for this_type in input_type:
        this_type_path = os.path.join(output_path, this_type)
        if not os.path.exists(this_type_path):
            os.makedirs(this_type_path)

        model_trans(this_type_path)
        camera_trans(input_path, this_type_path)
        img_trans(input_path, this_type_path)


if __name__ == '__main__':
    scene_path = "F:/my_desktop/kitti"
    PVNet_path = "F:/my_desktop/PycharmFiles/3D_detection/2. PVNet/data/KITTI"
    li3d_type = ["Car", "Tram", "Truck", "Van", "Pedestrian"]
    li3d_2_PVNet(scene_path, li3d_type, PVNet_path)
