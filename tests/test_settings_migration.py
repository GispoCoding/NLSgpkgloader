import pytest
from qgis.core import QgsSettings

from nlsgpkgloader.nls_geopackage_loader import (
    OLD_SETTINGS_GROUP_NAME,
    NLSGeoPackageLoader,
)
from nlsgpkgloader.qgis_plugin_tools.tools.settings import get_setting


@pytest.fixture
def old_settings():
    settings = QgsSettings()
    settings.beginGroup(OLD_SETTINGS_GROUP_NAME)
    settings.setValue("setting1", "value1")
    settings.setValue("setting2", True)
    settings.endGroup()

    yield settings


def test_settings_migration(old_settings):
    NLSGeoPackageLoader._migrate_settings()

    assert OLD_SETTINGS_GROUP_NAME not in old_settings.childGroups()

    assert get_setting("setting1") == "value1"
    assert get_setting("setting2", typehint=bool) is True
