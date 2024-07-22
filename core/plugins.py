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
        for file in os.listdir(self.plugin_folder):
            if file.endswith('.py'):
                name = file[:-3]
                module = self.dynamic_import('kitsu_connect_plugin_'+name, os.path.join(self.plugin_folder, file))
                plugin = module.Plugin(self.parent)
                plugin_list.append(plugin)
        
        return plugin_list







                


                # def dynamic_import_from_src(src, star_import = False):
                #     my_py_files = get_py_files(src)
                #     for py_file in my_py_files:
                #         module_name = os.path.split(py_file)[-1].strip(".py")
                #         imported_module = dynamic_import(module_name, py_file)
                #         if star_import:
                #             for obj in dir(imported_module):
                #                 globals()[obj] = imported_module.__dict__[obj]
                #         else:
                #             globals()[module_name] = imported_module
                #     return

                # if __name__ == "__main__":
                #     dynamic_import_from_src("first", star_import = False)
            