import os
import vtkmodules.all as vtk_all
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5 import QtCore, uic, QtWidgets, QtGui
# from label3d import QDraw3DViewer
import Ui_main


class Draw3D(QtWidgets.QMainWindow):
    def __init__(self, data_dir):
        # Parent constructor
        super(Draw3D, self).__init__()
        self.vtk_widget = None
        self.ui = None
        self.setup()

        # connect
        self.ui.image_list.signal_double_click.connect(self.ui.vtk_panel.loadImage)
        self.ui.model_list.signal_double_click.connect(self.ui.vtk_panel.loadModel)

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
        return super().mousePressEvent(ev)


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
