import logging
import os
import tarfile
import yaml
import psutil


LOGGER = logging.getLogger(__name__)
logging.basicConfig(encoding='utf-8', level=logging.DEBUG)


def get_memory_usage():
    """Displays current memory usage."""
    pid = psutil.Process()

    memory_info = pid.memory_info()

    return memory_info.rss / (1024 * 1024)  # Convert to MB


def extract_metabase_metadata(file_data):
    """Extracts Metabase metadata from a single Metabase Serializtion export YAML file dict."""
    MB_SERIALIZATION_FILE_YAML_ATTRIBUTES = (
        ('type', None),
        ('entity_id', None),
        ('name', None),
        ('display_name', None),
        ('archived', None),  # TODO: archive or archived? and how will change in v1.50.x when move to trash instead of archive?
        # ('active', None),
        # ('created_at', None),
    )

    KNOWN_TYPES = (
        '',
    )

    metadata = {}

    serdes_metadata = None if file_data.get('serdes/meta', None) is None else file_data.get('serdes/meta', None)[0]

    if file_data.get('type', None) not in KNOWN_TYPES:
        LOGGER.warning(f'Found object of unknown type: {file_data}')
        LOGGER.warning(f'.. "type": {file_data.get('type', None)}')
        LOGGER.warning(f'.. "serdes/metadata": {serdes_metadata}')
        import pdb; pdb.set_trace();  # TODO: REMOVE after debugging

    for attribute_name, default_value in MB_SERIALIZATION_FILE_YAML_ATTRIBUTES:
        metadata[attribute_name] = file_data.get(attribute_name, default_value)

    return metadata


def parse_yaml(file_object):
    """Return parsed YAML as dict from a file_object."""

    return yaml.safe_load(file_object)


def load_serialization_tgz_contents(tgz_path):
    """Returns an iterative of tuples like (member_name, file_type, file_data,).
        - `file_data` will return None if type is directory or file is empty.
    """

    with tarfile.open(tgz_path, 'r:gz') as tar_file:
        for member in tar_file.getmembers():
            try:
                file_type = 'file' if member.isfile() else ('dir' if member.isdir() else 'not file or dir')
                file_data = None if file_type is not 'file' else parse_yaml(tar_file.extractfile(member.name))

                yield (
                    member.name,
                    None,
                    file_type,
                    file_data,
                )
            except yaml.constructor.ConstructorError as error:
                yield (
                    member.name,
                    {  #parsing_message
                        'message': 'Error parsing YAML.',
                        'message_type': 'Non-fatal exception (file skipped).',
                        'message_details': error,
                    },
                    file_type,
                    None,
                )


def serialization_export_loader(serialization_file_path):
    """Loads Metabase Serialization file."""
    LOGGER.info('Attempting to load Metabase Serialization export tgz file.')

    contents = []

    for member_name, parsing_message, file_type, file_data in load_serialization_tgz_contents(serialization_file_path):
        LOGGER.debug(f'Current Memory Usage: {get_memory_usage():.2f} MB')
        LOGGER.info(f'Found object: {member_name}')
        LOGGER.debug(f'.. File type: {file_type}')
        LOGGER.debug(f'.. File data: {file_data}')

        metadata = None

        if file_type is 'file':
            if not (member_name.endswith('.yml') or member_name.endswith('.yaml')):
                LOGGER.info(f'Skipping non-YAML file: {member_name}')

                continue

            if parsing_message is None:
                serdes_metadata = None if file_data.get('serdes/meta', None) is None else file_data.get('serdes/meta', None)[0]

                if serdes_metadata is not None:
                    serdes_metadata_model = serdes_metadata.get('model', None)

                skip_metadata_extraction_conditions = (
                    'settings.yaml' in member_name or 'settings.yml' in member_name,  # Skip settings.yaml
                    # '/snippets/' in member_name,  # Skip snippets
                    # serdes_metadata_model is 'Collection',
                )

                if any(skip_metadata_extraction_conditions):
                    LOGGER.debug(f'No metadata to extract for : {member_name}')

                    continue

                metadata = extract_metabase_metadata(file_data)
            else:
                LOGGER.warning(f"{parsing_message['message']}")
                LOGGER.warning('.. Details:')
                LOGGER.warning(f"{parsing_message['message_type']}")
                LOGGER.warning(parsing_message['message_details'])

            LOGGER.info(f'.. Metadata: {metadata}')

        contents.append((
            member_name,
            parsing_message,
            file_type,
            metadata,
            file_data,
        ))

    return contents


def cli(export_path, change_list_path, output_path=os.getcwd()):
    """Metabase Serialization CLI entry point."""
    LOGGER.info(f'.. Export Path: {export_path}')
    export_data = serialization_export_loader(export_path)

    LOGGER.info(f'.. Change List Path: {change_list_path}')
    LOGGER.info(f'.. Output Path: {output_path}')


# def list_path_contents(path):
#     """Returns an iterative of tuples like (root, folder, file) for a given path."""
#
#     for root, folders, files in os.walk(path):
#         for file in files:
#             yield (root, None, file)
#
#         for folder in folders:
#             yield (root, folder, None)
#
#
