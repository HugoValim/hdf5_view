import os
from PyQt5.QtWidgets import QFileDialog
from PyQt5 import QtGui


class FileDialog(QFileDialog):
    """Inherit the QFileDialog to change its behavior when selecting more than 1 file at a time"""

    def __init__(self, *args):
        QtGui.QFileDialog.__init__(self, *args)
        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.ExistingFiles)
        btns = self.findChildren(QtGui.QPushButton)
        self.openBtn = [x for x in btns if "open" in str(x.text()).lower()][0]
        self.openBtn.clicked.disconnect()
        self.openBtn.clicked.connect(self.openClicked)
        self.tree = self.findChild(QtGui.QTreeView)

    def openClicked(self):
        inds = self.tree.selectionModel().selectedIndexes()
        files = []
        for i in inds:
            if i.column() == 0:
                files.append(
                    os.path.join(
                        str(self.directory().absolutePath()), str(i.data().toString())
                    )
                )
        self.selectedFiles = files
        self.hide()

    def filesSelected(self):
        return self.selectedFiles
