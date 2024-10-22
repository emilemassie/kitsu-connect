import sys
import subprocess
import os, getpass
import tempfile
import json

import requests
import zipfile
import shutil

from PyQt5 import QtWidgets, QtCore, QtGui, uic, QtSvg
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import Qt, QPoint, QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMessageBox


from core.workers import *
from core.settings import kitsu_settings
from core.ui_elements import *


import gazu


_VERSION = "1.2.0"
parent_folder = os.path.dirname(__file__)


class kitsu_connect(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        QtCore.QDir.addSearchPath('icons', os.path.join(os.path.dirname(__file__), 'icons'))
        uic.loadUi(os.path.join(parent_folder,'ui','kitsu-connect.ui'), self) 

        # updates
        self.current_version = _VERSION  # Set your current version here
        self.version_label.setText(f'v{self.current_version}')
        self.github_repo = "emilemassie/kitsu-publisher/releases/tags/standalone"  # Set your GitHub repo here

        # Variables to track mouse position for dragging
        self._isResizing = False
        self._isDragging = False
        self._dragPosition = QPoint()
        self._resizeMargin = 10  # Margin around edges for resizing
        self._dragArea = None


        self.check_for_updates()



        self.thread = QThread()

        # Create a Worker object and pass the print_hello function
        self.worker = Worker(self.refresh_tree)

        # Move the worker to the thread
        self.worker.moveToThread(self.thread)

        # Connect signals and slots
        self.thread.started.connect(self.worker.run)          # Start the worker's run method when the thread starts
        self.worker.finished.connect(self.thread.quit)        # Quit the thread when the worker finishes

        self.context = None
        self.ks = kitsu_settings(self)
        self.is_scanning = True

        self.shot_info_tab.setVisible(False)


        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__),'icons','icon.png')))


        # Remove the window frame and make the window transparent
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        #self.setAttribute(Qt.WA_TranslucentBackground)


        self.exit_button.released.connect(self.close)
        self.settings_button.released.connect(self.show_settings)
        self.connection_status = None


        self.loading_icon = LoadingIcon()
        self.load_icon_frame.layout().replaceWidget(self.image_label, self.loading_icon)
        self.image_label = self.loading_icon

        self.input_files = None
        
        #self.t_task_stat.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.tree_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        

        self.file_manager = DropZoneLabel('test', self)
        self.file_manager.setText(self.file_drop.text())  # Keep the existing text
        self.file_manager.setGeometry(self.file_drop.geometry())
        self.file_manager.fileSelected.connect(self.set_files)

        self.ff_layout.replaceWidget(self.file_drop, self.file_manager)
        self.file_drop.deleteLater()
        self.publish_button.released.connect(self.launch_publisher)
        #self.file_drop.mouseDoubleClickEvent.connect(self.file_browse)
        

        self.ks.check_connection()
        self.show_only_my_tasks.stateChanged.connect(self.build_tasks_tree)


    def check_for_updates(self):
        self.update_log('Checking for updates...')
        try:
            response = requests.get(f"https://api.github.com/repos/{self.github_repo}")
            self.latest_release = response.json()
            latest_version = self.latest_release['name'].split('v')[-1]

            if latest_version > self.current_version:
                reply = QMessageBox.question(self, 'Update Available', 
                                     f"{self.latest_release['name']} is available. Do you want to update?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    self.start_update()
                else:
                    return
            else:
                return
        except Exception as e:
            QMessageBox.warning(self, "Update Check Failed", f"Error: {str(e)}")

    def on_update_progress(self, message):
        self.update_log(message)

    def on_update_finished(self, success, message):
        if success:
            QMessageBox.information(self, "Update Successful", message)
        else:
            QMessageBox.warning(self, "Update Failed", message)
        #self.update_button.setText("Check for Updates")
        
        
    def start_update(self):
        update_file, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Select Update File", self.latest_release['name'], "Zip Files (*.zip)")
        if not update_file:
            return
        self.updater = Updater(self.github_repo, update_file)
        self.updater.update_progress.connect(self.on_update_progress)
        self.updater.update_finished.connect(self.on_update_finished)
        self.updater.start()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Detect if we're clicking in a resize area
            self._dragArea = self._detectDragArea(event.pos())
            if self._dragArea:
                self._isResizing = True
                self._dragPosition = event.globalPos()
                event.accept()
            else:
                # Otherwise, assume we're dragging the window
                self._isDragging = True
                self.old_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._isResizing and self._dragArea:
            # Calculate how much the mouse has moved
            delta = event.globalPos() - self._dragPosition
            self._resizeWindow(delta)
            self._dragPosition = event.globalPos()
            event.accept()
        elif self._isDragging:
            # Move the window if it's being dragged
            self.move(event.globalPos() - self.old_position)
            event.accept()
        else:
            # Change cursor shape when hovering over edges or corners
            self._setCursorShape(event.pos())
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Stop dragging and resizing
            self._isResizing = False
            self._isDragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def _detectDragArea(self, pos):
        """ Detect which area of the window is being clicked for resizing. """
        rect = self.rect()
        top, left, right, bottom = rect.top(), rect.left(), rect.right(), rect.bottom()
        margin = self._resizeMargin

        if left <= pos.x() <= left + margin and top <= pos.y() <= top + margin:
            return 'top-left'
        elif right - margin <= pos.x() <= right and top <= pos.y() <= top + margin:
            return 'top-right'
        elif left <= pos.x() <= left + margin and bottom - margin <= pos.y() <= bottom:
            return 'bottom-left'
        elif right - margin <= pos.x() <= right and bottom - margin <= pos.y() <= bottom:
            return 'bottom-right'
        elif left <= pos.x() <= left + margin:
            return 'left'
        elif right - margin <= pos.x() <= right:
            return 'right'
        elif top <= pos.y() <= top + margin:
            return 'top'
        elif bottom - margin <= pos.y() <= bottom:
            return 'bottom'
        return None

    def _resizeWindow(self, delta):
        """ Resize the window based on the mouse movement delta. """
        if self._dragArea == 'right':
            self.setGeometry(self.x(), self.y(), self.width() + delta.x(), self.height())
        elif self._dragArea == 'bottom':
            self.setGeometry(self.x(), self.y(), self.width(), self.height() + delta.y())
        elif self._dragArea == 'bottom-right':
            self.setGeometry(self.x(), self.y(), self.width() + delta.x(), self.height() + delta.y())
        elif self._dragArea == 'left':
            self.setGeometry(self.x() + delta.x(), self.y(), self.width() - delta.x(), self.height())
        elif self._dragArea == 'top':
            self.setGeometry(self.x(), self.y() + delta.y(), self.width(), self.height() - delta.y())
        elif self._dragArea == 'top-left':
            self.setGeometry(self.x() + delta.x(), self.y() + delta.y(), self.width() - delta.x(), self.height() - delta.y())
        elif self._dragArea == 'top-right':
            self.setGeometry(self.x(), self.y() + delta.y(), self.width() + delta.x(), self.height() - delta.y())
        elif self._dragArea == 'bottom-left':
            self.setGeometry(self.x() + delta.x(), self.y(), self.width() - delta.x(), self.height() + delta.y())

    def _setCursorShape(self, pos):
        """ Change the cursor shape based on the drag area detected. """
        area = self._detectDragArea(pos)
        if area in ['top-left', 'bottom-right']:
            self.setCursor(Qt.SizeFDiagCursor)
        elif area in ['top-right', 'bottom-left']:
            self.setCursor(Qt.SizeBDiagCursor)
        elif area in ['left', 'right']:
            self.setCursor(Qt.SizeHorCursor)
        elif area in ['top', 'bottom']:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.ArrowCursor)            

    def set_files(self, files):
        self.input_files = sorted(files)
        self.update_log('Selected '+str(len(files))+' files')
        if len(files)>1:
            self.file_list_text = f'{str(len(files))} files\n\n{os.path.basename(files[0])}\n[...]\n{os.path.basename(files[-1])}'
        else:
            self.file_list_text = f'{os.path.basename(files[0])}'

        self.t_worker = T_Extractor(self, files[0])
        self.t_worker.log_update.connect(self.update_log)          # Start the worker's run method when the thread starts
        self.t_worker.finished.connect(self.set_thumbnail) 
        self.t_worker.start()

        self.check_button_enable()

    def set_thumbnail(self, thumbnail):
        label_width = self.file_manager.width()
        label_height = self.file_manager.height()

        # Scale the pixmap to fit inside the QLabel's dimensions
        scaled_pixmap = thumbnail.scaled(label_width, label_height, Qt.AspectRatioMode.KeepAspectRatio)
        painter = QtGui.QPainter(scaled_pixmap)

        # Set the pen color for the border to black
        border_pen = QtGui.QPen(QtGui.QColor("black"))
        painter.setPen(border_pen)

        # Define the text with potential newlines
        text = str(self.file_list_text)

        # Split the text into lines
        lines = text.split('\n')

        # Get the bounding rectangle of the pixmap
        rect = scaled_pixmap.rect()

        # Calculate the initial vertical position to center the text
        line_height = painter.fontMetrics().height()  # Get the height of a single line of text
        total_height = line_height * len(lines)  # Total height of all lines
        start_y = (rect.height() - total_height) // 2  # Centering Y position

        # Draw the outline by drawing the text in black at slightly offset positions
        offsets = [-1, 0, 1]  # Offsets for x and y directions

        for i, line in enumerate(lines):
            # Calculate the position for each line
            
            i=i+1
            x = (rect.width() - painter.boundingRect(rect, 0, line).width()) // 2  # Centering X
            y = start_y + i * line_height  # Calculate Y position for the current line

            # Draw the outline for each line
            painter.setPen(QtGui.QColor("black"))
            for dx in offsets:
                for dy in offsets:
                    if dx != 0 or dy != 0:  # Avoid drawing in the center again
                        painter.drawText(x + dx, y + dy, line)

            # Set the pen color for the text to white
            painter.setPen(QtGui.QColor("white"))

            # Draw the text on top in white
            painter.drawText(x, y, line)

        # End painting
        painter.end()

        self.file_manager.setPixmap(scaled_pixmap)
        
     
    def find_or_create_child(self, parent_item, child_name, thumbnail=None):
        """ Helper function to find a child with the given name or create a new one """
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if child.text(0) == child_name:
                return child

        # If the child does not exist, create and add it
        new_child = QtWidgets.QTreeWidgetItem([child_name])
        parent_item.addChild(new_child)
        return new_child

    def on_item_double_clicked(self, item, column):
        # Print the stored context_id if it's a leaf item (Task level)
        context_id = item.data(1, 0)
        if context_id:
            self.set_context(context_id)
        else:
            self.set_context()

    def check_button_enable(self):
        if self.context and self.input_files:
            self.publish_button.setEnabled(True)
        else:
            self.publish_button.setEnabled(False)

    def set_context(self, context_id=None):
        if context_id:
            self.update_log(f"Setting Context ID: {context_id}")
            self.t_context.setText(context_id)
            self.context = context_id
        else:
            self.t_context.setText('')
            self.context = None
        self.check_button_enable()

    def build_tasks_tree(self):

        
        if self.thread is not None and self.thread.isRunning():
            self.is_scanning = False

            self.thread.quit()  # Stop the thread's event loop
            self.thread.wait()  # Wait until the thread has finished

        self.is_scanning = True
        self.thread.start()


    def refresh_tree(self):
        self.tree_widget.clear()
        self.t_task_stat.clear()
        self.image_label.setVisible(True)

        self.update_log('')
        self.update_log('Refreshing task list')

        if not self.is_scanning:
            self.update_log('User interupted task loading !', 'red')
            return False

        for stat in reversed(gazu.task.all_task_statuses()):
            self.t_task_stat.addItem(stat['name'])
            self.t_task_stat.setCurrentIndex(0)


        if self.connection_status:
            if self.show_only_my_tasks.isChecked():
                tasks = gazu.user.all_tasks_to_do()
            else:
                projects = gazu.project.all_open_projects()  # Retrieves all open projects
                # Step 3: Get all tasks for each project
                tasks = []  # Initialize a list to store all tasks

                for project in projects:
                    # Retrieve tasks for the current project
                    g_tasks = gazu.task.all_tasks_for_project(project)
                    tasks.extend(g_tasks)  # Add tasks to the all_tasks list

            
            self.update_log('Found '+str(len(tasks))+' tasks.\nGathering Kitsu informations...')
            if len(tasks)>40:
                self.update_log("This may take a while...",'orange')

            data = []
            for task in tasks:
                if not self.is_scanning:
                    self.update_log('User interupted task loading !', 'red')
                    self.image_label.setVisible(False)
                    return False
                task = gazu.task.get_task(task)
                try:
                    seq = task['sequence']['name']
                except:
                    seq = task['entity_type']['name']
                
                if seq is None:
                    seq = task['entity_type_name']
                dd = {
                    'project': task['project']['name'],
                    'type': task['task_type']['for_entity'],
                    'seq': seq,
                    'element': task['entity']['name'],
                    'task': task['task_type']['name'],
                    'context_id': task['id'],
                    'preview_id': task['entity']['preview_file_id'],
                    'task_preview': task['last_preview_file_id']
                }
                data.append(dd)

            root_items = {}
            self.update_log('Building Tree View...')
            for item_data in data:
                if not self.is_scanning:
                    self.update_log('User interupted task loading !', 'red')
                    self.image_label.setVisible(False)
                    return False
                # Create hierarchy: Project > Type > Sequence > Element > Task
                project_name = item_data.get('project', 'Unknown Project')  # Add a project key
                type_name = item_data['type']
                seq_name = item_data['seq']
                element_name = item_data['element']
                task_name = item_data['task']
                context_id = item_data['context_id']
                preview_id = item_data['preview_id']


                # Create or get the Project level item
                if project_name not in root_items:
                    project_item = QtWidgets.QTreeWidgetItem([project_name])
                    self.tree_widget.addTopLevelItem(project_item)
                    root_items[project_name] = {}
                
                project_item = self.tree_widget.findItems(project_name, Qt.MatchExactly | Qt.MatchRecursive)[0]

                # Create or get the Type level item
                if type_name not in root_items[project_name]:
                    type_item = QtWidgets.QTreeWidgetItem([type_name])
                    project_item.addChild(type_item)
                    root_items[project_name][type_name] = type_item
                else:
                    type_item = root_items[project_name][type_name]

                # Create or get the Sequence level item
                seq_item = self.find_or_create_child(type_item, seq_name)

                # Create or get the Element level item
                element_item = self.find_or_create_child(seq_item, element_name)

                temp_file = tempfile.NamedTemporaryFile(delete=False, prefix=element_name,suffix='.png')  # Keep the file after closing
                image = None
                try:
                    gazu.files.download_preview_file_thumbnail(preview_id, temp_file.name)  # Use temp_file.name              
                    image = QtGui.QImage(temp_file.name)  # Use temp_file.name to read the image
                except:
                    image = QtGui.QImage(16, 9, QtGui.QImage.Format.Format_ARGB32)
                    image.fill(Qt.transparent)

                
                element_item.setData(0,1, image.scaled(48,27,Qt.AspectRatioMode.KeepAspectRatioByExpanding))
                temp_file.close()
                os.remove(temp_file.name)


                # Create the Task level item
                task_item = QtWidgets.QTreeWidgetItem([task_name])
                task_item.setData(1, 0, context_id)


                # Add Task item under the Element level
                element_item.addChild(task_item)

                temp_file = tempfile.NamedTemporaryFile(delete=False, prefix=element_name+task_name,suffix='.png')  # Keep the file after closing

                if item_data['task_preview']:
                    try:
                        gazu.files.download_preview_file_thumbnail(item_data['task_preview'], temp_file.name)  # Use temp_file.name              
                        image = QtGui.QImage(temp_file.name)  # Use temp_file.name to read the image
                    except:
                        image = QtGui.QImage(16, 9, QtGui.QImage.Format.Format_ARGB32)
                        image.fill(Qt.transparent)
                else:
                    image = QtGui.QImage(16, 9, QtGui.QImage.Format.Format_ARGB32)
                    image.fill(Qt.transparent)

                task_item.setData(0,1, image.scaled(48,27,Qt.AspectRatioMode.KeepAspectRatioByExpanding))
                temp_file.close()
                os.remove(temp_file.name)
    
            self.update_log('Task Tree Refreshed !', 'green')
            self.update_log('')
            self.image_label.setVisible(False)


    def show_settings(self):
        self.update_log('Open Connection Settings')
        self.ks.show()

    def update_log(self, message, color=None):
        if color:
            self.log_view.append(f'<p style="color:{color};">'+message+'</p> ')
        else:
            self.log_view.append(message)  # Append message to log view

        self.log_view.moveCursor(QtGui.QTextCursor.End)


    def launch_publisher(self):
        self.convert()

    def publish_file_to_kitsu(self):

        try:
            status = gazu.task.get_task_status_by_name(self.t_task_stat.currentText())
            task = gazu.task.get_task(self.context)
            file_string = '\n\n<hr><b><u>FILE :</b></u><i>\n' + str(self.output_file) + '</i>\n'
            comment = gazu.task.add_comment(task, status, self.t_comment.toPlainText()+file_string)

            preview_file = gazu.task.add_preview(
                    task,
                    comment,
                    self.output_file
                )

            # Remove the temporary playblast file
            if os.path.exists(self.output_file):
                os.remove(self.output_file)
            return True
        except Exception as eee:
            self.update_log(f'<span style="color:red;">Cannot Publish File:\n\n</span>{str(eee)}')
            return False
        self.progress_bar.setValue(80)

    def convert(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        self.output_file = temp_file.name

        if not self.input_files or not self.output_file:
            QtWidgets.QMessageBox.critical(self, "Error", "Please select input and output files")
            return

        try:
            fps = float(self.fps_entry.text().replace(',', '.'))
            if fps <= 0:
                QtWidgets.QMessageBox.critical(self, "Error", f"FPS must be a positive number: {e}")
                return
        except ValueError as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Invalid FPS value: {e}")
            return

        self.progress_bar.setValue(0)  # Reset progress bar
        self.progress_bar.setMaximum(100)  # Set maximum for progress bar

        self.publish_button.setEnabled(False)  # Disable the Convert button
        self.worker = FFmpegWorker(self.input_files, self.output_file, fps)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.log_update.connect(self.update_log)  # Connect log update signal
        self.worker.start()  # Start the thread

    def update_progress(self, frame):
        # Update the progress bar based on the number of frames processed
        self.progress_bar.setValue(frame)
        if frame > 0 :
            self.update_log('Exporting frame: ' + str(frame))

    def on_finished(self):
        self.update_log(f'Uploaded Preview File !!!')
        #QtWidgets.QMessageBox.information(self, "Success", "Conversion completed successfully!")
        self.progress_bar.setValue(100)  # Set progress bar to complete
        self.publish_button.setEnabled(True)  # Re-enable the Convert button
        self.publish_file_to_kitsu()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = kitsu_connect()
    window.show()
    sys.exit(app.exec_())
