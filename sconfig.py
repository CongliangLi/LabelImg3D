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
    """Configure Dockable Widgets. This is a class for showing and modifying the configure of the software
    """
    def __init__(self, title, parent):
        """Constructor

        Args:
            title (str): windows title
            parent (QWdiget): the parent window
        """
        super().__init__(parent=parent)

        self.setWindowTitle(title)
        self.grid_layout = QGridLayout()
        # self.layout().addChildLayout(self.grid_layout)
        
        self.config_edit = QTextEdit()
        self.config = ConfigManager()

        width_spin = QSpinBox()
        width_spin.setMaximum(50000)
        self.add(width_spin, 'width', 960, 1, 1)

        height_spin = QSpinBox()
        height_spin.setMaximum(50000)
        self.add(height_spin, 'height', 540, 2, 1)

        self.window = QFrame()
        self.window.setLayout(self.grid_layout)
        self.setWidget(self.window)


    def add(self, widget, name, default_value, row, col):
        """The utils function of adding new configured items.

        Args:
            widget (QWidget): The widget you want to add for holding the configure item.
            name (str): configure item name. a QLabel widget will also be created.
            default_value (any): default value of the configure item.
            row (int): row index. (1-index based)
            col (int): column index. (1-index based)
        """
        hlayout = QHBoxLayout()
        label = QLabel(self)
        label.setText(name+": ")
        hlayout.addWidget(label)
        hlayout.addWidget(widget)

        self.config.set_defaults({name:default_value})
        self.grid_layout.addLayout(hlayout, row, col)
        self.config.add_handler(name, widget)

    def get(self, key):
        """Get the configure items

        Args:
            key (str): the key of configure item

        Returns:
            any: the value of configure item
        """
        return self.config.get(key)

    def connect(self, update):
        """connect the function `update` when the configure updated

        Args:
            update (function): the update function, def update(sender):
        """
        self.config.updated.connect(update)


if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self,parent=None):
            super(MainWindow, self).__init__(parent)
            layout=QHBoxLayout()

            self.items=SConfig("Title", self)
            self.items.connect(MainWindow.update)

            self.setCentralWidget(QTextEdit())
            self.addDockWidget(Qt.RightDockWidgetArea,self.items)

            self.setLayout(layout)
            self.setWindowTitle('Dock')

        @staticmethod
        def update(sender, value):
            print(sender, value)

    app=QApplication(sys.argv)
    demo=MainWindow()
    demo.show()
    sys.exit(app.exec_())
