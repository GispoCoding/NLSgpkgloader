# coding=utf-8
"""Dialog test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = "mikael@gispo.fi"
__date__ = "2019-03-02"
__copyright__ = "Copyright 2019, Gispo Oy"


import pytest
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox

from nlsgpkgloader.nls_geopackage_loader_dialog import NLSGeoPackageLoaderDialog


@pytest.fixture
def dialog():
    return NLSGeoPackageLoaderDialog(None)


def test_dialog_ok(dialog):
    """Test we can click OK."""

    button = dialog.button_box.button(QDialogButtonBox.Ok)
    button.click()
    result = dialog.result()
    assert result == QDialog.Accepted


def test_dialog_cancel(dialog):
    """Test we can click cancel."""
    button = dialog.button_box.button(QDialogButtonBox.Cancel)
    button.click()
    result = dialog.result()
    assert result == QDialog.Rejected
