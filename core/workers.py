
import sys
import subprocess
import os, getpass
import tempfile
import json

import requests
import zipfile
import shutil

from core import settings

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, pyqtSlot




class Updater(QThread):
    update_progress = pyqtSignal(str)
    update_finished = pyqtSignal(bool, str)

    def __init__(self, github_repo, updatefile):
        QThread.__init__(self)
        self.github_repo = github_repo
        self.zip_ref = None
        self.updatefile = updatefile

    def run(self):
        try:
            response = requests.get(f"https://api.github.com/repos/{self.github_repo}")
            self.latest_release = response.json()
            
            # Download the update
            self.update_progress.emit("<b>Downloading update...</b>")
            zip_url = self.latest_release['assets'][0]['browser_download_url']
            r = requests.get(zip_url)
            with open(self.updatefile, 'wb') as f:
                f.write(r.content)

            self.update_finished.emit(True, "New Version Downloaded ! Please close and replace the application.")
        except Exception as e:
            raise e
            self.update_finished.emit(False, f"Update failed: {str(e)}")


class T_Extractor(QtCore.QThread):
    finished = QtCore.pyqtSignal(QtGui.QPixmap)
    log_update = QtCore.pyqtSignal(str)  # Signal to update the log


    def __init__(self, parent, input_file):
        super().__init__()
        self.input_file = input_file
        self.output_file = tempfile.TemporaryFile()
        self.ffmpeg_exec = settings.get_ffmpeg_exec()


    def run(self):
        try:
            # Set the creation flags to avoid a popup window on Windows
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            file = self.input_file
            self.log_update.emit("Computing Preview...")

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_jpeg:
                temp_jpeg_path = temp_jpeg.name

            # ffmpeg command to output a single frame as a JPEG to the temporary file
            cmd = [
                self.ffmpeg_exec,
                "-apply_trc", "bt709",
                "-y","-i", file,
                "-vframes", "1",  # Output only 1 frame
                "-q:v", "2",      # Quality level for JPEG (lower is better, max quality = 2)
                "-loglevel", "info",
                temp_jpeg_path
            ]
            # Use subprocess.Popen to capture output in real-time and avoid window popup
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                creationflags=creationflags
            )
            while True:
                line = process.stderr.readline()  # Read the stderr line by line
                if line == '' and process.poll() is not None:
                    break  # Exit if no more output and the process has finished
            process.wait()  # Ensure the process completes before moving on
        finally:
            pixmap = QtGui.QPixmap(temp_jpeg_path)
            if os.path.exists(temp_jpeg_path):
                os.remove(temp_jpeg_path)
            self.finished.emit(pixmap)  # Emit finished signal when done

class Worker(QObject):
    finished = pyqtSignal()  # Signal to indicate when the worker is done
    progress = pyqtSignal(str)  # Signal to send progress back to the main thread

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func  # Store the reference to the function to be executed
        self.args = args  # Store any positional arguments for the function
        self.kwargs = kwargs  # Store any keyword arguments for the function

    @pyqtSlot()
    def run(self):
        # Execute the function with any given arguments
        self.func(*self.args, **self.kwargs)
        self.finished.emit()  # Emit the finished signal when done

class FFmpegWorker(QtCore.QThread):
    progress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()
    log_update = QtCore.pyqtSignal(str)  # Signal to update the log

    def __init__(self, input_files, output_file, fps):
        super().__init__()
        self.input_files = input_files
        self.output_file = output_file
        self.fps = fps 
        self.ffmpeg_exec = settings.get_ffmpeg_exec()

    def run(self):
       
        try:
            # Set the creation flags to avoid a popup window on Windows
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

            if len(self.input_files) == 1:
                # Single file conversion
                self.log_update.emit("Retrieving file...")
                cmd = [
                    self.ffmpeg_exec,
                    "-y", "-i", self.input_files[0], "-c:v", "libx264",
                    "-crf", "23", "-preset", "medium", "-c:a", "aac", "-b:a", "128k", self.output_file
                ]
                
            else:
                # Image sequence conversion
                self.log_update.emit("Retrieving image sequence files...")
                with open("temp_file_list.txt", "w") as f:
                    for file in self.input_files:
                        f.write(f"file '{file}'\n")
                
                cmd = [
                    self.ffmpeg_exec,
                    "-apply_trc","bt709",
                    "-y", "-f", "concat", "-safe", "0", "-r", str(self.fps),
                    "-i", "temp_file_list.txt",
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-r", str(self.fps),  # Linear to BT.709 with gamma correction
                    "-loglevel", "info",
                    self.output_file
                ]


            # Use subprocess.Popen to capture output in real-time and avoid window popup
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                creationflags=creationflags
            )

            # Monitor the output for progress updates
            while True:
                line = process.stderr.readline()  # Read the stderr line by line
                if line == '' and process.poll() is not None:
                    break  # Exit if no more output and the process has finished
                if "frame=" in line:
                    # Extract frame information and emit progress signal
                    frame_data = line.split("frame=")[1].split()[0]
                    if frame_data.isdigit():
                        self.progress.emit(int(frame_data))  # Emit progress signal with frame count

                # Optionally, emit other updates based on different ffmpeg output logs
                #if line:
                #    self.log_update.emit(line.strip())  # Emit log updates for other messages

            process.wait()  # Ensure the process completes before moving on
        finally:
            if os.path.exists("temp_file_list.txt"):
                os.remove("temp_file_list.txt")

            self.finished.emit()  # Emit finished signal when done
