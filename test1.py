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
        self.isPressedRight = False
        self.isPressedLeft = False
        self.super = super(MyInteractorStyle, self)
        self.InteractionPicker = vtkCellPicker()
        self.InteractionProp = None
        
    def __del__(self):
        del self.InteractionPicker

    def OnLeftButtonDown(self, obj, event):
        self.isPressedLeft = True
        # picker = self.GetInteractor().GetPicker()
        camera = self.GetCurrentRenderer().GetActiveCamera()
        actor = self.GetCurrentRenderer().GetActors().GetLastActor()
        print(actor.GetMatrix())

        x, y = self.GetInteractor().GetEventPosition()
        self.InteractionPicker.Pick(x, y, 0.0, self.GetCurrentRenderer())
        self.InteractionProp = self.InteractionPicker.GetViewProp()

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
        self.isPressedLeft = False
        self.super.OnLeftButtonUp()
        print("OnLeftButtonUp")

    def OnRightButtonDown(self, obj, event):
        print("RightButtonDown")
        self.isPressedRight = True

        x, y = self.GetInteractor().GetEventPosition()
        self.InteractionPicker.Pick(x, y, 0.0, self.GetCurrentRenderer())
        self.InteractionProp = self.InteractionPicker.GetViewProp()

        self.super.OnRightButtonDown()

    def OnRightButtonUp(self, obj, event):
        print("RightButtonUp")
        self.isPressedRight = False
        self.super.OnRightButtonUp()
        print(self.GetCurrentRenderer().GetActors().GetLastActor().GetMatrix())


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
        motion_vector = [-0.01 * d * dy for d in direction]
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

        # print(obj_center)

        # yf = dy / center[1] *  10.0
        # scaleFactor = 1.1 ** yf
        # rotate = None
        # scale = [scaleFactor]*3
        # self.Prop3DTransform(self.InteractionProp, obj_center, 0, rotate, scale)
        # rwi.Render()


    def OnMouseMove(self, obj, event):
        x, y = self.GetInteractor().GetEventPosition()

        if self.isPressedRight and not self.GetInteractor().GetShiftKey():
            self.FindPokedRenderer(x, y)
            self.UniformScale()
            self.InvokeEvent(vtkCommand.InteractionEvent, None)
            return 
        # if self.isPressedLeft:
        #     if self.GetInteractor().GetShiftKey():
        #         self.super.OnMouseMove()
        #         camera = self.GetCurrentRenderer().GetActiveCamera()
        #         print(camera.GetFocalPoint())
            
            # else:
            #     # camera = self.GetCurrentRenderer().GetActiveCamera()
            #     # origin = camera.GetFocalPoint()
            #     # camera.SetFocalPoint(0, 0, 0)
            #     self.FindPokedRenderer(x, y)
            #     self.UniformScale()
            #     self.InvokeEvent(vtkCommand.InteractionEvent, None)
            #     return 
                # camera.SetFocalPoint(origin)

            # camera = self.GetCurrentRenderer().GetActiveCamera()
            # camera.SetFocalPoint(0, 0, 0)
            # camera = self.GetCurrentRenderer().GetActiveCamera()
            # actor = self.GetCurrentRenderer().GetActors().GetLastActor()
            # print(camera.GetViewTransformMatrix())
        self.super.OnMouseMove()

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
    
