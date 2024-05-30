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
# See below examples for command prefixes  where `...` is shown.
$ ... metabase-serialization-cli.py ORIGINAL_EXPORT_ALL_COLLECTIONS.tgz change_list.yml [--output_path ./OUTPUT_TARGET_PATH]
```

- `ORIGINAL_EXPORT_ALL_COLLECTIONS.tgz`
  - MUST EXPORT ALL COLLECTIONS.
  - Failure to do so may cause naming collisions or overwrite your data when you import the results.
- `change_list.yml`
  - Follows `change_list.yml` format described below.
- `OUTPUT_TARGET_PATH` _optional_
  - Defaults to current working directory.
  - Directory must exist.
  - New sub-directory created with each run with a timestamp suffix.


### Examples Usage
```bash
# Using pdm run
$ pdm run metabase-serialization-cli.py export-12345.tgz change_list.yml --output_path ./output

# Create, enter, and run inside a virtual environment (re: bash/csh/zsh)
$ pdm venv create serialization-environment
$ eval $(pdm venv activate serialization-environment)
(serialization-environment) $ ./src/metabase-serialization-cli.py export-12345.tgz change_list.yml --output_path ./output
```


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
  - archive:
      - collection: collection_entity_id_12345
      - question: question_entity_id_12345
```


### [WIP] Process

1. [x] Export all collections via API to tgz file
1. Process changes
	1. [x] Untar/gzip
	1. [x] Verify input files exist
		1. [x] tar/gzip export
		1. [x] change_list.yml
		1. [x] Target output folder
	1. Index all entity_ids and names
	1. Find relevant files based on change_list.yml
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
- Add a flag to the change_list.yml to clear the contents (archive/move to trash) of the destination of contents prior to changes


## Notes

- Deletes/Archives/Moves to Trash
  - Objects cannot be deleted
  - Objects can be archived (in Metabase v49 and lower)
  - Objects can be moved to trash (in Metabase v50 and higher)
  - If a source object is archived/moved to trash, it will be archived/moved to trash in the target (or created in the archive/trash if it does not exist)
  - If a source object is created on the target and does not exist in the source, it will be unaffected (assuming there are no identity collisions)
  - Archiving objects just changes the `archived` flag to `true`, but otherwise do not alter the object

## Caveats
- Entity IDs must be unique
- Must handle nested dependencies
- Segments and Metrics
  - referred to by entity_id instead of name
  - because in Databases folder
- Filter IDs
  - unsure how handled, but don't seem to collide when share the same identifier
- Filenames ignored re: entity_ids and names
- lookout for errors on "duplicated entity_ids"
  - not sure when or why they occur


## Resources
- [Metabase Serialization Docs](https://www.metabase.com/docs/latest/installation-and-operation/serialization#how-import-works)
- 

