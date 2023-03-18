# json-to-mongodb

## Cli tool
```bash
Usage: bobby.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  addtags
  createresourcesjson
  getresource
  removetags
  updatemongodb
```

## Instructions to made JSON "parseable"

1. Get resources.txt from https://gem5.googlesource.com/public/gem5-resources/+/refs/heads/stable/resources.json?format=text

2. Then decode the base64 string by: `cat resources.txt | base64 -d > resources.json`

3. Then run `python3 create_new_json.py`

4. Then run `python3 modify_columns.py`

5. `resources_new.json` is the final JSON file

## Changes to Structure of JSON

1. Removed nested JSON (`["type"=="group"]`) and added `["group"]` as a field in the base JSON

2. Initialized all the empty fields to hold `None`

3. Changed the type to from the following:
    - Kernel
    - Disk Image
    - Bootloader
    - Benchmark
    - Binary
    - Simpoint
    - Checkpoint

4. Renamed:

    - `["name"]` to `["id"]`
    - `["type"]` to `["category"]`
    - `["url"]` to `["download_url"]`

5. Added the following fields:

    - Name of the Resource = `["name"]`
    - gem5 Version compatibility = `["gem5_version"]`
    - number of downloads = `["downloads"]`
    - links to example code = `["example_url"]`
    - links to documentation = `["documentation_url"]`
    - GitHub URL = `["github_url"]`

## Stuff To Do / Resolve

1. What is vega-mmio?
2. Add 'Test' to `['type']`
