from os import path
from pydm import Display
import os
import subprocess
import json
from pydm.widgets import PyDMEmbeddedDisplay
from PyQt5 import QtWidgets
from qtpy.QtWidgets import (QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame,
    QApplication, QWidget)

class MyDisplay(Display):

    def __init__(self, parent=None, args=None, macros=None):
        super(MyDisplay, self).__init__(parent=parent, args=args, macros=macros)
        self.initializa_setup()
        self.make_connections()
        self.display_hdf5_files()

    def ui_filename(self):
        return 'main.ui'

    def ui_filepath(self):
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())

    def initializa_setup(self):
        self.tab_dict = {}

    def make_connections(self):
        self.ui.listWidget_files.doubleClicked.connect(self.plot_tab)

    def display_hdf5_files(self):
        files = os.listdir(self.ui.lineEdit_dir_path.text())
        files = [i for i in files if i.endswith('.hdf5')]
        files.sort()
        self.ui.listWidget_files.clear()
        self.ui.listWidget_files.addItems(files)

    def plot_tab(self):
        item = self.ui.listWidget_files.currentItem()
        value = item.text()
        self.tab_dict[value] = {'widget' : QtWidgets.QWidget()}
        self.tabWidget.addTab(self.tab_dict[value]['widget'], value)
        self.tab_dict[value]['layout'] = QHBoxLayout()
        self.tab_dict[value]['widget'].setLayout(self.tab_dict[value]['layout'])
        self.tab_dict[value]['display'] = PyDMEmbeddedDisplay(parent=self)
        self.tab_dict[value]['display'].macros = json.dumps({"FILE":self.ui.lineEdit_dir_path.text() + value})
        self.tab_dict[value]['display'].filename = path.join(path.dirname(path.realpath(__file__)), 'plot_hdf5.py')
        self.tab_dict[value]['layout'].addWidget(self.tab_dict[value]['display'])




