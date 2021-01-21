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

        for i in range(1, len(self.slabel.renderers)):
            picker.Pick(clickPos[0], clickPos[1], 0, self.slabel.renderers[i])

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
    # scale = t.GetScale()
    # if abs(1 - scale[0]) > 1e-6:
    #     pos = t.GetPosition()
    #     scale = t.GetScale()
    #     rev_t = t.GetInverse()
    #     rev_pos = rev_t.GetPosition()
    #     rev_scale = rev_t.GetScale()
        
    #     # remove scale
    #     t.Translate(rev_pos)
    #     t.Scale(rev_t.GetScale())
    #     t.Translate(pos)

    #     # add z-axis translate
    #     # t.Translate(rev_t.GetPosition())
    #     # z_transform = (0, 0, 1-scale[0])
    #     # t.Translate(z_transform)
    #     # t.Translate(pos)
    #     print(t.GetPosition())
    obj.SetTransform(t)
    obj.GetProp3D().SetUserTransform(t)

class SLabel3DAnnotation(QtWidgets.QFrame):

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.interactor = QVTKRenderWindowInteractor(self)

        self.bg_renderer = vtk.vtkRenderer()
        self.bg_renderer.SetBackground(0, 0, 0)
        self.bg_renderer.SetBackgroundAlpha(1)
        self.bg_renderer.SetLayer(0)
        self.bg_renderer.InteractiveOff()

        # there are two layers: 1. bg_renderer to render images, 2. actor_renderers to render all actors
        self.actor_renderer = vtk.vtkRenderer()
        self.actor_renderer.SetLayer(1)
        self.actor_renderer.SetBackground(1, 1, 1)
        self.actor_renderer.InteractiveOff()
        self.actor_renderer.SetBackgroundAlpha(0)
        self.actor_renderer.GetActiveCamera().SetClippingRange(0.01, 10000)

        # share the first layer camera
        # camera = self.bg_renderer.GetActiveCamera()
        # self.actor_renderer.SetActiveCamera(camera)

        self.renderers = [self.bg_renderer, self.actor_renderer]

        self.render_window = self.interactor.GetRenderWindow()
        self.render_window.SetNumberOfLayers(2)
        self.render_window.AddRenderer(self.bg_renderer)
        self.render_window.AddRenderer(self.actor_renderer)

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

        self.actors = []
        self.boxes = []


    def start(self):
        self.interactor.Initialize()
        self.interactor.Start()

    def insertRenderer(self):
        # create renderer
        renderer = vtk.vtkRenderer()
        renderer.SetLayer(len(self.renderers))
        renderer.SetBackground(1, 1, 1)
        renderer.InteractiveOn()
        renderer.SetBackgroundAlpha(0)

        self.renderers.append(renderer)
        self.render_window.SetNumberOfLayers(len(self.renderers))
        self.render_window.AddRenderer(renderer)

        self.setActiveRenderer(-1)

        return renderer

    def removeRenderer(self, index):
        if index == 0 or len(self.renderers) == 0 or index >= len(self.renderers):
            raise Exception("Cannot remove {} renderer".format(index))

        self.render_window.RemoveRenderer(self.renderers[index])
        self.render_window.SetNumberOfLayers(len(self.renderers))
        self.setActiveRenderer(-1)
        del self.renderers[index]

    def mousePressEvent(self, QMouseEvent):
        super().mousePressEvent(QMouseEvent)
        pos = QMouseEvent.pos()
        x = pos.x()
        y = pos.y()
        self.lastPos = [x, y]

    def setActiveRenderer(self, index):
        # very important for set the default render
        self.interactor.GetInteractorStyle().SetDefaultRenderer(self.renderers[index])
        self.style.SetCurrentRenderer(self.renderers[index])
        self.renderers[index].Render()


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


    @PyQt5.QtCore.pyqtSlot(str)
    def loadModel(self, model_path):
        # analysis the obj model
        self.model_path = model_path

        # actor = self.readObj(model_path)
        actor = self.importObj(model_path)

        # move the actor to (0, 0, 0)
        min_x, _, min_y, _, min_z, _ =actor.GetBounds()
        transform = vtk.vtkTransform()
        
        transform.Translate(-min_x, -min_y, -min_z)

        self.actors.append(actor)
        self.actor_renderer.AddActor(actor)

        # create box widget
        boxWidget = vtk.vtkBoxWidget()
        boxWidget.AddObserver("InteractionEvent", boxCallback)
        boxWidget.SetInteractor(self.interactor)
        # boxWidget.ScalingEnabledOff()
        boxWidget.HandlesOff()
        boxWidget.SetProp3D(actor)
        boxWidget.SetPlaceFactor(1.0)
        boxWidget.PlaceWidget(actor.GetBounds())
        self.boxes.append(boxWidget)
        self.switchBoxWidgets(actor)

        # boxWidget should be set first and then set the actor
        boxWidget.SetTransform(transform)
        boxWidget.GetProp3D().SetUserTransform(transform)

    def switchBoxWidgets(self, actor):
        for b in self.boxes:
            b.Off()
        self.boxes[self.actors.index(actor)].On()
