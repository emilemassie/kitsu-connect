import gazu

gazu.client.set_host("https://kitsu.vivarium.ca/api")
gazu.log_in('emile.massie@gmail.com', 'emile220')

project = gazu.project.get_project_by_name('pipeline_test')
shots = gazu.shot.all_shots_for_project(project)
shot = shots[2]

#print(shot)
#print (project)

project['root_folder'] = 'zzzzzzzz'
project['data'] = {"project_root":"ffffffffffffffff"}
#print('updated')
gazu.project.update_project(project)
print(project)


file = '/Users/emile/Desktop/PXL_20230212_214606450-1.jpg'

# Step 3: Upload the preview file
#preview_file_path = file
#preview = gazu.files.up(shot, preview_file_path)

# Step 4: Update the shot with the new preview (if necessary)
#shot["preview_file_id"] = preview["id"]
#updated_shot = gazu.shot.update_shot(shot)

#print("Shot updated with new preview:", updated_shot)


#gazu.shot.update_shot_data(shot, data={'preview_file_id': file})


#sudo mount -t cifs -o rw,user=server,uid=user,nounix,dir_mode=0777,file_mode=0777 //10.8.0.1/vivarium /mnt/vivarium