# QuickShapeStatistics

Draw a circle or polygon directly on the map and instantly see area,
length, or point-count statistics for the active layer within that
shape — broken down by class if the layer is categorized.

<img src="screenshots/example.png" alt="QuickShapeStatistics in action" width="300">

## Features

- **Draw Circle for statistics** — click to set the center, click again to
  set the radius. A live tooltip shows the current radius and area while
  dragging, or type a number and press Enter to set an exact radius.
  Right-click or Escape aborts.
- **Draw Polygon for statistics** — click to add vertices, finish with a
  double-click, right-click, or Enter. Escape cancels.
- Automatically measures area (polygon layers), length (line layers), or
  count (point layers), clipped precisely to the drawn shape
- Automatically groups results by class using the active layer's existing
  Categorized symbology; falls back to a sensible non-ID field if the layer
  isn't categorized, with a dropdown to override the field manually
- Feature count per class alongside the measured value
- One-click copy of the results table (tab-separated, pastes directly
  into a spreadsheet)
- Warns and disables drawing (with a forbidden cursor) if the active layer
  isn't a vector layer
- Invalid drawn shapes are automatically repaired where possible; invalid
  features in the measured layer are skipped and reported rather than
  causing incorrect results

## Installation

**From the QGIS Plugin Repository**: Plugins > Manage
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

## Changelog

- **0.3** — Invalid geometry detection with automatic repair for drawn
  shapes, and invalid-feature skipping for the measured layer; live
  radius/area preview and typed-radius entry while drawing circles;
  right-click to abort a circle; cursor warning when the active layer
  isn't a vector layer; automatic fallback class field for uncategorized
  layers; adjusted results table column widths
- **0.2** — Removed unused scaffolding files flagged by the plugin
  repository scanner
- **0.1** — Initial release

## License

GPL v2 or later — see LICENSE.

## Acknowledgment

The creation of this plugin was prompted by Remo Probst, an independent
researcher from Austria who also works for Birdlife Austria.

This plugin was coded with the help of claude.ai.
