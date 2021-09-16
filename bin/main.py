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
        
    def ui_filename(self):
        return 'main.ui'

    def ui_filepath(self):
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())

    def initializa_setup(self):
        self.app = QApplication.instance()
        self.app.main_window.showNormal()
        self.tab_dict = {}
        self.make_connections()
        self.display_hdf5_files()

    def make_connections(self):
        self.ui.listWidget_files.doubleClicked.connect(self.plot_tab)
        self.ui.pushButton_multi_plot.clicked.connect(self.plot_tab)
        self.ui.pushButton_delete_tab.clicked.connect(self.delete_tab)
        self.ui.lineEdit_dir_path.returnPressed.connect(self.display_hdf5_files)


    def display_hdf5_files(self):
        files = os.listdir(self.ui.lineEdit_dir_path.text())
        files = [i for i in files if i.endswith('.hdf5')]
        files.sort()
        self.ui.listWidget_files.clear()
        self.ui.listWidget_files.addItems(files)

    def plot_tab(self):
        items = [item.text() for item in self.ui.listWidget_files.selectedItems()]
        tab_name = ''
        for item in items:
            tab_name += item + ' - '
        tab_name = tab_name[:-3]
        self.tab_dict[tab_name] = {'widget' : QtWidgets.QWidget()}
        self.tabWidget.addTab(self.tab_dict[tab_name]['widget'], tab_name)
        self.tab_dict[tab_name]['layout'] = QHBoxLayout()
        self.tab_dict[tab_name]['widget'].setLayout(self.tab_dict[tab_name]['layout'])
        self.tab_dict[tab_name]['display'] = PyDMEmbeddedDisplay(parent=self)
        self.tab_dict[tab_name]['display'].macros = json.dumps({"FILE":tab_name, "PATH":self.ui.lineEdit_dir_path.text()  + '/'})
        self.tab_dict[tab_name]['display'].filename = path.join(path.dirname(path.realpath(__file__)), 'plot_hdf5.py')
        self.tab_dict[tab_name]['layout'].addWidget(self.tab_dict[tab_name]['display'])

    def delete_tab(self):
        self.tabWidget.removeTab(self.tabWidget.currentIndex())

