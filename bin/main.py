from os import path
from pydm import Display
import os
import subprocess
import json
from pydm.widgets import PyDMEmbeddedDisplay
from PyQt5 import QtWidgets, QtCore
from qtpy.QtWidgets import (QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame,
    QApplication, QWidget)
from qdialog import FileDialog
from PyQt5.QtWidgets import QMenu

class MyDisplay(Display):

    def __init__(self, parent=None, args=None, macros=None):
        super(MyDisplay, self).__init__(parent=parent, args=args, macros=macros)
        self.initializa_setup()
        
    def ui_filename(self):
        return 'main.ui'

    def ui_filepath(self):
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            self.delete_tab()

    def _createMenuBar(self):
        menuBar = self.app.main_window.menuBar()
        menuBar.clear()
        # Creating menus using a QMenu object
        self.fileMenu = QMenu("&File", self)
        menuBar.addMenu(self.fileMenu)
        openaction = self.fileMenu.addAction('&Open File')
        editMenu = menuBar.addMenu("&Edit")
        helpMenu = menuBar.addMenu("&Help")

    def initializa_setup(self):
        self.app = QApplication.instance()
        self.app.main_window.showNormal()
        self._createMenuBar()
        self.tab_dict = {}
        self.make_connections()

    def make_connections(self):
        self.tabWidget.tabCloseRequested.connect(self.delete_tab)
        self.fileMenu.triggered.connect(self.display_hdf5_files)

    def display_hdf5_files(self):
        options = FileDialog.Options()
        options |= FileDialog.DontUseNativeDialog
        files, _ = FileDialog.getOpenFileNames(self,"QFileDialog.getOpenFileNames()", "","All Files (*);;HDF5 files (*.hdf5)", options=options)
        self.show()
        
        if files:
            self.files_now = files
        else: 
            self.files_now = None
        
        if self.files_now:
            self.plot_tab(self.files_now)

    def plot_tab(self, items):

        tab_name = ''
        for item in items:
            head, tail = os.path.split(item)
            tab_name += tail + ' - '
            path_file = head
        tab_name = tab_name[:-3]
        self.tab_dict[tab_name] = {'widget' : QtWidgets.QWidget()}
        index = self.tabWidget.addTab(self.tab_dict[tab_name]['widget'], tab_name)
        self.tab_dict[tab_name]['layout'] = QHBoxLayout()
        self.tab_dict[tab_name]['widget'].setLayout(self.tab_dict[tab_name]['layout'])
        self.tab_dict[tab_name]['display'] = PyDMEmbeddedDisplay(parent=self)
        self.tab_dict[tab_name]['display'].macros = json.dumps({"FILE":tab_name, "PATH" : path_file + '/'})
        self.tab_dict[tab_name]['display'].filename = path.join(path.dirname(path.realpath(__file__)), 'plot_hdf5.py')
        self.tab_dict[tab_name]['layout'].addWidget(self.tab_dict[tab_name]['display'])
        self.tabWidget.setCurrentIndex(index)

    def delete_tab(self):
        self.tabWidget.removeTab(self.tabWidget.currentIndex())

