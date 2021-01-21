import os
import sys
import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QListWidgetItem, QLabel, QListWidget, QPushButton, QWidget, QHBoxLayout, QFileDialog, QFrame
from PyQt5.QtCore import QSize, pyqtSignal, QCoreApplication
import typing
from slabel3dshow import SLabel3dShow


class SImageList(QFrame):
    signal_load_model = pyqtSignal(int, int)
    signal_double_click = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent=parent)
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
        self.btnOpenFolder.setText("&Open Images")
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

        self.setLayout(self.verticalLayout)

        ######### connect #########
        # connect openfiles
        self.btnOpenFolder.clicked.connect(self.open_files)
        # connect the double click event of self.listWidget
        self.listWidget.doubleClicked.connect(self.listWidgetDoubleClicked)

        # file list
        self.file_list = []

    def open_files(self):
        file_list, _ = QtWidgets.QFileDialog.getOpenFileNames(
            None, "Open images", "./", "Images (*.jpg)")

        file_list = list(set(file_list).difference(self.file_list))
        self.file_list += file_list

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
        item = QListWidgetItem(self.listWidget)
        item.setText(name)
        self.listWidget.addItem(item)

    def listWidgetDoubleClicked(self, index):
        self.signal_double_click.emit(self.file_list[index.row()])
        print(self.file_list[index.row()])
