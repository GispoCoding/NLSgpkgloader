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

import io
import os
import xml.etree.ElementTree
import zipfile
from zipfile import BadZipFile

import requests
from osgeo import ogr
from qgis.core import (
    QgsApplication,
    QgsLayerTreeGroup,
    QgsMessageLog,
    QgsProject,
    QgsSettings,
    QgsVectorLayer,
)
from qgis.gui import QgsFileWidget
from qgis.PyQt.QtCore import QCoreApplication, Qt, QTimer, QTranslator, qVersion
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QListWidgetItem, QMessageBox
from qgis.utils import iface

from nlsgpkgloader.nls_geopackage_loader_mtk_productdata import (
    MTK_ALL_PRODUCTS_TITLE,
    MTK_ALL_PRODUCTS_URL,
    MTK_LAYERS_KEY_PREFIX,
    MTK_PRESELECTED_PRODUCTS,
    MTK_PRODUCT_NAMES,
    MTK_STYLED_LAYERS,
)
from nlsgpkgloader.nls_geopackage_loader_tasks import (
    CleanUpTask,
    ClipLayersTask,
    CreateGeoPackageTask,
    DissolveFeaturesTask,
)
from nlsgpkgloader.qgis_plugin_tools.tools.resources import resources_path
from nlsgpkgloader.qgis_plugin_tools.tools.settings import get_setting, set_setting
from nlsgpkgloader.ui import (
    NLSGeoPackageLoaderMunicipalitySelectionDialog,
    NLSGeoPackageLoaderProgressDialog,
    NLSGeoPackageLoaderUserKeyDialog,
)

OLD_SETTINGS_GROUP_NAME = "NLSgpkgloader"


