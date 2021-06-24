import os
import sys
import numpy as np
import PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import typing
from slabel3dshow import SLabel3dShow
import vtk
from pathlib import Path
import json


class SModelList(QDockWidget):
    signal_load_model = pyqtSignal(int, int)
    signal_double_click = pyqtSignal(str, int, str)
    signal_model_class = pyqtSignal(list)
    obj = None

    @staticmethod
    def create(parent, title="models"):
        SModelList.obj = SModelList(parent, title)
        return SModelList.obj

    @staticmethod
    def get():
        return SModelList.obj

    def __init__(self, parent, title="models"):
        super().__init__(parent=parent)
        self.setWindowTitle(title)
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setAlignment(QtCore.Qt.AlignLeft)
        self.btnOpenFolder = QtWidgets.QPushButton(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnOpenFolder.sizePolicy().hasHeightForWidth())
        self.btnOpenFolder.setSizePolicy(sizePolicy)
        self.btnOpenFolder.setObjectName("btnOpenFolder")
        self.btnOpenFolder.setText("&Open 3D Models")
        self.btnOpenFolder.setVisible(False)
        self.horizontalLayout.addWidget(self.btnOpenFolder)
        self.progress_bar_load = QtWidgets.QProgressBar(self)
        self.progress_bar_load.setProperty("value", 24)
        self.progress_bar_load.setObjectName("progress_bar_load")
        self.progress_bar_load.setVisible(False)
        self.horizontalLayout.addWidget(self.progress_bar_load)
        self.horizontalLayout.setStretch(0, 2)
        self.horizontalLayout.setStretch(1, 8)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.listWidget = QtWidgets.QListWidget(self)
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout.addWidget(self.listWidget)

        self.window = QFrame()
        self.window.setLayout(self.verticalLayout)
        self.setWidget(self.window)
        # connect
        # self.btnOpenFolder.clicked.connect(self.open_files)
        # connect the double click event of self.listWidget
        self.listWidget.doubleClicked.connect(self.listWidgetDoubleClicked)

        # file list
        self.file_list = []
        self.model_list = {}
        self.model_info = {}

    @PyQt5.QtCore.pyqtSlot(str)
    def highlight_item(self, model_file):
        try:
            index = self.file_list.index(model_file)
            if index < self.listWidget.count():
                self.listWidget.setCurrentRow(index)
                self.listWidget.item(index).setSelected(True)
                self.listWidget.setFocus()
        except Exception as e:
            print(e)

    @PyQt5.QtCore.pyqtSlot(list)
    def open_files(self, file_list=None):
        # file_list, _ = QtWidgets.QFileDialog.getOpenFileNames(
        #     None, "Open 3D Model", "./", "3D Models (*.obj)")

        # # filter
        # file_list = list(set(file_list).difference(self.file_list))
        # self.file_list += file_list

        if file_list is None or len(file_list) == 0:
            return

        models_info_file = Path(file_list[0]).parent / "models.json"

        # if cannot find the models.json, then generate it automatically
        if not os.path.exists(models_info_file):
            for i, f in enumerate(file_list):
                self.model_info[Path(f).name] = {"class_name": Path(f).stem[:-4], "class_index": i+1}
            with open(models_info_file, 'w+') as f:
                json.dump(self.model_info, f, indent=4)
        else:
            with open(models_info_file, "r") as f:
                self.model_info = json.load(f)

        self.file_list = file_list
        self.progress_bar_load.setVisible(True)

        num_model = len(file_list)
        for i in range(num_model):
            self.signal_load_model.emit(i, num_model)
            self.add_item(file_list[i])
            self.progress_bar_load.setValue((i+1)/num_model*100)
            # event loop
            QCoreApplication.processEvents()

        self.progress_bar_load.setVisible(False)

    def add_item(self, model_path):
        name = os.path.split(model_path)[-1][:-4]
        item = QListWidgetItem(self.listWidget, 0)
        widgets = QWidget(self)
        model_label = SLabel3dShow(self, model_path)
        self.model_list[model_path] = model_label.actor
        text_label = QLabel(name)
        widget_layout = QHBoxLayout()

        item.setSizeHint(QSize(300, 300))
        widget_layout.addWidget(model_label)
        widget_layout.addWidget(text_label)
        widget_layout.setStretch(0, 3)
        widget_layout.setStretch(1, 1)
        widgets.setLayout(widget_layout)
        self.listWidget.setItemWidget(item, widgets)
        model_label.start()

    def getActor(self, model_path):
        if model_path not in self.model_list.keys():
            print("Cannot find the 3d model {}".format(model_path))
            return None
        actor = self.model_list[model_path]
        copy_data = vtk.vtkPolyData()
        copy_data.DeepCopy(actor.GetMapper().GetInput())

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(copy_data)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        return actor

    def listWidgetDoubleClicked(self, index):
        file_path = self.file_list[index.row()]
        class_name, class_index = self.model_info[Path(file_path).name].values()
        self.signal_double_click.emit(file_path, class_index, class_name)
        print(self.file_list[index.row()])


if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self,parent=None):
            super(MainWindow, self).__init__(parent)
            layout=QHBoxLayout()

            self.items=SModelList(self, "Models")

            self.setCentralWidget(QTextEdit())
            self.addDockWidget(Qt.LeftDockWidgetArea,self.items)

            self.setLayout(layout)
            self.setWindowTitle('Dock')

        @staticmethod
        def update(sender):
            print(sender)

    app=QApplication(sys.argv)
    demo=MainWindow()
    demo.show()
    sys.exit(app.exec_())