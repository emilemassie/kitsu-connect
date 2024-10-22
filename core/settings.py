import sys
import os, getpass
import json

from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtCore import Qt

import gazu

from appdirs import user_config_dir

def get_config_file():
    # Get the current username
    username = getpass.getuser()

    # Define your application name and author/company name
    app_name = "kitsu-connect"
    app_author = "kitsu-connect"  # Optional, not needed for Linux

    # Get the user-specific configuration directory
    config_dir = user_config_dir(app_name, app_author)

    # Create the configuration directory if it doesn't exist
    os.makedirs(config_dir, exist_ok=True)

    # Define the path for your configuration file
    config_file = os.path.join(config_dir, f"{username}_settings.conf")
    return config_file

def get_ffmpeg_exec():
    if getattr(sys, 'frozen', False):
        if sys.platform == "win32":  # Windows
            basedir = sys._MEIPASS
        elif sys.platform == "darwin":  # macOS
            basedir = os.path.dirname(os.path.abspath(__file__))
        elif sys.platform.startswith("linux"):  # Linux
            basedir = os.path.dirname(os.path.abspath(__file__))
            raise EnvironmentError("Unsupported operating system")
        
    else:
        basedir = '.'#os.path.dirname(os.path.abspath(__file__))
        basedir = str(basedir)

    # Determine the ffmpeg directory based on the OS
    if sys.platform == "win32":  # Windows
        ffmpeg_exec = basedir+'/ffmpeg.exe'
    elif sys.platform == "darwin":  # macOS
        ffmpeg_exec = basedir+'/ffmpeg'
    elif sys.platform.startswith("linux"):  # Linux
        ffmpeg_exec = basedir+'/ffmpeg'
        raise EnvironmentError("Unsupported operating system")

    return ffmpeg_exec

class kitsu_settings(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__()

        uic.loadUi(os.path.join('./ui','kitsu_publisher_settings.ui'), self) 


        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__),'icons','icon.png')))

        self.parent = parent

        # Remove the window frame and make the window transparent
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        #self.setAttribute(Qt.WA_TranslucentBackground)

        # Variables to track mouse position for dragging
        self.old_position = QtCore.QPoint()
        self.exit_button.released.connect(self.close)
        self.save_button.released.connect(self.save_pressed)

        self.access_token = None
        self.settings_dict = {}

        self.ffmpeg_exec = get_ffmpeg_exec()
        self.settings_file = get_config_file()

        self.parent.update_log(f"Checking for settings in : {self.settings_file}")
        if self.load_settings():
            self.parent.update_log('User configuration loaded !')
            self.check_connection()

   
                        
    def check_connection(self):
        if self.access_token:
            try:
                token = {'access_token': self.access_token}
                gazu.client.set_host(self.url+'/api')
                gazu.client.set_tokens(token)
                user = gazu.client.get_current_user()
                self.parent.connection_status = True
                return True
            except:
                self.parent.connection_status = True
                return False
        else:
            self.parent.connection_status = True
            return False

    def get_kitsu_token(self):
        try:
            self.user = self.t_user.text()
            self.url = self.t_url.text()
            gazu.client.set_host(self.url+'/api')
            gazu.log_in(self.user, self.t_pwd.text())
            self.access_token = gazu.refresh_token()['access_token']
            return self.access_token
        except Exception as eee:
            self.setConnectStatus(False)
            self.status_c.setText('<span style="color:red;">ERROR CONNECTING</span>'+str(eee))
            self.parent.update_log('<span style="color:red;">ERROR CONNECTING</span>'+str(eee))

            return False

    def save_pressed(self):
        if self.get_kitsu_token():
            self.save_settings()
            self.load_settings()
            self.close()
            return True
        else:

            return False
    
    def setConnectStatus(self,is_good):
        if is_good:
            self.parent.t_url.setText(self.url)
            self.parent.t_user.setText(self.user)
            self.parent.t_status.setText('<span style="color:green;">CONNECTED')
            self.status_c.setText('<span style="color:green;">CONNECTED')
            self.parent.build_tasks_tree()
            self.parent.connect_status = True
            return True
        else:
            self.parent.t_url.setText('https://kitsu.exemple.com')
            self.parent.t_user.setText('user@exemple.com')
            self.parent.t_status.setText('<span style="color:red;">NOT CONNECTED')
            self.status_c.setText('<span style="color:NOT CONNECTED;">')
            self.parent.connect_status = False
            return False

    def load_settings(self):
        try:
            with open(self.settings_file, 'r') as f:
                self.settings_dict = json.load(f)
                self.url = self.settings_dict['host']
                self.user = self.settings_dict['username']
                self.access_token = self.settings_dict['key']

                self.t_url.setText(self.url)
                self.t_user.setText(self.user)

                if self.check_connection():
                    self.setConnectStatus(True)
                    return True
                else:
                    self.setConnectStatus(False)
                    return False
        except Exception as eee:
            self.setConnectStatus(False)
            print('Cannot load settings')
            print(eee)
            return False

    def save_settings(self):
        new_dict = {
            "host": self.url,
            "username":self.user,
            "key": self.access_token
        }
        j = json.dumps(new_dict, indent=4)
        with open(self.settings_file, 'w') as f:
            print(j, file=f)

        self.parent.update_log('Saved Settings')

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.old_position)
            event.accept()

