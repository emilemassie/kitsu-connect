from PyQt5 import QtWidgets, QtCore, QtGui, QtSvg
from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, pyqtSlot
import os




class LoadingIcon(QtSvg.QSvgWidget):
    def __init__(self):
        super().__init__()
        self.__initUi()

    def __initUi(self):
        r = self.renderer()
        r.setFramesPerSecond(60)
        ico_filename = os.path.join('./icons', 'loading.svg')
        r.load(ico_filename)

class DropZoneLabel(QtWidgets.QLabel):
    fileSelected = QtCore.pyqtSignal(list)  # Signal to emit selected files

    def __init__(self, title, parent):
        super().__init__(title)
        self.parent = parent
        self.setAcceptDrops(True)
        self.setStyleSheet("border: 1.5px dashed #888;")
        self.setScaledContents(False)  # Prevent automatic scaling of the pixmap
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the pixmap
        self.setMinimumSize(200,200)
        

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        for i in files:
            if os.path.isdir(i):
                self.parent.update_log(f"{i} is a directory, adding all files in directory")
                files.remove(i)
                for g in os.listdir(i):
                    files.append(os.path.join(i,g))

        self.fileSelected.emit(files)  # Emit the selected files

    def mouseDoubleClickEvent(self, event):
        self.open_file_dialog()

    def open_file_dialog(self):
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Select Files", "", "All Files (*)")
        if files:
            self.fileSelected.emit(files)  # Emit the selected files
