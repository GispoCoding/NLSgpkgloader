# coding=utf-8
"""Resources test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = "mikael@gispo.fi"
__date__ = "2019-03-02"
__copyright__ = "Copyright 2019, Gispo Oy"


from qgis.PyQt.QtGui import QIcon

from nlsgpkgloader.qgis_plugin_tools.tools.resources import resources_path


def test_icon_png():
    """Test we can click OK."""
    path = resources_path("icons", "icon.png")
    icon = QIcon(path)
    assert icon is not None
