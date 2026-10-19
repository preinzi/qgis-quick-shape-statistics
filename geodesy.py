"""Geodesic helpers for the drawing tools.

Radius, segment length and area are measured on the ellipsoid in meters, so
they are correct whatever the map canvas CRS is - a projected CRS, a
geographic one such as EPSG:4326, or Web Mercator (EPSG:3857), where flat
map units are far from real meters.
"""
import math
from qgis.core import (
    QgsCoordinateTransform, QgsDistanceArea, QgsGeometry, QgsPointXY, QgsProject,
)

CIRCLE_VERTICES = 192  # same vertex density as the former buffer(radius, 48)


class Geodesy:
    """Measurements and constructions for points given in the canvas CRS.

    Uses the geographic CRS that the canvas CRS is based on (same datum), so
    no datum transformation is involved - only the map projection itself.
    Falls back to flat map-unit math if the CRS is unknown.
    """

    def __init__(self, crs):
        context = QgsProject.instance().transformContext()
        geographic = crs.toGeographicCrs() if crs.isValid() else None
        self.geodesic = geographic is not None and geographic.isValid()
        if not self.geodesic:
            return
        ellipsoid = geographic.ellipsoidAcronym() or "EPSG:7030"  # WGS 84 fallback

        self._to_geo = QgsCoordinateTransform(crs, geographic, context)
        self._from_geo = QgsCoordinateTransform(geographic, crs, context)

        self._da_geo = QgsDistanceArea()  # works on lon/lat of the geographic CRS
        self._da_geo.setSourceCrs(geographic, context)
        self._da_geo.setEllipsoid(ellipsoid)

        self._da = QgsDistanceArea()  # works on canvas CRS coordinates
        self._da.setSourceCrs(crs, context)
        self._da.setEllipsoid(ellipsoid)

    def distance(self, p1, p2):
        """Distance between two canvas points, in meters."""
        if not self.geodesic:
            return p1.distance(p2)
        return self._da.measureLine(p1, p2)

    def area(self, geom):
        """Area of a polygon in canvas coordinates, in square meters."""
        if not self.geodesic:
            return geom.area()
        return self._da.measureArea(geom)

    def circle(self, center, radius):
        """Polygon of all points at `radius` meters from `center`."""
        if not self.geodesic:
            return QgsGeometry.fromPointXY(center).buffer(radius, CIRCLE_VERTICES // 4)
        center_geo = self._to_geo.transform(center)
        ring = [self._da_geo.computeSpheroidProject(center_geo, radius,
                                                    2 * math.pi * i / CIRCLE_VERTICES)
                for i in range(CIRCLE_VERTICES)]
        ring.append(ring[0])
        geom = QgsGeometry.fromPolygonXY([ring])
        geom.transform(self._from_geo)
        return geom

    def point_towards(self, start, toward, distance):
        """Point `distance` meters from `start` in the direction of `toward`,
        or None if both points are the same."""
        if start == toward:
            return None
        if not self.geodesic:
            dx, dy = toward.x() - start.x(), toward.y() - start.y()
            length = math.hypot(dx, dy)
            return QgsPointXY(start.x() + dx / length * distance,
                              start.y() + dy / length * distance)
        azimuth = self._da.bearing(start, toward)
        target = self._da_geo.computeSpheroidProject(
            self._to_geo.transform(start), distance, azimuth)
        return self._from_geo.transform(target)
