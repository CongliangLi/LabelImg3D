from PyQt5.QtCore import *
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtWidgets
from libs.Ui_system_config import Ui_System_config
import json
from libs.utils.utils import get_distance, get_fov
import os
from pathlib import Path
import sys


class SystemConfig(QObject):
    if Path(sys.argv[0]).parent.joinpath('system_config.json').is_file():
        with open(Path(sys.argv[0]).parent.joinpath('system_config.json'), 'r') as load_f:
            config_data = json.load(load_f)
    else:
        with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'system_config.json'), 'r') as load_f:
            config_data = json.load(load_f)
    signal_update_camera_property = pyqtSignal(list)

    def __init__(self, parent):
        super().__init__(parent)
        self.window = QtWidgets.QWidget()
        self.ui = Ui_System_config()
        self.ui.setupUi(self.window)
        self.ui.Camera_parameter.addItem("fov")
        self.ui.Camera_parameter.addItem("distance")

        # system parameter
        self.initial_position = SystemConfig.config_data["model"]["initial_position"]
        self.max_position = SystemConfig.config_data["model"]["max_position"]
        self.position_accuracy = SystemConfig.config_data["model"]["position_accuracy"]
        self.size_accuracy = SystemConfig.config_data["model"]["size_accuracy"]
        self.scaling_factor = SystemConfig.config_data["model"]["scaling_factor"]

        self.camera_matrix = SystemConfig.config_data["camera"]["matrix"]
        self.camera_position = SystemConfig.config_data["camera"]["position"]
        self.camera_focalPoint = SystemConfig.config_data["camera"]["focalPoint"]
        self.camera_fov = SystemConfig.config_data["camera"]["fov"]
        self.camera_viewup = SystemConfig.config_data["camera"]["viewup"]
        self.camera_distance = SystemConfig.config_data["camera"]["distance"]

        self.camera_parameter_value = self.camera_fov

        # connect
        self.ui.Btn_apply.clicked.connect(self.apply)
        self.ui.Camera_parameter.currentIndexChanged.connect(self.change_camera_parameter)

    def show(self):
        self.ui.lineEdit_initial_position.setText(str(self.initial_position))
        self.ui.lineEdit_max_position.setText(str(self.max_position))
        self.ui.lineEdit_position_accuracy.setText(str(self.position_accuracy))
        self.ui.lineEdit_size_accuracy.setText(str(self.size_accuracy))
        self.ui.lineEdit_scaling_factor.setText(str(self.scaling_factor))
        self.ui.Camera_parameter_value.setText(str(self.camera_parameter_value))
        self.window.show()

    def change_camera_parameter(self):
        if self.ui.Camera_parameter.currentText() == "fov":
            self.camera_parameter_value = self.camera_fov
        else:
            self.camera_parameter_value = self.camera_distance
        self.ui.Camera_parameter_value.setText(str(self.camera_parameter_value))

    def apply(self):
        # camera config
        if self.ui.Camera_parameter.currentText() == "fov":
            try:
                self.camera_fov = float(self.ui.Camera_parameter_value.text())
            except ValueError:
                QMessageBox.critical(self.window, "Error",
                                     "Invalid input data {}!".format(self.ui.Camera_parameter_value.text()),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                return
            self.camera_distance = get_distance(self.camera_fov)
        else:
            try:
                self.camera_distance = float(self.ui.Camera_parameter_value.text())
            except ValueError:
                QMessageBox.critical(self.window, "Error",
                                     "Invalid input data {}!".format(self.ui.Camera_parameter_value.text()),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                return
            self.camera_fov = get_fov(self.camera_distance)

        self.camera_position = [0, 0, self.camera_distance]
        self.camera_matrix = [1.0, 0.0, 0.0, 0.0,
                              0.0, 1.0, 0.0, 0.0,
                              0.0, 0.0, 1.0, self.camera_distance,
                              0.0, 0.0, 0.0, 1.0]
        # model config
        try:
            self.initial_position = float(self.ui.lineEdit_initial_position.text())
            self.max_position = float(self.ui.lineEdit_max_position.text())
            self.position_accuracy = int(self.ui.lineEdit_position_accuracy.text())
            self.size_accuracy = int(self.ui.lineEdit_size_accuracy.text())
            self.scaling_factor = float(self.ui.lineEdit_scaling_factor.text())
        except ValueError:
            QMessageBox.critical(self.window, "Error", "Invalid input data!",
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

            self.initial_position = SystemConfig.config_data["model"]["initial_position"]
            self.max_position = SystemConfig.config_data["model"]["max_position"]
            self.position_accuracy = SystemConfig.config_data["model"]["position_accuracy"]
            self.size_accuracy = SystemConfig.config_data["model"]["size_accuracy"]
            self.scaling_factor = SystemConfig.config_data["model"]["scaling_factor"]

            return

            # update SystemConfig.config_data
        SystemConfig.config_data["camera"]["matrix"] = self.camera_matrix
        SystemConfig.config_data["camera"]["position"] = self.camera_position
        SystemConfig.config_data["camera"]["focalPoint"] = self.camera_focalPoint
        SystemConfig.config_data["camera"]["fov"] = self.camera_fov
        SystemConfig.config_data["camera"]["viewup"] = self.camera_viewup
        SystemConfig.config_data["camera"]["distance"] = self.camera_distance

        SystemConfig.config_data["model"]["initial_position"] = self.initial_position
        SystemConfig.config_data["model"]["max_position"] = self.max_position
        SystemConfig.config_data["model"]["position_accuracy"] = self.position_accuracy
        SystemConfig.config_data["model"]["size_accuracy"] = self.size_accuracy
        SystemConfig.config_data["model"]["scaling_factor"] = self.scaling_factor

        # Save to local file(.json)
        # if not Path(sys.argv[0]).parent.joinpath('system_config.json').is_file():

        with open(Path(sys.argv[0]).parent.joinpath('system_config.json'), 'w+') as f:
            json.dump(SystemConfig.config_data, f, indent=4)

        # update scene
        self.signal_update_camera_property.emit(self.camera_position + [self.camera_fov, self.camera_distance])
