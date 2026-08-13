from qgis.gui import QgsMapTool
from qgis.core import Qgis, QgsGeometry
from qgis.PyQt.QtCore import Qt


class PolygonTool(QgsMapTool):
    """Click to add vertices. Double-click, right-click, or Enter finishes.
    Escape cancels."""

    def __init__(self, canvas, rubber_band, on_finished):
        super().__init__(canvas)
        self.rb = rubber_band
        self.on_finished = on_finished
        self.points = []
        self._ignore_next_release = False

    def canvasReleaseEvent(self, e):
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
        self._update_band()

    def canvasDoubleClickEvent(self, e):
        self._ignore_next_release = True  # absorb the release that follows
        if self.points:
            self.points.pop()  # drop the vertex the double-click's own first click just added
        self._finish()

    def canvasMoveEvent(self, e):
        if self.points:
            self._update_band(preview_point=e.mapPoint())

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._finish()
        elif e.key() == Qt.Key.Key_Escape:
            self.reset()

    def _update_band(self, preview_point=None):
        pts = self.points + ([preview_point] if preview_point else [])
        if len(pts) >= 3:
            self.rb.setToGeometry(QgsGeometry.fromPolygonXY([pts]), None)
        elif len(pts) == 2:
            self.rb.setToGeometry(QgsGeometry.fromPolylineXY(pts), None)

    def _clear_sketch(self):
        self.points = []
        self.rb.reset(Qgis.GeometryType.Polygon)

    def _finish(self):
        if len(self.points) >= 3:
            geom = QgsGeometry.fromPolygonXY([self.points])
            self.rb.setToGeometry(geom, None)  # replace the live-cursor preview with the real final shape
            self.points = []
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
