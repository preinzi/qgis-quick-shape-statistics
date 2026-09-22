import math
from qgis.gui import QgsMapTool
from qgis.core import Qgis, QgsGeometry, QgsPointXY
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtWidgets import QToolTip


def _fmt(value, decimals=0):
    """Format a number with a space as the thousands separator, avoiding
    a comma that reads as a decimal separator in German/Austrian locales."""
    return f"{value:,.{decimals}f}".replace(",", " ")


class PolygonTool(QgsMapTool):
    """Click to add vertices, or type a segment length and press Enter to
    place the next vertex at an exact distance. Double-click, right-click,
    or Enter (with no typed length) finishes. Escape cancels."""

    def __init__(self, canvas, rubber_band, on_finished):
        super().__init__(canvas)
        self.rb = rubber_band
        self.on_finished = on_finished
        self.points = []
        self._ignore_next_release = False
        self._layer_valid = True
        self._typed_length = ""
        self._last_mouse_point = None

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
        self.points.append(e.mapPoint())
        self._typed_length = ""
        QToolTip.hideText()
        self._update_band()

    def canvasDoubleClickEvent(self, e):
        if not self._layer_valid:
            return
        self._ignore_next_release = True  # absorb the release that follows
        if self.points:
            self.points.pop()  # drop the vertex the double-click's own first click just added
        self._finish()

    def canvasMoveEvent(self, e):
        if not self.points:
            return
        self._last_mouse_point = e.mapPoint()
        if self._typed_length:
            self._refresh_typed_preview()
        else:
            self._show_preview(e.mapPoint())

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._typed_length and self.points:
                typed_pt = self._typed_point()
                if typed_pt is not None:
                    self._commit_point(typed_pt)
            else:
                self._finish()
        elif e.key() == Qt.Key.Key_Escape:
            self.reset()
        elif e.key() == Qt.Key.Key_Backspace:
            self._typed_length = self._typed_length[:-1]
            self._refresh_typed_preview()
        elif e.text() and (e.text().isdigit() or e.text() in ".,") and self.points:
            self._typed_length += e.text()
            self._refresh_typed_preview()

    def _typed_point(self):
        if not self.points or self._last_mouse_point is None:
            return None
        try:
            length = float(self._typed_length.replace(",", "."))
        except ValueError:
            return None
        last = self.points[-1]
        dx = self._last_mouse_point.x() - last.x()
        dy = self._last_mouse_point.y() - last.y()
        dist = math.hypot(dx, dy)
        if dist == 0:
            return None
        return QgsPointXY(last.x() + dx / dist * length, last.y() + dy / dist * length)

    def _refresh_typed_preview(self):
        if not self._typed_length:
            return
        typed_pt = self._typed_point()
        if typed_pt is not None:
            self._show_preview(typed_pt, typed=True)

    def _commit_point(self, point):
        self.points.append(point)
        self._typed_length = ""
        QToolTip.hideText()
        self._update_band()

    def _show_preview(self, point, typed=False):
        self._update_band(preview_point=point)
        last = self.points[-1]
        length = last.distance(point)
        text = f"Length: {_fmt(length)} m"
        preview_pts = self.points + [point]
        if len(preview_pts) >= 3:
            area = QgsGeometry.fromPolygonXY([preview_pts]).area()
            text += f"   Area: {_fmt(area)} m²"
        if typed:
            text += "  (typed - Enter to confirm)"
        QToolTip.showText(QCursor.pos(), text, self.canvas())

    def _update_band(self, preview_point=None):
        pts = self.points + ([preview_point] if preview_point else [])
        if len(pts) >= 3:
            self.rb.setToGeometry(QgsGeometry.fromPolygonXY([pts]), None)
        elif len(pts) == 2:
            self.rb.setToGeometry(QgsGeometry.fromPolylineXY(pts), None)

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