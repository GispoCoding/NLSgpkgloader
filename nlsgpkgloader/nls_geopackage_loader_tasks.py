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

import sqlite3
from pathlib import Path

from osgeo import gdal, ogr
from qgis import processing
from qgis.core import (
    QgsFeature,
    QgsFeatureRequest,
    QgsMessageLog,
    QgsProcessingContext,
    QgsTask,
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
        self.data_download_dir = Path(dlpath)
        self.gpkg_path = Path(path)

    def run(self):
        gdal.UseExceptions()
        all_gml_files = []
        try:
            for dl_index in range(0, self.total_download_count):
                url = self.all_urls[dl_index][0]
                url_parts = url.split("/")
                file_name = url_parts[-1].split("?")[0]
                data_dir_name = self.all_urls[dl_index][1]
                data_dir_name = data_dir_name.replace(":", "_suhde_")
                dir_path = (
                    self.data_download_dir / data_dir_name / file_name.split(".")[0]
                )
                data_type = self.all_urls[dl_index][3]

                percentage = dl_index / float(self.total_download_count) * 100.0
                self.setProgress(percentage)

                if not dir_path.exists():
                    QgsMessageLog.logMessage(
                        "Skipping directory: " + str(dir_path), "NLSgpkgloader", 1
                    )
                    continue

                for listed_file_name in dir_path.iterdir():
                    if data_type == "gml" and listed_file_name.suffix == ".xml":
                        all_gml_files.append(listed_file_name)

            if all_gml_files:
                merge_gmls(all_gml_files, self.gpkg_path)

            return True

        except Exception as e:
            QgsMessageLog.logMessage(f"Error: {str(e)}", "NLSgpkgloader", 2)
            return False

    def finished(self, result):
        if not result:
            QgsMessageLog.logMessage(
                "Writing GML to GPKG: task canceled", "NLSgpkgloader", 1
            )


def merge_gmls(gmls: list[Path], output: Path) -> None:
    gdal.UseExceptions()

    try:
        gpkg_driver = ogr.GetDriverByName("GPKG")
        if not output.exists():
            gpkg_driver.CreateDataSource(str(output))
        creation_options = gdal.VectorTranslateOptions(
            layerCreationOptions=["FID=id", "GEOMETRY_NAME=geom", "SPATIAL_INDEX=NONE"],
            mapFieldType="StringList=String",
        )
        append_options = gdal.VectorTranslateOptions(
            accessMode="append",
            mapFieldType="StringList=String",
        )
        for i, gml in enumerate(gmls):
            QgsMessageLog.logMessage(f"Processing GML file: {gml}", "NLSgpkgloader", 1)

            source_datasource = gdal.OpenEx(
                str(gml),
                nOpenFlags=gdal.OF_VECTOR,
            )

            if source_datasource is None:
                QgsMessageLog.logMessage(
                    f"Failed to open GML file: {gml}", "NLSgpkgloader", 2
                )
                continue
            QgsMessageLog.logMessage(
                f"Merging into GeoPackage: {output}", "NLSgpkgloader", 1
            )
            options = creation_options if i == 0 else append_options

            result = gdal.VectorTranslate(
                destNameOrDestDS=str(output),
                srcDS=source_datasource,
                options=options,
            )
            if not result:
                QgsMessageLog.logMessage(
                    f"Merge failed for GML file: {gml}", "NLSgpkgloader", 2
                )
            else:
                QgsMessageLog.logMessage(
                    f"Successfully merged GML file: {gml} into {output}",
                    "NLSgpkgloader",
                    1,
                )

    except Exception as e:
        QgsMessageLog.logMessage(
            f"Error merging GML files: {str(e)}", "NLSgpkgloader", 2
        )
        raise e


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

            context = QgsProcessingContext()
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
