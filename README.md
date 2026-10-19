# QuickShapeStatistics

Draw a circle or polygon directly on the map and instantly see area,
length, or point-count statistics for the active layer within that
shape — broken down by class if the layer is categorized.

<img src="screenshots/example.png" alt="QuickShapeStatistics in action" width="300">

## Features

- **Draw Circle for statistics** — click to set the center, click again to
  set the radius. A live tooltip shows the current radius and area while
  dragging, or type a number and press Enter (or click) to set an exact
  radius. Right-click or Escape aborts.
- **Draw Polygon for statistics** — click to add vertices, finish with a
  double-click, right-click, or Enter. While drawing, a live tooltip shows
  the current segment's length and the polygon's area so far; type a
  number and press Enter (or click) to set an exact segment length.
  Backspace removes the last vertex, Escape cancels.
- Automatically measures area (polygon layers), length (line layers), or
  count (point layers), clipped precisely to the drawn shape
- Automatically groups results by class using the active layer's existing
  Categorized symbology (a field or an expression); falls back to a
  sensible non-ID field if the layer isn't categorized, with a dropdown to
  override the field manually
- Feature count per class alongside the measured value
- Results table columns can be resized and sorted by clicking a column
  header, similar to a QGIS attribute table
- One-click copy of the results table (tab-separated, pastes directly
  into a spreadsheet, respects the current sort order)
- Warns and disables drawing (with a forbidden cursor) if the active layer
  isn't a vector layer with point, line or polygon geometry
- Invalid drawn shapes are automatically repaired where possible; invalid
  features in the measured layer are skipped and reported rather than
  causing incorrect results

## Installation

**From the QGIS Plugin Repository** (show experimental plugins): Plugins > Manage
and Install Plugins > search "QuickShapeStatistics" > Install

**From a ZIP file**: Plugins > Manage and Install Plugins > Install from
ZIP > select the .zip > Install

## Requirements

QGIS 3.34 or later, including QGIS 4 (tested on QGIS 3.44 and QGIS 4.2)

## Known limitation

Statistics are calculated on the main thread. Only features near the
drawn shape are read, using the data source's spatial index, so this is
fast for typical layers. On a very large drawn shape over a very dense
layer, QGIS may still briefly become unresponsive during calculation —
it resolves on its own once the calculation finishes.

## How measurements are calculated

Area and length are calculated geodesically — accounting for the earth's
curvature via QGIS's ellipsoid settings — rather than with flat planar
math. Results are always in square meters / meters, regardless of the
active layer's CRS. This relies on the project's Ellipsoid setting being
enabled, which is QGIS's default; if it's explicitly set to "None,"
the plugin silently falls back to flat calculations in the layer's
native units instead.

Drawing is geodesic as well: the circle radius, a typed segment length
and the live tooltips while drawing are true distances and areas in
meters on the ellipsoid, in any map CRS — projected, geographic (e.g.
EPSG:4326) or Web Mercator (EPSG:3857).

## Changelog

- **0.6** — Fixed loading on QGIS 4 (Qt6): the results panel is now built
  in Python and the Qt Designer .ui file was removed; fixed feature counts
  including features that only touch the boundary of the drawn shape;
  fixed crashes for tables without geometry and for Categorized renderers
  that classify by an expression; automatic grouping now only uses
  Categorized symbology; class colors only shown when grouping by the
  renderer's own field; unloading or reloading the plugin now removes its
  toolbar, panel, sketch and active map tool; the results panel keeps its
  docked or floating position when reopened; a manually selected class
  field is kept when drawing again on the same layer; Backspace removes
  the last polygon vertex; fixed Backspace/Delete while drawing also
  triggering QGIS' Delete Selected; a typed radius or segment length is
  also used when clicking; plugin warnings disappear after a few seconds;
  circle radius, typed segment lengths and the live tooltips are now true
  geodesic meters in any map CRS (previously wrong in geographic CRSs and
  Web Mercator); much faster statistics on large layers
- **0.5** — Fixed thousands separator (space instead of comma); results
  table columns are now resizable and sortable by clicking headers;
  results panel reopens automatically when a shape is finished, if it
  was closed; live segment length and running area preview while
  drawing polygons, with typed segment length entry
- **0.4** — Documented ellipsoidal measurement behavior and units in the
  README
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
