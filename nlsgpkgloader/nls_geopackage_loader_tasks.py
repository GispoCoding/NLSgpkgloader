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

import os
import sqlite3

import processing  # pylint: disable=import-error
from osgeo import ogr
from processing.tools import dataobjects  # pylint: disable=import-error
from qgis.core import (
    QgsFeature,
    QgsFeatureRequest,
    QgsMessageLog,
    QgsTask,
    QgsVectorFileWriter,
    QgsVectorLayer,
)

from nlsgpkgloader.qgis_plugin_tools.tools.resources import resources_path

from .nls_geopackage_loader_mtk_productdata import MTK_PRODUCT_NAMES, MTK_STYLED_LAYERS


class CreateGeoPackageTask(QgsTask):
    def __init__(self, description, urls, dlcount, products, dlpath, path):
        super().__init__(description, QgsTask.CanCancel)
        self.all_urls = urls
        self.total_download_count = dlcount
        self.products = products
        self.data_download_dir = dlpath
        self.gpkg_path = path

    def run(self):
        for dl_index in range(0, self.total_download_count):
            url = self.all_urls[dl_index][0]
            url_parts = url.split("/")
            file_name = url_parts[-1].split("?")[0]
            data_dir_name = self.all_urls[dl_index][1]
            data_dir_name = data_dir_name.replace(":", "_suhde_")
            dir_path = os.path.join(self.data_download_dir, data_dir_name)
            dir_path = os.path.join(dir_path, file_name.split(".")[0])
            data_type = self.all_urls[dl_index][3]

            percentage = dl_index / float(self.total_download_count) * 100.0
            self.setProgress(percentage)

            if not os.path.exists(dir_path):
                QgsMessageLog.logMessage(
                    "Skipping directory: " + dir_path, "NLSgpkgloader", 1
                )
                continue

            for listed_file_name in os.listdir(dir_path):
                if data_type == "gml" and listed_file_name.endswith(".xml"):
                    driver = ogr.GetDriverByName("GML")
                    data_source = driver.Open(
                        os.path.join(dir_path, listed_file_name), 0
                    )
                    layer_count = data_source.GetLayerCount()

                    mtk_layer_count = 0  # Used for breaking from the for loop
                    # when all MTK layers chosen by the user have been added
                    for i in range(layer_count):
                        if self.isCanceled():
                            return False
                        layer = data_source.GetLayerByIndex(i)
                        layer_name = layer.GetName()
                        if layer_name in self.products:
                            new_layer = QgsVectorLayer(
                                os.path.join(dir_path, listed_file_name)
                                + "|layerid="
                                + str(i),
                                layer_name,
                                "ogr",
                            )
                            if new_layer.isValid():
                                options = QgsVectorFileWriter.SaveVectorOptions()
                                options.layerName = layer_name
                                options.driverName = "GPKG"
                                options.fileEncoding = "UTF-8"
                                if os.path.isfile(self.gpkg_path):
                                    if QgsVectorLayer(
                                        self.gpkg_path + "|layername=" + layer_name
                                    ).isValid():
                                        options.actionOnExistingFile = (
                                            QgsVectorFileWriter.AppendToLayerNoNewFields
                                        )
                                    else:
                                        options.actionOnExistingFile = (
                                            QgsVectorFileWriter.CreateOrOverwriteLayer
                                        )
                                else:
                                    options.actionOnExistingFile = (
                                        QgsVectorFileWriter.CreateOrOverwriteFile
                                    )
                                e = QgsVectorFileWriter.writeAsVectorFormat(
                                    new_layer, self.gpkg_path, options
                                )
                                if e[0]:
                                    QgsMessageLog.logMessage(
                                        "Failed to write layer "
                                        + layer_name
                                        + " to geopackage",
                                        "NLSgpkgloader",
                                        2,
                                    )
                                    break
                                mtk_layer_count += 1
                            else:
                                layer_name = ""
                                # TODO: handle invalid layer error
                                # QgsMessageLog.logMessage(
                                #     "Invalid layer: {} : {}".format(
                                #         listed_file_name, layer_name
                                #     ),
                                #     "NLSgpkgloader",
                                #     2,
                                # )
                                pass

                        if mtk_layer_count == len(self.products):
                            break
                else:
                    QgsMessageLog.logMessage(
                        "cannot add the data type "
                        + data_type
                        + ", listed_file_name: "
                        + listed_file_name,
                        "NLSgpkgloader",
                        0,
                    )
        return True

    def finished(self, result):
        if not result:
            QgsMessageLog.logMessage(
                "Writing GML to GPKG: task canceled", "NLSgpkgloader", 1
            )


