import os
import sys
import vtk
import cv2
import json
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import PyQt5
from PyQt5 import QtCore, QtWidgets, QtGui
import typing
import math
from actor_manager import Actor, ActorManager


class MouseInteractorHighLightActor(vtk.vtkInteractorStyleTrackballCamera):

    def __init__(self, slabel, parent=None):
        self.slabel = slabel
        self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)

    def switchBoxWidgets(actor):
        self.slabel.switchBoxWidgets(actor)


    def leftButtonPressEvent(self, obj, event):
        clickPos = self.GetInteractor().GetEventPosition()

        picker = vtk.vtkPropPicker()

        for a in self.slabel.actor_manager.actors:
            picker.Pick(clickPos[0], clickPos[1], 0, a.renderer)
            # get the new
            self.NewPickedActor = picker.GetProp3D()
            # If something was selected
            if self.NewPickedActor and self.NewPickedActor is self.slabel.actor_manager.actors[-1].actor:
                print(self.NewPickedActor.GetBounds())
                self.slabel.switchBoxWidgets(self.NewPickedActor)
                break

        self.OnLeftButtonDown()
        return



class SLabel3DAnnotation(QtWidgets.QFrame):

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.interactor = QVTKRenderWindowInteractor(self)

        self.bg_renderer = vtk.vtkRenderer()
        self.bg_renderer.SetBackground(0, 0, 0)
        self.bg_renderer.SetBackgroundAlpha(1)
        self.bg_renderer.SetLayer(0)
        self.bg_renderer.InteractiveOff()

        self.renderer_window = self.interactor.GetRenderWindow()
        self.renderer_window.SetNumberOfLayers(1)
        self.renderer_window.AddRenderer(self.bg_renderer)

        self.style = MouseInteractorHighLightActor(self)
        self.interactor.SetInteractorStyle(self.style)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.interactor)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # add the axes actor to the background
        axes = vtk.vtkAxesActor()
        axes.SetAxisLabels(False)
        transform = vtk.vtkTransform()
        transform.Translate(0, 0, 0.01)
        axes.SetUserTransform(transform)
        self.bg_renderer.AddActor(axes)

        self.image_actor = None
        self.image_path = None

        self.actor_manager = ActorManager(self.renderer_window, self.interactor)

    def start(self):
        self.interactor.Initialize()
        self.interactor.Start()
    

    @PyQt5.QtCore.pyqtSlot(str)
    def loadImage(self, image_path):
        if not os.path.exists(image_path):
            return 

        self.image_path = image_path

        # remove the previous loaded actors
        if self.image_actor is not None:
            self.bg_renderer.RemoveActor(self.image_actor)
            self.image_actor = None

        # get image width and height
        image = cv2.imread(image_path)
        image_height, image_width, _ = image.shape
        scale = 0.1

        # Read image data
        jpeg_reader = vtk.vtkJPEGReader()
        jpeg_reader.SetFileName(image_path)
        jpeg_reader.Update()
        image_data = jpeg_reader.GetOutput()
        self.image_actor = vtk.vtkImageActor()
        self.image_actor.SetInputData(image_data)

        transform = vtk.vtkTransform()
        transform.Scale(scale, scale, scale)
        transform.Translate(-image_width/2, -image_height/2, 0)
        self.image_actor.SetUserTransform(transform)
        self.bg_renderer.AddActor(self.image_actor)
        self.bg_renderer.ResetCamera()
        self.interactor.Render()


    @PyQt5.QtCore.pyqtSlot(str)
    def loadModel(self, model_path):
        self.actor_manager.newActor(model_path)


    def switchBoxWidgets(self, actor):
        index = self.actor_manager.getIndex(actor)
        if index != -1:
            self.actor_manager.setActiveActor(index)


    @PyQt5.QtCore.pyqtSlot(str, str, str)
    def loadScenes(self, scene_folder, image_file, annotation_file):
        self.scene_folder, self.image_file, self.annotation_file = scene_folder, image_file, annotation_file
        # remove the image layer
        if self.image_actor is not None:
            self.bg_renderer.RemoveActor(self.image_actor)
            self.image_actor.Delete()
        # remove all actors
        self.actor_manager.clear()

        # load the image
        self.loadImage(image_file)

        # load the scenes
        self.actor_manager.loadAnnotation(self.scene_folder, annotation_file)
        

    @PyQt5.QtCore.pyqtSlot()
    def saveScenes(self):
        self.data = {}
        self.data["image_file"] = os.path.relpath(self.image_path, self.scene_folder)
        self.data.update(self.actor_manager.toJson(self.scene_folder))
        if not os.path.exists(os.path.dirname(self.annotation_file)):
            os.makedirs(os.path.dirname(self.annotation_file))
        with open(self.annotation_file, 'w+') as f:
            json.dump(self.data, f)

