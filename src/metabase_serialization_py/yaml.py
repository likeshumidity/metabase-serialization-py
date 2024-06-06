"""YAML helper for Metabase Serialization."""
import yaml


# YAML Loader updates for Metabase YAML
class Loader(yaml.SafeLoader):
    pass


def parse_yaml(file_object, Loader=Loader):
    """Return parsed YAML as dict from a file_object."""

    return yaml.load(file_object, Loader=Loader)
