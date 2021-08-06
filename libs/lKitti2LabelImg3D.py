from PyQt5.QtCore import *
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtWidgets
from libs.Ui_kitti_2_labelimg3d import Ui_FormKitti2LabelImg3D
import os
import json
from libs.utils.kitti_util import Calibration, roty
from libs.utils.utils import get_all_path
import numpy as np
import pandas as pd


class Kitti2LabelImg3D(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.window = QtWidgets.QWidget()
        self.ui = Ui_FormKitti2LabelImg3D()
        self.ui.setupUi(self.window)

        # Data
        self.speed_of_progress = 0

        self.scene_folder = ""
        self.images_folder = ""
        self.models_folder = ""
        self.label_folder = ""
        self.calib_folder = ""
        self.annotations_folder = ""
        self.c_distance = 0.52

        # button connect
        self.ui.openFolder_Btn.clicked.connect(self.openFolder)
        self.ui.btn_Run.clicked.connect(self.run)

        # progressBar status
        self.ui.progressBar.setValue(0)

    def openFolder(self):
        """load the scenes, the folder structure should be as follows:

        ..--------
        . --------
        |--models <only obj support>
        |--images
            |--scene1
            |--scene2
            |-- ...
        |--label
            |--scene1
            |--scene2
            |-- ...
        |--calib
            |--scene1
            |--scene2
            |-- ...
        |--annotations
            |--scene1
            |--scene2
            |-- ...
        """
        scene_folder = QtWidgets.QFileDialog.getExistingDirectory(None, "Choose Scene Folder")
        if scene_folder == '':
            return

        self.scene_folder = scene_folder

        self.images_folder = os.path.join(scene_folder, 'images')
        self.label_folder = os.path.join(scene_folder, 'label')
        self.models_folder = os.path.join(scene_folder, 'models')
        self.calib_folder = os.path.join(scene_folder, 'calib')
        if not os.path.exists(self.scene_folder) or not os.path.exists(self.images_folder) or not os.path.exists(
                self.label_folder) or not os.path.exists(self.models_folder) or not os.path.exists(self.calib_folder):
            QMessageBox.critical(self.window, "Error", "File structure error!",
                                 QMessageBox.Yes | QMessageBox.No,
                                 QMessageBox.Yes)
            return
        else:
            self.ui.lineEdit_Edt.setText(self.scene_folder)

    def run(self):
        self.ui.progressBar.setValue(0)
        img_path = get_all_path(self.images_folder)
        label_path = get_all_path(self.label_folder)
        calib_path = get_all_path(self.calib_folder)

        if len(img_path) != len(label_path) or len(img_path) != len(calib_path):
            QMessageBox.critical(self.window, "Error",
                                 "The number of images, labels and calibration files does not match!",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            return

        for i in range(0, len(img_path)):
            img = img_path[i]
            label = label_path[i]
            calib = calib_path[i]
            self.annotations_folder = "\\".join(self.label_folder.split("\\")[:-1]) + "\\annotations\\" + \
                                      img.split("\\")[-2] + "\\"

            if img.split("\\")[-1].split(".")[0] == label.split("\\")[-1].split(".")[0] == \
                    calib.split("\\")[-1].split(".")[0]:
                self.KITTI_2_LabelImg3D(img, label, self.models_folder, self.annotations_folder, calib, self.c_distance)

            current_speed_of_progress = (i + 1) / len(img_path) * 100
            if current_speed_of_progress != self.speed_of_progress:
                self.ui.progressBar.setValue(current_speed_of_progress)
            QCoreApplication.processEvents()

    def show(self):
        self.ui.lineEdit_Edt.setText(" ")
        self.ui.progressBar.setValue(0)
        self.window.show()

    def KITTI_2_LabelImg3D(self, img_path, label_path, model_path, annotation_path, calib_path, c_distance):
        with open(model_path + "/models.json", 'r') as load_f:
            model_json_data = json.load(load_f)
        model_data = {"Tram": {}, "Car": {}, "Truck": {}, "Van": {}, "Pedestrian": {}}
        for d in model_data:
            for j_d in model_json_data:
                if model_json_data[j_d]["class_name"] == d:
                    model_data[d]["path"] = "models\\" + j_d
                    model_data[d]["index"] = model_json_data[j_d]["class_index"]
                    model_data[d]["size"] = model_json_data[j_d]["size"]
                    break

        calib = Calibration(calib_path)
        data = {}

        data["image_file"] = "\\".join(img_path.split("\\")[len(img_path.split("\\")) - 3:])

        data["model"] = {}
        data["model"]["num"] = 0
        num = 0

        # calib = pd.read_table(calib_path, sep=' ', header=None)
        # calib_velo2c0 = [[calib[4 * i + n][5] for n in range(1, 5)] for i in range(0, 3)]
        # calib_velo2c0 = np.row_stack([calib_velo2c0, np.array([0, 0, 0, 1])])
        #
        # calib_R0rect = [[calib[3 * i + n][4] for n in range(1, 4)] for i in range(0, 3)]
        # calib_R0rect = np.column_stack([calib_R0rect, np.array([0, 0, 0])])
        # calib_R0rect = np.row_stack([calib_R0rect, np.array([0, 0, 0, 1])])
        #
        # calib_velo2c = np.dot(calib_R0rect, calib_velo2c0)
        # R_velo2c = [[calib_velo2c[i][n] for n in range(0, 3)] for i in range(0, 3)]
        # T_velo2c = [calib_velo2c[i][3] for i in range(0, 3)]

        R_c02c = np.array([[0.9999758, -0.005267463, - 0.004552439],
                           [0.00251945, 0.9999804, - 0.003413835],
                           [0.004570332, 0.003389843, 0.9999838]])

        a = pd.read_table(label_path, sep=' ', header=None)
        for i in reversed(range(0, len(a))):
            obj_class = a[0][i]

            if obj_class == "DontCare" or obj_class == "Misc" or obj_class == "Person_sitting":
                continue

            obj_position_c0 = np.array([[a[j][i] for j in range(11, 14)]])
            obj_position_c0 = np.array(obj_position_c0)

            # obj_position_c = np.matmul(R_rect_02, np.matmul(T_02, np.vstack((np.matmul(np.linalg.inv(R_rect_00), obj_position_c0[:3, :]), [1])))[:3, :])
            # obj_position_c = np.matmul(R_rect_02, obj_position_c0[:3, :])
            obj_position_c = calib.project_rect0_to_rect2(obj_position_c0)
            obj_position_c = obj_position_c.squeeze()
            # obj_position_c = [obj_position_c0[i] + T_c02c[i] for i in range(0, 3)]
            obj_position_w = np.array([obj_position_c[0], -obj_position_c[1], -(obj_position_c[2] - c_distance)])

            obj_alpha = a[3][i]
            R_oK2oL = [[0, 0, 1],
                       [0, 1, 0],
                       [-1, 0, 0]]

            obj_r_y = a[14][i]
            R_oK2c0 = roty(3.14 - obj_r_y)
            R_oK2c = np.dot(R_oK2c0, R_c02c)

            R_c2w = [[0, 1, 0],
                     [1, 0, 0],
                     [0, 0, -1]]
            # R_oL2w = np.dot(np.dot(R_oL2oK, R_oK2c), R_c2w)
            R_oL2w = np.dot(np.dot(R_oK2c, R_c2w), R_oK2oL)
            # R_oL2w = np.dot(R_oK2c, R_c2w)
            oL_2_w = np.column_stack([R_oL2w, obj_position_w])
            oL_2_w = np.row_stack([oL_2_w, np.array([0, 0, 0, 1])])

            if obj_class == "Cyclist":
                obj_class = "Pedestrian"
            data["model"]["{}".format(num)] = {
                "model_file": model_data[obj_class]["path"],
                "matrix": oL_2_w.reshape(1, 16).tolist()[0],
                "class": model_data[obj_class]["index"],
                "class_name": obj_class,
                "size": model_data[obj_class]["size"]
            }

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
