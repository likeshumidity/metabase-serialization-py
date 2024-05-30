"""Hashing helper for Metabase Serialization."""


def generate_hash_for_object(string_data):
    """Generates MD5 hash for string_data."""

    return hashlib.md5(string_data.encode()).hexdigest()
