import json
import os
import shutil
from math import pow, sqrt
from PIL import Image
import yaml
from cv2 import imread, line, imshow, waitKey, imwrite
from libs.utils.utils import get_all_path, get_camera_intrinsics, get_dirname, parse_yaml, draw_projected_box3d, \
    get_R_obj2c, get_T_obj2c, load_model_ply, get_T_obj_bottom2center, axis_angle_to_rotation_mat, \
    rotation_mat_to_axis_angle, draw_box
import numpy as np
import cv2


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
                                                 pow(model_json_data[j_d]["size"][2], 2)) * 1000

                model_data[d]["min_x"] = -model_json_data[j_d]["size"][0] / 2 * 1000
                model_data[d]["min_y"] = -model_json_data[j_d]["size"][1] / 2 * 1000
                model_data[d]["min_z"] = 0

                model_data[d]["size_x"] = model_json_data[j_d]["size"][0] * 1000
                model_data[d]["size_y"] = model_json_data[j_d]["size"][1] * 1000
                model_data[d]["size_z"] = model_json_data[j_d]["size"][2] * 1000
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

        if not os.path.exists(os.path.dirname(ep_data_path + "/{}/truth_2d/".format("%02d" % class_num))):
            os.makedirs(os.path.dirname(ep_data_path + "/{}/truth_2d/".format("%02d" % class_num)))

        if not os.path.exists(os.path.dirname(ep_data_path + "/{}/truth_3d/".format("%02d" % class_num))):
            os.makedirs(os.path.dirname(ep_data_path + "/{}/truth_3d/".format("%02d" % class_num)))

        gt_yml = {}
        num = 0

        for annotation in annotations:
            with open(annotation, 'r') as load_f:
                # print(annotation)
                annotation_data = json.load(load_f)

            for i in range(0, annotation_data["model"]["num"]):
                if annotation_data["model"][str(i)]["class"] is not class_num:
                    continue

                T_model_bottom2center = get_T_obj_bottom2center(annotation_data["model"][str(i)]["size"])

                R_obj2c = get_R_obj2c(np.array(annotation_data["model"][str(i)]["matrix"]))
                cam_R_m2c = R_obj2c.reshape(1, 9).tolist()[0]

                T_obj2c = get_T_obj2c(np.array(annotation_data["model"][str(i)]["matrix"]),
                                      annotation_data["camera"]["fov"])
                # cam_t_m2c = (T_model_bottom2center + T_obj2c).reshape(1, 3).tolist()[0]
                cam_t_m2c = T_obj2c.reshape(1, 3).tolist()[0]

                ep_data_path + "/" + "%02d" % annotation_data["model"][str(i)]["class"]
                # a, b, c, d = annotation_data["model"][str(i)]["2d_bbox"]
                # rmin, rmax, cmin, cmax = int(b), int(d), int(a), int(c)
                # obj_bb = [rmin, rmax, cmin, cmax]
                obj_bb = annotation_data["model"][str(i)]["2d_bbox"]

                gt_yml[num] = [{"cam_R_m2c": cam_R_m2c,
                                "cam_t_m2c": [-cam_t_m2c[0] * 1000, cam_t_m2c[1] * 1000, -cam_t_m2c[2] * 1000],
                                "obj_bb": obj_bb,
                                "obj_id": annotation_data["model"][str(i)]["class"]}]

                this_img_path = os.path.join(li3d_scene_path, annotation_data["image_file"])
                copy_img_path = os.path.join(
                    ep_data_path + "/{}/rgb".format("%02d" % annotation_data["model"][str(i)]["class"]),
                    "{}.png".format("%04d" % num))
                shutil.copyfile(this_img_path, copy_img_path)

                # truth 2d bbox
                truth2d_img_path = os.path.join(
                    ep_data_path + "/{}/truth_2d".format("%02d" % annotation_data["model"][str(i)]["class"]),
                    "{}.png".format("%04d" % num))
                # shutil.copyfile(this_img_path, copy_img_path)
                img = imread(this_img_path)
                # a, b, c, d = annotation_data["model"][str(i)]["2d_bbox"]
                img = draw_box(img.copy(), annotation_data["model"][str(i)]["2d_bbox"])
                imwrite(truth2d_img_path, img)

                # end truth of 2d bbox

                # truth 3d bbox
                truth3d_img_path = os.path.join(
                    ep_data_path + "/{}/truth_3d".format("%02d" % annotation_data["model"][str(i)]["class"]),
                    "{}.png".format("%04d" % num))

                img = imread(this_img_path)
                img = draw_projected_box3d(img.copy(), np.array(annotation_data["model"][str(i)]["3d_bbox"])[:, :2])
                imwrite(truth3d_img_path, img)
                # end truth of 3d bbox

                num += 1

        with open(ep_data_path + "/{}/gt.yml".format("%02d" % class_num), "w",
                  encoding="utf-8") as f:
            yaml.dump(gt_yml, f, default_flow_style=False)


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
    depth_scale = 1.0

    for path in get_dirname(ep_data_path):
        file_path = os.path.join(path, "rgb")
        info_yml = {}
        all_img_opath = get_all_path(file_path)
        for i in range(len(all_img_opath)):
            img_size = Image.open(all_img_opath[i]).size

            cam_K = [get_camera_intrinsics(fov, img_size)]

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


