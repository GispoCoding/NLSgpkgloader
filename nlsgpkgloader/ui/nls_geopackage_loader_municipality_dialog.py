from qgis.PyQt.QtWidgets import QDialog

from nlsgpkgloader.qgis_plugin_tools.tools.resources import load_ui

FORM_CLASS = load_ui("nls_geopackage_loader_dialog_municipality_selection.ui")


class NLSGeoPackageLoaderMunicipalitySelectionDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
