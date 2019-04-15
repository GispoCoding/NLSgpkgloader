import os
import processing
from osgeo import ogr

from qgis.core import (QgsApplication, QgsTask, QgsMessageLog, QgsVectorLayer, QgsVectorFileWriter, QgsFeature)
from .nls_geopackage_loader_mtk_productdata import MTK_PRODUCT_NAMES, MTK_STYLED_LAYERS

class CreateGeoPackageTask(QgsTask):
    def __init__(self, description, urls, dlcount, products, dlpath, path, nexttask):
        super().__init__(description, QgsTask.CanCancel)
        self.all_urls = urls
        self.total_download_count = dlcount
        self.products = products
        self.data_download_dir = dlpath
        self.gpkg_path = path
        self.next_task = nexttask

    def run(self):
        for dlIndex in range(0, self.total_download_count):
            url = self.all_urls[dlIndex][0]
            url_parts = url.split('/')
            file_name = url_parts[-1].split('?')[0]
            data_dir_name = self.all_urls[dlIndex][1]
            data_dir_name = data_dir_name.replace(":", "_suhde_")
            dir_path = os.path.join(self.data_download_dir, data_dir_name)
            dir_path = os.path.join(dir_path, file_name.split('.')[0])
            data_type = self.all_urls[dlIndex][3]

            percentage = dlIndex / float(self.total_download_count) * 100.0
            self.setProgress(percentage)

            for listed_file_name in os.listdir(dir_path):
                if data_type == "gml" and listed_file_name.endswith(".xml"):
                    driver = ogr.GetDriverByName('GML')
                    data_source = driver.Open(os.path.join(dir_path, listed_file_name), 0)
                    layer_count = data_source.GetLayerCount()
                    mtk_layer_count = 0 # Used for breaking from the for loop when all MTK layers chosen by the user have been added
                    for i in range(layer_count):
                        layer = data_source.GetLayerByIndex(i)
                        layer_name = layer.GetName()
                        if layer_name in self.products:
                            new_layer = QgsVectorLayer(os.path.join(dir_path, listed_file_name) + "|layerid=" + str(i), layer_name, "ogr")
                            if new_layer.isValid():
                                options = QgsVectorFileWriter.SaveVectorOptions()
                                options.layerName = layer_name
                                options.driverName = "GPKG"
                                options.fileEncoding = "UTF-8"
                                if os.path.isfile(self.gpkg_path):
                                    if QgsVectorLayer(self.gpkg_path + "|layername=" + layer_name).isValid():
                                        options.actionOnExistingFile = QgsVectorFileWriter.AppendToLayerNoNewFields
                                    else:
                                        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
                                else:
                                    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
                                e = QgsVectorFileWriter.writeAsVectorFormat(new_layer, self.gpkg_path, options)
                                if e[0]:
                                    QgsMessageLog.logMessage("Failed to write layer " + layer_name + " to geopackage", 'NLSgpkgloader', 2)
                                    break
                                mtk_layer_count += 1
                            else:
                                # TODO: handle invalid layer error
                                #QgsMessageLog.logMessage("Invalid layer: " + listed_file_name + ":" layer_name, 'NLSgpkgloader', 2)
                                pass

                        if mtk_layer_count == len(self.products):
                            break
                else:
                    QgsMessageLog.logMessage("cannot add the data type " + data_type + ", listed_file_name: " + listed_file_name, 'NLSgpkgloader', 0)
        return True

    def finished(self, result):
        if result:
            QgsApplication.taskManager().addTask(self.next_task)


class DissolveFeaturesTask(QgsTask):
    def __init__(self, description, path, nexttask):
        super().__init__(description, QgsTask.CanCancel)
        self.gpkg_path = path
        self.next_task = nexttask

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
                'INPUT': self.gpkg_path + "|layername=" + table_name,
                'FIELD': ['gid'],
                'OUTPUT': "ogr:dbname='" + self.gpkg_path + '\' table="' + layer_name + '" (geom) sql='
            }
            processing.run("native:dissolve", params)
            percentage = i / float(total_tables) * 100.0
            self.setProgress(percentage)
        return True

    def finished(self, result):
        if result:
            QgsApplication.taskManager().addTask(self.next_task)

class ClipLayersTask(QgsTask):
    def __init__(self, description, selected_geoms, path, nexttask):
        super().__init__(description, QgsTask.CanCancel)
        self.selected_geoms = selected_geoms
        self.gpkg_path = path
        self.next_task = nexttask

    def run(self):
        combinedGeomLayer = QgsVectorLayer("MultiPolygon?crs=EPSG:3067", "clipLayer", "memory")
        geom_union = None
        for geom in self.selected_geoms:
            if not geom_union:
                geom_union = geom
            else:
                geom_union = geom_union.combine(geom)
        dp = combinedGeomLayer.dataProvider()

        combinedGeomLayer.startEditing()
        feat = QgsFeature()
        feat.setGeometry(geom_union)
        dp.addFeature(feat)
        combinedGeomLayer.commitChanges()

        params = {'INPUT': combinedGeomLayer, 'OUTPUT': 'memory:geomUnionLayer'}
        result = processing.run("native:dissolve", params)
        geomUnionLayer = result['OUTPUT']

        conn = ogr.Open(self.gpkg_path)
        total_tables = len(conn)
        i = 0
        for table in conn:
            i += 1
            table_name = table.GetName()
            if table_name[2:] not in MTK_PRODUCT_NAMES:
                percentage = i / float(total_tables) * 100.0
                self.setProgress(percentage)
                continue
            layer_name = table_name[2:]
            if layer_name in MTK_STYLED_LAYERS.keys():
                layer_name = MTK_STYLED_LAYERS[layer_name]
            else:
                layer_name = 'zz_' + layer_name
            params = {
                'INPUT': self.gpkg_path + "|layername=" + table_name,
                'OVERLAY': geomUnionLayer,
                'OUTPUT': "ogr:dbname='" + self.gpkg_path + '\' table="' + layer_name + '" (geom) sql='
            }
            processing.run("native:clip", params)
            percentage = i / float(total_tables) * 100.0
            self.setProgress(percentage)
        return True

    def finished(self, result):
        if result:
            QgsApplication.taskManager().addTask(self.next_task)

class FinishTask(QgsTask):
    def __init__(self, description, path, instance, add_data):
        super().__init__(description, QgsTask.CanCancel)
        self.instance = instance
        self.addDownloadedDataAsLayer = add_data

    def run(self):
        if self.addDownloadedDataAsLayer:
            conn = ogr.Open(self.gpkg_path)
            for i in conn:
                if i.GetName() in MTK_STYLED_LAYERS.values() or i.GetName()[3:] in MTK_PRODUCT_NAMES:
                    self.instance.addMapLayer(QgsVectorLayer(self.gpkg_path + "|layername=" + i.GetName(), i.GetName(), "ogr"))
            return True

    def finished(self, result):
        self.iface.messageBar().pushMessage(self.tr(u'GeoPackage creation finished'), \
            self.tr(u'NLS data download finished. Data located under ') + \
            self.gpkg_path, level=3)
        return True
