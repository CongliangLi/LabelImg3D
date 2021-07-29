import os
import sys
import PyQt5
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .pyqtconfig.config import ConfigManager

from .pyqtconfig.qt import (QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox, QMainWindow,
                            QLineEdit, QApplication, QTextEdit,
                            QGridLayout, QWidget, QDockWidget)

from vtk import *
import json


class SProperty(QDockWidget):
    """Configure Dockable Widgets. This is a class for showing and modifying the configure of the software
    """
    signal_property_change = pyqtSignal(list)

    def __init__(self, parent, title="3DProperty"):
        """Constructor

        Args:
            title (str): windows title
            parent (QWdiget): the parent window
        """
        super().__init__(parent=parent)

        self.setWindowTitle(title)
        self.grid_layout = QGridLayout()
        self.config_edit = QTextEdit()
        self.config = ConfigManager()
        self.is_changed = True

        # Load config
        with open("libs/config.json", 'r') as load_f:
            config_data = json.load(load_f)
        self.max_position = config_data["model"]["max_position"]
        self.position_accuracy = config_data["model"]["position_accuracy"]
        self.size_accuracy = config_data["model"]["size_accuracy"]

        for i, x in enumerate(['x', 'y', 'z', 'rx', 'ry', 'rz', 'w', 'l', 'h', 's']):
            width_spin = QDoubleSpinBox()
            width_spin.setMaximum(50000)
            width_spin.setMinimum(-50000)
            if x == "x" or x == "y" or x == "z":
                width_spin.setDecimals(self.position_accuracy)
            if x == "w" or x == "l" or x == "h":
                width_spin.setDecimals(self.size_accuracy)

            self.add(width_spin, x, 1 if x == 's' else 0, i + 1, 1)

            width_spin.valueChanged.connect(lambda: self.parent(
            ).ui.vtk_panel.model_update_with_property(self.is_changed))

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

    @PyQt5.QtCore.pyqtSlot(list)
    def update_property(self, data):
        # for i in range(len(data)):
        #     print(data[i])
        if data[2] > self.max_position:
            self.config.set(
                "x", self.parent().ui.vtk_panel.actor_manager.model_initial_position[0])
            self.config.set(
                "y", self.parent().ui.vtk_panel.actor_manager.model_initial_position[1])
            self.config.set(
                "z", self.parent().ui.vtk_panel.actor_manager.model_initial_position[2])

        self.is_changed = False
        [self.config.set(s, d) for s, d in zip(
            ["x", "y", "z", "rz", "rx", "ry", "w", "l", "h"], data)
         ]
        self.is_changed = True

    def connect(self, update):
        """connect the function `update` when the configure updated

        Args:
            update (function): the update function, def update(sender):
        """
        self.config.updated.connect(update)

    def roateX(self):
        self.is_changed = True
        self.config.set("rx", float(self.config.get("rx")) +
                        float(self.config.get("s")))

    def roateX_M(self):
        self.config.set("rx", float(self.config.get("rx")) -
                        float(self.config.get("s")))

    def roateY(self):
        self.config.set("ry", float(self.config.get("ry")) +
                        float(self.config.get("s")))

    def roateY_M(self):
        self.config.set("ry", float(self.config.get("ry")) -
                        float(self.config.get("s")))

    def roateZ(self):
        self.config.set("rz", float(self.config.get("rz")) +
                        float(self.config.get("s")))

    def roateZ_M(self):
        self.config.set("rz", float(self.config.get("rz")) -
                        float(self.config.get("s")))


if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self, parent=None):
            super(MainWindow, self).__init__(parent)
            layout = QHBoxLayout()

            self.items = SProperty(self, "3DProperty")

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
