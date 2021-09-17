# -*- coding: utf-8 -*-



#  Gispo Ltd., hereby disclaims all copyright interest in the program NLSgpkgloadert
#  Copyright (C) 2018-2020 Gispo Ltd (https://www.gispo.fi/).
#
#
#  This file is part of NLSgpkgloadert.
#
#  NLSgpkgloadert is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  NLSgpkgloadert is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with NLSgpkgloadert.  If not, see <https://www.gnu.org/licenses/>.



# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load NLSGeoPackageLoader class from file NLSGeoPackageLoader.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .nls_geopackage_loader import NLSGeoPackageLoader
    return NLSGeoPackageLoader(iface)
