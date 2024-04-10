# Template for GO Projects
This template repository was designed as starting point for US GO projects and is equipped with GitHub Actions to automate deployments.
Project leaders are required to complete minor "tweaks" when initially cloning this repository for a new project.

1. Include the project version in the repository name, for example: "SA_PROJECT_V1". This will be the name of the directory that appears in the Databricks workspace.
2. Send an email to ADEOLA DAVID to add the repository to the ephemeral runner. The workflows will not work (aside from the init) prior to the repository being added to the ephemeral runner.
3. Define DE and DS lead(S) in the CODEOWNERS file for enhanced branch protection.
4. Snowflake workflows require a repository variable named US_SF_DATABASE.
5. GO workflows require respoisory secerets of the publishing profiles for each environment (dev, int, stg, and prod). The names of these secrets should be relected in the workflows.
6. Decision Rules workflows require the alias.py file to include the alias of the rules/rule flows you wish to migrate.

The remaining workflow secrets are not project specific, and as such are maintained at the organization level.
