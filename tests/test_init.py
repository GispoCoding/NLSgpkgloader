import configparser
from pathlib import Path


def test_metadata_has_required_keys():
    """
    http://github.com/qgis/qgis-django/blob/master/qgis-app/plugins/validator.py
    """

    metadata_path = Path("nlsgpkgloader/metadata.txt")

    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(metadata_path)

    assert parser.has_section("general"), 'Metadata.txt has no section "[general]"'

    metadata_keys = {key for key, _ in parser.items("general")}
    required_metadata = [
        "name",
        "description",
        "version",
        "qgisMinimumVersion",
        "email",
        "author",
    ]
    for required in required_metadata:
        assert required in metadata_keys
