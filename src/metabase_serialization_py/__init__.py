import yaml


def serialization_export_loader(serialization_file_path):
    """Loads Metabase Serialization file."""
    with open(serialization_file_path, 'r') as file:
        yaml_export = yaml.safe_load(file)

        return yaml_export


def cli(export_path, output_path, change_list_path):
    """Metabase Serialization CLI entry point."""
    print(export_path)
    print(output_path)
    print(change_list_path)

    print(serialization_export_loader(export_path))
