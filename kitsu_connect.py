
import sys, os, json
import subprocess


root_folder = os.path.dirname(__file__)
sys.path.insert(0, root_folder)

site_packages = os.path.join(root_folder, 'site-packages')

sys.path.insert(0,site_packages)

from PyQt6 import uic, QtCore, QtSvg
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6 import QtGui

import gazu
from core import settings
from core.project_settings import project_settings
from core.plugins import KitsuConnectPlugins


class kitsu_tree_item(QtGui.QStandardItem):
    def __init__(self, project_root=None, text=''):
        super().__init__(text)
        self.id = None
        self.file_path = None
        self.name = None
        self.image = None
        self.kitsu_item = None
        self.project_root = project_root

    def get_path(self):
        filepath = None
        if self.kitsu_item:
            item_type = self.kitsu_item['type']
            if item_type == 'Sequence':
                filepath = os.path.join(self.project_root,'shots', self.kitsu_item['name'])
            if item_type == 'Shot':
                filepath = os.path.join(self.project_root,'shots', self.kitsu_item['sequence_name'],self.kitsu_item['name'])
            if item_type =='Task':
                if self.kitsu_item['task_type_for_entity'] == 'Shot':
                    filepath = os.path.join(self.project_root,'shots', self.kitsu_item['sequence_name'], self.kitsu_item['entity_name'], 'project_files',self.kitsu_item['task_type_name'])
                elif self.kitsu_item['task_type_for_entity'] == 'Asset':
                    filepath = os.path.join(self.project_root,'assets', self.kitsu_item['entity_name'], self.kitsu_item['task_type_name'], 'project_files')
        return filepath

class kitsu_plugin_button(QtWidgets.QPushButton):
    def __init__(self, text=''):
        super().__init__(text)
        self.file_path = None

    def set_button_icon(self, img):
        icon = QtGui.QIcon(img)
        self.setIcon(icon)

