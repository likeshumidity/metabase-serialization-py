from datetime import datetime
import logging
import os
import hashlib

from metabase_serialization_py.metabase_export import MetabaseExport
from metabase_serialization_py.change_requests import ChangeRequests

LOGGER = logging.getLogger(__name__)
logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

TIMESTAMP = datetime.now().isoformat().replace('-', '').replace('.', '').replace('T', '').replace(':', '')

# TODOs
# TODO: replace references to "member" with something more clear like "archive member" or "exported object"
# TODO: add CLI parameter for logging level


def cli(export_path, change_list_file_path, output_path=os.getcwd()):
    """Metabase Serialization CLI entry point."""

    PARAMETERS = (
        ('Export Path', export_path, 'EXPORT_PATH argument', os.path.isfile, ),
        ('Change List Path', change_list_file_path, 'CHANGE_LIST_FILE_PATH argument', os.path.isfile, ),
        ('Output Path', output_path, '--output flag', os.path.isdir, ),
    )

    for param_title, param_value, param_instructions, param_test in PARAMETERS:
        LOGGER.info(f'{param_title}: {param_value}')

        if not param_test(param_value):
            LOGGER.error(f'.. Specified {param_title.lower()} not found: "{param_value}". Review the parameter for the {param_instructions}.')
            exit(1)


    metabase_export = MetabaseExport(export_path)

    change_requests = ChangeRequests(change_list_file_path, metabase_export)

    import pdb; pdb.set_trace();  # TODO: REMOVE after debugging

    # process_changes(metabse_export, change_requests, output_path)
