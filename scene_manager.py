import os
import sys
import vtk
import cv2
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import PyQt5
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QSize, pyqtSignal, QCoreApplication, QObject
import typing
import math
from utils import *
from actor_manager import ActorManager
from simagelist import SImageList
from slabel3dannotation import SLabel3DAnnotation


class SceneManager(QObject):
    signal_open_files = pyqtSignal(list)
    signal_open_models = pyqtSignal(list)
    signal_load_scene = pyqtSignal(str, str)

    def __init__(self, parent, image_list_panel, model_list_panel, vtk_panel) -> None:
        super().__init__(parent=parent)
        self.image_list_panel = image_list_panel
        self.model_list_panel = model_list_panel
        self.vtk_panel = vtk_panel

        self.scene_folder = ''
        self.images_folder = ''
        self.models_folder = ''
        self.annotations_folder = ''

        self.image_name_list = []
        self.model_name_list = []
        self.annotation_name_list = []

    def load_scenes(self):
        """load the scenes, the folder structure should be as follows:

        ..--------
        . --------
        |--models <only obj support>
        |--images <only jpg support>
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
        # 1. get all the images
        self.images_folder = os.path.join(self.scene_folder, 'images')
        self.image_name_list = getFiles(self.images_folder, ['.jpg'])

        # 2. get all the annotations
        self.annotations_folder = os.path.join(self.scene_folder, 'annotations')
        self.annotation_name_list = [
            os.path.relpath(os.path.join(self.annotations_folder, i)[:-4] + '.json', self.annotations_folder) for i in
            self.image_name_list]

        # 3. get all the models
        self.models_folder = os.path.join(self.scene_folder, 'models')
        self.model_name_list = getFiles(self.models_folder, ['.obj'])

        # 4. get the first item
        if len(self) > 0:
            self.signal_open_models.emit([os.path.join(self.models_folder, i) for i in self.model_name_list])
            self.signal_open_files.emit([os.path.join(self.images_folder, i) for i in self.image_name_list])
            self[0]

    def __len__(self):
        return len(self.image_name_list)

    def __getitem__(self, index):
        # 1. check annotation_folder
        self.vtk_panel.loadScenes(self.scene_folder, os.path.join(self.images_folder, self.image_name_list[index]), \
                                  os.path.join(self.annotations_folder, self.annotation_name_list[index]))
        # 2. read annotation file
        # 3. clear all the renderers and actors
        # 4. add image and actors
        pass

    def next(self):
        pass

    def previous(self):
        pass

    def home(self):
        pass

    def end(self):
        pass

    def save(self):
        pass
