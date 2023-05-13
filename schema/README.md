# gem5 Vision Database Schema

This schema defines the structure and validation rules for storing gem5 Resources data in the gem5 Vision Database.

## Description

The gem5 Vision Database Schema provides a standardized format for storing and validating various types of resources in the gem5 ecosystem. It defines properties such as category, author, description, source URL, license, tags, example usage, gem5 versions compatibility, and more.

## Important Information

The schema contains the following key components:

- **Properties**: Defines the attributes of a Resource, such as category, author, code examples, description, source URL, ID, license, tags, example usage, gem5 versions compatibility, resource version, size, URL, and more.
- **Required Fields**: Specifies the fields that are mandatory for every resource, including `author`, `category`, `description`, `ID`, `license`, `source_url`, `tags`, `example_usage`, `gem5_versions`, and `resource_version`.
- **oneOf**: Provides a list of possible Resource definitions that can be used, including `diskimage`, `binary`, `kernel`, `checkpoint`, `git`, `bootloader`, `file`, `directory`, `simpoint`, `simpoint-directory`, `resource`, `looppoint-pinpoint-csv`, `looppoint-json`, and `workload`.
- **Definitions**: Defines specific resource types with their respective properties and dependencies. The resource types include `architecture`, `abstract-file`, `abstract-workload`, `abstract-binary`, `abstract-directory`, `abstract-simpoint`, `file`, `workload`, `diskimage`, `binary`, `kernel`, `checkpoint`, `git`, `bootloader`, `directory`, `simpoint`, `simpoint-directory`, `resource`, `looppoint-pinpoint-csv`, and `looppoint-json`. A Resource must adhere to at least one of these definitions.

Please refer to the schema for detailed information about the structure and properties of each resource type.

Note: This README.md file provides an overview of the gem5 Vision Database Schema. For more detailed information, refer to the [schema](./schema.json) itself.