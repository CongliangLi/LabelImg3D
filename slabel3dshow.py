import os
import sys
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal
import typing



class SLabel3dShow(QtWidgets.QLabel):

    def __init__(self, parent, model_path):
        super().__init__(parent=parent)
        self.interactor = QVTKRenderWindowInteractor(self)
        self.render_window = self.interactor.GetRenderWindow()
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(1, 1, 1)
        self.renderer.SetBackgroundAlpha(1)
        self.style = vtk.vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(self.style)
        self.render_window.AddRenderer(self.renderer)
        
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.interactor)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # analysis the obj model
        self.model_path = model_path
        self.model_folder, self.obj_name = os.path.split(self.model_path)
        self.obj_name = self.obj_name[:-4]
        self.mtl_path = self.model_folder + "/" + self.obj_name+".mtl"

        self.load_3d_model()

    def load_3d_model(self):        
        reader = vtk.vtkOBJImporter()
        reader.SetFileName(self.model_path)
        reader.SetFileNameMTL(self.mtl_path)
        reader.SetTexturePath(self.model_folder)
        reader.SetRenderWindow(self.render_window)
        reader.Update()
        self.renderer.ResetCamera()

    def start(self):
        self.interactor.Initialize()
        self.interactor.Start()

    def __del__(self):
        self.interactor.Finalize()
