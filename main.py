import os
from sproperty import SProperty
import vtkmodules.all as vtk_all
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
# from label3d import QDraw3DViewer
import Ui_main
from scene_manager import SceneManager
from simagelist import SImageList
from smodellist import SModelList
from sproperty import SProperty
from slog import SLog

import os
import vtkmodules.all as vtk_all
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5 import QtCore, uic, QtWidgets, QtGui
# from label3d import QDraw3DViewer
import Ui_main
from scene_manager import SceneManager
from slog import SLog

from vtk import *


class Draw3D(QtWidgets.QMainWindow):
    def __init__(self, data_dir):
        # Parent constructor
        super(Draw3D, self).__init__()
        self.vtk_widget = None
        self.ui = None
        self.setup()

        self.image_list = SImageList(self, "Images")
        self.model_list = SModelList(self, "Models")
        self.property3d = SProperty(self, "3DProperty")
        self.widget_log = SLog(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.image_list)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.model_list)
        self.addDockWidget(Qt.RightDockWidgetArea, self.property3d)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.widget_log)

        self.scene_manager = SceneManager(self, self.image_list, self.model_list, self.ui.vtk_panel)

        # menu in main window
        self.ui.action_Load_Scenes.triggered.connect(self.load_scenes)
        self.ui.action_Save_Scenes.triggered.connect(self.ui.vtk_panel.saveScenes)

        # connect the signals and slots
        self.image_list.signal_double_click.connect(self.ui.vtk_panel.loadImage)
        self.model_list.signal_double_click.connect(self.ui.vtk_panel.loadModel)
        self.scene_manager.signal_open_files.connect(self.image_list.open_files)
        self.scene_manager.signal_open_models.connect(self.model_list.open_files)
        self.ui.vtk_panel.actor_manager.signal_active_model.connect(self.property3d.updateBoxBounding)
        self.ui.vtk_panel.signal_on_left_button_up.connect(self.property3d.update_property)
        
    def setup(self):
        self.ui = Ui_main.Ui_MainWindow()
        self.ui.setupUi(self)
        # self.vtk_widget = ui.vtk_panel
        # self.ui.vtk_layout = QtWidgets.QHBoxLayout()
        # self.ui.vtk_layout.addWidget(self.vtk_widget)
        # self.ui.vtk_layout.setContentsMargins(0, 0, 0, 0)
        # self.ui.vtk_panel.setLayout(self.ui.vtk_layout)

    def initialize(self):
        self.ui.vtk_panel.start()

    def mousePressEvent(self, ev: QtGui.QMouseEvent) -> None:
        print("hello world")
        return self.super.mousePressEvent(ev)

    def load_scenes(self):
        self.scene_manager.load_scenes()


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    # Recompile ui
    with open("main.ui") as ui_file:
        with open("Ui_main.py", "w") as py_ui_file:
            uic.compileUi(ui_file, py_ui_file)

    app = QtWidgets.QApplication([])
    # qtmodern.styles.dark(app)
    main_window = Draw3D("volume")
    # style_main_window = qtmodern.windows.ModernWindow(main_window)
    main_window.show()
    main_window.initialize()
    app.exec_()