class kitsu_connect(QtWidgets.QWidget):
    def __init__(self):
        super(kitsu_connect, self).__init__()

        # UI SETUP
        self.root_folder = os.path.dirname(__file__)
        uic.loadUi(os.path.join(self.root_folder, 'ui', 'kitsu-connect.ui'), self)
        self.setWindowTitle("KITSU - CONNECT")
        self.setWindowIcon(QtGui.QIcon(os.path.join(self.root_folder,'icons','icon.png')))
        self.shot_info_tab.setVisible(False)
        self.shot_info_tab.setMaximumHeight(500)
        self.asset_info_tab.setVisible(False)
        self.asset_info_tab.setMaximumHeight(500)
        self.project_settings_button.setIcon(QtGui.QIcon(os.path.join(self.root_folder, 'icons', 'tool.svg')))
        self.refresh_button.setIcon(QtGui.QIcon(os.path.join(self.root_folder, 'icons', 'rotate-cw.svg')))


        # Grab Plugins
        self.plugins = []
        self.load_plugins()

        # Load Settings
        self.access_token = None
        os.environ['KITSU_CONNECT_PACKAGES'] = site_packages
        self.settings = settings.kitsu_connect_settings(self)
        self.good_settings = self.settings.load_settings()
        #print(gazu.project.all_projects())

        # Setup Loading Screen
        self.loading_icon_movie = QtGui.QMovie(os.path.join(self.root_folder,'icons','loading_icon_2.gif'))
        self.loading_icon_movie.start()
        self.loading_icon_label.setMovie(self.loading_icon_movie)

        # Connect actions 
        self.files_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.files_tree.customContextMenuRequested.connect(self.asset_right_click_menu)
        self.my_task_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.my_task_tree.customContextMenuRequested.connect(self.task_right_click_menu)
        self.refresh_button.released.connect(self.update_trees)

        self.my_task_tree.doubleClicked.connect(self.set_context)
        self.my_task_tree.clicked.connect(self.item_clicked)
        self.project_box.currentTextChanged.connect(self.update_trees)
        self.task_expend_button.pressed.connect(self.my_task_tree.expandAll)
        self.task_collapse_button.pressed.connect(self.my_task_tree.collapseAll)
        self.save_settings_button.pressed.connect(self.settings.save_settings)
        self.project_settings_button.pressed.connect(self.open_project_settings)

        self.open_dir_button.released.connect(self.open_directory)
        #self.version_list.currentTextChanged.connect(self.task_item_doubleclicked)

        self.context_id = None
        self.context_set = False
        self.gui = 0
        self.project_root = None
        self.gui = 1
        self.center()
        self.update_trees()

    
    def open_directory(self):
        pass

    def item_clicked(self, index):
        self.my_task_tree.expand(index)
    
    def task_item_doubleclicked(self, item):
        if item.kitsu_item['task_type_for_entity'] == 'Shot':
            file = self.version_list.currentText().split('/')
            box = self.action_box_layout
        elif item.kitsu_item['task_type_for_entity'] == 'Asset':
            box = self.asset_action_box_layout
            file = self.asset_version_list.currentText().split('/')

        folder_path = item.get_path()

        # Clear all the layout
        while box.count():
            witem = box.takeAt(0)
            widget = witem.widget()
            if widget is not None:
                widget.deleteLater()

        # check all the files and plugins
        if len(file)>1:
            file_path = os.path.join(folder_path, file[0], file[1])
        else:
            file_path = None

        # add plugin buttons
        for plugin in self.plugins:
            if '.'+file[-1].rsplit('.',1)[-1] == plugin.extension:
                file_path = os.path.join(folder_path, file[0], file[1])
            for button in plugin.get_push_buttons(item, file_path):
                box.addWidget(button)
        return True

    def load_plugins(self):
        plugin_engine = KitsuConnectPlugins(self)
        plugins = plugin_engine.get_plugins(os.path.join(self.root_folder, 'plugins'))
        self.plugins = plugins
        tree_model = QtGui.QStandardItemModel()
        rootNode = tree_model.invisibleRootItem()
        for plugin in plugins:
            app = QtGui.QStandardItem(plugin.name)
            app.setEditable(False)
            rootNode.appendRow(app)
        self.plugin_tree.setModel(tree_model)
        
    def center(self):
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    #def mousePressEvent(self, event):
    #   self.dragPos = event.globalPosition().toPoint()

    #def mouseMoveEvent(self, event):
    #   self.move(self.pos() + event.globalPosition().toPoint() - self.dragPos )
    #   self.dragPos = event.globalPosition().toPoint()
    #   event.accept()
    
    def set_loading(self, load_bool=True):
        if load_bool:
            self.stacked_loading_screen.setCurrentIndex(1)
        else:
            self.stacked_loading_screen.setCurrentIndex(0)

    def set_status(self, status, is_running=False):  
        if is_running:
            self.loading_icon.setMovie(self.loading_icon_movie)
        else:
            self.loading_icon.setMovie(None)
        self.status.setText(status)
        #QCoreApplication.processEvents()
        #QtWidgets.QApplication.processEvents()


        #self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

    def open_project_settings(self):
        if self.good_settings:
            self.ps = project_settings(self)
            if self.ps.getInfos():
                self.ps.show()
                return
        else:
            return

    def build_plugin_shelf(self):
        layout = self.apps_tab.layout()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                # If the item is a layout, recursively delete its children
                sub_layout = item.layout()
                if sub_layout:
                    while sub_layout.count():
                        sub_item = sub_layout.takeAt(0)
                        sub_widget = sub_item.widget()
                        if sub_widget:
                            sub_widget.deleteLater()

        for plugin in self.plugins:
            app_button = QtWidgets.QToolButton()
            app_button.setText(plugin.name)
            app_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            app_button.setIcon(QtGui.QIcon(plugin.icon))
            app_button.setIconSize(QtCore.QSize(50,50))
            app_button.released.connect(plugin.launch)
            layout.addWidget(app_button)
            
    def get_item_file_path(self, item):
        filepath = None
        if item.type == 'Sequence':
            filepath = os.path.join(self.project_root,'shots', item.text())
        elif item.type == 'Shot':
            shot = gazu.shot.get_shot(item.id)
            filepath = os.path.join(self.project_root,'shots', shot['sequence_name'],shot['name'])
        elif item.type =='Task':
            task = gazu.task.get_task(item.id)
            if item.kitsu_item['task_type_for_entity'] == 'Shot':
                filepath = os.path.join(self.project_root,'shots', task['sequence']['name'], task['entity']['name'], 'project_files',task['task_type']['name'])
            elif item.kitsu_item['task_type_for_entity'] == 'Asset':
                filepath = os.path.join(self.project_root,'assets', task['entity']['name'], task['task_type']['name'],'project_files')
        return filepath

    def set_context(self, index):

        item = index.model().itemFromIndex(index)
        id = item.id

        if item.kitsu_item:

            context = ''

            if item.type == 'Sequence':
                context = f"{self.project['name']} : {item.text()}".upper()
                self.shot_info_tab.setVisible(False)
            elif item.type == 'Shot':
                shot = gazu.shot.get_shot(id)
                context = f"{shot['project_name']} : {shot['sequence_name']} : {shot['name']}".upper()
                self.shot_info_tab.setVisible(False)
            elif item.type == 'Task':
                task = gazu.task.get_task(id)
                if item.kitsu_item['task_type_for_entity'] == 'Shot':
                    context = f"{task['project']['name']} : {task['sequence']['name']} : {task['entity']['name']} : {task['task_type']['name']}".upper()
                    self.set_shot_tab(item)
                elif item.kitsu_item['task_type_for_entity'] == 'Asset':
                    context = f"{task['project']['name']} : Assets : {task['entity']['name']} : {task['task_type']['name']}".upper()
                    self.set_asset_tab(item)
                #self.build_plugin_shelf()
            self.context_label.setText(context) 
            self.context_id = id
            self.context_set = True
            return True
        else:
            self.context_id = None
            self.context_set = False
            self.context_label.setText('')
            self.shot_info_tab.setVisible(False)
            return False
            #self.apps_tab.setVisible(False)

    def get_asset_path(self):
        index = self.asset_tree.currentIndex()
        item = self.asset_tree_model.itemFromIndex(index)
        try:
            self.project_root = self.project['data']['project_root']
            asset = gazu.asset.get_asset(item.whatsThis())
            asset_path = os.path.join(self.project_root,'assets', asset['name'])
            return asset_path
        except:
            return None

