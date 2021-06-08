import os
import sys
import numpy as np
from datetime import datetime
import sys
import PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import cv2


class SLabelImage(QDockWidget):
    """The Log Window
    """
    def __init__(self, parent, title="Label Image"):
        """Constructor

        Args:
            title (str): windows title
            parent (QWdiget): the parent window
        """
        super().__init__(parent=parent)

        self.setWindowTitle(title)
        self.grid_layout = QGridLayout()
        self.grid_layout.setContentsMargins(20, 20, 20, 20)

        self.label = QLabel("")
        self.grid_layout.addWidget(self.label, 1, 1)

        self.window = QFrame()
        self.window.setLayout(self.grid_layout)
        self.setWidget(self.window)

        self.image = None

    def resizeEvent(self, event):
        self.showImage(self.image)

    @PyQt5.QtCore.pyqtSlot(np.ndarray)
    def showImage(self, image=None):
        if image is None or image.size == 0:
            image = np.zeros((512,512,3), np.uint8)
        self.image = image
        width, height = self.label.geometry().width(), self.label.geometry().height()
        self.label.setPixmap(
            SLabelImage.image_cv2qt(self.image, width, height)
        )

    def image_cv2qt(cv_img, width, height):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(width, height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)



if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self,parent=None):
            super(MainWindow, self).__init__(parent)
            layout=QHBoxLayout()

            self.items=SLabelImage(self)

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
