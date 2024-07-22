import os, sys, subprocess
from PyQt6 import QtGui

class Plugin:
    def __init__(self, parent):
        self.parent = parent

        # Define name of the plugin app
        self.name = 'Nuke 14.0v3'
        self.icon = './icons/nuke.png'
        self.extension = '.nk'
        # Takes the path for the executable file
        self.exec = self.getExec()
        self.args = '- x'

        self.onPluginLoad()

    def onPluginLoad(self):
        print('LOADED PLUGIN : ' + self.name)

    def launch(self):
        env = self.setEnviron()
        print(self.getExec())
        subprocess.Popen(self.exec, env=env)

    def setEnviron(self):
        data = {
            "KITSU_TASK_ID": self.parent.context_id,
            "KITSU_PROJECT_ROOT": self.parent.project_root_label.text(),
        }

        for i in data:
            os.environ[i] = data[i]
    def getExec(self):
        if os.name == 'nt':
            # Do something specific for Windows
            exec = ''
            # Your Windows-specific code here
        elif os.name == 'posix':
            if sys.platform == 'darwin':
                # Do something specific for macOS
                exec = '/Applications/Nuke15.0v4/Nuke15.0v4.app/Contents/MacOS/Nuke15.0'
                # Your macOS-specific code here
            else:
                # Do something specific for Linux
                exec = ''
                # Your Linux-specific code here
        else:
            raise NameError("Unknown operating system.")
        
        return exec
    
    def tree_right_click_action(self, menu, item):
        item_type = None
        icon = QtGui.QIcon(self.icon)
        if item.whatsThis().startswith('SEQUENCE:'):
            return
        if item.whatsThis().startswith('SHOT:'):
            return
        if item.whatsThis().startswith('TASK:'):
            menu.addAction(icon, 'Create New Nuke Script', self.create_new_script)
        if item.whatsThis().startswith('FILE:'):
            menu.addAction(icon, 'Open in Nuke', self.open_script)
        
        

    def create_new_script(self):
        print('test')
    
    def open_script(self):
        args = ''
        self.launch()

