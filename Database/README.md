# Database GitHub Actions
The two subdirectories herein are monitored by GitHub Actions to support automated migrations. The file structure and naming conventions are critical to ensure the workflow function properly.  

# Snowflake
The workflows have already been configured for our specific use cases, as well as the folder structure. However, the name of the files must be adhered to depending on the type of SQL change. Additional documentation can be found here: [Snowflake-Labs/schemachange ](https://github.com/Snowflake-Labs/schemachange).

Each script must begin with the following code snippet, the schema is passed from the workflow execution file:

> ` USE SCHEMA {{ schema }} `

## Versioned Script Naming

The script name must follow this pattern (taken directtly from documentation above):
  - Prefix: The letter 'V' for versioned change
  - Version: A unique version number with dots or underscores separating as many number parts as you like
  - Separator: __ (two underscores)
  - Description: An arbitrary description with words separated by underscores or spaces (can not include two underscores)
  - Suffix: .sql or .sql.jinja

For example: 
  - V1__Table_Name.sql
  - V1.1__TableName.sql
  - V1_1__Table_Name_Here.sql

Version number must stay consistent within the repository. The recomended approach would be V1__, V2__, V3__. The version numbers also must be unique, the workflow will throw an error if it finds a duplicate.

## Repeatable Script Naming

The script name must follow this pattern: 
  - Prefix: The letter 'R'
  - Separator: __ (two underscores)
  - Description: An arbitrary description with words separated by underscores or spaces (can not include two underscores)
  - Suffix: .sql or .sql.jinja

For example:
  -  R__Table_Name.sql
  -  R__TableName.sql
  -  R__Table_Name_Here.sql

Repeatable change scripts are applied each time the workflow is triggered, if there is a change in the file. They are best used for code that needs to be run in it's entirety everytime. They are always executed after all pending versioned scripts have been executed, and they are executed alphabetcially based on their description.

## Always Script Naming
The script name must follow this pattern: 
  - Prefix: The letter 'A'
  - Separator: __ (two underscores)
  - Description: An arbitrary description with words separated by underscores or spaces (can not include two underscores)
  - Suffix: .sql or .sql.jinja

For example:
  -  A__Table_Name.sql
  -  A__TableName.sql
  -  A__Table_Name_Here.sql

Always change scripts are applied each time the workflow is triggered, regardless of a change detected in the file. They are always executed last.

# Azure SQL
The workflows have already been configured for our specific use cases, as well as the folder structure. Please ensure DDL or DML scripts are in their respective database and type subdirectories. Additional documentation can be found here: [DbUp](https://dbup.readthedocs.io/en/latest/).
