from qgis.gui import QgsMapTool
from qgis.core import Qgis, QgsGeometry
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtWidgets import QToolTip
from .geodesy import Geodesy
from .utils import fmt_number, parse_number

NUMBER_KEYS = "0123456789.,"


class PolygonTool(QgsMapTool):
    """Click to add vertices, or type a segment length and press Enter to
    place the next vertex at an exact distance. Backspace removes the last
    vertex. Double-click, right-click, or Enter (with no typed length)
    finishes. Escape cancels. Lengths and areas are true values in meters on
    the ellipsoid, whatever the map canvas CRS."""

    def __init__(self, canvas, rubber_band, on_finished):
        super().__init__(canvas)
        self.rb = rubber_band
        self.on_finished = on_finished
        self.points = []
        self._ignore_next_release = False
        self._layer_valid = True
        self._typed_length = ""
        self._last_mouse_point = None
        self._geodesy = None

    def _geo(self):
        """Geodesic measuring for the current canvas CRS (created on demand)."""
        if self._geodesy is None:
            self._geodesy = Geodesy(self.canvas().mapSettings().destinationCrs())
        return self._geodesy

    def set_layer_valid(self, valid):
        self._layer_valid = valid
        self.setCursor(QCursor(
            Qt.CursorShape.CrossCursor if valid else Qt.CursorShape.ForbiddenCursor))

    def canvasReleaseEvent(self, e):
        if not self._layer_valid:
            return
        if self._ignore_next_release:
            self._ignore_next_release = False
            return
        if e.button() == Qt.MouseButton.RightButton:
            self._finish()
            return
        if e.button() != Qt.MouseButton.LeftButton:
            return
        if not self.points:
            self.rb.reset(Qgis.GeometryType.Polygon)
            self._geodesy = None  # pick up the current canvas CRS for this polygon
        # A typed length wins over the mouse position, same as pressing Enter.
        typed_pt = self._typed_point() if self._typed_length else None
        self._commit_point(typed_pt if typed_pt is not None else e.mapPoint())

    def canvasDoubleClickEvent(self, e):
        if not self._layer_valid:
            return
        self._ignore_next_release = True  # absorb the release that follows
        if self.points:
            self.points.pop()  # drop the vertex the double-click's own first click just added
        self._finish()

    def canvasMoveEvent(self, e):
        self._last_mouse_point = e.mapPoint()
        if not self.points:
            return
        if self._typed_length:
            self._refresh_preview()
        else:
            self._show_preview(self._last_mouse_point)

    def keyPressEvent(self, e):
        # Note: in QGIS a map tool marks a key as handled with e.ignore() (yes,
        # backwards). Otherwise QGIS also processes it - Backspace/Delete would
        # run "Delete Selected" on the active layer.
        key, text = e.key(), e.text()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._typed_length and self.points:
                typed_pt = self._typed_point()
                if typed_pt is not None:
                    self._commit_point(typed_pt)
            else:
                self._finish()
            e.ignore()
        elif key == Qt.Key.Key_Escape:
            self.reset()
            e.ignore()
        elif key in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            if self._typed_length:
                self._typed_length = self._typed_length[:-1]
                self._refresh_preview()
            elif self.points:
                self._remove_last_point()
            e.ignore()
        elif len(text) == 1 and text in NUMBER_KEYS and self.points:
            self._typed_length += text
            self._refresh_preview()
            e.ignore()

    def _remove_last_point(self):
        self.points.pop()
        if self.points:
            self._refresh_preview()
        else:
            self._clear_sketch()

    def _typed_point(self):
        """Point at the typed distance (meters) from the last vertex, in the
        direction of the mouse pointer."""
        if not self.points or self._last_mouse_point is None:
            return None
        length = parse_number(self._typed_length)
        if not length:
            return None
        return self._geo().point_towards(self.points[-1], self._last_mouse_point, length)

    def _refresh_preview(self):
        """Typed length if there is one, otherwise follow the mouse again."""
        if self._typed_length:
            typed_pt = self._typed_point()
            if typed_pt is not None:
                self._show_preview(typed_pt, typed=True)
        elif self._last_mouse_point is not None:
            self._show_preview(self._last_mouse_point)
        else:
            self._update_band()

    def _commit_point(self, point):
        self.points.append(point)
        self._typed_length = ""
        QToolTip.hideText()
        self._update_band()

    def _show_preview(self, point, typed=False):
        self._update_band(preview_point=point)
        length = self._geo().distance(self.points[-1], point)
        text = f"Length: {fmt_number(length)} m"
        preview_pts = self.points + [point]
        if len(preview_pts) >= 3:
            area = self._geo().area(QgsGeometry.fromPolygonXY([preview_pts]))
            text += f"   Area: {fmt_number(area)} m²"
        if typed:
            text += "  (typed - Enter to confirm)"
        QToolTip.showText(QCursor.pos(), text, self.canvas())

    def _update_band(self, preview_point=None):
        pts = self.points + ([preview_point] if preview_point else [])
        if len(pts) >= 3:
            self.rb.setToGeometry(QgsGeometry.fromPolygonXY([pts]), None)
        elif len(pts) == 2:
            self.rb.setToGeometry(QgsGeometry.fromPolylineXY(pts), None)
        else:
            self.rb.reset(Qgis.GeometryType.Polygon)

    def _clear_sketch(self):
        self.points = []
        self._typed_length = ""
        self.rb.reset(Qgis.GeometryType.Polygon)
        QToolTip.hideText()

    def _finish(self):
        if len(self.points) >= 3:
            geom = QgsGeometry.fromPolygonXY([self.points])
            self.rb.setToGeometry(geom, None)
            self.points = []
            self._typed_length = ""
            QToolTip.hideText()
            if not geom.isEmpty():
                self.on_finished(geom)
        else:
            self._clear_sketch()

    def reset(self):
        self._clear_sketch()
        self._ignore_next_release = False

    def deactivate(self):
        self.reset()
        super().deactivate()
