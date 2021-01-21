import os
import sys
import vtk
import cv2
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import PyQt5
from PyQt5 import QtCore, QtWidgets, QtGui
import typing
import math


class MouseInteractorHighLightActor(vtk.vtkInteractorStyleTrackballCamera):

    def __init__(self, slabel, parent=None):
        self.slabel = slabel
        self.AddObserver("LeftButtonPressEvent", self.leftButtonPressEvent)

    def leftButtonPressEvent(self, obj, event):
        clickPos = self.GetInteractor().GetEventPosition()

        picker = vtk.vtkPropPicker()

        for a in self.slabel.actor_manager.actors:
            picker.Pick(clickPos[0], clickPos[1], 0, a.renderer)
            # get the new
            self.NewPickedActor = picker.GetProp3D()
            # If something was selected
            if self.NewPickedActor:
                print(self.NewPickedActor.GetBounds())
                self.slabel.switchBoxWidgets(self.NewPickedActor)
                break

        self.OnLeftButtonDown()
        return


def boxCallback(obj, event):
    t = vtk.vtkTransform()
    obj.GetTransform(t)
    obj.GetProp3D().SetUserTransform(t)


class Actor:
    def __init__(self, render_window, interactor, model_path, layer_num):
        self.renderer_window = render_window
        self.interactor = interactor
        self.renderer = None
        self.actor = None
        self.box_widget = None
        self.model_path = model_path
        self.createRenderer(layer_num)
        self.loadModel(model_path)
        self.createBoxWidget()

    def readObj(self, model_path):
        reader = vtk.vtkOBJReader()
        reader.SetFileName(model_path)
        reader.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        return actor

    def importObj(self, model_path):
        self.model_folder, self.obj_name = os.path.split(self.model_path)
        self.obj_name = self.obj_name[:-4]
        self.mtl_path = self.model_folder + "/" + self.obj_name+".mtl"
        importer = vtk.vtkOBJImporter()
        importer.SetFileName(self.model_path)
        importer.SetFileNameMTL(self.mtl_path)
        importer.SetTexturePath(self.model_folder)

        importer.Read()
        importer.InitializeObjectBase()

        # get all actors and assembly
        actors = importer.GetRenderer().GetActors()
        actors.InitTraversal()
        assembly = vtk.vtkAssembly()
        for i in range(actors.GetNumberOfItems()):
            a = actors.GetNextActor()
            assembly.AddPart(a)

        return assembly

    def loadModel(self, model_path):
        self.model_path = model_path
        # actor = self.readObj(model_path)
        self.actor = self.importObj(model_path)

        # # move the actor to (0, 0, 0)
        # min_x, _, min_y, _, min_z, _ = self.actor.GetBounds()
        # transform = vtk.vtkTransform()
        # transform.Translate(-min_x, -min_y, -min_z)
        # self.actor.SetUserTransform(transform)

        self.renderer.AddActor(self.actor)

    def createRenderer(self, layer_num):
        self.renderer = vtk.vtkRenderer()
        self.renderer_window.SetNumberOfLayers(layer_num+1)
        self.renderer.SetLayer(layer_num)
        self.renderer.SetBackground(1, 1, 1)
        self.renderer.InteractiveOff()
        self.renderer.SetBackgroundAlpha(0)
        self.renderer_window.AddRenderer(self.renderer)
        return self.renderer

    def createBoxWidget(self):
        # create box widget
        self.box_widget = vtk.vtkBoxWidget()
        self.box_widget.AddObserver("InteractionEvent", boxCallback)
        self.box_widget.SetInteractor(self.interactor)

        # move the actor to (0, 0, 0)
        # min_x, _, min_y, _, min_z, _ =self.actor.GetBounds()
        # transform = vtk.vtkTransform()
        # transform.Translate(-min_x, -min_y, -min_z)

        self.box_widget.HandlesOff()
        self.box_widget.SetProp3D(self.actor)
        self.box_widget.SetPlaceFactor(1.0)
        self.box_widget.PlaceWidget(self.actor.GetBounds())

        # boxWidget should be set first and then set the actor
        # self.box_widget.SetTransform(transform)
        self.box_widget.On()
        

class ActorManager:
    def __init__(self, render_window, interactor):
        self.render_window = render_window
        self.interactor = interactor
        self.actors = []

    def newActor(self, model_path):
        actor = Actor(self.render_window, self.interactor, model_path, len(self.actors)+1)
        self.actors.append(actor)
        self.setActiveActor(-1)

    def setActiveActor(self, index):
        # very important for set the default render
        self.interactor.GetInteractorStyle().SetDefaultRenderer(self.actors[index].renderer)
        self.interactor.GetInteractorStyle().SetCurrentRenderer(self.actors[index].renderer)
        self.actors[index].renderer.Render()

        # for a in self.actors:
        #     a.box_widget.Off()
        
        # self.actors[index].box_widget.On()

    def getIndex(self, actor):
        i = -1
        for i in range(len(self.actors)):
            if self.actors[i].actor is actor:
                break
        return i


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
