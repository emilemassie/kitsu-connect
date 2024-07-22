import os, json, gazu


class kitsu_connect_settings:
    def __init__(self, kitsu_connect):
        self.connect_window = kitsu_connect
        self.settings_file = os.path.join(self.connect_window.root_folder, 'settings.json')


    def check_settings(self):
        pass

    def save_settings(self):
        new_dict = {
            "host": self.connect_window.kitsu_host.text(),
            "username":self.connect_window.kitsu_username.text(),
            "password": self.connect_window.kitsu_password.text()
        }
        j = json.dumps(new_dict, indent=4)
        with open(self.settings_file, 'w') as f:
            print(j, file=f)
        
        return self.load_settings()

    def load_settings(self):
        self.connect_window.asset_tree_model = None
        self.connect_window.set_status('Connecting', False)
        try:
            with open(self.settings_file, 'r') as f:
                self.settings_dict = json.load(f)

                self.connect_window.kitsu_host.setText(self.settings_dict['host'])
                self.connect_window.kitsu_username.setText(self.settings_dict['username'])
                self.connect_window.kitsu_password.setText(self.settings_dict['password'])

                gazu.client.set_host(self.settings_dict['host']+'/api')
                gazu.log_in(self.settings_dict['username'], self.settings_dict['password'])

                self.connect_window.set_status('Connected !!!', False)
                self.connect_window.connectionStatus.setText('<html><head/><body><p><span style=" font-size:10pt; color:#008F00;">Connected !!!</span></p></body></html>')

                self.connect_window.set_projects()
                self.connect_window.good_settings = True
            return True
        except:
            self.connect_window.good_settings = False
            self.connect_window.asset_tree_model = None
            self.connect_window.project_box.clear()
            self.connect_window.set_status('Connection Failed', False)
            self.connect_window.connectionStatus.setText('<html><head/><body><p><span style=" font-size:10pt; color:#8F0000;">Connection Failed.</span></p></body></html>')
            return False
        
