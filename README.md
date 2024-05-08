# metabase-serialization-py: CLI to modify Metabase Serialization Exports/Imports

## Dependencies
- Python
- [PDM](https://pdm-project.org/en/stable/)
- [Python Fire](https://google.github.io/python-fire/)


## Installation

```bash
$ pdm install
```



## TODO
- export serialization files via API curl from localhost test environment
- Python script open and load to memory single serialization file from given `EXPORT_PATH`
- Python script open and load to memory all serialization files in given `EXPORT_PATH`
  - list directory contents
  - load each file
- Python script create output file (check for overwrite with --force)
- Python script create output folders (check for overwrite with --force)
- Python script to load `change_list_path.yml` file with list of changes to be made like:
```yaml
replace:
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

- Python script to apply `change_list_path.yml` changes to given `EXPORT_PATH`