class NLSGeoPackageLoader:
    """QGIS Plugin Implementation."""

    def __init__(self):
        """Constructor"""

        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = get_setting("locale/userLocale", internal=False)[0:2]
        locale_path = resources_path("i18n", "NLSGeoPackageLoader_{}.qm".format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > "4.3.3":
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr("&NLS GeoPackage Downloader")

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

        self.path = os.path.dirname(__file__)
        self.data_download_dir = self.path

        self.nls_user_key_dialog = NLSGeoPackageLoaderUserKeyDialog()

        if OLD_SETTINGS_GROUP_NAME in QgsSettings().childGroups():
            self._migrate_settings()

        self.first_run = get_setting("first_run", True, bool)
        if self.first_run:
            set_setting("first_run", False)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate("NLSGeoPackageLoader", message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None,
    ):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)

        return action

    def initGui(self):  # noqa N802
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        self.add_action(
            resources_path("icons", "icon.png"),
            text=self.tr("NLS GeoPackage Downloader"),
            callback=self.run,
            parent=self.iface.mainWindow(),
        )

        # will be set False in run()
        self.first_start = True

    @staticmethod
    def _migrate_settings():
        settings = QgsSettings()
        settings.beginGroup(OLD_SETTINGS_GROUP_NAME)
        for key in settings.allKeys():
            set_setting(key, settings.value(key))
        settings.endGroup()
        settings.remove(OLD_SETTINGS_GROUP_NAME)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr("&NLS GeoPackage Downloader"), action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        """Run method that performs all the real work"""
        self.nls_user_key = get_setting("userKey", "", typehint=str)

        self.data_download_dir = get_setting("dataDownloadDir", "", typehint=str)
        self.fileName = get_setting("defaultFileName", "mtk.gpkg", typehint=str)
        self.addDownloadedDataAsLayer = get_setting(
            "addDownloadedDataAsLayer", True, typehint=bool
        )
        self.showMunicipalitiesAsLayer = get_setting(
            "showMunicipalitiesAsLayer", True, typehint=bool
        )
        self.showUTMGridsAsLayer = get_setting(
            "showUTMGridsAsLayer", False, typehint=bool
        )
        self.showSeatilesAsLayer = get_setting(
            "showSeatilesAsLayer", False, typehint=bool
        )

        if self.nls_user_key == "":
            res = self.show_settings_dialog()
            if not res:
                return
        if not self.load_layers():
            QMessageBox.critical(
                self.iface.mainWindow(),
                self.tr("Failed to load data"),
                self.tr("Check that necessary files exist in data folder"),
            )
            return

        self.product_types = self.download_nls_product_types()

        self.municipalities_dialog = NLSGeoPackageLoaderMunicipalitySelectionDialog()

        self.municipalities_dialog.settingsPushButton.clicked.connect(
            self.show_settings_dialog
        )
        self.municipalities_dialog.fileNameEdit.setValue(self.fileName)
        self.municipalities_dialog.loadLayers.setChecked(self.addDownloadedDataAsLayer)
        self.municipalities_dialog.loadMunLayer.setChecked(
            self.showMunicipalitiesAsLayer
        )
        self.municipalities_dialog.loadUtmGrids.setChecked(self.showUTMGridsAsLayer)
        self.municipalities_dialog.loadSeaGrids.setChecked(self.showSeatilesAsLayer)
        self.municipalities_dialog.loadLayers.stateChanged.connect(self.toggle_layers)
        self.municipalities_dialog.loadMunLayer.stateChanged.connect(self.toggle_layers)
        self.municipalities_dialog.loadUtmGrids.stateChanged.connect(self.toggle_layers)
        self.municipalities_dialog.loadSeaGrids.stateChanged.connect(self.toggle_layers)
        self.toggle_layers()

        for feature in self.municipality_layer.getFeatures():
            item = QListWidgetItem(feature["NAMEFIN"])
            self.municipalities_dialog.municipalityListWidget.addItem(item)

        for value in self.product_types.values():
            item = QListWidgetItem(value)
            self.municipalities_dialog.productListWidget.addItem(item)
            if value in MTK_PRESELECTED_PRODUCTS:
                self.municipalities_dialog.productListWidget.setCurrentItem(item)

        self.municipalities_dialog.show()

        self.municipalities_dialog.selectDeselectAll.clicked.connect(
            self.select_deselect_all_layers
        )

        result = self.municipalities_dialog.exec_()
        if result:
            self.fileName = self.municipalities_dialog.fileNameEdit.text().strip()
            if self.fileName == "":
                QMessageBox.critical(
                    self.iface.mainWindow(),
                    self.tr("Invalid filename"),
                    self.tr("Please enter a filename"),
                )
                return
            if self.fileName.split(".")[-1].lower() != "gpkg":
                self.fileName += ".gpkg"
            set_setting("defaultFileName", self.fileName)
            self.gpkg_path = os.path.join(self.data_download_dir, self.fileName)
            if os.path.isfile(self.gpkg_path):
                reply = QMessageBox.question(
                    self.iface.mainWindow(),
                    "Overwrite?",
                    "Overwrite file " + self.gpkg_path + "?",
                    QMessageBox.Yes,
                    QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    os.remove(self.gpkg_path)
                else:
                    return

            self.progress_dialog = NLSGeoPackageLoaderProgressDialog()
            self.progress_dialog.progressBar.hide()
            self.progress_dialog.label.setText("Initializing...")
            self.progress_dialog.show()

            self.utm25lr_features = []
            self.selected_geoms = []
            for feature in self.utm25lr_layer.selectedFeatures():
                self.utm25lr_features.append(feature)
                self.selected_geoms.append(feature.geometry())
            grids = [
                self.utm5_layer,
                self.utm10_layer,
                self.utm25_layer,
                self.utm50_layer,
                self.utm100_layer,
                self.utm200_layer,
            ]
            for grid in grids:
                for feature in grid.selectedFeatures():
                    self.selected_geoms.append(feature.geometry())

            selected_mun_names = []
            for (
                item
            ) in self.municipalities_dialog.municipalityListWidget.selectedItems():
                selected_mun_names.append(item.text())
            for feature in self.municipality_layer.getFeatures():
                if feature["NAMEFIN"] in selected_mun_names:
                    self.selected_geoms.append(feature.geometry())

            for feature in self.municipality_layer.selectedFeatures():
                self.selected_geoms.append(feature.geometry())
            for feature in self.seatile_layer.selectedFeatures():
                self.selected_geoms.append(feature.geometry())

            product_types = {}  # TODO ask from the user via dialog that lists types
            # based on NLS Atom service
            self.selected_mtk_product_types = []
            for (
                selected_prod_title
            ) in (
                self.municipalities_dialog.productListWidget.selectedItems()
            ):  # TODO: clean up the loop
                for key, value in list(self.product_types.items()):
                    if selected_prod_title.text() == value:
                        if key.startswith(
                            MTK_LAYERS_KEY_PREFIX
                        ):  # Individual MTK layer
                            self.selected_mtk_product_types.append(
                                selected_prod_title.text()
                            )
                            product_types[MTK_ALL_PRODUCTS_URL] = MTK_ALL_PRODUCTS_TITLE
                        else:
                            product_types[key] = value

            if len(product_types) > 0 and len(self.selected_geoms) > 0:
                QCoreApplication.processEvents()

                self.get_intersecting_features(
                    self.municipality_layer.selectedFeatures(),
                    self.utm25lr_layer,
                    selected_mun_names,
                )
                self.get_intersecting_features(
                    self.seatile_layer.selectedFeatures(), self.utm25lr_layer
                )
                for grid in grids:
                    self.get_intersecting_features(
                        grid.selectedFeatures(), self.utm25lr_layer
                    )

                self.download_data(product_types)

            else:
                self.progress_dialog.hide()
                QMessageBox.critical(
                    self.iface.mainWindow(),
                    self.tr("Invalid selection"),
                    self.tr("Found nothing to download!"),
                )
                return

    def toggle_layers(self):
        """Load municipality and map tile layers"""
        self.addDownloadedDataAsLayer = (
            self.municipalities_dialog.loadLayers.isChecked()
        )
        self.showMunicipalitiesAsLayer = (
            self.municipalities_dialog.loadMunLayer.isChecked()
        )
        self.showUTMGridsAsLayer = self.municipalities_dialog.loadUtmGrids.isChecked()
        self.showSeatilesAsLayer = self.municipalities_dialog.loadSeaGrids.isChecked()
        set_setting("addDownloadedDataAsLayer", self.addDownloadedDataAsLayer)
        set_setting("showMunicipalitiesAsLayer", self.showMunicipalitiesAsLayer)
        set_setting("showUTMGridsAsLayer", self.showUTMGridsAsLayer)
        set_setting("showSeatilesAsLayer", self.showSeatilesAsLayer)

        found_utm5_layer = (
            found_utm10_layer
        ) = (
            found_utm25lr_layer
        ) = (
            found_utm25_layer
        ) = (
            found_utm50_layer
        ) = (
            found_utm100_layer
        ) = found_utm200_layer = found_seatiles_layer = found_municipality_layer = False

        current_layers = self.get_layers(self.instance.layerTreeRoot())

        for current_layer in current_layers:
            if current_layer.layer() == self.utm5_layer:
                found_utm5_layer = True
                current_layer.setItemVisibilityChecked(self.showUTMGridsAsLayer)
            if current_layer.layer() == self.utm10_layer:
                found_utm10_layer = True
                current_layer.setItemVisibilityChecked(self.showUTMGridsAsLayer)
            if current_layer.layer() == self.utm25lr_layer:
                found_utm25lr_layer = True
                current_layer.setItemVisibilityChecked(self.showUTMGridsAsLayer)
            if current_layer.layer() == self.utm25_layer:
                found_utm25_layer = True
                current_layer.setItemVisibilityChecked(self.showUTMGridsAsLayer)
            if current_layer.layer() == self.utm50_layer:
                found_utm50_layer = True
                current_layer.setItemVisibilityChecked(self.showUTMGridsAsLayer)
            if current_layer.layer() == self.utm100_layer:
                found_utm100_layer = True
                current_layer.setItemVisibilityChecked(self.showUTMGridsAsLayer)
            if current_layer.layer() == self.utm200_layer:
                found_utm200_layer = True
                current_layer.setItemVisibilityChecked(self.showUTMGridsAsLayer)
            if current_layer.layer() == self.seatile_layer:
                found_seatiles_layer = True
                current_layer.setItemVisibilityChecked(self.showSeatilesAsLayer)
            if current_layer.layer() == self.municipality_layer:
                found_municipality_layer = True
                current_layer.setItemVisibilityChecked(self.showMunicipalitiesAsLayer)

        if self.showUTMGridsAsLayer:
            try:
                if not found_utm200_layer and self.utm200_layer:
                    self.instance.addMapLayer(self.utm200_layer)
                if not found_utm100_layer and self.utm100_layer:
                    self.instance.addMapLayer(self.utm100_layer)
                if not found_utm50_layer and self.utm50_layer:
                    self.instance.addMapLayer(self.utm50_layer)
                if not found_utm25_layer and self.utm25_layer:
                    self.instance.addMapLayer(self.utm25_layer)
                if not found_utm25lr_layer:
                    self.instance.addMapLayer(self.utm25lr_layer)
                if not found_utm10_layer and self.utm10_layer:
                    self.instance.addMapLayer(self.utm10_layer)
                if not found_utm5_layer and self.utm5_layer:
                    self.instance.addMapLayer(self.utm5_layer)
            except Exception:
                self.load_layers()
                if not found_utm200_layer and self.utm200_layer:
                    self.instance.addMapLayer(self.utm200_layer)
                if not found_utm100_layer and self.utm100_layer:
                    self.instance.addMapLayer(self.utm100_layer)
                if not found_utm50_layer and self.utm50_layer:
                    self.instance.addMapLayer(self.utm50_layer)
                if not found_utm25_layer and self.utm25_layer:
                    self.instance.addMapLayer(self.utm25_layer)
                if not found_utm25lr_layer:
                    self.instance.addMapLayer(self.utm25lr_layer)
                if not found_utm10_layer and self.utm10_layer:
                    self.instance.addMapLayer(self.utm10_layer)
                if not found_utm5_layer and self.utm5_layer:
                    self.instance.addMapLayer(self.utm5_layer)

        if self.showSeatilesAsLayer and not found_seatiles_layer:
            try:
                self.instance.addMapLayer(self.seatile_layer)
            except Exception:
                self.load_layers()
                self.instance.addMapLayer(self.seatile_layer)

        if self.showMunicipalitiesAsLayer and not found_municipality_layer:
            try:
                self.instance.addMapLayer(self.municipality_layer)
            except Exception:
                self.load_layers()
                self.instance.addMapLayer(self.municipality_layer)

    def load_layers(self):
        self.municipality_layer = QgsVectorLayer(
            resources_path("data", "SuomenKuntajako_2018_10k.shp"),
            "municipalities",
            "ogr",
        )
        if not self.municipality_layer.isValid():
            QgsMessageLog.logMessage(
                "Failed to load the municipality layer", "NLSgpkgloader", 2
            )
            self.iface.messageBar().pushMessage(
                "Error", "Failed to load the municipality layer", level=2, duration=5
            )
            return False
        self.municipality_layer.setProviderEncoding("ISO-8859-1")
        self.utm5_layer = QgsVectorLayer(
            resources_path("data", "utm5.shp"), "utm5", "ogr"
        )
        if not self.utm5_layer.isValid():
            QgsMessageLog.logMessage(
                "Failed to load the UTM 5 grid layer", "NLSgpkgloader", 1
            )
            self.iface.messageBar().pushMessage(
                "Error", "Failed to load the UTM 5 grid layer", level=1, duration=5
            )
            self.utm5_layer = False
        self.utm10_layer = QgsVectorLayer(
            resources_path("data", "utm10.shp"), "utm10", "ogr"
        )
        if not self.utm10_layer.isValid():
            QgsMessageLog.logMessage(
                "Failed to load the UTM 10 grid layer", "NLSgpkgloader", 1
            )
            self.iface.messageBar().pushMessage(
                "Error", "Failed to load the UTM 10 grid layer", level=1, duration=5
            )
            self.utm10_layer = False
        self.utm25lr_layer = QgsVectorLayer(
            resources_path("data", "utm25LR.shp"), "utm25lr", "ogr"
        )
        if not self.utm25lr_layer.isValid():
            QgsMessageLog.logMessage(
                "Failed to load the UTM 25LR grid layer", "NLSgpkgloader", 2
            )
            self.iface.messageBar().pushMessage(
                "Error", "Failed to load the UTM 25LR grid layer", level=2, duration=5
            )
            return False
        self.utm25_layer = QgsVectorLayer(
            resources_path("data", "utm25.shp"), "utm25", "ogr"
        )
        if not self.utm25_layer.isValid():
            QgsMessageLog.logMessage(
                "Failed to load the UTM 25 grid layer", "NLSgpkgloader", 1
            )
            self.iface.messageBar().pushMessage(
                "Error", "Failed to load the UTM 25 grid layer", level=1, duration=5
            )
            self.utm25_layer = False
        self.utm50_layer = QgsVectorLayer(
            resources_path("data", "utm50.shp"), "utm50", "ogr"
        )
        if not self.utm50_layer.isValid():
            QgsMessageLog.logMessage(
                "Failed to load the UTM 50 grid layer", "NLSgpkgloader", 1
            )
            self.iface.messageBar().pushMessage(
                "Error", "Failed to load the UTM 50 grid layer", level=1, duration=5
            )
            self.utm50_layer = False
        self.utm100_layer = QgsVectorLayer(
            resources_path("data", "utm100.shp"), "utm100", "ogr"
        )
        if not self.utm100_layer.isValid():
            QgsMessageLog.logMessage(
                "Failed to load the UTM 100 grid layer", "NLSgpkgloader", 1
            )
            self.iface.messageBar().pushMessage(
                "Error", "Failed to load the UTM 100 grid layer", level=1, duration=5
            )
            self.utm100_layer = False
        self.utm200_layer = QgsVectorLayer(
            resources_path("data", "utm200.shp"), "utm200", "ogr"
        )
        if not self.utm200_layer.isValid():
            QgsMessageLog.logMessage(
                "Failed to load the UTM 200 grid layer", "NLSgpkgloader", 1
            )
            self.iface.messageBar().pushMessage(
                "Error", "Failed to load the UTM 200 grid layer", level=1, duration=5
            )
            self.utm200_layer = False

        expression = '"product_group_id" = 5'
        self.seatile_layer = QgsVectorLayer(
            resources_path("data", "seatiles_3067.gpkg"), "seatiles", "ogr"
        )
        self.seatile_layer.setSubsetString(expression)
        if not self.seatile_layer.isValid():
            QgsMessageLog.logMessage(
                "Failed to load the ocean grid layer", "NLSgpkgloader", 2
            )
            self.iface.messageBar().pushMessage(
                "Error", "Failed to load the sea grid layer", level=2, duration=5
            )
            self.seatile_layer = False

        self.instance = QgsProject.instance()
        current_layers = self.get_layers(self.instance.layerTreeRoot())

        for lnode in current_layers:
            if (
                lnode.layer().dataProvider().dataSourceUri()
                == self.municipality_layer.dataProvider().dataSourceUri()
            ):
                self.municipality_layer = lnode.layer()
            if (
                lnode.layer().dataProvider().dataSourceUri()
                == self.seatile_layer.dataProvider().dataSourceUri()
            ):
                self.seatile_layer = lnode.layer()
            if (
                lnode.layer().dataProvider().dataSourceUri()
                == self.utm5_layer.dataProvider().dataSourceUri()
            ):
                self.utm5_layer = lnode.layer()
            if (
                lnode.layer().dataProvider().dataSourceUri()
                == self.utm10_layer.dataProvider().dataSourceUri()
            ):
                self.utm10_layer = lnode.layer()
            if (
                lnode.layer().dataProvider().dataSourceUri()
                == self.utm25_layer.dataProvider().dataSourceUri()
            ):
                self.utm25_layer = lnode.layer()
            if (
                lnode.layer().dataProvider().dataSourceUri()
                == self.utm25lr_layer.dataProvider().dataSourceUri()
            ):
                self.utm25lr_layer = lnode.layer()
            if (
                lnode.layer().dataProvider().dataSourceUri()
                == self.utm50_layer.dataProvider().dataSourceUri()
            ):
                self.utm50_layer = lnode.layer()
            if (
                lnode.layer().dataProvider().dataSourceUri()
                == self.utm100_layer.dataProvider().dataSourceUri()
            ):
                self.utm100_layer = lnode.layer()
            if (
                lnode.layer().dataProvider().dataSourceUri()
                == self.utm200_layer.dataProvider().dataSourceUri()
            ):
                self.utm200_layer = lnode.layer()

        return True

    def select_deselect_all_layers(self):
        if self.municipalities_dialog.selectDeselectAll.isChecked():
            for value in self.product_types.values():
                items = self.municipalities_dialog.productListWidget.findItems(
                    value, Qt.MatchExactly
                )
                if items:
                    items[0].setSelected(True)
        else:
            self.municipalities_dialog.productListWidget.clearSelection()

    def get_layers(self, root):
        layers = []
        for node in root.children():
            if isinstance(node, QgsLayerTreeGroup):
                layers.extend(self.get_layers(node))
            else:
                layers.append(node)
        return layers

    def get_intersecting_features(self, features, layer, selected_mun_names=None):
        if selected_mun_names:
            expression = ""
            for mun in selected_mun_names:
                expression += '"NAMEFIN" = \'' + mun + "' OR "
            expression = expression[:-4]

            iter = self.municipality_layer.getFeatures(expression)
            for feature in iter:
                mun_geom = feature.geometry()
                for layer_feature in layer.getFeatures():
                    layer_geom = layer_feature.geometry()
                    if mun_geom.intersects(layer_geom):
                        if feature not in self.utm25lr_features:
                            self.utm25lr_features.append(layer_feature)

        for feature in features:
            feat_geom = feature.geometry()
            for layer_feature in layer.getFeatures():
                layer_geom = layer_feature.geometry()
                if feat_geom.intersects(layer_geom):
                    if feature not in self.utm25lr_features:
                        self.utm25lr_features.append(layer_feature)

    def download_data(self, product_types):
        self.all_urls = []
        self.total_download_count = 0
        self.download_count = 0
        self.layers_added_count = 0

        for product_key, product_title in product_types.items():
            urls = self.create_download_urls(product_key, product_title)
            self.all_urls.extend(urls)
            self.total_download_count += len(urls)

        self.progress_dialog.progressBar.reset()
        self.progress_dialog.progressBar.show()
        self.progress_dialog.label.setText("Downloading data...")
        QTimer.singleShot(1000, self.download_one_file)

    def download_nls_product_types(self):
        products = {}

        url = (
            "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp?api_key="
            + self.nls_user_key
        )
        # TODO: use qgis.gui.QgsFileDownloader?
        self.verify = True
        try:
            r = requests.get(url, verify=self.verify)
        except requests.exceptions.SSLError:
            # TODO: warn user of certification fail
            self.verify = False
            r = requests.get(url, verify=self.verify)

        e = xml.etree.ElementTree.fromstring(r.text)

        for entry in e.findall("{http://www.w3.org/2005/Atom}entry"):
            title = entry.find("{http://www.w3.org/2005/Atom}title")
            QgsMessageLog.logMessage(title.text, "NLSgpkgloader", 0)
            id = entry.find("{http://www.w3.org/2005/Atom}id")
            QgsMessageLog.logMessage(id.text, "NLSgpkgloader", 0)

            if title.text == "Maastotietokanta, kaikki kohteet":
                # TODO let user choose in the options dialog if the individual
                # layers can be selected
                for mtk_product_name in MTK_PRODUCT_NAMES:
                    products[
                        MTK_LAYERS_KEY_PREFIX + mtk_product_name
                    ] = mtk_product_name
            else:
                # products[id.text] = title.text
                pass

        return products

    def download_one_file(self):
        if (
            self.download_count == self.total_download_count
            or self.download_count >= len(self.all_urls)
        ):
            QgsMessageLog.logMessage(
                (
                    "download_count == total_download_count or "
                    "download_count >= len(all_urls)"
                ),
                "NLSgpkgloader",
                2,
            )
            return

        url = self.all_urls[self.download_count][0]
        # QgsMessageLog.logMessage(url, 'NLSgpkgloader', 0)
        r = requests.get(url, stream=True, verify=self.verify)
        # TODO check r.status_code & r.ok

        url_parts = url.split("/")
        file_name = url_parts[-1].split("?")[0]

        data_dir_name = self.all_urls[self.download_count][1]
        data_dir_name = data_dir_name.replace(":", "_suhde_")
        dir_path = os.path.join(self.data_download_dir, data_dir_name)

        # QgsMessageLog.logMessage(dir_path, 'NLSgpkgloader', 0)
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
            except OSError as exc:
                QgsMessageLog.logMessage(str(exc.errno), "NLSgpkgloader", 2)
        if not os.path.exists(dir_path):
            QgsMessageLog.logMessage("dir not created", "NLSgpkgloader", 2)

        # TODO: don't keep zipfiles
        # z = zipfile.ZipFile(StringIO.StringIO(r.content))
        # z.extractall(os.path.join(self.data_download_dir, value))
        with open(os.path.join(dir_path, file_name), "wb") as f:
            f.write(r.content)

        if "zip" in file_name:
            dir_path = os.path.join(dir_path, file_name.split(".")[0])
            try:
                z = zipfile.ZipFile(io.BytesIO(r.content))
                z.extractall(dir_path)
            except BadZipFile:
                QgsMessageLog.logMessage(
                    "Bad zip file: " + file_name, "NLSgpkgloader", 1
                )

        self.download_count += 1
        percentage = self.download_count / float(self.total_download_count) * 100.0
        self.progress_dialog.progressBar.setValue(int(percentage))

        if self.download_count == self.total_download_count:
            QgsMessageLog.logMessage("done downloading data", "NLSgpkgloader", 0)
            self.create_geopackage()
        else:
            QTimer.singleShot(10, self.download_one_file)

    def create_geopackage(self):
        """Creates a GeoPackage from the downloaded MTK data"""
        self.progress_dialog.progressBar.reset()
        self.progress_dialog.label.setText("Writing layers to GeoPackage...")

        write_task = CreateGeoPackageTask(
            "Write GML to GPKG",
            self.all_urls,
            self.total_download_count,
            self.selected_mtk_product_types,
            self.data_download_dir,
            self.gpkg_path,
        )
        dissolve_task = DissolveFeaturesTask("Dissolve features", self.gpkg_path)
        clip_task = ClipLayersTask("Clip layers", self.selected_geoms, self.gpkg_path)
        cleanup_task = CleanUpTask("Delete temporary tables", self.path, self.gpkg_path)

        write_task.taskCompleted.connect(lambda: self.run_task(dissolve_task))
        dissolve_task.taskCompleted.connect(lambda: self.run_task(clip_task))
        clip_task.taskCompleted.connect(lambda: self.run_task(cleanup_task))
        cleanup_task.taskCompleted.connect(lambda: self.finish_processing())

        self.run_task(write_task)

    def run_task(self, task):
        self.progress_dialog.label.setText(task.description())
        task.progressChanged.connect(
            lambda: self.progress_dialog.progressBar.setValue(int(task.progress()))
        )
        QgsApplication.taskManager().addTask(task)

    def finish_processing(self):
        if self.addDownloadedDataAsLayer:
            self.progress_dialog.label.setText("Adding layers to QGIS")
            self.progress_dialog.progressBar.hide()
            conn = ogr.Open(self.gpkg_path)
            for i in conn:
                if (
                    i.GetName() in MTK_STYLED_LAYERS.values()
                    or i.GetName()[3:] in MTK_PRODUCT_NAMES
                ):
                    self.instance.addMapLayer(
                        QgsVectorLayer(
                            self.gpkg_path + "|layername=" + i.GetName(),
                            i.GetName(),
                            "ogr",
                        )
                    )
        self.iface.messageBar().pushMessage(
            self.tr("GeoPackage creation finished"),
            self.tr("NLS data download finished. Data located under ") + self.gpkg_path,
            level=3,
        )
        self.progress_dialog.hide()
        return True

    def show_settings_dialog(self):
        self.nls_user_key_dialog.dataLocationQgsFileWidget.setStorageMode(
            QgsFileWidget.GetDirectory
        )
        self.nls_user_key_dialog.userKeyLineEdit.setText(self.nls_user_key)
        self.nls_user_key_dialog.dataLocationQgsFileWidget.setFilePath(
            get_setting(
                "dataDownloadDir",
                os.path.join(self.path, "data"),
                typehint=str,
            )
        )

        self.nls_user_key_dialog.show()
        result = self.nls_user_key_dialog.exec_()
        if result:
            self.nls_user_key = self.nls_user_key_dialog.userKeyLineEdit.text().strip()
            if self.nls_user_key == "":
                # cannot work without the key, so user needs to be notified
                QMessageBox.critical(
                    self.iface.mainWindow(),
                    self.tr("User-key is needed"),
                    self.tr("Data cannot be downloaded without the NLS key"),
                )
                return False
            self.data_download_dir = (
                self.nls_user_key_dialog.dataLocationQgsFileWidget.filePath()
            )

            set_setting("userKey", self.nls_user_key)
            set_setting("dataDownloadDir", self.data_download_dir)
            return True

        else:
            # cannot work without the key, so user needs to be notified
            QMessageBox.critical(
                self.iface.mainWindow(),
                self.tr("User-key is needed"),
                self.tr("Data cannot be downloaded without the NLS key"),
            )
            return False

    def create_download_urls(self, product_key, product_title):
        urls = []
        if product_key == (
            "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed"
            "/mtp/maastotietokanta/kaikki"
        ):
            for utm_feature in self.utm25lr_features:
                sheet_name = utm_feature["LEHTITUNNU"]
                sn1 = sheet_name[:2]
                sn2 = sheet_name[:3]
                modified_key = product_key.replace(
                    "/feed/mtp", "/tilauslataus/tuotteet"
                )
                url = (
                    modified_key
                    + "/etrs89/gml/"
                    + sn1
                    + "/"
                    + sn2
                    + "/"
                    + sheet_name
                    + "_mtk.zip?api_key="
                    + self.nls_user_key
                )
                urls.append((url, product_title, product_key, "gml"))
        else:
            QgsMessageLog.logMessage(
                "Unknown product "
                + product_title
                + ", please send error report to the author",
                "NLSgpkgloader",
                2,
            )
            self.iface.messageBar().pushMessage(
                "Unknown product "
                + product_title
                + ", please send error report to the author",
                level=2,
                duration=10,
            )

        return urls
