from collections import defaultdict
from qgis.core import (
    QgsProject, QgsSpatialIndex, QgsDistanceArea,
    QgsCoordinateTransform, Qgis, QgsFeatureRequest, QgsGeometry, NULL
)


def calculate_stats(aoi_geom, layer, class_field=None):
    canvas_crs = QgsProject.instance().crs()
    if layer.crs() != canvas_crs:
        xform = QgsCoordinateTransform(canvas_crs, layer.crs(), QgsProject.instance())
        aoi_geom = QgsGeometry(aoi_geom)
        aoi_geom.transform(xform)

    geom_type = layer.geometryType()
    da = QgsDistanceArea()
    da.setSourceCrs(layer.crs(), QgsProject.instance().transformContext())
    da.setEllipsoid(QgsProject.instance().ellipsoid())

    if class_field is None:
        renderer = layer.renderer()
        class_field = getattr(renderer, "classAttribute", lambda: None)() or None

    index = QgsSpatialIndex(layer.getFeatures())
    req = QgsFeatureRequest().setFilterFids(index.intersects(aoi_geom.boundingBox()))

    results, counts, total = defaultdict(float), defaultdict(int), 0.0
    for feat in layer.getFeatures(req):
        geom = feat.geometry()
        if not geom.intersects(aoi_geom):
            continue
        clipped = geom.intersection(aoi_geom)
        if clipped.isEmpty():
            continue

        if class_field:
            raw_key = feat[class_field]
            key = "(no value)" if raw_key == NULL else raw_key
        else:
            key = "Total"

        if geom_type == Qgis.GeometryType.Polygon:
            value = da.measureArea(clipped)
        elif geom_type == Qgis.GeometryType.Line:
            value = da.measureLength(clipped)
        else:
            value = 1

        results[key] += value
        counts[key] += 1
        total += value

    return {"results": dict(results), "counts": dict(counts), "total": total,
            "class_field": class_field,
            "metric": {Qgis.GeometryType.Polygon: "area",
                       Qgis.GeometryType.Line: "length",
                       Qgis.GeometryType.Point: "count"}[geom_type]}
