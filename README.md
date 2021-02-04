# NLS GeoPackage Downloader QGIS plugin

This plugin lets users download NLS.fi open MTK data (CC-BY 4.0) using QGIS3. It utilizes the NLS Open data file updating service (Atom feed). You need to order a user-specific identification key from NLS to be able to use this plugin: http://www.maanmittauslaitos.fi/en/e-services/open-data-file-download-service/open-data-file-updating-service-interface.

The plugin is still in beta-development. Please report issues preferably to Issues or to tuki@gispo.fi.

**Developed by [Gispo Ltd.](https://www.gispo.fi)**

## Licences

This plugin utilizes data licensed by Traficom and National Land Survey of Finland. **Please read [data/LICENCE.txt](data/LICENCE.txt) for more information.**

## Installation instructions

1. Download the latest release zip from GitHub releases (above) either via Clone or Download ZIP.

2. Launch QGIS and navigate to the plugins menu by selecting Plugins - Manage and Install Plugins from the top menu.

3. Select the Install from ZIP tab, browse to the zip file you just downloaded, and click Install Plugin!

## Usage

Using the plugin is fairly straightforward:

1. Click the NLS plugin icon. Download Data window opens. Click Settings button in the left bottom corner.
2. Another pop-up window opens. In the Settings window, enter a valid identification key (received via email from NLS)
   and set the save directory.
3. Select which areas to download either by picking municipalities / UTM grids / Sea grids from the list or by selecting
   features from the map.
4. Choose which layers to write to the GeoPackage. Note that some layers are preselected.
5. Enter a filename. If you wish to load the GeoPackage layers into QGIS, activate Load data check box.
6. Click OK and wait for processing to finish.

More documentation, including more detailed installation and usage instructions in Finnish, can be found in the [Wiki](https://github.com/GispoCoding/NLSgpkgloader/wiki).
