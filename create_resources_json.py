import json
import requests
import base64
import pandas as pd
import os


class ResourceJsonCreator:
    # Global Variables
    base_url = "https://github.com/gem5/gem5/tree/develop"  # gem5 GitHub URL
    resource_url_map = {
        'dev': "https://gem5.googlesource.com/public/gem5-resources/+/refs/heads/develop/resources.json?format=TEXT",
        '22.1': "https://gem5.googlesource.com/public/gem5-resources/+/refs/heads/stable/resources.json?format=TEXT",
        '22.0': "http://resources.gem5.org/prev-resources-json/resources-21-2.json",
        '21.2': "http://resources.gem5.org/prev-resources-json/resources-22-0.json"}

    def __init__(self,  versions, debug,):
        if debug:
            print("Creating Resource JSON for gem5 versions: ", versions)
        # print(src)
        self.debug = debug
        self.link_map = self.__create_resource_map(versions)

    def __get_file_data(self, url):
        json_data = None
        try:
            json_data = requests.get(url).text
            json_data = base64.b64decode(json_data).decode('utf-8')
            return json.loads(json_data)
        except:
            json_data = requests.get(url).json()
            return json_data

    def __create_resource_map(self, versions):
        url = 'http://dist.gem5.org/dist/'
        ver_map = {}
        for version in versions:
            if version != 'dev':
                ver_map[version] = url + 'v' + version.replace(".", "-")
            else:
                ver_map[version] = url + 'develop'
        # print(ver_map)
        return ver_map

    def __merge_jsons(self):
        dfs = []
        for k, v in self.link_map.items():
            df = self.__json_to_pd(k, v)
            df = df.where((pd.notnull(df)), None)
            if self.debug:
                print(df.shape)
            dfs.append(df)
            # store the dataframe as a json file
            resources = df.to_dict('records')
            if self.debug:
                with open('resources_test_'+k+'.json', 'w') as f:
                    json.dump(resources, f, indent=4)
            # print the first row of the first dataframe
            # read the json files
            """ for k, v in ver_map.items():
                with open('resources_test_'+k+'.json', 'r') as f:
                data = json.load(f)
                df = pd.DataFrame(data)
                dfs.append(df) """
        return self.__merge_dataframes(dfs)

    def __getSize(self, url):
        if self.debug:
            return 0
        try:
            response = requests.head(url)
            size = int(response.headers.get("content-length", 0))
            return size
        except Exception as e:
            if self.debug:
                print(e)
            return 0

    def __search_folder(self, folder_path, id):
        matching_files = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    contents = f.read()
                    if id in contents:
                        file_path = file_path.replace('\\', '/')
                        matching_files.append(file_path)
            elif os.path.isdir(file_path):
                matching_files.extend(self.__search_folder(file_path, id))
        return matching_files

    def __change_type(self, resource):
        if resource['type'] == 'workload':
            # get the architecture from the name and remove 64 from it
            resource['architecture'] = resource['name'].split(
                '-')[0].replace('64', '').upper()
            return resource
        if 'kernel' in resource['name']:
            resource['type'] = 'kernel'
        elif 'bootloader' in resource['name']:
            resource['type'] = 'bootloader'
        elif 'benchmark' in resource['documentation']:
            resource['type'] = 'benchmark'
        elif resource['url'] is not None and '.img.gz' in resource['url']:
            resource['type'] = 'diskimage'
        elif 'binary' in resource['documentation']:
            resource['type'] = 'binary'
        elif 'checkpoint' in resource['documentation']:
            resource['type'] = 'checkpoint'
        elif 'simpoint' in resource['documentation']:
            resource['type'] = 'simpoint'
        return resource

    def __json_to_pd(self, ver, url):
        data = self.__get_file_data(self.resource_url_map[ver])
        resources = data['resources']
        new_resources = []
        for resource in resources:
            if resource['type'] == 'group':
                for group in resource['contents']:
                    group['tags'] = [resource['name']]
                    # replace the {url_base} with the url
                    download_url = ""
                    if(group['url'] is not None):
                        download_url = group['url'].replace('{url_base}', url)
                    group[ver] = {
                        "version": ver,
                        "url": url,
                        "size": self.__getSize(download_url)
                    }

                    group = self.__change_type(group)
                    new_resources.append(group)
                    if self.debug:
                        print(len(new_resources))
            else:
                resource = self.__change_type(resource)
                download_url = ""
                if("url" in resource and resource['url'] is not None):
                    download_url = resource['url'].replace('{url_base}', url)
                resource[ver] = {
                    "version": ver,
                    "url": url,
                    "size": self.__getSize(download_url)
                }
                new_resources.append(resource)
                if self.debug:
                    print(len(new_resources))
        df = pd.DataFrame(new_resources)
        return df

    def __merge_dataframes(self, dfs):
        fin_df = dfs[0]
        for df in dfs[1:]:
            fin_df = pd.merge(fin_df, df, on='name',
                              how='outer', suffixes=('', '_y'))
            fin_df = fin_df.loc[:, ~fin_df.columns.str.endswith('_y')]
        keys = list(self.link_map.keys())
        fin_df[keys[0]] = fin_df[keys].apply(
            lambda x: list(x.dropna()), axis=1)
        fin_df['versions'] = fin_df[keys[0]]
        fin_df.drop(keys, axis=1, inplace=True)
        fin_df = fin_df.where((pd.notnull(fin_df)), None)
        return fin_df

    def __extract_code_examples(self, resources, source):
        for index, resource in resources.iterrows():
            # if self.debug:
            # print(resource)
            id = resource['id']
            # search for files in the folder tree that contain the 'id' value
            matching_files = self.__search_folder(
                source+'/configs', id)
            matching_files = [file.replace(source+'/', '')
                              for file in matching_files]
            matching_files = [self.base_url + '/' +
                              file for file in matching_files]
            if (self.debug and len(matching_files) > 0):
                print('Files containing id {}:'.format(id))
                print(matching_files)
            resources.at[index, 'example_urls'] = matching_files

        return resources

    def __populate_resources(self, resources):
        categories = resources['type'].unique()
        if self.debug:
            print(categories)

        archs = resources[resources['architecture'].notnull()
                          ]['architecture'].unique()
        if self.debug:
            print(archs)
            print(resources[resources['type'] == 'resource']['name'])

        resources.rename(columns={'name': 'id'}, inplace=True)
        resources.rename(columns={'type': 'category'}, inplace=True)
        resources.rename(columns={'url': 'download_url'}, inplace=True)
        resources.rename(
            columns={'documentation': 'description'}, inplace=True)
        resources['name'] = resources['id'].str.replace('-', ' ')
        resources['example_urls'] = None
        resources['license'] = None
        resources['author'] = None
        resources['github_url'] = None
        resources = resources.where((pd.notnull(resources)), None)
        # resources = resources.to_dict('records')
        if self.debug:
            return resources
        for index, resource in resources.iterrows():
            if resource['source'] is not None:
                try:
                    # print(resource['source'])
                    resources.at[index, 'github_url'] = 'https://github.com/gem5/gem5-resources/tree/develop/' + \
                        str(resource['source'])
                    request = requests.get(
                        'https://raw.githubusercontent.com/gem5/gem5-resources/develop/'+str(resource['source'])+'/README.md')
                    content = request.text
                    content = content.split('---')[1]
                    content = content.split('---')[0]
                    if('tags:' in content):
                        tags = content.split('tags:\n')[1]
                        tags = tags.split(':')[0]
                        tags = tags.split('\n')[:-1]
                        tags = [tag.strip().replace('- ', '') for tag in tags]
                        if tags == ['']:
                            tags = None
                        if resource['tags'] is None:
                            resources.at[index, 'tags'] = tags
                        else:
                            resources.at[index, 'tags'].extend(tags)
                    if('author:' in content):
                        author = content.split('author:')[1]
                        author = author.split('\n')[0]
                        author = author.replace(
                            '[', '').replace(']', '').replace('"', '')
                        author = author.split(',')
                        author = [a.strip() for a in author]
                        resources.at[index, 'author'] = author
                    if 'license:' in content:
                        license = content.split('license:')[1].split('\n')[0]
                        resources.at[index, 'license'] = license
                except:
                    pass
        return resources

    def create_json(self, source, output):
        print("Merging json files and adding sizes")
        resources = self.__merge_jsons()
        print("Populating resources with additional information")
        resources = self.__populate_resources(resources)
        print("Extracting code examples from the gem5 repository")
        resources = self.__extract_code_examples(resources, source)
        resources = resources.to_dict('records')
        with open(output, 'w') as f:
            json.dump(resources, f, indent=4)

# res = ResourceJsonCreator('/home/adsad', ["22.1", "22.0", "21.2"])
# res.create_json()
