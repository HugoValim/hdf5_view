from os import path
from pydm import Display
import os
import subprocess
import json
from pydm.widgets import PyDMEmbeddedDisplay
from PyQt5 import QtWidgets, QtCore
from qtpy.QtWidgets import (QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame,
    QApplication, QWidget, QAction)
from PyQt5.QtWidgets import QMenu
from qdialog import FileDialog
import qdarkstyle

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
        if event.key() == QtCore.Qt.Key_F11:
            if self.app.main_window.isFullScreen():
                self.app.main_window.showNormal()
            else:
                self.app.main_window.showFullScreen()
            

    def _createMenuBar(self):
        """Create the menu bar and shortcuts"""
        menu_bar = self.app.main_window.menuBar()
        menu_bar.clear()
        # Creating menus using a QMenu object
        self.file_menu = QMenu("&File", self)
        self.option_menu = QMenu("&Options", self)

        menu_bar.addMenu(self.file_menu)
        open_action = self.file_menu.addAction('&Open File')
        open_action.setShortcut("Ctrl+o")

        menu_bar.addMenu(self.option_menu)
        style_action = self.option_menu.addAction(QAction('Dark Theme', menu_bar, checkable=True))
        for action in self.option_menu.actions():
            if action.text() == 'Dark Theme':
                action.setChecked(True)
        # style_action.setShortcut("Ctrl+k")
        

    def initializa_setup(self):
        """Initialiaze all needed things"""
        self.app = QApplication.instance()
        # self.app.setWindowState().showNormal()
        self.app.main_window.setWindowTitle('SOL-View')
        self.main_tab = True
        self.tab_now = None
        self._createMenuBar()
        self.tab_dict = {}
        self.make_connections()
        style = qdarkstyle.load_stylesheet_pyqt5()
        self.app.setStyleSheet(style)


    def make_connections(self):
        """Connect methods"""
        self.tabWidget.tabCloseRequested.connect(self.delete_tab)
        self.file_menu.triggered.connect(self.display_hdf5_files)
        self.option_menu.triggered.connect(self.style_sheet_handler)
        self.pushButton.clicked.connect(self.display_hdf5_files)

    def style_sheet_handler(self):
        for action in self.option_menu.actions():
            if action.text() == 'Dark Theme':
                if action.isChecked():
                    style = qdarkstyle.load_stylesheet_pyqt5()
                    self.app.setStyleSheet(style)
                else:
                    self.app.setStyleSheet('')

    def display_hdf5_files(self):
        """Open the file browser modified to accept more than 1 file selected"""
        options = FileDialog.Options()
        options |= FileDialog.DontUseNativeDialog
        files, _ = FileDialog.getOpenFileNames(self,"Select one or more files", "","HDF5 files (*.hdf5);;All Files (*)", options=options)
        self.show()
        if files:
            self.files_now = files
        else: 
            self.files_now = None
        
        if self.files_now:
            self.plot_tab(self.files_now)

    def tab_name_handler(self):
        if self.main_tab:
            self.tabWidget.removeTab(self.tabWidget.currentIndex())
            self.main_tab = False
        if self.tab_now is not None:
            a = self.tab_now
            self.tab_now = None
            return a

        tab_index = self.tabWidget.count() + 1
        tab_name = 'Plot ' + str(tab_index).zfill(3)
        return tab_name



    def plot_tab(self, items):
        """Manage all plot tab and load an embedded display for it chunk of files selected in browser file menu"""
        
        tab_name = self.tab_name_handler()
        
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
        self.tab_now = self.tabWidget.tabText(self.tabWidget.currentIndex())
        self.tabWidget.removeTab(self.tabWidget.currentIndex())


