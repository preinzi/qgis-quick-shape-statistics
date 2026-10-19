from qgis.gui import QgsMapTool
from qgis.core import Qgis
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtWidgets import QToolTip
from .geodesy import Geodesy
from .utils import fmt_number, parse_number

NUMBER_KEYS = "0123456789.,"


class CircleTool(QgsMapTool):
    """Click to set center, click again (or type a radius and press Enter)
    to finish. Escape or right-click cancels. The radius is a true distance
    in meters on the ellipsoid, whatever the map canvas CRS."""

    def __init__(self, canvas, rubber_band, on_finished):
        super().__init__(canvas)
        self.rb = rubber_band
        self.on_finished = on_finished
        self.center = None
        self._layer_valid = True
        self._typed_radius = ""
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
        if e.button() == Qt.MouseButton.RightButton:
            self.reset()
            return
        if e.button() != Qt.MouseButton.LeftButton:
            return
        point = e.mapPoint()
        if self.center is None:
            self.rb.reset(Qgis.GeometryType.Polygon)
            self.center = point
            self._typed_radius = ""
            self._geodesy = None  # pick up the current canvas CRS for this circle
            QToolTip.showText(
                QCursor.pos(), "Move mouse to set radius, or type a number and press Enter",
                self.canvas())
        else:
            # A typed radius wins over the mouse position, same as pressing Enter.
            typed = parse_number(self._typed_radius) if self._typed_radius else None
            self._finish(typed if typed else self._geo().distance(self.center, point))

    def canvasMoveEvent(self, e):
        self._last_mouse_point = e.mapPoint()
        if self.center is not None and not self._typed_radius:
            self._show_preview(self._geo().distance(self.center, self._last_mouse_point))

    def keyPressEvent(self, e):
        # Note: in QGIS a map tool marks a key as handled with e.ignore() (yes,
        # backwards). Otherwise QGIS also processes it - Backspace/Delete would
        # run "Delete Selected" on the active layer.
        key, text = e.key(), e.text()
        if key == Qt.Key.Key_Escape:
            self.reset()
            e.ignore()
        elif key in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            if self.center is not None:
                self._typed_radius = self._typed_radius[:-1]
                self._refresh_preview()
            e.ignore()
        elif self.center is None:
            return
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            radius = parse_number(self._typed_radius) if self._typed_radius else None
            if radius:
                self._finish(radius)
            e.ignore()
        elif len(text) == 1 and text in NUMBER_KEYS:
            self._typed_radius += text
            self._refresh_preview()
            e.ignore()

    def _refresh_preview(self):
        """Typed radius if there is one, otherwise follow the mouse again."""
        if self._typed_radius:
            radius = parse_number(self._typed_radius)
            if radius is not None:
                self._show_preview(radius, typed=True)
        elif self._last_mouse_point is not None:
            self._show_preview(self._geo().distance(self.center, self._last_mouse_point))

    def _show_preview(self, radius, typed=False):
        geom = self._geo().circle(self.center, radius)
        self.rb.setToGeometry(geom, None)
        area = self._geo().area(geom)
        suffix = "  (typed - Enter to confirm)" if typed else ""
        QToolTip.showText(
            QCursor.pos(),
            f"Radius: {fmt_number(radius)} m   Area: {fmt_number(area)} m²{suffix}",
            self.canvas())

    def _finish(self, radius):
        geom = self._geo().circle(self.center, radius)
        self.rb.setToGeometry(geom, None)
        self.center = None
        self._typed_radius = ""
        QToolTip.hideText()
        if not geom.isEmpty():
            self.on_finished(geom)

    def reset(self):
        self.center = None
        self._typed_radius = ""
        self.rb.reset(Qgis.GeometryType.Polygon)
        QToolTip.hideText()

    def deactivate(self):
        self.reset()
        super().deactivate()
