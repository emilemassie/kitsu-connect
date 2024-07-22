
import sys, os, json
import subprocess


root_folder = os.path.dirname(__file__)
sys.path.insert(0, root_folder)


if os.name == 'nt':
            os_platform = 'win'
elif os.name == 'posix':
    if sys.platform == 'darwin':
        os_platform = 'mac'
    else:
        os_platform = 'lin'
else:
    raise NameError("Unknown operating system.")

sys.path.insert(0, os.path.join(root_folder, 'site-packages', os_platform))

from PyQt6 import uic, QtCore, QtSvg
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6 import QtGui

import gazu
from core import settings
from core.project_settings import project_settings
from core.plugins import KitsuConnectPlugins


class kitsu_connect(QtWidgets.QWidget):
    def __init__(self):
        super(kitsu_connect, self).__init__()

        # UI SETUP
        self.root_folder = os.path.dirname(__file__)
        uic.loadUi(os.path.join(self.root_folder, 'ui', 'kitsu-connect.ui'), self)
        self.setWindowTitle("KITSU - CONNECT")
        self.setWindowIcon(QtGui.QIcon(os.path.join(self.root_folder,'icons','icon.png')))
        self.apps_tab.setVisible(False)


        # Grab Plugins
        self.plugins = []
        self.load_plugins()

        # Load Settings
        
        self.settings = settings.kitsu_connect_settings(self)
        self.good_settings = self.settings.load_settings()

        # Setup Loading Screen
        self.loading_icon_movie = QtGui.QMovie(os.path.join(self.root_folder,'icons','loading_icon_2.gif'))
        self.loading_icon_movie.start()
        self.loading_icon_label.setMovie(self.loading_icon_movie)

        # Connect actions 
        self.asset_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.asset_tree.customContextMenuRequested.connect(self.asset_right_click_menu)
        self.my_task_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.my_task_tree.customContextMenuRequested.connect(self.shot_right_click_menu)

        self.my_task_tree.doubleClicked.connect(self.set_context)
        self.project_box.currentTextChanged.connect(self.update_trees)
        self.task_expend_button.pressed.connect(self.my_task_tree.expandAll)
        self.task_collapse_button.pressed.connect(self.my_task_tree.collapseAll)
        self.save_settings_button.pressed.connect(self.settings.save_settings)
        self.project_settings_button.pressed.connect(self.open_project_settings)

        self.context_id = None
        self.context_set = False
        self.gui = 0
        self.project_root = None
        self.gui = 1
        self.center()

        

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
        self.ps = project_settings(self)
        if self.ps.getInfos():
            self.ps.show()

    def build_plugin_shelf(self):
        self.apps_tab
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
            
            


    def set_context(self, index):
        item = index.model().itemFromIndex(index)
        id = item.whatsThis()
        self.build_plugin_shelf()
        try:
            task = gazu.task.get_task(id)
            context = f"{task['project']['name']} : {task['sequence']['name']} : {task['entity']['name']} : {task['task_type']['name']}".upper()
            self.context_id = id
            self.context_set = True
            self.context_label.setText(context)
            
            self.apps_tab.setVisible(True)
        except:
            self.context_id = None
            self.context_set = False
            self.context_label.setText('')
            self.apps_tab.setVisible(False)

    def get_asset_path(self):
        index = self.asset_tree.currentIndex()
        item = self.asset_tree_model.itemFromIndex(index)
        try:
            self.project_root = self.project['data']['project_root']
            asset = gazu.asset.get_asset(item.whatsThis())
            asset_path = os.path.join(self.project_root,'assets', asset['name'])
            print(asset_path)
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
        print(app,context_id)
        subprocess.call(app['exec'], env=app['environ'])
        
    def shot_right_click_menu(self, position):
        menu = QtWidgets.QMenu()

        index = self.my_task_tree.currentIndex()
        item = self.my_task_tree_model.itemFromIndex(index)
        if item.whatsThis():
            for plugin in self.plugins:
                icon = QtGui.QIcon(plugin.icon)
                menu.addAction(icon, plugin.name, plugin.launch)
        #    for app in self.plugin_settings:
        #        menu.addAction('Launch '+app, lambda: self.launch_app(self.plugin_settings[app], item.whatsThis()))
            #menu.addAction('Get asset path', self.show_asset_path)
            #menu.addAction('Open in browser', self.open_asset_path)

        
        menu.exec(self.my_task_tree.viewport().mapToGlobal(position))

    def set_projects(self):
        project_list = [project['name'] for project in gazu.user.all_open_projects()]
        self.project_box.clear()
        self.project_box.addItems(project_list)

    def update_trees(self):
        
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

            sequence_item = QtGui.QStandardItem(sequence)
            sequence_item.setEditable(False)
            rootNode.appendRow(sequence_item)

            for shot in shots:
                shot_item = QtGui.QStandardItem(shot)
                
                shot_id = shots[shot][0]['entity_id']
                shot_kitsu = gazu.entity.get_entity(shot_id)
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
                        task_item = QtGui.QStandardItem(task['task_type_name'])
                        task_item.setWhatsThis(task['id'])
                        
                        task_item.setEditable(False)
                        shot_item.appendRow(task_item)
            
        self.my_task_tree.setModel(self.my_task_tree_model)


        # set asset tree
        self.asset_tree_model = QtGui.QStandardItemModel()
        rootNode = self.asset_tree_model.invisibleRootItem()

        asset_list = gazu.asset.all_assets_for_project(self.project)

        for asset in asset_list:
            asset_item = QtGui.QStandardItem(asset['name'])
            try:
                preview_id = asset['preview_file_id']
                img_file_path = os.path.join(root_folder,'.cache_images',self.project_box.currentText(),'assets',asset['name']+'_preview.jpeg')
                os.makedirs(os.path.dirname(img_file_path), exist_ok=True)
                gazu.files.download_preview_file_thumbnail(preview_id, img_file_path)
                image = QtGui.QImage(img_file_path)
            except:
                image = QtGui.QImage(16, 9, QtGui.QImage.Format.Format_RGB32)
            
            asset_item.setData(image.scaled(64,27,Qt.AspectRatioMode.KeepAspectRatioByExpanding),Qt.ItemDataRole.DecorationRole)
            asset_item.setEditable(False)
            asset_item.setWhatsThis(asset['id'])
            rootNode.appendRow(asset_item)

        self.asset_tree.setModel(self.asset_tree_model)

        self.set_status('Tree refreshed !', False)
        self.set_loading(False)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = kitsu_connect()
    window.show()
    sys.exit(app.exec())
