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

from vtk import *

class MouseInteractorHighLightActor(vtkInteractorStyleTrackballActor):
    def __init__(self, slabel, parent=None):
        self.slabel = slabel
        self.AddObserver('LeftButtonPressEvent', self.OnLeftButtonDown, -1)
        self.AddObserver('LeftButtonReleaseEvent', self.OnLeftButtonUp, -1)
        self.AddObserver('RightButtonPressEvent', self.OnRightButtonDown, -1)
        self.AddObserver('RightButtonReleaseEvent', self.OnRightButtonUp, -1)
        self.AddObserver('MouseMoveEvent', self.OnMouseMove, -1)
        self.AddObserver('MouseWheelForwardEvent', self.OnMouseWheelForward, -1)
        self.AddObserver('MouseWheelBackwardEvent', self.OnMouseWheelBackward, -1)
        self.isPressedRight = False
        self.isPressedLeft = False
        self.super = super(MouseInteractorHighLightActor, self)
        self.InteractionPicker = vtkCellPicker()
        self.InteractionProp = None
        
    def __del__(self):
        del self.InteractionPicker

    def SetOpacity(self, op = 0.5):
        if self.InteractionProp is not None:
            self.InteractionProp.GetProperty().SetOpacity(op)

    def switchLayer(self):
        x, y = self.GetInteractor().GetEventPosition()

        all_picked_actors = [self.InteractionPicker.GetProp3D() for a in self.slabel.actor_manager.actors \
                             if self.InteractionPicker.Pick(x, y, 0, a.renderer) != 0]
        if len(all_picked_actors) > 0:
            self.NewPickedActor = all_picked_actors[0]
            if self.NewPickedActor and self.NewPickedActor is not self.slabel.actor_manager.actors[-1].actor:
                print(self.NewPickedActor.GetBounds())
                self.slabel.switchBoxWidgets(self.NewPickedActor)

    def OnLeftButtonDown(self, obj, event):
        self.isPressedLeft = True
        x, y = self.GetInteractor().GetEventPosition()
        self.switchLayer()

        self.InteractionPicker.Pick(x, y, 0.0, self.GetCurrentRenderer())
        self.InteractionProp = self.InteractionPicker.GetViewProp()

        self.super.OnLeftButtonDown()
            
    def OnLeftButtonUp(self, obj, event):
        self.isPressedLeft = False
        self.super.OnLeftButtonUp()

    def OnRightButtonDown(self, obj, event):
        self.isPressedRight = True

        self.switchLayer()
        x, y = self.GetInteractor().GetEventPosition()
        self.InteractionPicker.Pick(x, y, 0.0, self.GetCurrentRenderer())
        self.InteractionProp = self.InteractionPicker.GetViewProp()

        self.super.OnRightButtonDown()

    def OnRightButtonUp(self, obj, event):
        self.isPressedRight = False
        self.super.OnRightButtonUp()


    def Prop3DTransform(self, prop3D, boxCenter, numRotation, rotate, scale):
        oldMatrix = vtkMatrix4x4()
        prop3D.GetMatrix(oldMatrix)
        
        orig = prop3D.GetOrigin()

        newTransform = vtkTransform()
        newTransform.PostMultiply()
        if prop3D.GetUserMatrix() is not None:
            newTransform.SetMatrix(prop3D.GetUserMatrix())
        else:
            newTransform.SetMatrix(oldMatrix)
        
        newTransform.Translate(-boxCenter[0], -boxCenter[1], -boxCenter[2])

        for i in range(numRotation):
            newTransform.RotateWXYZ(*(rotate[i][j] for j in range(3)))

        if 0 not in scale:
            newTransform.Scale(*scale)
        
        newTransform.Translate(*boxCenter)

        newTransform.Translate(*(-orig[i] for i in range(3)))
        newTransform.PreMultiply()
        newTransform.Translate(*orig)

        if prop3D.GetUserMatrix() is not None:
            newTransform.GetMatrix(prop3D.GetUserMatrix())
        else:
            prop3D.SetPosition(newTransform.GetPosition())
            prop3D.SetScale(newTransform.GetScale())
            prop3D.SetOrientation(newTransform.GetOrientation())

        del oldMatrix
        del newTransform

    def UniformScale(self):
        if self.GetCurrentRenderer() is None or self.InteractionProp is None:
            return 
        rwi = self.GetInteractor()
        dy = rwi.GetEventPosition()[1] - rwi.GetLastEventPosition()[1]
        obj_center = self.InteractionProp.GetCenter()
        center = self.GetCurrentRenderer().GetCenter()

        direction = []
        camera = self.GetCurrentRenderer().GetActiveCamera()
        if camera.GetParallelProjection():
            camera.ComputeViewPlaneNormal()
            direction = camera.GetViewPlaneNormal()
        else:
            cam_x, cam_y, cam_z = self.GetCurrentRenderer().GetActiveCamera().GetPosition()
            direction = list((obj_center[0] - cam_x, obj_center[1] - cam_y, obj_center[2] - cam_z))

        vtkMath.Normalize(direction)

        # yf = dy / center[1] *  10.0
        # scaleFactor = 0.1 * (1.1 ** yf)
        motion_vector = [-0.1 * d * dy for d in direction]
        if self.InteractionProp.GetUserMatrix() is not None:
            t = vtkTransform()
            t.PostMultiply()
            t.SetMatrix(self.InteractionProp.GetUserMatrix())
            t.Translate(*motion_vector)
            self.InteractionProp.GetUserMatrix().DeepCopy(t.GetMatrix())
            del t
        else:
            self.InteractionProp.AddPosition(*motion_vector)

        if self.GetAutoAdjustCameraClippingRange():
            self.GetCurrentRenderer().ResetCameraClippingRange()
        
        rwi.Render()


    def OnMouseMove(self, obj, event):
        x, y = self.GetInteractor().GetEventPosition()

        self.HighlightProp3D(self.InteractionProp)
        self.SetOpacity(0.5)

        if self.isPressedRight and not self.GetInteractor().GetShiftKey():
            self.FindPokedRenderer(x, y)
            self.UniformScale()
            self.InvokeEvent(vtkCommand.InteractionEvent, None)
        else:
            self.super.OnMouseMove()
        self.SetOpacity(1)

    def OnMouseWheelForward(self, obj, event):
        self.super.OnMouseWheelForward()

    def OnMouseWheelBackward(self, obj, event):
        self.super.OnMouseWheelBackward()



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

