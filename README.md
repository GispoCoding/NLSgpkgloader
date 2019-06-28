# NLS GeoPackage Downloader QGIS plugin

This plugin lets users download NLS.fi open MTK data (CC-BY 4.0) using QGIS3. It utilizes the NLS Open data file updating service (Atom feed). You need to order a user-specific identification key from NLS to be able to use this plugin: http://www.maanmittauslaitos.fi/en/e-services/open-data-file-download-service/open-data-file-updating-service-interface.

The plugin is still in beta-development. Please report issues preferably to Issues or to tuki@gispo.fi.

**Developed by [Gispo Ltd.](https://www.gispo.fi)**

## Licences

This plugin utilizes data licensed by Traficom and National Land Survey of Finland. **Please read [data/LICENCE.txt](data/LICENCE.txt) for more information.**

## Installation instructions

### Dependencies

Before installing the plugin, make sure to install the Python [requests-library](http://docs.python-requests.org/). This can be done by executing the command:

```pip install requests```

On Windows QGIS installations, installing the requests library can be done using the OSGeo4W Shell. Open the shell as an administrator and run commands:

```
py3_env
pip install requests
```

Python-requests may be replaced by the QGIS built-in [QgsFileDownloader](https://qgis.org/pyqgis/3.2/core/File/QgsFileDownloader.html) class in a future version of the plugin.

### QGIS Plugin

1. Download the repository as a zip using the Clone or download button in GitHub (above).

2. Launch QGIS and the plugins menu by selecting Plugins - Manage and Install Plugins from the top menu.

3. Select the Install from ZIP tab, browse to the zip file you just downloaded, and click Install Plugin!

## Usage

Using the plugin is fairly straightforward:

1. Enter a valid identification key and set the save directory in the settings window
2. Choose which layers to write to the GeoPackage. Note that some layers are preselected.
3. Select which areas to download either by picking municipalities from the list or selecting features from the map.
4. Enter a filename and whether to load the finished GeoPackage layers into QGIS.
5. Click OK and wait for processing to finish.

More documentation, including more detailed installation and usage instructions in Finnish can be found in the [Wiki](https://github.com/GispoCoding/NLSgpkgloader/wiki).