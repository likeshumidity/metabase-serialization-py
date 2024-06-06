"""Change List helper for Metabase Serialization."""

# from yaml.constructor import ConstructorError as ConstructorError_yaml

from metabase_serialization_py.yaml import parse_yaml


# TODOs
# TODO: handle create card
# TODO: handle create model
# TODO: handle create dashboard
# TODO: handle create collection
# TODO: handle archive collection contents before update
# TODO: handle replace card
# TODO: handle replace model
# TODO: handle replace dashboard
# TODO: handle replace collection
# TODO: handle update database
# TODO: handle update schema
# TODO: handle update table
# TODO: handle update field
# TODO: handle update card
# TODO: handle update model
# TODO: handle update dashboard
# TODO: handle update collection


class ChangeRequests:
    change_requests = None

    def __init__(self, change_list_file_path, metabase_export):
        """Creates list of changes based on change_list_file and dependencies."""
        with open (change_list_file_path, 'r') as change_list_file:
            self.change_requests = parse_yaml(change_list_file)

        self.validate_change_requests(metabase_export)

        self.sort_change_requests_by_precedence()

        import pdb; pdb.set_trace();  # TODO: REMOVE after debugging

        return change_list

    def sort_change_requests_by_precedence(self):
        """Sorts change requests by order of precendence to avoid dependency issues."""

        import pdb; pdb.set_trace();  # TODO: REMOVE after debugging

    def validate_change_requests(self, metabase_export):
        """Validates change requests against Metabase Export."""

        for i, change_request in enumerate(self.change_requests):
            # TODO: traverse tree of change and dependent changes
            # TODO: validate that specified entity keys and path references exist
            import pdb; pdb.set_trace();  # TODO: REMOVE after debugging
