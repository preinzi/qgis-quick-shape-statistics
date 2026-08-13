# QuickShapeStatistics

Draw a circle or polygon directly on the map and instantly see area,
length, or point-count statistics for the active layer within that
shape — broken down by class if the layer is categorized.

## Features

- **Draw Circle for statistics** — click to set the center, click again to set the radius
- **Draw Polygon for statistics** — click to add vertices, finish with a double-click,
  right-click, or Enter
- Automatically measures area (polygon layers), length (line layers), or
  count (point layers), clipped precisely to the drawn shape
- Automatically groups results by class using the active layer's existing
  Categorized symbology, with a dropdown to override the field
- Feature count per class alongside the measured value
- One-click copy of the results table (tab-separated, pastes directly
  into a spreadsheet)

## Installation

**From the QGIS Plugin Repository** (once approved): Plugins > Manage
and Install Plugins > search "QuickShapeStatistics" > Install

**From a ZIP file**: Plugins > Manage and Install Plugins > Install from
ZIP > select the .zip > Install

## Requirements

QGIS 3.34 or later (tested on QGIS 3.34 LTR)

## Known limitation

Statistics are calculated on the main thread. On a very large active
layer or an unusually large drawn shape, QGIS may briefly become
unresponsive during calculation — it resolves on its own once the
calculation finishes. Not a crash, just a current trade-off.

## License

GPL v2 or later — see LICENSE.

## Acknowledgment

The creation of this plugin was prompted by Remo Probst, an independent
researcher from Austria who also works for Birdlife Austria.

This plugin was coded with the help of claude.ai.
