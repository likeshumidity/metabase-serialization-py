"""Helpers for working with Metabase Serialization Exports."""
import logging
import tarfile

from yaml.constructor import ConstructorError as ConstructorError_yaml

from metabase_serialization_py.memory_usage import get_memory_usage
from metabase_serialization_py.hashing import generate_hash_for_object
from metabase_serialization_py.yaml import parse_yaml, Loader

LOGGER = logging.getLogger(__name__)
logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

# TODOs
# TODO: replace references to "member" with something more clear like "archive member" or "exported object"
# TODO: ignore archived content, take CLI flag to un-ignore archived content
# TODO: check serdes/meta.id == file_data['entity_id']
# TODO: process changes in order of precedence (delete first, then rename, then move, then copy, etc.)
# TODO: fix assumption of only one item in list re: serdes/meta


# Disables '=' loader
Loader.yaml_implicit_resolvers.pop('=')


def extract_metabase_metadata(file_data):
    """Extracts Metabase metadata from a single Metabase Serializtion export YAML file dict."""
    MB_SERIALIZATION_FILE_YAML_ATTRIBUTES = (
        ('entity_id', None),
        ('name', None),
        ('display_name', None),
        ('archived', None),  # TODO: archive or archived? and how will change in v1.50.x when move to trash instead of archive?
        ('entity_type', None),
        # ('active', None),
        # ('created_at', None),
        # ('serdes/meta', None),
        # ('type', None),
    )

    SERDES_META_MODELS = (
        'Action',
        'Card',
        'Collection',
        'Dashboard',
        'Database',
        'Field',
        'Metric',
        'NativeQuerySnippet',
        'Segment',
        'Table',
        'Timeline',
    )

    metadata = {}

    detected_serdes_meta_model = file_data.get('serdes/meta', [{}])[-1].get('model', None)

    serdes_metadata = None if file_data.get('serdes/meta', None) is None else file_data.get('serdes/meta', None)[-1]

    if detected_serdes_meta_model not in SERDES_META_MODELS:
        LOGGER.warning(f'Found object of unknown type: {file_data}')
        LOGGER.warning(f'.. "type": {file_data.get('type', None)}')
        LOGGER.warning(f'.. "serdes/metadata": {serdes_metadata}')

        import pdb; pdb.set_trace();  # TODO: REMOVE after debugging


    metadata['serdes/meta.model'] = detected_serdes_meta_model

    if len(file_data.get('serdes/meta', [{}])) > 1:
        metadata['serdes/meta.id'] = tuple([meta.get('id', None) for meta in file_data.get('serdes/meta', [{}])])
    else:
        metadata['serdes/meta.id'] = file_data.get('serdes/meta', [{}])[0].get('id', None)

    if metadata['serdes/meta.id'] is None or (not isinstance(metadata['serdes/meta.id'], str) and not isinstance(metadata['serdes/meta.id'], tuple)):
        import pdb; pdb.set_trace();  # TODO: REMOVE after debugging

    for attribute_name, default_value in MB_SERIALIZATION_FILE_YAML_ATTRIBUTES:
        metadata[attribute_name] = file_data.get(attribute_name, default_value)

    return metadata


def load_serialization_tgz_contents(tgz_path):
    """Returns an iterative of tuples like (member_name, file_type, file_data,).
        - `file_data` will return None if type is directory or file is empty.
    """

    with tarfile.open(tgz_path, 'r:gz') as tar_file:
        for member in tar_file.getmembers():
            try:
                file_type = 'file' if member.isfile() else ('dir' if member.isdir() else 'not file or dir')
                file_data = None if file_type != 'file' else parse_yaml(tar_file.extractfile(member.name), Loader)

                yield (
                    member.name,
                    None,
                    file_type,
                    file_data,
                )
            except ConstructorError_yaml as error:
                # import pdb; pdb.set_trace();  # TODO: REMOVE after debugging
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

        if file_type == 'file':
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

            LOGGER.debug(f'.. Metadata: {metadata}')

        contents.append((
            member_name,
            parsing_message,
            file_type,
            metadata,
            file_data,
        ))

    return tuple(contents)


