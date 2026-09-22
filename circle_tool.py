import math
from qgis.gui import QgsMapTool
from qgis.core import Qgis, QgsGeometry
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtWidgets import QToolTip


def _fmt(value, decimals=0):
    """Format a number with a space as the thousands separator, avoiding
    a comma that reads as a decimal separator in German/Austrian locales."""
    return f"{value:,.{decimals}f}".replace(",", " ")


class CircleTool(QgsMapTool):
    """Click to set center, click again (or type a radius and press Enter)
    to finish. Escape or right-click cancels."""

    def __init__(self, canvas, rubber_band, on_finished):
        super().__init__(canvas)
        self.rb = rubber_band
        self.on_finished = on_finished
        self.center = None
        self._layer_valid = True
        self._typed_radius = ""

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
            QToolTip.showText(
                QCursor.pos(), "Move mouse to set radius, or type a number and press Enter",
                self.canvas())
        else:
            self._finish(self.center.distance(point))

    def canvasMoveEvent(self, e):
        if self.center is not None and not self._typed_radius:
            self._show_preview(self.center.distance(e.mapPoint()))

    def keyPressEvent(self, e):
        if self.center is None:
            if e.key() == Qt.Key.Key_Escape:
                self.reset()
            return

        if e.key() == Qt.Key.Key_Escape:
            self.reset()
        elif e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._typed_radius:
                try:
                    self._finish(float(self._typed_radius.replace(",", ".")))
                except ValueError:
                    pass
        elif e.key() == Qt.Key.Key_Backspace:
            self._typed_radius = self._typed_radius[:-1]
            self._show_typed_preview()
        elif e.text() and (e.text().isdigit() or e.text() in ".,"):
            self._typed_radius += e.text()
            self._show_typed_preview()

    def _show_typed_preview(self):
        if not self._typed_radius:
            return
        try:
            self._show_preview(float(self._typed_radius.replace(",", ".")), typed=True)
        except ValueError:
            pass

    def _show_preview(self, radius, typed=False):
        geom = QgsGeometry.fromPointXY(self.center).buffer(radius, 48)
        self.rb.setToGeometry(geom, None)
        area = math.pi * radius * radius
        suffix = "  (typed - Enter to confirm)" if typed else ""
        QToolTip.showText(
            QCursor.pos(), f"Radius: {_fmt(radius)} m   Area: {_fmt(area)} m²{suffix}", self.canvas())

    def _finish(self, radius):
        geom = QgsGeometry.fromPointXY(self.center).buffer(radius, 48)
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