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
from utils import *
from PyQt5.QtCore import pyqtSignal
from PyQt5.Qt import QObject
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

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
        # self.createBoxWidget()
        self.type_class = 0

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
        self.actor = self.readObj(model_path)
        # self.actor = self.importObj(model_path)

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
        self.renderer.SetBackground(0, 0, 0)
        self.renderer.InteractiveOff()
        self.renderer.SetBackgroundAlpha(0)
        self.renderer.SetActiveCamera(
            self.renderer_window.GetRenderers().GetFirstRenderer().GetActiveCamera()
            )
        self.renderer_window.AddRenderer(self.renderer)
        return self.renderer


    def setUserTransform(self, transform):
        # self.box_widget.SetTransform(transform)
        self.actor.SetUserTransform(transform)

    @staticmethod
    def copyTransformFromActor(src_actor, dst_actor):  
        # copy camera parameters      
        src_camera = src_actor.renderer.GetActiveCamera()
        dst_camera = dst_actor.renderer.GetActiveCamera()
        dst_camera.SetPosition(src_camera.GetPosition())
        dst_camera.SetFocalPoint(src_camera.GetFocalPoint())
        dst_camera.SetViewUp(src_camera.GetViewUp())

        # copy actor parameters
        transform = vtk.vtkTransform()
        transform.DeepCopy(src_actor.actor.GetUserTransform())
        dst_actor.setUserTransform(transform)

    def getCameraMatrix(self):
        matrix = self.renderer.GetActiveCamera().GetModelViewTransformMatrix()
        return [matrix.GetElement(i, j) for i in range(4) for j in range(4)]


    def toJson(self, scene_folder):
        return {
            "model_file": os.path.relpath(self.model_path, scene_folder),
            "matrix": self.getCameraMatrix(),
            "class": self.type_class
        }


class ActorManager(QObject):
    signal_active_model = pyqtSignal(list)

    def __init__(self, render_window, interactor, bg_renderer):
        super(ActorManager, self).__init__()
        self.render_window = render_window
        self.interactor = interactor
        self.bg_renderer = bg_renderer
        self.bg_renderer.GetActiveCamera()
        self.interactor.GetInteractorStyle().SetAutoAdjustCameraClippingRange(False)
        self.bg_renderer.GetActiveCamera().SetClippingRange(0.00001, 1000000)
        self.actors = []

    def newActor(self, model_path, camera_matrix = None):
        actor = Actor(self.render_window, self.interactor, model_path, len(self.actors)+1)
        if camera_matrix is None:
            # only copy the matrix of previous actors
            if len(self.actors) > 0:
                pass
                # Actor.copyTransformFromActor(self.actors[-1], actor)
        else:
            # copy the camera matrix
            matrix = vtk.vtkMatrix4x4()
            matrix.DeepCopy(camera_matrix)
            # matrix.Invert()
            transform = getTransform(matrix)

            if actor.actor.GetUserMatrix() is not None:
                transform.GetMatrix(actor.actor.GetUserMatrix())
            else:
                actor.actor.SetOrientation(transform.GetOrientation())
                actor.actor.SetPosition(transform.GetPosition())
                actor.actor.SetScale(transform.GetScale())
        
        self.actors.append(actor)
        self.setActiveActor(-1)

        if self.interactor.GetInteractorStyle().GetAutoAdjustCameraClippingRange():
            actor.renderer.ResetCameraClippingRange()

        self.interactor.Render()


    def setActiveActor(self, index):
        if index == -1:
            index = len(self.actors) - 1
        actor = self.actors[index]
        del self.actors[index]
        self.actors.append(actor)
        
        self.render_window.SetNumberOfLayers(len(self.actors)+1)

        for i, a in enumerate(self.actors):
            a.renderer.SetLayer(i+1)
            # a.renderer.Render()
        
        renderer = self.actors[-1].renderer
        # very important for set the default render
        self.interactor.GetInteractorStyle().SetDefaultRenderer(renderer)
        self.interactor.GetInteractorStyle().SetCurrentRenderer(renderer)
        if actor is not None:
            self.signal_active_model.emit(list(actor.actor.GetBounds()))


    #TODO: Remove the function
    def reformat(self):
        for a in self.actors:
            actor_matrix = deepCopyMatrix(a.actor.GetMatrix())
            actor_matrix.Invert()
            actor_transform = getTransform(actor_matrix)

            a.actor.SetUserMatrix(vtk.vtkMatrix4x4())
            # a.box_widget.SetTransform(vtk.vtkTransform())

            print(a.actor.GetBounds())
            camera = a.renderer.GetActiveCamera()
            camera.ApplyTransform(actor_transform)

    def getCurrentActiveActor(self):
        return self.actors[-1].actor

    def getCurrentActiveRenderer(self):
        return self.actors[-1].renderer

    def getIndex(self, actor):
        i = -1
        for i in reversed(range(len(self.actors))):
            if self.actors[i].actor is actor:
                break
        return i

    def clear(self):
        for a in self.actors:
            a.renderer.RemoveActor(a)
            a.actor.Delete()
            self.render_window.RemoveRenderer(a.renderer)
        self.actors = []
        pass

    def loadAnnotation(self, annotation_file):
        if not os.path.exists(annotation_file):
            return
        data = None
        with open(annotation_file, 'r') as f:
            data = json.load(f)
        
        return data

    def setCamera(self, camera_data):
        camera = self.bg_renderer.GetActiveCamera()
        camera.SetPosition(camera_data["position"])
        camera.SetFocalPoint(camera_data["focalPoint"])
        camera.SetViewAngle(camera_data["fov"])
        camera.SetViewUp(camera_data["viewup"])
        camera.SetDistance(camera_data["distance"])
        

    def createActors(self, scene_folder, data):
        for i in range(data["model"]["num"]):
            model_path = os.path.join(scene_folder, data["model"][str(i)]["model_file"])
            self.newActor(model_path, data["model"][str(i)]["matrix"])

    def toJson(self, scene_folder):
        # self.reformat()
        # print info
        for i, a in enumerate(self.actors):
            print("======{}======\n".format(i), a.actor.GetUserTransform().GetMatrix())
            print(a.renderer.GetActiveCamera().GetViewTransformMatrix())
        data = {"model": {}}
        data["model"]["num"] = len(self.actors)
        for i in range(len(self.actors)):
            data["model"]["{}".format(i)] = self.actors[i].toJson(scene_folder)
        return data