class MetabaseExport:
    index_by_id = {}
    data_index_by_path = {}

    def __init__(self, export_path):
        LOGGER.debug(f'Current Memory Usage: {get_memory_usage():.2f} MB')
        self.export_data = serialization_export_loader(export_path)

        self.files_skipped = tuple([(member_name, parsing_message,) for member_name, parsing_message, file_type, metadata, file_data in self.export_data if parsing_message is not None])

        if self.files_skipped:
            LOGGER.warning('Could not parse the following files in export.')

            for file_skipped_name, message in files_skipped:
                LOGGER.warning(f'.. {file_skipped_name}')
                LOGGER.warning(f'.. {message}')

        self.create_entity_index_by_id()
        LOGGER.debug(f'Current Memory Usage: {get_memory_usage():.2f} MB')

    def __getattr__(self, search_name):
        """Looks up value of either entity_id or tuple of data path."""

        if isinstance(search_name, tuple):
            return self.data_index_by_path[search_name]

        return self.index_by_id[search_name]

    def create_entity_index_by_id(self):
        """Creates index of entity ids, references, and reference paths from export_data."""

        for i, (member_name, parsing_message, file_type, metadata, file_data) in enumerate(self.export_data):
            if file_type != 'file':
                # Only review files (skip directories, etc.).

                continue

            if metadata is None:
                LOGGER.warning(f'Found member with empty metadata: {member_name}')

                import pdb; pdb.set_trace();  # TODO: REMOVE after debugging

            serdes_meta_id = metadata['serdes/meta.id']

            self.add_entity_to_index_by_id(serdes_meta_id, i, member_name)

            # Find external references and add to index
            self.update_entity_references(file_data, member_name, serdes_meta_id, metadata)

        # import pdb; pdb.set_trace();  # TODO: REMOVE after debugging

    def add_entity_to_index_by_id(self,  serdes_meta_id, i, member_name):
        """Create entity entry in index by id."""

        if serdes_meta_id is None:
            # Generate unique entity_id if none exists.
            LOGGER.warning(f'Found object with no serdes/meta.id: {member_name}. Generating unique id based on file name and path.')
            generated_hash = 'mb_' + generate_hash_for_object(member_name)
            LOGGER.warning(f'.. Using {generated_hash} as entity_id.')

            import pdb; pdb.set_trace();  # TODO: REMOVE after debugging

        if serdes_meta_id not in self.index_by_id:
            self.index_by_id[serdes_meta_id] = {}

        if serdes_meta_id in self.index_by_id and 'i' in self.index_by_id[serdes_meta_id] and self.index_by_id[serdes_meta_id]['i'] != i:
            # Check for entity ID duplicates.
            LOGGER.warning(f'Found existing reference to {member_name} at index {i}. Potential duplicate entity key.')

            import pdb; pdb.set_trace();  # TODO: REMOVE after debugging

        self.index_by_id[serdes_meta_id]['i'] = i
        self.index_by_id[serdes_meta_id]['filename'] = member_name

        if 'references' not in self.index_by_id[serdes_meta_id]:
            self.index_by_id[serdes_meta_id]['references'] = []

    def update_entity_references_collection(self, file_data, serdes_meta_id, member_name):
        """Updates Collection entity indices by adding external references found in file_data to referenced entities."""

        # Collections only have parent_id references or no references if at the top level.

        if file_data['parent_id'] is not None:
            self.add_entity_reference_to_index_by_id(file_data['parent_id'], 'Collection', 'parent_id', serdes_meta_id, member_name)

    def update_entity_references_timeline(self, file_data, serdes_meta_id, member_name):
        """Updates Timeline entity indices by adding external references found in file_data to referenced entities."""

        if file_data['collection_id']:
            self.add_entity_reference_to_index_by_id(file_data['collection_id'], 'Timeline', 'collection_id', serdes_meta_id, member_name)

    def update_entity_references_action(self, file_data, serdes_meta_id, member_name):
        """Updates Action entity indices by adding external references found in file_data to referenced entities."""

        if file_data['model_id']:
            self.add_entity_reference_to_index_by_id(file_data['model_id'], 'Action', 'model_id', serdes_meta_id, member_name)

    def update_entity_references_field(self, file_data, serdes_meta_id, member_name):
        """Updates Field entity indices by adding external references found in file_data to referenced entities."""

        if file_data['table_id']:
            self.add_entity_reference_to_data_index_by_path(tuple(file_data['table_id']), 'Field', 'table_id', serdes_meta_id, member_name)

        for i, serdes_meta in enumerate(file_data['serdes/meta'][:-1]):
            path_reference = tuple([meta['id'] for meta in file_data['serdes/meta']])[:i + 1]
            # TODO: may need to refactor to be .path_reference instead of .id
            self.add_entity_reference_to_data_index_by_path(path_reference, 'Field', f'serdes/meta[{i}].id', serdes_meta_id, member_name)

    def update_entity_references_table(self, file_data, serdes_meta_id, member_name):
        """Updates Table entity indices by adding external references found in file_data to referenced entities."""

        if file_data['db_id']:
            self.add_entity_reference_to_data_index_by_path(tuple(file_data['db_id']), 'Table', 'db_id', serdes_meta_id, member_name)

        for i, serdes_meta in enumerate(file_data['serdes/meta'][:-1]):
            path_reference = tuple([meta['id'] for meta in file_data['serdes/meta']])[:i + 1]
            # TODO: may need to refactor to be .path_reference instead of .id
            self.add_entity_reference_to_data_index_by_path(path_reference, 'Table', f'serdes/meta[{i}].id', serdes_meta_id, member_name)

    def update_entity_references_metric(self, file_data, serdes_meta_id, member_name):
        """Updates Metric entity indices by adding external references found in file_data to referenced entities."""


        if file_data['table_id']:
            self.add_entity_reference_to_data_index_by_path(tuple(file_data['table_id']), 'Metric', 'table_id', serdes_meta_id, member_name)
        else:
            self.add_entity_reference_to_data_index_by_path(tuple(file_data['definition']['source-table']), 'Metric', 'definition.source-table', serdes_meta_id, member_name)

    def update_entity_references_segment(self, file_data, serdes_meta_id, member_name):
        """Updates Segment entity indices by adding external references found in file_data to referenced entities."""

        if file_data['table_id']:
            self.add_entity_reference_to_data_index_by_path(tuple(file_data['table_id']), 'Segment', 'table_id', serdes_meta_id, member_name)
        else:
            self.add_entity_reference_to_data_index_by_path(tuple(file_data['definition']['source-table']), 'Segment', 'definition.source-table', serdes_meta_id, member_name)

    def update_entity_references_dashboard(self, file_data, serdes_meta_id, member_name):
        """Updates Dashboard entity indices by adding external references found in file_data to referenced entities."""

        if file_data['collection_id']:
            self.add_entity_reference_to_index_by_id(file_data['collection_id'], 'Dashboard', 'collection_id', serdes_meta_id, member_name)

        # Dashboard entities with content other than text/headers should have external references in the dashcards array.

        for i, dashcard in enumerate(file_data['dashcards']):
            self.add_entity_reference_to_index_by_id(dashcard['entity_id'], 'Dashboard', f'dashboard.dashcards[{i}].entity_id', serdes_meta_id, member_name)

            # Skip virtual cards like headings and text blocks since they don't have a 'card_id' in the 'dashcard' statement.

            if  'visualization_settings' not in dashcard or 'virtual_card' not in dashcard['visualization_settings']:
                self.add_entity_reference_to_index_by_id(dashcard['card_id'], 'Dashboard', f'dashboard.dashcards[{i}].card_id', serdes_meta_id, member_name)

            for j, parameter_mappings in enumerate(dashcard['parameter_mappings']):
                if 'card_id' in parameter_mappings:
                    self.add_entity_reference_to_index_by_id(
                        parameter_mappings['card_id'],
                        'Dashboard',
                        f'dashboard.dashcards[{i}].parameter_mappings[{j}].card_id',
                        serdes_meta_id,
                        member_name
                    )

                if 'action_id' in parameter_mappings:
                    self.add_entity_reference_to_index_by_id(
                        parameter_mappings['action_id'],
                        'Dashboard',
                        f'dashboard.dashcards[{i}].parameter_mappings[{j}].action_id',
                        serdes_meta_id,
                        member_name
                    )

    def update_source_table_reference_to_index(self, source_table_reference, entity_model, relationship, serdes_meta_id, member_name):
        """Adds source-table reference to either data_index_by_path or index_by_id depending on whether the source-table
            reference is to a data path list or an entity_id."""

        if isinstance(source_table_reference, list):
            add_entity_reference_func = self.add_entity_reference_to_data_index_by_path
            source_table_reference_for_func = tuple(source_table_reference)
        else:
            add_entity_reference_func = self.add_entity_reference_to_index_by_id
            source_table_reference_for_func = source_table_reference

        add_entity_reference_func(
            source_table_reference_for_func,
            entity_model,
            relationship,
            serdes_meta_id,
            member_name
        )

    def update_entity_references_card(self, file_data, serdes_meta_id, member_name):
        """Updates Card entity indices by adding external references found in file_data to referenced entities."""

        if file_data['collection_id']:
            self.add_entity_reference_to_index_by_id(file_data['collection_id'], 'Card', 'collection_id', serdes_meta_id, member_name)

        self.add_entity_reference_to_data_index_by_path((file_data['database_id'], ), 'Card', 'database_id', serdes_meta_id, member_name)

        if file_data['table_id']:
            # All non-native queries not based on other queries/cards should have a table_id.
            self.add_entity_reference_to_data_index_by_path(tuple(file_data['table_id']), 'Card', 'table_id', serdes_meta_id, member_name)

        # TODO: handle recursively from tuple of paths and parameters

        # TODO: Capture dataset_query ... - data_index_by_path ANY MORE??
        # TODO: Capture dataset_query ... - index_by_id ANY MORE??

        if 'dataset_query' in file_data:
            # Capture dataset_query.database - data_index_by_path

            if 'database' in file_data['dataset_query']:
                self.add_entity_reference_to_data_index_by_path(
                    (file_data['dataset_query']['database'], ),
                    'Card',
                    'dataset_query.database',
                    serdes_meta_id,
                    member_name
                )
            # Capture dataset_query.query.source-table - data_index_by_path or index_by_id depending on reference type

            if 'query' in file_data['dataset_query']:
                if 'source-table' in file_data['dataset_query']['query']:
                    self.update_source_table_reference_to_index(
                        file_data['dataset_query']['query']['source-table'],
                        'Card',
                        'dataset_query.query.source-table',
                        serdes_meta_id,
                        member_name
                    )

                if 'joins' in file_data['dataset_query']['query']:
                    for i, join_clause in enumerate(file_data['dataset_query']['query']['joins']):
                        # Capture dataset_query.query.joins[].source-table - data_index_by_path

                        if 'source-table' in join_clause:
                            self.update_source_table_reference_to_index(
                                file_data['dataset_query']['query']['joins'][i]['source-table'],
                                'Card',
                                f'dataset_query.query.joins[{i}].source-table',
                                serdes_meta_id,
                                member_name
                            )

                        # Capture dataset_query.query.joins[].condition[][1] - data_index_by_path

                        if 'condition' in join_clause:
                            for j, condition_clause in enumerate(file_data['dataset_query']['query']['joins'][i]['condition']):
                                if isinstance(condition_clause, list) and condition_clause[0] == 'field':
                                    self.add_entity_reference_to_data_index_by_path(
                                        tuple(file_data['dataset_query']['query']['joins'][i]['condition'][j][1]),
                                        'Card',
                                        f'dataset_query.query.joins[{i}].condition[{j}][1]',
                                        serdes_meta_id,
                                        member_name
                                    )

        # TODO: Capture result_metadata - data_index_by_path

        if 'results_metadata' in file_data:
            for i, result_metadata_clause in enumerate(file_data['result_metadata']):
                # Capture result_metadata[].id - data_index_by_path

                if 'id' in result_metadata_clause:
                    self.add_entity_reference_to_data_index_by_path(
                        tuple(file_data['dataset_query']['result_metadata'][i]['id']),
                        'Card',
                        f'dataset_query.result_metadata[{i}].id',
                        serdes_meta_id,
                        member_name
                    )

                # Capture result_metadata[].field_ref[1] - data_index_by_path

                if 'field_ref' in result_metadata_clause and isinstance(result_metadata_clause['field_ref'], list) and result_metadata_clause['field_ref'][0] == 'field':
                    self.add_entity_reference_to_data_index_by_path(
                        tuple(file_data['dataset_query']['result_metadata'][i]['field_ref'][1]),
                        'Card',
                        f'dataset_query.result_metadata[{i}].field_ref[1]',
                        serdes_meta_id,
                        member_name
                    )

        # TODO: embedding_params
        # TODO: parameter_mappings
        # TODO: visualization_settings

    def update_entity_references(self, file_data, member_name, serdes_meta_id, metadata):
        """Updates entity index by id adding external references found in file_data to referenced entities."""

        # TODO: refactor all of these `self.update_entity_references_xyz` methods, lots of repeated code
        ENTITY_MODELS = {
            'Collection': self.update_entity_references_collection,
            'Card': self.update_entity_references_card,
            'Dashboard': self.update_entity_references_dashboard,
            'Timeline': self.update_entity_references_timeline,
            'Action': self.update_entity_references_action,
            'Field': self.update_entity_references_field,
            'Table': self.update_entity_references_table,
            'Metric': self.update_entity_references_metric,
            'Segment': self.update_entity_references_segment,
        }

        ENTITY_MODELS_NO_EXTERNAL_REFERENCES = (
            'NativeQuerySnippet',
            'Database',
        )

        serdes_meta_model = metadata['serdes/meta.model']

        if serdes_meta_model in ENTITY_MODELS_NO_EXTERNAL_REFERENCES:
            return

        entity_model_updater = ENTITY_MODELS.get(serdes_meta_model, None)

        if entity_model_updater is None:
            import pdb; pdb.set_trace();  # TODO: REMOVE after debugging

        entity_model_updater(file_data, serdes_meta_id, member_name)

        if serdes_meta_model in ('Card', ):  # TODO: REMOVE after debugging
            # Skip entities with no external references.
            # LOGGER.debug('-------------------------------------')
            # LOGGER.debug('-------------------------------------')
            # LOGGER.debug(member_name)
            # LOGGER.debug(serdes_meta_id)
            # LOGGER.debug(metadata['serdes/meta.model'])
            # LOGGER.debug(file_data)

            if file_data['embedding_params'] or file_data['parameter_mappings']:  # TODO: REMOVE this line after debugging
                import pdb; pdb.set_trace();  # TODO: REMOVE after debugging


    def add_entity_reference_to_index_by_id(self, reference_entity_id, entity_model, relationship, serdes_meta_id, member_name):
        """Adds entity reference to entity index by id."""

        if reference_entity_id is None:
            LOGGER.error(f'Cannot add entity id reference to "{relationship}" for None in {member_name}.')
            import pdb; pdb.set_trace();  # TODO: REMOVE after debugging

        if isinstance(reference_entity_id, list):
            import pdb; pdb.set_trace();  # TODO: REMOVE after debugging

        if reference_entity_id not in self.index_by_id:
            self.index_by_id[reference_entity_id] = {
                'references': []
            }

        self.index_by_id[reference_entity_id]['references'].append((entity_model, relationship, serdes_meta_id, member_name, ))


    def add_entity_reference_to_data_index_by_path(self, reference_data_entity_path, entity_model, relationship, serdes_meta_id, member_name):
        """Adds entity data path reference to entity data index by path."""

        if reference_data_entity_path is None:
            LOGGER.error(f'Cannot add entity data path reference to "{relationship}" for None in {member_name}.')
            import pdb; pdb.set_trace();  # TODO: REMOVE after debugging

        if reference_data_entity_path not in self.data_index_by_path:
            self.data_index_by_path[reference_data_entity_path] = {
                'references': []
            }

        self.data_index_by_path[reference_data_entity_path]['references'].append((entity_model, relationship, serdes_meta_id, member_name, ))
