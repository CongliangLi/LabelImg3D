import os
import sys
import vtk
import cv2
import json
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import PyQt5
from PyQt5 import QtCore, QtWidgets, QtGui
import typing
import math
from vtk import *
from utils import *

from actor_manager import Actor, ActorManager
from sproperty import *
# from PIL import Image


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
        self.super = super(MouseInteractorHighLightActor, self)
        self.reset()

    def reset(self):
        self.is_first = True
        self.InteractionPicker = vtkCellPicker()
        self.isPressedRight = False
        self.isPressedLeft = False
        self.isMouse_Pressed_Move = False
        # self.resetHighlight()
        self.InteractionProp = None
        self.HighlightProp3D(None)

    def resetHighlight(self):
        if len(self.slabel.actor_manager.actors) > 0:
            self.InteractionProp = self.slabel.actor_manager.actors[-1].actor
            self.slabel.switchBoxWidgets(self.InteractionProp)
        else:
            self.InteractionProp = None

        self.HighlightProp3D(self.InteractionProp)

    def __del__(self):
        del self.InteractionPicker

    def SetOpacity(self, op=0.5):
        if self.InteractionProp is not None:
            self.InteractionProp.GetProperty().SetOpacity(op)

    def switchLayer(self):
        x, y = self.GetInteractor().GetEventPosition()

        all_picked_actors = [self.InteractionPicker.GetProp3D() for a in self.slabel.actor_manager.actors \
                             if self.InteractionPicker.Pick(x, y, 0, a.renderer) != 0]
        if len(all_picked_actors) > 0:
            self.NewPickedActor = all_picked_actors[-1]
            if self.NewPickedActor and self.NewPickedActor is not self.slabel.actor_manager.actors[-1].actor:
                self.slabel.switchBoxWidgets(self.NewPickedActor)

    def OnLeftButtonDown(self, obj, event):
        if self.GetCurrentRenderer() is None:
            return

        self.isPressedLeft = True
        self.isMouse_Pressed_Move = False

        if not self.isMouse_Pressed_Move:
            x, y = self.GetInteractor().GetEventPosition()
            self.switchLayer()

            self.InteractionPicker.Pick(x, y, 0.0, self.GetCurrentRenderer())
            self.InteractionProp = self.InteractionPicker.GetViewProp()
            self.HighlightProp3D(self.InteractionProp)

            self.super.OnLeftButtonDown()

    def OnLeftButtonUp(self, obj, event):
        self.isPressedLeft = False
        if self.InteractionProp is None:
            return
        self.SetOpacity(1)

        self.slabel.signal_on_left_button_up.emit(
            list(self.InteractionProp.GetPosition() + self.InteractionProp.GetOrientation()) +
            self.slabel.actor_manager.actors[-1].size
        )

        self.super.OnLeftButtonUp()

    def OnRightButtonDown(self, obj, event):
        self.isPressedRight = True
        self.isMouse_Pressed_Move = False
        self.switchLayer()
        x, y = self.GetInteractor().GetEventPosition()
        self.InteractionPicker.Pick(x, y, 0.0, self.GetCurrentRenderer())
        self.InteractionProp = self.InteractionPicker.GetViewProp()
        self.HighlightProp3D(self.InteractionProp)

        self.super.OnRightButtonDown()

    def OnRightButtonUp(self, obj, event):
        self.isPressedRight = False
        self.SetOpacity(1)
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

        # if self.GetAutoAdjustCameraClippingRange():
        #     self.GetCurrentRenderer().ResetCameraClippingRange()

        rwi.Render()

    def OnMouseMove(self, obj, event):
        if self.InteractionProp is None or (not self.isPressedLeft and not self.isPressedRight):
            return

        self.isMouse_Pressed_Move = True

        self.HighlightProp3D(self.InteractionProp)
        self.SetOpacity(0.5)

        x, y = self.GetInteractor().GetEventPosition()

        # Right mouse button movement operation
        if self.isPressedRight and not self.GetInteractor().GetShiftKey():
            self.FindPokedRenderer(x, y)
            self.UniformScale()
            self.InvokeEvent(vtkCommand.InteractionEvent, None)
        else:
            self.super.OnMouseMove()
            self.GetInteractor().Render()

        self.slabel.signal_on_left_button_up.emit(
            list(self.InteractionProp.GetPosition() + self.InteractionProp.GetOrientation()) +
            self.slabel.actor_manager.actors[-1].size
        )
        self.slabel.actor_manager.ResetCameraClippingRange()
        self.GetInteractor().Render()

    def OnMouseWheelForward(self, obj, event):
        self.super.OnMouseWheelForward()

    def OnMouseWheelBackward(self, obj, event):
        self.super.OnMouseWheelBackward()


