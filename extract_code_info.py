import json
import os

base_url = "https://github.com/gem5/gem5/tree/develop"
folder_path = 'gem5/configs'

def search_folder(folder_path, id):
        matching_files = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    contents = f.read()
                    if id in contents:
                        matching_files.append(file_path)
            elif os.path.isdir(file_path):
                matching_files.extend(search_folder(file_path, id))
        return matching_files
# load the JSON file
with open('resources.json', 'r+') as f:
    data = json.load(f)

    # ids = [obj['id'] for obj in data]
    for resource in data:
        print(resource)
        id=resource['id']
        # search for files in the folder tree that contain the 'id' value
        matching_files = search_folder(folder_path, id)

        # print the list of matching files for this 'id'
        print('Files containing id {}:'.format(id))
        matching_files = [file[5:] for file in matching_files]
        matching_files = [base_url + '/' + file for file in matching_files]
        resource['example_urls']=matching_files
    
    # write the JSON file
    f.seek(0)
    f.write(json.dumps(data, indent=4))
    