import os
from osgeo import ogr

from qgis.core import (QgsApplication, QgsTask, QgsMessageLog, QgsVectorLayer, QgsVectorFileWriter)

class CreateGeoPackageTask(QgsTask):
    def __init__(self, description, urls, dlcount, products, dlpath, path):
        super().__init__(description, QgsTask.CanCancel)
        self.all_urls = urls
        self.total_download_count = dlcount
        self.products = products
        self.data_download_dir = dlpath
        self.gpkg_path = path

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

    # def finished(self, result):
    #     pass