class SLabel3DAnnotation(QtWidgets.QFrame):
    signal_on_left_button_up = pyqtSignal(list)

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
        # self.bg_renderer.AddActor(axes)

        self.image_actor = None
        self.image_path = None

        self.actor_manager = ActorManager(self.renderer_window, self.interactor, self.bg_renderer)

        self.image_scale = 0

        self.json_data = None

        self.is_first_scene = True

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
        self.image_scale = 1 / image_width

        # Read image data
        if self.image_path.split(".")[-1] == "png":
            img_reader = vtk.vtkPNGReader()
        else:
            img_reader = vtk.vtkJPEGReader()

        img_reader.SetFileName(image_path)
        img_reader.Update()
        image_data = img_reader.GetOutput()
        self.image_actor = vtk.vtkImageActor()
        self.image_actor.SetInputData(image_data)

        transform = vtk.vtkTransform()
        transform.Scale(self.image_scale, self.image_scale, self.image_scale)
        transform.Translate(-image_width / 2, -image_height / 2, 0)
        self.image_actor.SetUserTransform(transform)
        self.bg_renderer.AddActor(self.image_actor)
        self.bg_renderer.ResetCamera()
        self.interactor.Render()

    @PyQt5.QtCore.pyqtSlot(str, int)
    def loadModel(self, model_path, model_class):
        self.actor_manager.newActor(model_path, model_class)

    def switchBoxWidgets(self, actor):
        index = self.actor_manager.getIndex(actor)
        if index != -1:
            self.actor_manager.setActiveActor(index)

    @PyQt5.QtCore.pyqtSlot(str, str, str)
    def loadScenes(self, scene_folder, image_file, annotation_file):
        # save the last scene before switch scenes
        if self.is_first_scene is True:
            self.is_first_scene = False
        else:
            self.saveScenes()

        # clear all the actors
        self.scene_folder, self.image_file, self.annotation_file = scene_folder, image_file, annotation_file
        # remove the image layer
        if self.image_actor is not None:
            self.bg_renderer.RemoveActor(self.image_actor)
        # remove all actors
        self.actor_manager.clear()
        self.style.reset()

        # load the image
        self.loadImage(image_file)

        # load the scenes
        data = self.actor_manager.loadAnnotation(annotation_file)

        if data is None:
            data = self.actor_manager.getEmptyJson(os.path.relpath(self.image_path, self.scene_folder))

        self.json_data = data
        self.actor_manager.setCamera(self.json_data["camera"])
        self.actor_manager.createActors(self.scene_folder, self.json_data)
        self.actor_manager.ResetCameraClippingRange()

    @PyQt5.QtCore.pyqtSlot()
    def saveScenes(self):
        if self.image_path is None or self.image_actor is None:
            return
        self.data = {}
        self.data["image_file"] = os.path.relpath(self.image_path, self.scene_folder)
        self.data.update(self.actor_manager.toJson(self.scene_folder))
        camera = self.bg_renderer.GetActiveCamera()
        self.data["camera"] = {}

        transform = getTransform(camera.GetModelViewTransformMatrix()).GetInverse()
        self.data["camera"]["matrix"] = matrix2List(transform.GetMatrix())
        self.data["camera"]["position"] = transform.GetPosition()
        self.data["camera"]["focalPoint"] = list(camera.GetFocalPoint())
        self.data["camera"]["fov"] = camera.GetViewAngle()
        self.data["camera"]["viewup"] = list(camera.GetViewUp())
        self.data["camera"]["distance"] = camera.GetDistance()
        if not os.path.exists(os.path.dirname(self.annotation_file)):
            os.makedirs(os.path.dirname(self.annotation_file))
        with open(self.annotation_file, 'w+') as f:
            json.dump(self.data, f, indent=4)

    @PyQt5.QtCore.pyqtSlot(bool)
    def model_update_with_property(self, is_changed):
        if is_changed is False:
            return
        if not self.style.isPressedLeft:
            if self.style.InteractionProp is None and len(self.actor_manager.actors) > 0:
                self.style.InteractionProp = self.actor_manager.actors[-1].actor
            elif self.style.InteractionProp is None and len(self.actor_manager.actors) == 0:
                return

            data = [self.parent().parent().property3d.config.get(p)
                    for p in ["x", "y", "z", "rz", "rx", "ry"]]
            self.style.InteractionProp.SetPosition(*data[:3])
            self.style.InteractionProp.SetOrientation(*data[3:])
            self.style.HighlightProp3D(self.style.InteractionProp)
            self.style.GetInteractor().Render()

            if self.interactor.GetInteractorStyle().GetAutoAdjustCameraClippingRange():
                self.actor_manager.ResetCameraClippingRange()
                # self.style.GetCurrentRenderer().ResetCameraClippingRange()

    # Shortcut key operation: delete selected model
    def delete_model(self):
        self.actor_manager.delete_actor()
