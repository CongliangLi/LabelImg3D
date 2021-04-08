import os
from sproperty import SProperty
import vtkmodules.all as vtk_all
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
# from label3d import QDraw3DViewer
import Ui_main
from scene_manager import SceneManager
from simagelist import SImageList
from smodellist import SModelList
from sproperty import SProperty
from slog import SLog

import os
import vtkmodules.all as vtk_all
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5 import QtCore, uic, QtWidgets, QtGui
# from label3d import QDraw3DViewer
import Ui_main
from scene_manager import SceneManager
from slog import SLog


from vtk import *

class MyInteractorStyle(vtkInteractorStyleTrackballActor):
    def __init__(self):
        self.AddObserver('LeftButtonPressEvent', self.OnLeftButtonDown, -1)
        self.AddObserver('LeftButtonReleaseEvent', self.OnLeftButtonUp, -1)
        self.AddObserver('RightButtonPressEvent', self.OnRightButtonDown, -1)
        self.AddObserver('RightButtonReleaseEvent', self.OnRightButtonUp, -1)
        self.AddObserver('MouseMoveEvent', self.OnMouseMove, -1)
        self.AddObserver('MouseWheelForwardEvent', self.OnMouseWheelForward, -1)
        self.AddObserver('MouseWheelBackwardEvent', self.OnMouseWheelBackward, -1)
        self.isPressed = False
        self.super = super(MyInteractorStyle, self)
        
    def OnLeftButtonDown(self, obj, event):
        self.isPressed = True
        # picker = self.GetInteractor().GetPicker()
        camera = self.GetCurrentRenderer().GetActiveCamera()
        actor = self.GetCurrentRenderer().GetActors().GetLastActor()
        print(actor.GetMatrix())

        # if self.PositionPicked() != 0:
        #    camera.SetFocalPoint(picker.GetPickPosition())
        # camera = self.GetCurrentRenderer().GetActiveCamera()
        # camera.SetWindowCenter(*(self.GetOriginPointDisplay()))

        self.super.OnLeftButtonDown()

        # self.GetInteractor().Render()

        # focalPoint = camera.GetFocalPoint()
        # viewUp = camera.GetViewUp()
        # position = camera.GetPosition()

        # print(camera.GetViewTransformMatrix())
        # print(self.GetActorCenter())

    def OnLeftButtonUp(self, obj, event):
        self.isPressed = False
        self.super.OnLeftButtonUp()
        print("OnLeftButtonUp")

    def OnRightButtonDown(self, obj, event):
        print("RightButtonDown")
        self.isPressed = True
        self.super.OnRightButtonDown()

    def OnRightButtonUp(self, obj, event):
        print("RightButtonUp")
        self.isPressed = False
        self.super.OnRightButtonUp()
        print(self.GetCurrentRenderer().GetActors().GetLastActor().GetMatrix())



    def OnMouseMove(self, obj, event):
        if self.isPressed:
            if self.GetInteractor().GetShiftKey():
                self.super.OnMouseMove()
                camera = self.GetCurrentRenderer().GetActiveCamera()
                print(camera.GetFocalPoint())
            else:
                # camera = self.GetCurrentRenderer().GetActiveCamera()
                # origin = camera.GetFocalPoint()
                # camera.SetFocalPoint(0, 0, 0)
                self.super.OnMouseMove()
                # camera.SetFocalPoint(origin)

            # camera = self.GetCurrentRenderer().GetActiveCamera()
            # camera.SetFocalPoint(0, 0, 0)
            camera = self.GetCurrentRenderer().GetActiveCamera()
            # actor = self.GetCurrentRenderer().GetActors().GetLastActor()
            # print(camera.GetViewTransformMatrix())

    def OnMouseWheelForward(self, obj, event):
        self.super.OnMouseWheelForward()

        camera = self.GetCurrentRenderer().GetActiveCamera()
        # actor = self.GetCurrentRenderer().GetActors().GetLastActor()
        print(camera.GetViewTransformMatrix())

    def OnMouseWheelBackward(self, obj, event):
        self.super.OnMouseWheelBackward()
        camera = self.GetCurrentRenderer().GetActiveCamera()
        # actor = self.GetCurrentRenderer().GetActors().GetLastActor()
        print(camera.GetViewTransformMatrix())

    def GetActorCenter(self):
        actor = self.GetCurrentRenderer().GetActors().GetLastActor()
        bounds = actor.GetBounds()
        print(bounds)
        return [(bounds[i*2]+bounds[i*2+1])/2.0 for i in range(3)]

    def GetOriginPointDisplay(self):
        center = [0.0, 0.0, 0.0]
        MyInteractorStyle.ComputeWorldToDisplay(self.GetCurrentRenderer(), 0, 0, 0, center)
        w, h = self.GetCurrentRenderer().GetRenderWindow().GetSize()
        return center[0]/w*2-1, center[1]/h*2-1

    def Rotate(self):
        print("hello world======================================================")
        if self.GetCurrentRenderer() is None:
            return 

        rwi = self.GetInteractor()
        dx, dy = (rwi.GetEventPosition()[i] - rwi.GetLastEventPosition()[i] for i in range(2))
        size = self.GetCurrentRenderer().GetRenderWindow().GetSize()
        delta_azimuth = -20.0 / size[0]
        delta_elevation = -20.0 / size[1]

        rxf = dx * delta_azimuth * self.GetMotionFactor()
        ryf = dy * delta_elevation * self.GetMotionFactor()

        camera = self.GetCurrentRenderer().GetActiveCamera()
        camera.Azimuth(rxf)
        camera.Elevation(ryf)
        camera.OrthogonalizeViewUp()

        if self.GetAutoAdjustCameraClippingRange():
            self.GetCurrentRenderer().ResetCameraClippingRange()

        if rwi.GetLightFollowCamera():
            self.GetCurrentRenderer().UpdateLightsGeometryToFollowCamera()

        rwi.Render()

    def PositionPicked(self):
        click_pos = self.GetInteractor().GetEventPosition()
        picker = self.GetInteractor().GetPicker()
        t = picker.Pick(click_pos[0], click_pos[1], 0, self.GetCurrentRenderer())
        return t


if __name__ == "__main__":
    cone = vtkConeSource()
    cone.Update()

    mapper = vtkPolyDataMapper()
    mapper.SetInputData(cone.GetOutput())
    mapper.ScalarVisibilityOn()
    mapper.SetScalarModeToUsePointData()
    mapper.SetColorModeToMapScalars()

    actor = vtkActor()
    actor.SetMapper(mapper)

    renderer = vtkRenderer()

    renderWindow = vtkRenderWindow()
    renderWindow.AddRenderer(renderer)

    renderWindowInteractor = vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)

    # style = vtkInteractorStyleTrackballCamera()
    # style = vtkInteractorStyleTrackballActor()
    # style = vtkInteractorStyleTerrain()
    # style = vtkInteractorStyleSwitch()
    # style = vtkInteractorStyleRubberBandZoom()
    # style = vtkInteractorStyleRubberBandPick()
    # style = vtkInteractorStyleRubberBand3D()
    # style = vtkInteractorStyleJoystickCamera()
    # style = vtkInteractorStyleJoystickActor()
    style = MyInteractorStyle()
    style.SetCurrentRenderer(renderer)
    renderWindowInteractor.SetInteractorStyle(style)

    renderer.AddActor(actor)

    renderWindow.Render()
    renderWindowInteractor.Start()
    
