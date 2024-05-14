# metabase-serialization-py: CLI to modify Metabase Serialization Exports/Imports

## Dependencies
- Python
- [PDM](https://pdm-project.org/en/stable/)
- [Python Fire](https://google.github.io/python-fire/)


## Installation

```bash
$ pdm install
```


## Usage

```bash
$ ./pdm run metabase-serialization-cli.py ORIGINAL_EXPORT_ALL_COLLECTIONS.tgz ./OUTPUT_TARGET_PATH change_list.yml
# OR create virtual environment, and run inside (re: bash/csh/zsh)
$ ./pdm venv create serialization-environment
$ eval $(pdm venv activate serialization-environment)
(serialization-environment) $ ./metabase-serialization-cli.py ORIGINAL_EXPORT_ALL_COLLECTIONS.tgz ./OUTPUT_TARGET_PATH change_list.yml
```

- `ORIGINAL_EXPORT_ALL_COLLECTIONS.tgz`
  - MUST EXPORT ALL COLLECTIONS.
  - Failure to do so may cause naming collisions or overwrite your data when you import the results.
- `OUTPUT_TARGET_PATH`
  - Directory must exist.
  - Defaults to current working directory.
  - New sub-directory created with each run with a timestamp suffix.
- `change_list.yml`
  - Follows `change_list.yml` format described below.


### Format of `change_list.yml`

```yaml
# change_list.yml
changes:
  # use a `create` clause if the target collection does not exist
  # you can leave `to` clauses blank if you want them to be generated
  # a fatal error will occur if there are any naming collisions detected
  - create: # checks for naming collisions and does not overwrite
      database:
        from:
          name: name_12345
        to:
          name: name_56789
      collection:
        from:
          entity_id: collection_entity_id_1234
        to:
          entity_id: collection_entity_id_5678
  # use a `replace` clause if the target collection does not exist
  # ?? existing contents in the collection will be unaltered unless they are included in the export and change list
  # every object`to` must be specified
  # a warning will occur if there are any naming collisions detected in the `to` clause
  - replace: # warns on naming collisions but does overwrite
      database:
        from:
          name: name_12345
        to:
          name: name_56789
      collection:
        from:
          entity_id: collection_entity_id_1234
        to:
          entity_id: collection_entity_id_5678
```


### Process Draft

1. Export all collections
1. Copy export
1. Process changes
	1. Untar/gzip
	1. Verify input files
		1. tar/gzip export
		1. change_list.yml
		1. Target output folder
	1. Index all entity_ids and names
	1. Find relevant files
		1. Examine the change list and trace dependencies
			1. Dependencies found to STDOUT
			1. Trace dependencies
				1. Start at highest level
					- Dashboard
					- Question/Model
						- Can have multiple levels of nesting
					- Model
					- Field
					- Table
					- Schema
					- Database
		1. Exceptions if not found
		1. Update files
			1. Update file sections
			1. Find relevant sections
				1. Exceptions if not found
				1. Update section
				1. Save new file/overwrite


## TODO
- export serialization files via API curl from localhost test environment
- Python script open and load to memory single serialization file from given `EXPORT_PATH`
- Python script open and load to memory all serialization files in given `EXPORT_PATH`
  - list directory contents
  - load each file
- Python script create output file (check for overwrite with --force)
- Python script create output folders (check for overwrite with --force)
- Python script to load `change_list_path.yml` file with list of changes to be made like:
- Python script to apply `change_list_path.yml` changes to given `EXPORT_PATH`


## Resources
- [Metabase Serialization Docs](https://www.metabase.com/docs/latest/installation-and-operation/serialization#how-import-works)
- 

