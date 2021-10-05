import shutil
import json
import numpy as np
from libs.utils.utils import get_all_path, get_model_center_3d, trans_3d_2_2d, get_R_obj2c, get_T_obj2c, \
    get_camera_intrinsics, load_model_ply, get_mask_img
import os
from PIL import Image
from cv2 import imwrite
from math import sqrt, pow


def li3d_2_linemod(li3d_path, li3d_type, lm_path):
    model_path = os.path.join(li3d_path, "models")
    img_path = os.path.join(li3d_path, "images")
    anno_path = os.path.join(li3d_path, "annotations")

    annotations = get_all_path(anno_path)

    for this_class in li3d_type:
        num = 0
        this_class_path = os.path.join(lm_path, this_class)
        if not os.path.exists(this_class_path):
            os.makedirs(this_class_path)

        test_txt = list()
        train_txt = list()
        train_range_txt = list()

        # move model to linemod path
        this_model_path = os.path.join(model_path, "{}_001.obj".format(this_class))
        copy_model_path = os.path.join(this_class_path, "{}.obj".format(this_class))
        shutil.copyfile(this_model_path, copy_model_path)
        # TODO: Convert .obj format to .ply format, here we use meshlab to do that

        img_w, img_h = Image.open(get_all_path(img_path)[1]).size

        # move image to linemod path
        for annotation in annotations:
            with open(annotation, 'r') as load_f:
                # print(annotation)
                annotation_data = json.load(load_f)
            for i in range(0, annotation_data["model"]["num"]):
                if annotation_data["model"][str(i)]["class_name"] != this_class:
                    continue

                # get labels
                this_label_path = os.path.join(this_class_path, "labels")
                if not os.path.exists(this_label_path):
                    os.makedirs(this_label_path)

                this_class_num = annotation_data["model"][str(i)]["class"]

                model_center_3d = get_model_center_3d(os.path.join(this_class_path, "{}.ply".format(this_class)))
                # model_bbox_3d = get_model_bbox_3d(os.path.join(this_class_path, "{}.ply".format(this_class)))
                R_obj2c = get_R_obj2c(np.array(annotation_data["model"][str(i)]["matrix"])).T
                T_obj2c = get_T_obj2c(np.array(annotation_data["model"][str(i)]["matrix"]),
                                      annotation_data["camera"]["fov"])
                T_obj2c = [-T_obj2c[0], T_obj2c[1], -T_obj2c[2]]
                fov = annotation_data["camera"]["fov"]
                img_size = Image.open(get_all_path(img_path)[1]).size
                cam_K = np.array([get_camera_intrinsics(fov, img_size)]).reshape(3, 3)
                model_center_2d = trans_3d_2_2d([model_center_3d], R_obj2c, T_obj2c, cam_K).tolist()

                txt_data = list()
                txt_data.append(this_class_num)
                txt_data.append(model_center_2d[0] / img_w)
                txt_data.append(model_center_2d[1] / img_h)

                bbox_3d = np.array(annotation_data["model"][str(i)]["3d_bbox"])

                for p in range(len(bbox_3d)):
                    txt_data.append(float(bbox_3d[p][0] / img_w))
                    txt_data.append(float(bbox_3d[p][1] / img_h))

                x_range = (bbox_3d.T[0].max() - bbox_3d.T[0].min()) / img_w
                y_range = (bbox_3d.T[1].max() - bbox_3d.T[1].min()) / img_h
                txt_data.append(x_range)
                txt_data.append(y_range)
                txt_path = os.path.join(this_label_path, "{}.txt".format("%06d" % num))
                np.set_printoptions(suppress=True)
                np.set_printoptions(precision=4)
                np.savetxt(txt_path, [txt_data], fmt='%.06f')

                # move jpeg image
                li3d_img_path = os.path.join(li3d_path, annotation_data["image_file"])
                this_img_path = os.path.join(this_class_path, "JPEGImages")
                if not os.path.exists(this_img_path):
                    os.makedirs(this_img_path)
                img_path_one = os.path.join(this_img_path, "{}.jpg".format("%06d" % num))
                shutil.copyfile(li3d_img_path, img_path_one)

                # get mask image
                mask_path = os.path.join(this_class_path, "mask")
                if not os.path.exists(mask_path):
                    os.makedirs(mask_path)
                model_3d_points = load_model_ply(os.path.join(this_class_path, "{}.ply".format(this_class)))
                camera_intrinsics = get_camera_intrinsics(annotation_data["camera"]["fov"],
                                                          Image.open(get_all_path(img_path)[1]).size)
                mask_img = get_mask_img(img_size, model_3d_points, R_obj2c, T_obj2c, cam_K)
                imwrite(os.path.join(mask_path, "{}.png".format("%06d" % num)), mask_img)

                # get train.txt, training_range.txt and test.txt
                if num % 6 == 0:
                    train_txt.append(img_path_one.split("/")[-1])
                    train_range_txt.append(num)
                else:
                    test_txt.append(img_path_one.split("/")[-1])
                num += 1

        test_txt_path = os.path.join(this_class_path, "test.txt")
        train_txt_path = os.path.join(this_class_path, "train.txt")
        train_range_txt_path = os.path.join(this_class_path, "training_range.txt")
        np.savetxt(test_txt_path, test_txt, fmt="%s")
        np.savetxt(train_txt_path, train_txt, fmt="%s")
        np.savetxt(train_range_txt_path, train_range_txt, fmt="%s")

    return fov


