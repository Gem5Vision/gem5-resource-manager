import json
import os

# load the JSON file
with open('resources.json', 'r') as f:
    data = json.load(f)

ids = [obj['id'] for obj in data]

# specify the folder path to search
folder_path = 'example'

# define a function to recursively search for files that contain the 'id' value
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

# iterate through each 'id' value
for id in ids:
    # search for files in the folder tree that contain the 'id' value
    matching_files = search_folder(folder_path, id)

    # print the list of matching files for this 'id'
    print('Files containing id {}:'.format(id))
    for f in matching_files:
        print(f)