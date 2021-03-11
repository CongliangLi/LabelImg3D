import os
import sys
import numpy as np
from datetime import datetime
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


class SLog(QDockWidget):
    """The Log Window
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

        self.btn_clear = QPushButton("clear")
        self.btn_clear.clicked.connect(self.clear_log)
        self.btn_clear.setMaximumWidth(80)
        self.grid_layout.addWidget(self.btn_clear, 1, 1)

        self.textEdit = QTextEdit()
        self.textEdit.setReadOnly(True)
        self.textEdit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.textEdit.setLineWrapMode(self.textEdit.NoWrap)
        self.textEdit.ensureCursorVisible()
        self.grid_layout.addWidget(self.textEdit, 2, 1, 1, 2)


        self.window = QFrame()
        self.window.setLayout(self.grid_layout)
        self.setWidget(self.window)

    def clear_log(self):
        self.textEdit.clear()

    def append_log(self, *args, **kwargs):
        for a in args:
            self.textEdit.setPlainText(
              self.textEdit.toPlainText() + "\n{}".format(a)
            )
        for _, v in kwargs:
            self.textEdit.setPlainText(
              self.textEdit.toPlainText() + "\n{}".format(v)
            )

        self.textEdit.moveCursor(QtGui.QTextCursor.End)


if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self,parent=None):
            super(MainWindow, self).__init__(parent)
            layout=QHBoxLayout()

            self.items=SLog("Log", self)

            self.setCentralWidget(QTextEdit())
            self.addDockWidget(Qt.BottomDockWidgetArea,self.items)

            self.items.append_log(*("this is a log", "this is not a log")*100)

            self.setLayout(layout)
            self.setWindowTitle('Dock')

        @staticmethod
        def update(sender):
            print(sender)

    app=QApplication(sys.argv)
    demo=MainWindow()
    demo.show()
    sys.exit(app.exec_())
