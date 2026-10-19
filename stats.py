from collections import defaultdict
from qgis.core import (
    Qgis, QgsCategorizedSymbolRenderer, QgsCoordinateTransform,
    QgsDistanceArea, QgsExpression, QgsExpressionContext,
    QgsExpressionContextUtils, QgsFeatureRequest, QgsGeometry, QgsProject,
    QgsVariantUtils,
)

# Geometry types the plugin can summarize, and what it measures for each.
METRICS = {
    Qgis.GeometryType.Polygon: "area",
    Qgis.GeometryType.Line: "length",
    Qgis.GeometryType.Point: "count",
}

NO_VALUE = "(no value)"


def clean_value(value):
    """Turn NULL attribute values (NULL in Qt5 builds, None in Qt6 builds)
    into a readable label so they can be used as a dictionary key."""
    if value is None or QgsVariantUtils.isNull(value):
        return NO_VALUE
    return value


def renderer_class_field(layer):
    """The field or expression a Categorized renderer groups by, or None if
    the layer is not symbolized with a Categorized renderer."""
    renderer = layer.renderer()
    if isinstance(renderer, QgsCategorizedSymbolRenderer):
        return renderer.classAttribute() or None
    return None


def _pick_fallback_class_field(layer):
    """No categorized renderer to read a class field from - fall back to the
    first non-ID field, or the only field if there's just one."""
    fields = [f.name() for f in layer.fields()]
    if not fields:
        return None
    if len(fields) == 1:
        return fields[0]
    id_like = {"fid", "id", "objectid"}
    for name in fields:
        lower = name.lower()
        if lower not in id_like and not lower.endswith("_id"):
            return name
    return fields[0]


def _class_value_getter(layer, class_field):
    """Return (getter, attributes) for grouping. getter maps a feature to its
    group key; attributes are the field names it needs, so only those have to
    be read from the data source. class_field can be a field name or, as a
    Categorized renderer allows, an expression. Returns (None, None) if it is
    neither a field nor a valid expression."""
    if not class_field:
        return (lambda feat: "Total"), []

    index = layer.fields().lookupField(class_field)
    if index >= 0:
        return (lambda feat: clean_value(feat.attribute(index))), [layer.fields().at(index).name()]

    expression = QgsExpression(class_field)
    if expression.hasParserError():
        return None, None
    context = QgsExpressionContext(
        QgsExpressionContextUtils.globalProjectLayerScopes(layer))
    expression.prepare(context)
    columns = expression.referencedColumns()
    attributes = None if QgsFeatureRequest.ALL_ATTRIBUTES in columns else sorted(columns)

    def evaluate(feat):
        context.setFeature(feat)
        return clean_value(expression.evaluate(context))
    return evaluate, attributes


def calculate_stats(aoi_geom, layer, class_field=None):
    geom_type = layer.geometryType()
    metric = METRICS.get(geom_type)
    if metric is None:
        raise ValueError("The layer has no point, line or polygon geometry.")

    canvas_crs = QgsProject.instance().crs()
    if layer.crs() != canvas_crs:
        xform = QgsCoordinateTransform(canvas_crs, layer.crs(), QgsProject.instance())
        aoi_geom = QgsGeometry(aoi_geom)
        aoi_geom.transform(xform)

    da = QgsDistanceArea()
    da.setSourceCrs(layer.crs(), QgsProject.instance().transformContext())
    da.setEllipsoid(QgsProject.instance().ellipsoid())

    if class_field is None:
        class_field = renderer_class_field(layer) or _pick_fallback_class_field(layer)
    get_key, attributes = _class_value_getter(layer, class_field)
    if get_key is None:
        class_field = _pick_fallback_class_field(layer)
        get_key, attributes = _class_value_getter(layer, class_field)

    # Only fetch features whose bounding box touches the drawn shape - the data
    # source answers this with its own spatial index (e.g. GeoPackage R-tree) -
    # and only the attributes needed for grouping.
    request = QgsFeatureRequest().setFilterRect(aoi_geom.boundingBox())
    if attributes is not None:
        request.setSubsetOfAttributes(attributes, layer.fields())

    # Prepared geometry: much faster for repeated tests against the same shape.
    engine = QgsGeometry.createGeometryEngine(aoi_geom.constGet())
    engine.prepareGeometry()

    results, counts, total = defaultdict(float), defaultdict(int), 0.0
    invalid_count = 0
    for feat in layer.getFeatures(request):
        geom = feat.geometry()
        if geom.isNull():
            continue
        if not engine.intersects(geom.constGet()):
            continue
        if not geom.isGeosValid():
            invalid_count += 1
            continue
        if engine.contains(geom.constGet()):
            clipped = geom  # completely inside - no clipping needed
        else:
            clipped = geom.intersection(aoi_geom)
            if clipped.isEmpty():
                continue

        if metric == "area":
            value = da.measureArea(clipped)
        elif metric == "length":
            value = da.measureLength(clipped)
        else:
            value = 1
        if value <= 0:
            # Only touches the drawn shape's boundary - nothing lies inside.
            continue

        key = get_key(feat)
        results[key] += value
        counts[key] += 1
        total += value

    return {"results": dict(results), "counts": dict(counts), "total": total,
            "class_field": class_field, "invalid_count": invalid_count,
            "metric": metric}
