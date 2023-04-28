# Help

## Load Previous Session
Checks LocalStorage for a previous session, whether MongoDB or JSON, and restores the editor view for that database. 

## MongoDB
Set up editor view for MongoDB Instance. 

### Login: Enter URI
Utilize if the MongoDB connection string is known. 

#### Fields:
  - URI: [MongoDB](https://www.mongodb.com/docs/manual/reference/connection-string/)

#### Additional Fields:
  - Collection: Specify collection in MongoDB instance to retrieve   
  - Database: Specify database in MongoDB instance to retrieve
  - Alias: Optional. Provide a display alias to show on editor view instead of URI

### Login: Generate URI
Provides method to generate MongoDB URI connection string if it is not known.

#### Fields:
  
  - Connection: Specify connection mode, Standard or DNS Seed List, as defined by [MongoDB](https://www.mongodb.com/docs/manual/reference/connection-string/)
  - Username: Optional.
  - Password: Optional.
  - Host: Specify host where instance is running 
  - Retry Writes: Allow MongoDB to retry a write to database once if they fail the first time 
  - Write Concern: Determines level of acknowledgement required from database for write operations, specifies how many nodes must acknowledge the operation before it is considered sucessful. (Currently set to majority)  
  - Options: Optional. Additional parameters that can be set when connecting to the instance

#### Additional Fields: 
  - Collection: Specify collection in MongoDB instance to retrieve   
  - Database: Specify database in MongoDB instance to retrieve
  - Alias: Optional field to provide a display alias to show on editor view instead of URI

## JSON
Set up editor view for JSON file. Can Specify a URL to a remote JSON file to be imported
or select a local JSON file.


## Editor
Page containing Monaco VSCode Diff Editor to allow editing of database entries. 

### Database Actions:
Actions that can be performed on database current in use.

- Search: Search for resource in database with exact Resource ID
- Version: Dropdown that allows for selection of a particular resource version of resource currently in view
- Category: Specify category of resource to viewed as defined by schema
- View Schema for Database: Sets view for schema for current database (read only) 
- Change Database: Reset current editor to change to a different database 

### Editing Actions:
Actions that can be performed on resource currently in view.

- Update: Update current resource with changes made  
- Add:
- Delete: Permanently Delete current resource  
- Add new Version: Add a new version to resource version field of resource  
