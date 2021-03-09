import sys
from pyqtconfig.config import ConfigManager

from pyqtconfig.qt import (QComboBox, QCheckBox, QSpinBox, QMainWindow,
                QLineEdit, QApplication, QTextEdit,
                QGridLayout, QWidget)

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle('PyQtConfig Demo')
        self.config = ConfigManager()

        CHOICE_A = 1
        CHOICE_B = 2
        CHOICE_C = 3
        CHOICE_D = 4

        map_dict = {
            'Choice A': CHOICE_A,
            'Choice B': CHOICE_B,
            'Choice C': CHOICE_C,
            'Choice D': CHOICE_D,
        }

        self.config.set_defaults({
            'number': 13,
            'text': 'hello',
            'active': True,
            'combo': CHOICE_C,
        })

        self.gd = QGridLayout()

        self.add(QSpinBox, 'number', 110, 0, 1)
        # sb = QSpinBox()
        # self.gd.addWidget(sb, 0, 1)
        # self.config.add_handler('number', sb)

        te = QLineEdit()
        self.gd.addWidget(te, 1, 1)
        self.config.add_handler('text', te)

        cb = QCheckBox()
        self.gd.addWidget(cb, 2, 1)
        self.config.add_handler('active', cb)

        cmb = QComboBox()
        cmb.addItems(map_dict.keys())
        self.gd.addWidget(cmb, 3, 1)
        self.config.add_handler('combo', cmb, mapper=map_dict)

        self.current_config_output = QTextEdit()
        self.gd.addWidget(self.current_config_output, 0, 3, 3, 1)

        self.config.updated.connect(self.show_config)

        self.show_config()

        self.window = QWidget()
        self.window.setLayout(self.gd)
        self.setCentralWidget(self.window)

    def add(self, ui_type, name, default_value, row, col):
        ui = ui_type()
        self.config.set_defaults({name:default_value})
        self.gd.addWidget(ui, row, col)
        self.config.add_handler(name, ui)

    def show_config(self):
        self.current_config_output.setText(str(self.config.as_dict()))

# Create a Qt application
app = QApplication(sys.argv)
app.setOrganizationName("PyQtConfig")
app.setOrganizationDomain("martinfitzpatrick.name")
app.setApplicationName("PyQtConfig")

w = MainWindow()
w.show()
app.exec_()  # Enter Qt application main loop