# Right click menu triggers for assets            
    def show_asset_path(self):
        asset_path = self.get_asset_path()
        msg_box = QtWidgets.QMessageBox()
        if asset_path:
            msg_box.setWindowTitle('file path')
            msg_box.setText(asset_path)
            #msg_box.setIcon(QtWidgets.QMessageBox.Icon.Information)
        else:
            msg_box.setWindowTitle('No project root')
            msg_box.setText('Cannot resolve project root')
            msg_box.setIcon(QtWidgets.QMessageBox.Icon.Critical) 
        msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        return msg_box.exec()
    
    def open_asset_path(self):
        url = QtCore.QUrl.fromLocalFile(self.get_asset_path())
        QtGui.QDesktopServices.openUrl(url)

    def open_file_in_browser(self,file):
        url = QtCore.QUrl.fromLocalFile(file)
        QtGui.QDesktopServices.openUrl(url)

    def task_right_click_menu(self, position):
        menu = QtWidgets.QMenu()
        menu.addAction('Get asset path', self.show_asset_path)
        menu.addAction('Open in browser', self.open_asset_path)
        menu.exec(self.asset_tree.viewport().mapToGlobal(position))

    def asset_right_click_menu(self, position):
        menu = QtWidgets.QMenu()
        menu.addAction('Get asset path', self.show_asset_path)
        menu.addAction('Open in browser', self.open_asset_path)
        menu.exec(self.asset_tree.viewport().mapToGlobal(position))

    def launch_app(self, app, context_id):
        subprocess.call(app['exec'], env=app['environ'])

    # Right Click Menu for tasks
    def task_right_click_menu(self, position):
        menu = QtWidgets.QMenu()

        index = self.my_task_tree.currentIndex()
        item = self.my_task_tree_model.itemFromIndex(index)
        
        if item:
            if not item.whatsThis().startswith('FILE:'):
                menu.addAction('Open in Browser', lambda: self.open_file_in_browser(self.get_item_file_path(item)))

            self.set_context(index)

        for plugin in self.plugins:
            try:
                icon = QtGui.QIcon(plugin.icon)
                plugin.tree_right_click_action(menu, icon=icon)
            except Exception as eee:
                print(eee)
                pass

            
                
        #    for app in self.plugin_settings:
        #        menu.addAction('Launch '+app, lambda: self.launch_app(self.plugin_settings[app], item.whatsThis()))
            #menu.addAction('Get asset path', self.show_asset_path)
            #menu.addAction('Open in browser', self.open_asset_path)

        
        menu.exec(self.my_task_tree.viewport().mapToGlobal(position))

    def set_projects(self):
        project_list = [project['name'] for project in gazu.user.all_open_projects()]
        self.project_box.clear()
        self.project_box.addItems(project_list)

    def set_shot_tab(self, item):
        task = item.kitsu_item
        shot = gazu.shot.get_shot(task['entity_id'])

        self.shot_info_name.setText(shot['name'])
        self.shot_info_id.setText(shot['id'])

        try:
            self.shot_info_frames.setText(str(shot['nb_frames']))
        except:
            pass
        try:
            self.shot_info_framein.setText(str(shot['frame_in']))
        except:
            try:
                self.shot_info_framein.setText(str(shot['data']['frame_in']))
            except:
                self.shot_info_framein.setText('?')
        try:
            self.shot_info_frameout.setText(str(shot['frame_out']))
        except:
            try:
                self.shot_info_frameout.setText(str(shot['data']['frame_out']))
            except:
                self.shot_info_frameout.setText('?')
        try:
            self.shot_info_fps.setText(str(shot['fps']))
        except:
            try:
                self.shot_info_fps.setText(str(shot['data']['fps']))
            except:
                self.shot_info_fps.setText('?')
        try:
            self.shot_info_format.setText(shot['data']['resolution'])
        except:
            self.shot_info_format.setText('?')

        img_path = os.path.join(root_folder, '.cache_images', shot['project_name'], 'shots',shot['sequence_name'], shot['name']+'_preview.jpeg')
        pixmap = QtGui.QPixmap(img_path)
        self.shot_info_image.setPixmap(pixmap)

        # get versions
        if self.project_root:
            version_folder = self.get_item_file_path(item)
            self.version_list.currentTextChanged.connect(lambda: None)

            self.version_list.clear()
            items = []

            for version in os.listdir(version_folder):
                file_path = os.path.join(version_folder, version)

                # add plugin buttons
                for plugin in self.plugins:
                    if os.path.isdir(file_path):
                        for file in os.listdir(file_path):
                            if '.'+file.rsplit('.',1)[-1] == plugin.extension:
                                items.append(os.path.basename(file_path)+'/'+file)

            items.sort(reverse=True)
            self.version_list.currentTextChanged.disconnect()
            
            self.task_item_doubleclicked(item)
            self.version_list.clear()
            self.version_list.currentTextChanged.connect(lambda: self.task_item_doubleclicked(item))
            self.version_list.addItems(items)
            
            
            self.asset_info_tab.setVisible(False)
            self.shot_info_tab.setVisible(True)
            
        else:
            dlg = QtWidgets.QMessageBox(self)
            dlg.setWindowTitle('No Project Root')
            dlg.setText("There is no project root set on the project.\nPlease set a project root")
            button = dlg.exec()

    def set_asset_tab(self, item):
        task = item.kitsu_item
        asset =  gazu.asset.get_asset(task['entity_id'])

        self.asset_info_name.setText(asset['name'])
        self.asset_info_id.setText(asset['id'])

        img_path = os.path.join(root_folder, '.cache_images', asset['project_name'], 'assets', asset['name']+'_preview.jpeg')
        pixmap = QtGui.QPixmap(img_path)
        self.asset_info_image.setPixmap(pixmap)

        # get versions
        if self.project_root:
            version_folder = self.get_item_file_path(item)
            self.asset_version_list.currentTextChanged.connect(lambda: None)

            self.asset_version_list.clear()
            items = []

            if not os.path.exists(version_folder):
                os.makedirs(version_folder)


            for version in os.listdir(version_folder):
                file_path = os.path.join(version_folder, version)

                # add plugin buttons
                for plugin in self.plugins:
                    if os.path.isdir(file_path):
                        for file in os.listdir(file_path):
                            if '.'+file.rsplit('.',1)[-1] == plugin.extension:
                                items.append(os.path.basename(file_path)+'/'+file)

            items.sort(reverse=True)
            self.asset_version_list.currentTextChanged.disconnect()
        
            self.task_item_doubleclicked(item)
            self.asset_version_list.clear()
            self.asset_version_list.currentTextChanged.connect(lambda: self.task_item_doubleclicked(item))
            self.asset_version_list.addItems(items)
            
            
            self.shot_info_tab.setVisible(False)
            self.asset_info_tab.setVisible(True)
        else:
            dlg = QtWidgets.QMessageBox(self)
            dlg.setWindowTitle('No Project Root')
            dlg.setText("There is no project root set on the project.\nPlease set a project root")
            button = dlg.exec()

    def update_trees(self):
        self.update_task_tree()
        self.update_file_tree()

    def update_file_tree(self):
        if not self.project_root:
            return 
        if not os.path.exists(self.project_root):
            return


        model = QtGui.QFileSystemModel()
        model.setRootPath(self.project_root)
        model.sort(0, Qt.SortOrder.AscendingOrder)
        sorting_model = QtCore.QSortFilterProxyModel()
        sorting_model.setSourceModel(model)

        self.files_tree.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        
        self.files_tree.setModel(sorting_model)
        self.files_tree.setRootIndex(sorting_model.mapFromSource(model.index(self.project_root)))
        #self.files_tree.header().setSortIndicator(0, endingOrder)
        self.files_tree.setSortingEnabled(True)
        self.files_tree.resizeColumnToContents(0)
        self.files_tree.setAcceptDrops(True)

    def update_task_tree(self):
        
        if not self.good_settings:
            return
        self.set_status('Updating shot tree ...', True)
        self.set_loading()

        self.project = gazu.project.get_project_by_name(self.project_box.currentText())
        try:
            self.project_root = self.project['data']['project_root']
        except:
            self.project_root = None

        self.project_root_label.setText(str(self.project_root))

        self.my_task_tree_model = QtGui.QStandardItemModel()
        rootNode = self.my_task_tree_model.invisibleRootItem()

        task_list = gazu.user.all_tasks_to_do()
        sequences = {}

        for task in task_list:
            
            if task['project_name'] == self.project_box.currentText():
                try:
                    sequences[task['sequence_name']].append(task)
                except:
                    sequences[task['sequence_name']] = [task]

        for sequence in sequences:
            task_list = sequences[sequence]
            shots = {}
            for task in task_list:
                try:
                    shots[task['entity_name']].append(task)
                except:
                    shots[task['entity_name']] = [task]

            if sequence == None:
                sequence = 'ASSETS TASKS'

            sequence_item = kitsu_tree_item(self.project_root, sequence)

            for x in gazu.shot.all_sequences_for_project(self.project):
                if x['name'] == sequence:
                    sequence_item.kitsu_item = x
                    sequence_item.id = x['id']
                    sequence_item.type = x['type']
            sequence_item.setIcon(QtGui.QIcon('./icons/sequence.svg'))
            
            sequence_item.setEditable(False)
            rootNode.appendRow(sequence_item)

            for shot in shots:
                shot_item = kitsu_tree_item(self.project_root, shot)
                shot_item.id = shots[shot][0]['entity_id']
                shot_kitsu = gazu.entity.get_entity(shot_item.id)
                shot_item.type = shot_kitsu['type'] 
                
                
                shot_item.kitsu_item = shot_kitsu
                try:
                    preview_id = shot_kitsu['preview_file_id']
                    img_file_path = os.path.join(root_folder,'.cache_images', self.project_box.currentText(),'shots',sequence,shot+'_preview.jpeg')
                    #print(img_file_path)
                    os.makedirs(os.path.dirname(img_file_path), exist_ok=True)

                    #thumnail_id = shot_kitsu.keys()
                    #print(thumnail_id)
                    #print(self.kitsu_host.text()+'/api/pictures/originals/preview-files/'+preview_id+'.png')

                    gazu.files.download_preview_file_thumbnail(preview_id, img_file_path)
                    image = QtGui.QImage(img_file_path)

                except:
                    image = QtGui.QImage(16, 9, QtGui.QImage.Format.Format_RGB32)

                shot_item.setData(image.scaled(64,27,Qt.AspectRatioMode.KeepAspectRatioByExpanding),Qt.ItemDataRole.DecorationRole)
                shot_item.setEditable(False)
                sequence_item.appendRow(shot_item)

                for task in shots[shot]:

                    if self.gui:
                        QCoreApplication.processEvents()
                    if task['project_name'] == self.project_box.currentText():
                        task_item = kitsu_tree_item(self.project_root, task['task_type_name'])
                        task_item.id = task['id']
                        task_item.type = task['type']
                        task_item.kitsu_item = task
                        task_item.setEditable(False)
                        task_item.setIcon(QtGui.QIcon('./icons/task.svg'))
                        shot_item.appendRow(task_item)
                        if self.project_root != None:
                            folder_path = os.path.join(self.project_root, 'shots',sequence,shot,'project_files',task['task_type_name'])
                            os.makedirs(folder_path, exist_ok=True)

        self.my_task_tree.setModel(self.my_task_tree_model)
        self.set_status('Tree refreshed !', False)
        self.set_loading(False)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = kitsu_connect()
    window.show()
    sys.exit(app.exec())
