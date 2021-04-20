import os
import sys
import PyQt5
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from pyqtconfig.config import ConfigManager

from pyqtconfig.qt import (QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox, QMainWindow,
                           QLineEdit, QApplication, QTextEdit,
                           QGridLayout, QWidget, QDockWidget)

from vtk import *
from math import atan
from math import tan
from PIL import Image


class LCamera_Property(QDockWidget):
    """Configure Dockable Widgets. This is a class for showing and modifying the configure of the camera
    """
    signal_camera_change = pyqtSignal(list)

    def __init__(self, parent, title="Camera_Property"):
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
        self.camera_data = []
        self.is_change = True
        self.img_size = []

        for i, x in enumerate(['x', 'y', 'z', "fov", 'distance']):
            width_spin = QDoubleSpinBox()
            width_spin.setMaximum(50000)
            width_spin.setMinimum(-50000)
            self.add(width_spin, x, 0, i + 1, 1)

            width_spin.valueChanged.connect(lambda: self.update_camera_data())
            width_spin.valueChanged.connect(
                lambda: self.parent().ui.vtk_panel.actor_manager.update_camera(self.camera_data, self.is_change))

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
        label.setText(name + ": ")
        hlayout.addWidget(label)
        hlayout.addWidget(widget)

        self.config.set_defaults({name: default_value})
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

    @PyQt5.QtCore.pyqtSlot()
    def update_camera_data(self):
        if self.is_change is False:
            return

        camera_data_present = [self.config.get(p)
                               for p in ["x", "y", "z", "fov", "distance"]]

        num = -1
        for i in range(len(camera_data_present)):
            if camera_data_present[i] == self.camera_data[i]:
                pass
            else:
                num = i

        if num == 0 or num == 1:  # x or y
            self.config.set("x", 0.00)
            self.config.set("y", 0.00)

        # The three(z, fov and distance) are interrelated
        if num == 2:  # z
            self.is_change = False
            self.config.set("distance", camera_data_present[2])
            fov = 2 * atan((self.img_size[1] * self.parent().ui.vtk_panel.image_scale) / (2 * camera_data_present[2]))
            self.config.set("fov", fov)

            self.is_change = True

        if num == 3:  # fov
            self.is_change = False
            distance = (self.img_size[1] * self.parent().ui.vtk_panel.image_scale) / \
                       (2 * (tan(camera_data_present[3] / 2)))
            self.config.set("z", distance)
            self.config.set("distance", distance)
            self.is_change = True

        if num == 4:  # distance
            self.is_change = False
            self.config.set("z", camera_data_present[4])

            fov = 2 * atan((self.img_size[1] * self.parent().ui.vtk_panel.image_scale) / (2 * camera_data_present[2]))
            self.config.set("fov", fov)

            self.is_change = True

        self.camera_data.clear()
        self.camera_data = [self.config.get(p)
                            for p in ["x", "y", "z", "fov", "distance"]]

    @PyQt5.QtCore.pyqtSlot(list)
    def new_camera_data(self, new_camera_data):
        self.camera_data.clear()
        self.is_change = False

        for i in range(len(new_camera_data)):
            self.camera_data.append(new_camera_data[i])
            # print(self.camera_data[i])

        self.config.set("x", self.camera_data[0])
        self.config.set("y", self.camera_data[1])
        self.config.set("z", self.camera_data[2])
        self.config.set("fov", self.camera_data[3])
        self.config.set("distance", self.camera_data[4])
        self.img_size = Image.open(self.parent().image_list.file_list[0]).size

        self.is_change = True


if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self, parent=None):
            super(MainWindow, self).__init__(parent)
            layout = QHBoxLayout()

            self.items = LCamera_Property(self, "Camera_Property")

            self.setCentralWidget(QTextEdit())
            self.addDockWidget(Qt.RightDockWidgetArea, self.items)

            self.setLayout(layout)
            self.setWindowTitle('Dock')

        @staticmethod
        def update(sender):
            print(sender)


    app = QApplication(sys.argv)
    demo = MainWindow()
    demo.show()
    sys.exit(app.exec_())
