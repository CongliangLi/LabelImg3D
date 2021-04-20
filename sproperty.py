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
        # self.layout().addChildLayout(self.grid_layout)
        self.config_edit = QTextEdit()
        self.config = ConfigManager()

        for i, x in enumerate(['x', 'y', 'z', 'rx', 'ry', 'rz', 'w', 'h', 'l']):
            width_spin = QDoubleSpinBox()
            width_spin.setMaximum(50000)
            width_spin.setMinimum(-50000)
            self.add(width_spin, x, 540, i + 1, 1)

            width_spin.valueChanged.connect(lambda: self.parent().ui.vtk_panel.model_update_with_property())

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
    def updateBoxBounding(self, data):
        self.config.set('x', data[0])
        self.config.set('y', data[2])
        self.config.set('z', data[4])
        self.config.set('w', data[1] - data[0])
        self.config.set('h', data[3] - data[2])
        self.config.set('l', data[5] - data[4])

    @PyQt5.QtCore.pyqtSlot(list)
    def update_property(self, data):
        # for i in range(len(data)):
        #     print(data[i])
        self.config.set("x", data[0])
        self.config.set("y", data[1])
        self.config.set("z", data[2])
        self.config.set("rx", data[4])
        self.config.set("ry", data[5])
        self.config.set("rz", data[3])

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

            self.items=SProperty(self, "3DProperty")

            self.setCentralWidget(QTextEdit())
            self.addDockWidget(Qt.RightDockWidgetArea,self.items)

            self.setLayout(layout)
            self.setWindowTitle('Dock')

        @staticmethod
        def update(sender):
            print(sender)

    app=QApplication(sys.argv)
    demo=MainWindow()
    demo.show()
    sys.exit(app.exec_())
