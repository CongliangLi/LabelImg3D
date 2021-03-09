import os
import sys
import numpy as np
import PyQt5
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QListWidgetItem, QLabel, QListWidget, QPushButton, QWidget, QHBoxLayout, QFileDialog, QFrame
from PyQt5.QtCore import QSize, pyqtSignal, QCoreApplication
import typing
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from pyqtconfig.config import ConfigManager

from pyqtconfig.qt import (QComboBox, QCheckBox, QSpinBox, QMainWindow,
                QLineEdit, QApplication, QTextEdit,
                QGridLayout, QWidget, QDockWidget)


class SConfig(QDockWidget):
    def __init__(self, title, parent):
        super().__init__(parent=parent)

        self.setWindowTitle(title)
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        
        self.config_edit = QTextEdit()
        self.config = ConfigManager()

        width_spin = QSpinBox()
        width_spin.setMaximum(50000)
        self.add(width_spin, 'width', 960, 1, 1)

        height_spin = QSpinBox()
        height_spin.setMaximum(50000)
        self.add(height_spin, 'height', 540, 2, 1)
        
        self.config.updated.connect(self.show_config)

        self.window = QWidget()
        self.window.setLayout(self.grid_layout)
        self.setWidget(self.window)


    def add(self, widget, name, default_value, row, col):
        hlayout = QHBoxLayout()
        label = QLabel(self)
        label.setText(name+": ")
        hlayout.addWidget(label)
        hlayout.addWidget(widget)

        self.config.set_defaults({name:default_value})
        self.grid_layout.addLayout(hlayout, row, col)
        self.config.add_handler(name, widget)

    def show_config(self):
        self.config_edit.setText(str(self.config.as_dict()))


if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self,parent=None):
            super(MainWindow, self).__init__(parent)
            layout=QHBoxLayout()

            self.items=SConfig("Title", self)

            self.setCentralWidget(QTextEdit())
            self.addDockWidget(Qt.RightDockWidgetArea,self.items)

            self.setLayout(layout)
            self.setWindowTitle('Dock')
    app=QApplication(sys.argv)
    demo=MainWindow()
    demo.show()
    sys.exit(app.exec_())
