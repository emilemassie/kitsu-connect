import os, importlib

class KitsuConnectPlugins():
    def __init__(self, parent):
        self.plugin_folder = None
        self.parent = parent

    def dynamic_import(self, module_name, py_path):
        module_spec = importlib.util.spec_from_file_location(module_name, py_path)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        return module 
    def get_plugins(self, folder = None):
        if folder:
            self.plugin_folder = folder
        plugin_list = []
        for folder in os.listdir(self.plugin_folder):
            if os.path.isdir(os.path.join(self.plugin_folder, folder)):
                for file in os.listdir(os.path.join(self.plugin_folder, folder)):
                    if file == folder+'.py':
                        name = file[:-3]
                        module = self.dynamic_import('kitsu_connect_plugin_'+name, os.path.join(self.plugin_folder, folder,file))
                        plugin = module.Plugin(self.parent)
                        plugin_list.append(plugin)
        
        return plugin_list