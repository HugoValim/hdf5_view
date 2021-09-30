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
from PyQt5.QtWidgets import QMenu
from qdialog import FileDialog

class MyDisplay(Display):

    def __init__(self, parent=None, args=None, macros=None):
        super(MyDisplay, self).__init__(parent=parent, args=args, macros=macros)
        self.initializa_setup()
        
    def ui_filename(self):
        return 'main.ui'

    def ui_filepath(self):
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())

    def keyPressEvent(self, event):
        """Connect keys to methods"""
        if event.key() == QtCore.Qt.Key_Delete:
            self.delete_tab()

    def _createMenuBar(self):
        """Create the menu bar and shortcuts"""
        menuBar = self.app.main_window.menuBar()
        menuBar.clear()
        # Creating menus using a QMenu object
        self.fileMenu = QMenu("&File", self)
        menuBar.addMenu(self.fileMenu)
        openaction = self.fileMenu.addAction('&Open File')
        openaction.setShortcut("Ctrl+o")
        editMenu = menuBar.addMenu("&Edit")
        helpMenu = menuBar.addMenu("&Help")

    def initializa_setup(self):
        """Initialiaze all needed things"""
        self.app = QApplication.instance()
        self.app.main_window.showNormal()
        self.app.main_window.setWindowTitle('SOL-View')
        self._createMenuBar()
        self.tab_dict = {}
        self.make_connections()

    def make_connections(self):
        """Connect methods"""
        self.tabWidget.tabCloseRequested.connect(self.delete_tab)
        self.fileMenu.triggered.connect(self.display_hdf5_files)

    def display_hdf5_files(self):
        """Open the file browser modified to accept more than 1 file selected"""
        options = FileDialog.Options()
        options |= FileDialog.DontUseNativeDialog
        files, _ = FileDialog.getOpenFileNames(self,"QFileDialog.getOpenFileNames()", "","HDF5 files (*.hdf5);;All Files (*)", options=options)
        self.show()
        if files:
            self.files_now = files
        else: 
            self.files_now = None
        
        if self.files_now:
            self.plot_tab(self.files_now)

    def plot_tab(self, items):
        """Manage all plot tab and load an embedded display for it chunk of files selected in browser file menu"""
        tab_index = self.tabWidget.count()
        tab_name = 'Plot ' + str(tab_index)
        self.tab_dict[tab_name] = {'widget' : QtWidgets.QWidget()}
        index = self.tabWidget.addTab(self.tab_dict[tab_name]['widget'], tab_name)
        self.tab_dict[tab_name]['layout'] = QHBoxLayout()
        self.tab_dict[tab_name]['widget'].setLayout(self.tab_dict[tab_name]['layout'])
        self.tab_dict[tab_name]['display'] = PyDMEmbeddedDisplay(parent=self)
        self.tab_dict[tab_name]['display'].macros = json.dumps({"FILES": self.files_now})
        self.tab_dict[tab_name]['display'].filename = path.join(path.dirname(path.realpath(__file__)), 'plot_hdf5.py')
        self.tab_dict[tab_name]['layout'].addWidget(self.tab_dict[tab_name]['display'])
        self.tabWidget.setCurrentIndex(index)

    def delete_tab(self):
        """Delte a tab from the tabWidget"""
        self.tabWidget.removeTab(self.tabWidget.currentIndex())
