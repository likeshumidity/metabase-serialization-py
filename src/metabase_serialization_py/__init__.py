from datetime import datetime
import logging
import os
import hashlib

from metabase_serialization_py.metabase_export import MetabaseExport


LOGGER = logging.getLogger(__name__)
logging.basicConfig(encoding='utf-8', level=logging.DEBUG)
# TODO: add CLI parameter for logging level

TIMESTAMP = datetime.now().isoformat().replace('-', '').replace('.', '').replace('T', '').replace(':', '')


# TODOs
# TODO: replace references to "member" with something more clear like "archive member" or "exported object"


def create_change_list(change_list_file_path, metabase_export):
    """Creates list of changes based on change_list_file and dependencies."""
    change_list = ()

    with open (change_list_file_path, 'r') as change_list_file:
        change_list = parse_yaml(change_list_file)

    # TODO: create entity_id index from metabase_export
    # TODO: for each change in change list
    # TODO: traverse tree of change and dependent changes
    # TODO: validate that related entity keys exist

    import pdb; pdb.set_trace();  # TODO: REMOVE after debugging

    return change_list


def cli(export_path, change_list_file_path, output_path=os.getcwd()):
    """Metabase Serialization CLI entry point."""

    LOGGER.info(f'.. Export Path: {export_path}')
    LOGGER.info(f'.. Change List Path: {change_list_file_path}')
    LOGGER.info(f'.. Output Path: {output_path}')

    if not os.path.isdir(output_path):
        LOGGER.error(f'Specified output path not found: "{output_path}". Please create the directory or update the --output flag.')
        exit(1)

    metabase_export = MetabaseExport(export_path)

    change_list = create_change_list(change_list_file_path, metabase_export)

    import pdb; pdb.set_trace();  # TODO: REMOVE after debugging

    # process_changes(metabse_export, change_list, output_path)