def config_BB8(cfg_path, li3d_type, lm_path, fov):
    if not os.path.exists(cfg_path):
        os.makedirs(cfg_path)

    for this_class in li3d_type:
        data_path = os.path.join(cfg_path, "{}.data".format(this_class))
        train = lm_path.split("/")[-1] + "/{}/train.txt".format(this_class)
        valid = lm_path.split("/")[-1] + "/{}/test.txt".format(this_class)
        back_up = "backup/{}".format(this_class)
        mesh = lm_path.split("/")[-1] + "/{}/{}.ply".format(this_class, this_class)
        tr_range = lm_path.split("/")[-1] + "/{}/training_range.txt".format(this_class)
        name = this_class
        model = load_model_ply(os.path.join(lm_path, "{}/{}.ply".format(this_class, this_class))).T
        diam = pow(sqrt(model[0].max() - model[0].min()) + sqrt(model[0].max() - model[0].min()) +
                   sqrt(model[0].max() - model[0].min()), 0.5)
        gpus = "2, 3"
        num_workers = 0
        img_size = Image.open(get_all_path(lm_path + "/{}/JPEGImages".format(this_class))[1]).size
        width, height = img_size
        cam_K = np.array(get_camera_intrinsics(fov, img_size)).reshape(3, 3)
        fx = cam_K[0][0]
        fy = cam_K[1][1]
        u0 = cam_K[0][2]
        v0 = cam_K[1][2]

        data = ["train = {}".format(train),
                "valid = {}".format(valid),
                "backup = {}".format(back_up),
                "mesh = {}".format(mesh),
                "tr_range = {}".format(tr_range),
                "name = {}".format(name),
                "diam = {}".format(diam),
                "gpus = {}".format(gpus),
                "num_workers = {}".format(num_workers),
                "width = {}".format(width),
                "height = {}".format(height),
                "fx = {}".format(fx),
                "fy = {}".format(fy),
                "u0 = {}".format(u0),
                "v0 = {}".format(v0)]
        np.savetxt(data_path, data, fmt="%s")


if __name__ == '__main__':
    labelImg3d_scene_path = "F:/my_desktop/kitti"
    linemod_path = "F:/my_desktop/PycharmFiles/3D_detection/segmentation_driven_pose/Data/kitti"
    li3d_type = ["Car", "Tram", "Truck", "Van", "Pedestrian"]
    fov = li3d_2_linemod(labelImg3d_scene_path, li3d_type, linemod_path)

    cfg_path = "F:/my_desktop/PycharmFiles/3D_detection/segmentation_driven_pose/Data/cfg"
    # fov = 88.8
    config_BB8(cfg_path, li3d_type, linemod_path, fov)
    pass
