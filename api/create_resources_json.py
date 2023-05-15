import json
import requests
import base64
import pandas as pd
import os


class ResourceJsonCreator:
    """
    This class generates the JSON which is pushed onto MongoDB.
    On a high-level, it does the following:
        - Merges all the current available JSONs of gem5 versions into one.
        - Adds certain fields to the JSON.
        - Populates those fields.
    """

    # Global Variables
    base_url = "https://github.com/gem5/gem5/tree/develop"  # gem5 GitHub URL
    resource_url_map = {
        "dev": "https://gem5.googlesource.com/public/gem5-resources/+/refs/heads/develop/resources.json?format=TEXT",
        "22.1": "https://gem5.googlesource.com/public/gem5-resources/+/refs/heads/stable/resources.json?format=TEXT",
        "22.0": "http://resources.gem5.org/prev-resources-json/resources-21-2.json",
        "21.2": "http://resources.gem5.org/prev-resources-json/resources-22-0.json",
    }

    def __init__(self, versions, debug=False):
        if debug:
            print("Creating Resource JSON for gem5 versions: ", versions)
        # print(src)
        self.debug = debug
        self.link_map = self.__create_resource_map(versions)

    def __get_file_data(self, url):
        json_data = None
        try:
            json_data = requests.get(url).text
            json_data = base64.b64decode(json_data).decode("utf-8")
            return json.loads(json_data)
        except:
            json_data = requests.get(url).json()
            return json_data

    def __create_resource_map(self, versions):
        url = "http://dist.gem5.org/dist/"
        ver_map = {}
        for version in versions:
            if version != "dev":
                ver_map[version] = url + "v" + version.replace(".", "-")
            else:
                ver_map[version] = url + "develop"
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
            resources = df.to_dict("records")
            if self.debug:
                with open("resources_test_" + k + ".json", "w") as f:
                    json.dump(resources, f, indent=4)
        return self.__merge_dataframes(dfs)

    def __getSize(self, url):
        """
        Helper function to return the size of a download through its URL.
        Returns 0 if URL has an error.

        :param url: Download URL
        """
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
        """
        Helper function to find the instance of a string in a folder.
        This is recursive, i.e., subfolders will also be searched.

        :param folder_path: Path to the folder to begin searching
        :param id: Phrase to search in the folder

        :returns matching_files: List of file paths to the files containing id
        """
        matching_files = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    contents = f.read()
                    if id in contents:
                        file_path = file_path.replace("\\", "/")
                        matching_files.append(file_path)
            elif os.path.isdir(file_path):
                matching_files.extend(self.__search_folder(file_path, id))
        return matching_files

    def __change_type(self, resource):
        if resource["type"] == "workload":
            # get the architecture from the name and remove 64 from it
            resource["architecture"] = (
                resource["name"].split("-")[0].replace("64", "").upper()
            )
            resources = {}
            if "resources" in resource:
                for key in resource["resources"]:
                    if "disk_image" in key:
                        resources["diskimage"] = resource["resources"][key]
                    else:
                        resources[key] = resource["resources"][key]
            resource["resources"] = resources

            return resource
        if "kernel" in resource["name"]:
            resource["type"] = "kernel"
        elif "bootloader" in resource["name"]:
            resource["type"] = "bootloader"
        elif "benchmark" in resource["documentation"]:
            resource["type"] = "diskimage"
            # if tags not in resource:
            if "tags" not in resource:
                resource["tags"] = []
            resource["tags"].append("benchmark")
            if (
                "additional_metadata" in resource
                and "root_partition" in resource["additional_metadata"]
                and resource["additional_metadata"]["root_partition"] is not None
            ):
                resource["root_partition"] = resource["additional_metadata"][
                    "root_partition"
                ]
            else:
                resource["root_partition"] = ""
        elif resource["url"] is not None and ".img.gz" in resource["url"]:
            resource["type"] = "diskimage"
            if (
                "additional_metadata" in resource
                and "root_partition" in resource["additional_metadata"]
                and resource["additional_metadata"]["root_partition"] is not None
            ):
                resource["root_partition"] = resource["additional_metadata"][
                    "root_partition"
                ]
            else:
                resource["root_partition"] = ""
        elif "binary" in resource["documentation"]:
            resource["type"] = "binary"
        elif "checkpoint" in resource["documentation"]:
            resource["type"] = "checkpoint"
        elif "simpoint" in resource["documentation"]:
            resource["type"] = "simpoint"
        return resource

    def __json_to_pd(self, ver, url):
        data = self.__get_file_data(self.resource_url_map[ver])
        resources = data["resources"]
        new_resources = []
        for resource in resources:
            if resource["type"] == "group":
                for group in resource["contents"]:
                    group["tags"] = [resource["name"]]
                    # replace the {url_base} with the url
                    download_url = ""
                    if group["url"] is not None:
                        download_url = group["url"].replace("{url_base}", url)
                        group["url"] = download_url
                        group["size"] = self.__getSize(download_url)
                    else:
                        group["size"] = 0

                    group = self.__change_type(group)
                    new_resources.append(group)
                    if self.debug:
                        print(len(new_resources))
            else:
                resource = self.__change_type(resource)
                download_url = ""
                if "url" in resource and resource["url"] is not None:
                    download_url = resource["url"].replace("{url_base}", url)
                    resource["url"] = download_url
                    resource["size"] = self.__getSize(download_url)
                else:
                    resource["size"] = 0
                if "tags" not in resource:
                    resource["tags"] = []
                new_resources.append(resource)
                if self.debug:
                    print(len(new_resources))
        df = pd.DataFrame(new_resources)
        return df

    def __merge_dataframes(self, dfs):
        fin_df = dfs[0]
        for df in dfs[1:]:
            fin_df = pd.merge(fin_df, df, on="name", how="outer", suffixes=("", "_y"))
            fin_df = fin_df.loc[:, ~fin_df.columns.str.endswith("_y")]
        keys = list(self.link_map.keys())
        fin_df[keys[0]] = fin_df[keys].apply(lambda x: list(x.dropna()), axis=1)
        fin_df["versions"] = fin_df[keys[0]]
        fin_df.drop(keys, axis=1, inplace=True)
        fin_df = fin_df.dropna(axis=1, how="all")
        # fin_df = fin_df.where((pd.notnull(fin_df)), None)
        return fin_df

    def __extract_code_examples(self, resources, source):
        """
        This function goes by IDs present in the resources DataFrame.
        It finds which files use those IDs in gem5/configs.
        It adds the GitHub URL of those files under "example".
        It finds whether those files are used in gem5/tests/gem5.
        If yes, it marks "tested" as True. If not, it marks "tested" as False.
        "example" and "tested" are made into a JSON for every code example.
        This list of JSONs is assigned to the 'code_examples' field of the DataFrame.

        :param resources: A DataFrame containing the current state of resources.
        :param source: Path to gem5

        :returns resources: DataFrame with ['code-examples'] populated.
        """
        for index, resource in resources.iterrows():
            id = resource["id"]
            # search for files in the folder tree that contain the 'id' value
            matching_files = self.__search_folder(source + "/configs", '"' + id + '"')
            filenames = [os.path.basename(path) for path in matching_files]
            tested_files = []
            for file in filenames:
                tested_files.append(
                    True
                    if len(self.__search_folder(source + "/tests/gem5", file)) > 0
                    else False
                )
            matching_files = [file.replace(source + "/", "") for file in matching_files]
            matching_files = [self.base_url + "/" + file for file in matching_files]
            if self.debug and len(matching_files) > 0:
                print("Files containing id {}:".format(id))
                print(matching_files)

            code_examples = []

            # Loop through matching_files and tested_files, and
            # create a new JSON object for each element
            for i in range(len(matching_files)):
                json_obj = {"example": matching_files[i], "tested": tested_files[i]}
                code_examples.append(json_obj)
            json_result = json.dumps(code_examples)

            if self.debug:
                print(json.dumps(code_examples, indent=4))

            resources.at[index, "code_examples"] = json.loads(json_result)

        return resources

    def __populate_resources(self, resources):
        categories = resources["type"].unique()
        if self.debug:
            print(categories)

        archs = resources[resources["architecture"].notnull()]["architecture"].unique()
        if self.debug:
            print(archs)
            print(resources[resources["type"] == "resource"]["name"])

        resources.rename(columns={"name": "id"}, inplace=True)
        resources.rename(columns={"type": "category"}, inplace=True)
        # resources.rename(columns={"url": "download_url"}, inplace=True)
        resources.rename(columns={"documentation": "description"}, inplace=True)
        # resources["name"] = resources["id"].str.replace("-", " ")

        # initialize code_examples to empty list
        resources["code_examples"] = [[] for _ in range(len(resources))]
        resources["license"] = ""
        resources["author"] = [[] for _ in range(len(resources))]
        # resources["tags"] = [[] for _ in range(len(resources))]
        resources["source_url"] = ""
        resources["resource_version"] = "1.0.0"
        resources["gem5_versions"] = [["23.0"] for _ in range(len(resources))]
        # resources = resources.where((pd.notnull(resources)), None)
        # resources = resources.to_dict('records')
        if not self.debug:
            for index, resource in resources.iterrows():
                if resource["category"] == "workload":
                    resources.at[
                        index, "example_usage"
                    ] = f"Workload(\"{resource['id']}\")"
                else:
                    resources.at[
                        index, "example_usage"
                    ] = f"get_resource(resource_name=\"{resource['id']}\")"
                if resource["source"] is not None and str(resource["source"]) != "nan":
                    try:
                        if str(resource["source"]) == "nan":
                            print(resource["source"])
                        resources.at[index, "source_url"] = (
                            "https://github.com/gem5/gem5-resources/tree/develop/"
                            + str(resource["source"])
                        )
                        request = requests.get(
                            "https://raw.githubusercontent.com/gem5/gem5-resources/develop/"
                            + str(resource["source"])
                            + "/README.md"
                        )
                        content = request.text
                        content = content.split("---")[1]
                        content = content.split("---")[0]
                        if "tags:" in content:
                            tags = content.split("tags:\n")[1]
                            tags = tags.split(":")[0]
                            tags = tags.split("\n")[:-1]
                            tags = [tag.strip().replace("- ", "") for tag in tags]
                            if tags == [""] or tags == None:
                                tags = []
                            if resource["tags"] is None:
                                resources.at[index, "tags"] = tags
                            else:
                                resources.at[index, "tags"].extend(tags)
                        if "author:" in content:
                            author = content.split("author:")[1]
                            author = author.split("\n")[0]
                            author = (
                                author.replace("[", "")
                                .replace("]", "")
                                .replace('"', "")
                            )
                            author = author.split(",")
                            author = [a.strip() for a in author]
                            resources.at[index, "author"] = author
                        if "license:" in content:
                            license = content.split("license:")[1].split("\n")[0]
                            resources.at[index, "license"] = license
                    except:
                        pass
        return resources

    def __create_new_json(self):
        # "dev": "https://gem5.googlesource.com/public/gem5-resources/+/refs/heads/develop/resources.json?format=TEXT"
        return self.__json_to_pd("dev", "http://dist.gem5.org/dist/develop")

    def create_json(self, source, output):
        print("Merging json files and adding sizes")
        resources = self.__create_new_json()
        print("Populating resources with additional information")
        resources = self.__populate_resources(resources)
        print("Extracting code examples from the gem5 repository")
        resources = self.__extract_code_examples(resources, source)
        # resources = resources.drop('versions', axis=1)
        # replace nan with None
        resources = resources.where((pd.notnull(resources)), None)
        resources = resources.to_dict("records")
        # remove NaN values
        for resource in resources:
            if (
                "additional_metadata" in resource
                and resource["additional_metadata"] is not None
            ):
                for k, v in resource["additional_metadata"].items():
                    resource[k] = v
                del resource["additional_metadata"]
            """ if "additional_params" in resource and resource["additional_params"] is not None:
                for k, v in resource["additional_params"].items():
                    resource[k] = v
                del resource["additional_params"] """
            for key in list(resource.keys()):
                if resource[key] is None or str(resource[key]) == "nan":
                    resource.pop(key)
        with open(output, "w") as f:
            json.dump(resources, f, indent=4)


""" res = ResourceJsonCreator(["dev", "22.1", "22.0", "21.2"], True)
res.create_json('gem5', 'harshil.json') """
