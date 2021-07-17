from PyQt5.QtCore import *
from PyQt5.QtGui import *
import libs.Ui_main as Ui_main
from libs.simagelist import SImageList
from libs.smodellist import SModelList
from libs.sproperty import SProperty
from libs.lcamera_property import LCamera_Property

import os
from PyQt5 import QtCore, uic, QtWidgets, QtGui
from libs.scene_manager import SceneManager
from libs.slog import SLog
from libs.slabelimage import SLabelImage


class Draw3D(QtWidgets.QMainWindow):
    def __init__(self, data_dir):
        # Parent constructor
        self.super = super(Draw3D, self)
        self.super.__init__()
        self.vtk_widget = None
        self.ui = None
        self.setup()
        self.setWindowIcon(QIcon('libs/icons/icon.ico'))

        self.image_list = SImageList(self, "Images")
        self.model_list = SModelList.create(self, "Models")
        self.property3d = SProperty(self, "3DProperty")
        self.widget_log = SLog(self)
        self.camera_property = LCamera_Property(self, "Camera_Property")
        self.label_image = SLabelImage(self, "LabelImage")
        self.label_image.showImage()

        self.addDockWidget(Qt.RightDockWidgetArea, self.image_list)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.model_list)
        self.addDockWidget(Qt.RightDockWidgetArea, self.property3d)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.widget_log)
        self.addDockWidget(Qt.RightDockWidgetArea, self.camera_property)
        self.addDockWidget(Qt.RightDockWidgetArea, self.label_image)

        self.scene_manager = SceneManager(self, self.image_list, self.model_list, self.ui.vtk_panel)

        # menu in main window
        self.ui.action_Load_Scenes.triggered.connect(self.init_scenes)
        self.ui.action_Save_Scenes.triggered.connect(self.ui.vtk_panel.saveScenes)
        self.ui.action_Save_Scenes.triggered.connect(self.ui.vtk_panel.exportScenes)
        self.ui.actionHome.triggered.connect(self.scene_manager.home)
        self.ui.actionEnd.triggered.connect(self.scene_manager.end)
        self.ui.actionPrevious.triggered.connect(self.scene_manager.previous)
        self.ui.actionNext.triggered.connect(self.scene_manager.next)
        self.ui.action_Delete_Model.triggered.connect(self.ui.vtk_panel.delete_model)
        # self.ui.actionKITTI.triggered.connect(self.exportKITTI)

        # rotate
        for s in ['X', 'Y', 'Z', 'X_M', 'Y_M', 'Z_M']:
            eval('self.ui.actionRoate{}.triggered.connect'.format(s))(eval('self.property3d.roate{}'.format(s)))
        self.ui.actionCopy.triggered.connect(self.ui.vtk_panel.copy)
        self.ui.actionPaste.triggered.connect(self.ui.vtk_panel.paste)

        # connect the signals and slots
        # self.image_list.signal_double_click.connect(self.ui.vtk_panel.loadImage)
        self.image_list.listWidget.doubleClicked.connect(self.scene_manager.__getitem__)
        self.model_list.signal_double_click.connect(self.ui.vtk_panel.loadModel)
        self.scene_manager.signal_open_files.connect(self.image_list.open_files)
        self.scene_manager.signal_open_models.connect(self.model_list.open_files)
        self.ui.vtk_panel.signal_on_left_button_up.connect(self.property3d.update_property)
        self.ui.vtk_panel.signal_update_images.connect(self.label_image.showImage)
        self.ui.vtk_panel.signal_load_scene.connect(self.camera_property.new_camera_data)

        # highlist listWidget item
        self.ui.vtk_panel.actor_manager.signal_highlight_model_list.connect(self.model_list.highlight_item)
        self.scene_manager.signal_highlight_image_list.connect(self.image_list.highlight_item)

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
        return self.super.mousePressEvent(ev)

    def init_scenes(self):
        self.scene_manager.init_scenes()

    # def exportKITTI(self, checked):
    #     if checked:
    #         reconnect(self.ui.action_Save_Scenes.triggered, self.ui.vtk_panel.exportScenes, self.ui.vtk_panel.exportScenes)
    #     else:
    #         reconnect(self.ui.action_Save_Scenes.triggered, None, self.ui.vtk_panel.exportScenes)


def main():
    os.chdir(os.path.dirname(__file__))
    # Recompile ui
    with open("libs/main.ui") as ui_file:
        with open("libs/Ui_main.py", "w") as py_ui_file:
            uic.compileUi(ui_file, py_ui_file)

    app = QtWidgets.QApplication([])
    # qtmodern.styles.dark(app)
    main_window = Draw3D("volume")
    # style_main_window = qtmodern.windows.ModernWindow(main_window)
    main_window.show()
    main_window.initialize()
    app.exec_()


if __name__ == "__main__":
    main()
