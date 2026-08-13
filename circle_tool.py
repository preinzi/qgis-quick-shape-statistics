from qgis.gui import QgsMapTool
from qgis.core import Qgis, QgsGeometry
from qgis.PyQt.QtCore import Qt


class CircleTool(QgsMapTool):
    """Click to set center, click again to set radius. Escape cancels."""

    def __init__(self, canvas, rubber_band, on_finished):
        super().__init__(canvas)
        self.rb = rubber_band
        self.on_finished = on_finished
        self.center = None

    def canvasReleaseEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton:
            return
        point = e.mapPoint()
        if self.center is None:
            self.rb.reset(Qgis.GeometryType.Polygon)
            self.center = point
        else:
            radius = self.center.distance(point)
            geom = QgsGeometry.fromPointXY(self.center).buffer(radius, 48)
            self.rb.setToGeometry(geom, None)
            self.center = None
            if not geom.isEmpty():
                self.on_finished(geom)

    def canvasMoveEvent(self, e):
        if self.center is not None:
            radius = self.center.distance(e.mapPoint())
            self.rb.setToGeometry(QgsGeometry.fromPointXY(self.center).buffer(radius, 48), None)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.reset()

    def reset(self):
        self.center = None
        self.rb.reset(Qgis.GeometryType.Polygon)

    def deactivate(self):
        self.reset()
        super().deactivate()