def test(ep_path):
    ep_models_path = ep_path + "/models"
    ep_data_path = ep_path + "/data"
    model_3d_points = load_model_ply(path_to_ply_file=os.path.join(ep_models_path, "obj_{:02}.ply".format(2)))
    class_to_model_3d_points = {0: model_3d_points}
    name_to_model_3d_points = {"object": model_3d_points}
    all_3d_models = class_to_model_3d_points

    ep_data_2_rgb = os.path.join(os.path.join(ep_data_path, "02"), "rgb")
    all_img_paths = get_all_path(ep_data_2_rgb)
    info_yml = parse_yaml(os.path.join(os.path.join(ep_data_path, "02"), "info.yml"))
    gt_yml = parse_yaml(os.path.join(os.path.join(ep_data_path, "02"), "gt.yml"))

    for i in range(len(all_img_paths)):
        img = cv2.imread(all_img_paths[i])
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        camera_matrix = np.array(info_yml[i]["cam_K"]).reshape(3, 3)
        annotations = gt_yml[i][0]
        assigned_translation = np.array(annotations["cam_t_m2c"])
        ass = np.array(annotations["cam_R_m2c"]).reshape(3, 3)
        model_3d_points = all_3d_models[0]
        # model_3d_points[:, :] = 0
        assigned_rotation = rotation_mat_to_axis_angle(ass)
        assigned_rotation = axis_angle_to_rotation_mat(assigned_rotation)

        transformed_points_gt = np.dot(model_3d_points, assigned_rotation.T) + np.squeeze(assigned_translation)

        # #draw transformed gt points in image to test the transformation
        img_gt = draw_point3d(img.copy(), camera_matrix, transformed_points_gt)

        img_gt = draw_box(img_gt, annotations["obj_bb"])

        if not os.path.exists(
                os.path.dirname("F:/my_desktop/PycharmFiles/3D_detection/EfficientPose/kitti/data/02/truth_obj/")):
            os.makedirs(
                os.path.dirname("F:/my_desktop/PycharmFiles/3D_detection/EfficientPose/kitti/data/02/truth_obj/"))

        cv2.imwrite(
            "F:/my_desktop/PycharmFiles/3D_detection/EfficientPose/kitti/data/02/truth_obj/{}.png".format(i),
            img_gt)


def draw_point3d(image, camera_matrix, points_3d):
    """ Projects and draws 3D points onto a 2D image and shows the image for debugging purposes

    # Arguments
        image: The image to draw on
        camera_matrix: numpy array with shape (3, 3) containing the camera matrix
        points_3d: numpy array with shape (num_3D_points, 3) containing the 3D points to project and draw (usually the object's 3D points transformed with the ground truth 6D pose)
    """
    points_2D, jacobian = cv2.projectPoints(points_3d, np.zeros((3,)), np.zeros((3,)), camera_matrix, None)
    points_2D = np.squeeze(points_2D)
    points_2D = np.copy(points_2D).astype(np.int32)

    tuple_points = tuple(map(tuple, points_2D))
    for point in tuple_points:
        cv2.circle(image, point, 2, (255, 0, 0), -1)

    # cv2.imshow('image', image)
    # cv2.waitKey(0)
    return image


if __name__ == '__main__':
    scene_path = "F:/my_desktop/kitti"
    efficentPose_path = "F:/my_desktop/PycharmFiles/3D_detection/EfficientPose/kitti"
    li3d_2_efficentpose(scene_path, efficentPose_path)
    test(efficentPose_path)