class DissolveFeaturesTask(QgsTask):
    def __init__(self, description, path):
        super().__init__(description, QgsTask.CanCancel)
        self.gpkg_path = path

    def run(self):
        conn = ogr.Open(self.gpkg_path)
        i = 0
        total_tables = len(conn)
        for table in conn:
            i += 1
            table_name = table.GetName()
            if table_name not in MTK_PRODUCT_NAMES:
                percentage = i / float(total_tables) * 100.0
                self.setProgress(percentage)
                continue
            layer_name = "d_" + table_name
            params = {
                "INPUT": self.gpkg_path + "|layername=" + table_name,
                "FIELD": ["gid"],
                "OUTPUT": "ogr:dbname='"
                + self.gpkg_path
                + "' table=\""
                + layer_name
                + '" (geom) sql=',
            }
            context = dataobjects.createContext()
            context.setInvalidGeometryCheck(QgsFeatureRequest.GeometrySkipInvalid)
            processing.run("native:dissolve", params, context=context)
            percentage = i / float(total_tables) * 100.0
            self.setProgress(percentage)
            if self.isCanceled():
                return False
        return True

    def finished(self, result):
        if not result:
            QgsMessageLog.logMessage(
                "Writing GML to GPKG: task canceled", "NLSgpkgloader", 1
            )


class ClipLayersTask(QgsTask):
    def __init__(self, description, selected_geoms, path):
        super().__init__(description, QgsTask.CanCancel)
        self.selected_geoms = selected_geoms
        self.gpkg_path = path

    def run(self):
        combined_geom_layer = QgsVectorLayer(
            "MultiPolygon?crs=EPSG:3067", "clipLayer", "memory"
        )
        geom_union = None
        for geom in self.selected_geoms:
            if not geom_union:
                geom_union = geom
            else:
                geom_union = geom_union.combine(geom)
        dp = combined_geom_layer.dataProvider()

        combined_geom_layer.startEditing()
        feat = QgsFeature()
        feat.setGeometry(geom_union)
        dp.addFeature(feat)
        combined_geom_layer.commitChanges()

        params = {"INPUT": combined_geom_layer, "OUTPUT": "memory:geomUnionLayer"}
        result = processing.run("native:dissolve", params)
        geom_union_layer = result["OUTPUT"]

        conn = ogr.Open(self.gpkg_path)
        total_tables = len(conn)
        i = 0
        for table in conn:
            i += 1
            table_name = table.GetName()
            if table_name[2:] not in MTK_PRODUCT_NAMES:
                percentage = i / float(total_tables) * 100.0
                self.setProgress(percentage)
                if self.isCanceled():
                    return False
                continue
            layer_name = table_name[2:]
            if layer_name in MTK_STYLED_LAYERS.keys():
                layer_name = MTK_STYLED_LAYERS[layer_name]
            else:
                layer_name = "zz_" + layer_name
            params = {
                "INPUT": self.gpkg_path + "|layername=" + table_name,
                "OVERLAY": geom_union_layer,
                "OUTPUT": "ogr:dbname='"
                + self.gpkg_path
                + "' table=\""
                + layer_name
                + '" (geom) sql=',
            }
            processing.run("native:clip", params)
            percentage = i / float(total_tables) * 100.0
            self.setProgress(percentage)
            if self.isCanceled():
                return False
        return True

    def finished(self, result):
        if not result:
            QgsMessageLog.logMessage(
                "Writing GML to GPKG: task canceled", "NLSgpkgloader", 1
            )


class CleanUpTask(QgsTask):
    def __init__(self, description, selfpath, gpkgpath):
        super().__init__(description, QgsTask.CanCancel)
        self.path = selfpath
        self.gpkg_path = gpkgpath

    def run(self):
        conn = sqlite3.connect(self.gpkg_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        result = cur.fetchall()
        total_tables = len(result)
        i = 0
        for table in result:
            if table[0][:2] == "d_" or table[0] in MTK_PRODUCT_NAMES:
                cur.execute("DROP TABLE " + table[0])
                cur.execute("DROP TABLE IF EXISTS rtree_" + table[0])
            i += 1
            percentage = i / float(total_tables) * 100.0
            self.setProgress(percentage)
            if self.isCanceled():
                return False
        try:
            with open(resources_path("data", "layer_styles.sql")) as stylefile:
                cur.executescript(stylefile.read())
        except FileNotFoundError:
            self.iface.messageBar().pushMessage(
                "Error",
                "Failed to load style table from data/layer_styles.sql",
                level=2,
                duration=5,
            )
            conn.commit()
            conn.close()
            return False
        conn.commit()
        cur.execute("VACUUM")
        conn.commit()
        conn.close()
        return True

    def finished(self, result):
        if not result:
            QgsMessageLog.logMessage(
                "Writing GML to GPKG: task canceled", "NLSgpkgloader", 1
            )
