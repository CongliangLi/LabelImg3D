from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import QtCore, uic, QtWidgets, QtGui
from libs.Ui_kitti_2_labelimg3d import Ui_FormKitti2LabelImg3D
        
class Kitti2LabelImg3D(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.window = QtWidgets.QWidget()
        self.ui = Ui_FormKitti2LabelImg3D()
        self.ui.setupUi(self.window)
        self.ui.openFolder_Btn.clicked.connect(self.openFolder)


    def openFolder(self):
        print("hello world")
        pass

    def convert(self):
        pass


    def show(self):
        self.window.show()