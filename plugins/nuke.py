import os, sys, subprocess

class Plugin:
    def __init__(self, parent):
        self.parent = parent

        # Define name of the plugin app
        self.name = 'Nuke 14.0v3'
        self.icon = './icons/nuke.png'
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

