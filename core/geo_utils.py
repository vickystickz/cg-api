from shapely.geometry import shape, Point, Polygon, MultiPolygon
from shapely import wkt
import io
import json
import zipfile
import xml.etree.ElementTree as ET

SRID = 4326


def parse_geometry(geom):
    """Accept WKT, EWKT, GeoJSON dict, or GeoJSON string. Return EWKT MultiPolygon for PostGIS."""

    if isinstance(geom, str):
        geom = geom.strip()
        if not geom:
            raise ValueError("Geometry string cannot be empty")

        # Already EWKT — extract and re-parse the WKT portion
        if geom.upper().startswith("SRID="):
            wkt_part = geom.split(";", 1)[1]
            parsed = wkt.loads(wkt_part)
            return f"SRID={SRID};{_ensure_multi(parsed).wkt}"

        # Try WKT
        wkt_types = ("POINT", "LINESTRING", "POLYGON", "MULTIPOINT",
                     "MULTILINESTRING", "MULTIPOLYGON", "GEOMETRYCOLLECTION")
        if geom.upper().startswith(wkt_types):
            parsed = wkt.loads(geom)
            return f"SRID={SRID};{_ensure_multi(parsed).wkt}"

        # Try parsing as JSON string
        try:
            geom = json.loads(geom)
        except (json.JSONDecodeError, TypeError):
            raise ValueError(
                "Invalid geometry. Expected WKT, EWKT, or GeoJSON.")

    # GeoJSON dict
    if isinstance(geom, dict):
        if "type" in geom and "coordinates" in geom:
            parsed = shape(geom)
            return f"SRID={SRID};{_ensure_multi(parsed).wkt}"
        raise ValueError("GeoJSON must have 'type' and 'coordinates' fields")

    # Coordinate list [[lon, lat], ...]
    if isinstance(geom, list):
        if len(geom) == 2 and all(isinstance(v, (int, float)) for v in geom):
            point = Point(float(geom[1]), float(geom[0]))
            return f"SRID={SRID};{point.wkt}"
        if all(isinstance(v, (list, tuple)) and len(v) == 2 for v in geom):
            coords = [(float(c[0]), float(c[1])) for c in geom]
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            polygon = Polygon(coords)
            return f"SRID={SRID};{_ensure_multi(polygon).wkt}"

    raise ValueError("Geometry must be WKT, EWKT, GeoJSON, or coordinate list")


def _ensure_multi(geom):
    """Wrap Polygon as MultiPolygon for column type consistency."""
    if isinstance(geom, Polygon):
        return MultiPolygon([geom])
    return geom


# --- File Upload Parsing ---

def _extract_kml_namespace(tag: str) -> str:
    """Extract namespace URI from Clark notation {uri}localname."""
    if tag.startswith("{"):
        return tag[1:].split("}")[0]
    return ""


def _parse_ring_coords(ring_el, ns: str, boundary_tag: str):
    """Extract [lon, lat] pairs from a KML boundary element."""
    prefix = f"{{{ns}}}" if ns else ""
    boundary = ring_el.find(f"{prefix}{boundary_tag}")
    if boundary is None:
        return None
    ring = boundary.find(f"{prefix}LinearRing")
    if ring is None:
        return None
    coords_el = ring.find(f"{prefix}coordinates")
    if coords_el is None or not coords_el.text:
        return None
    pairs = []
    for token in coords_el.text.strip().split():
        parts = token.split(",")
        if len(parts) < 2:
            raise ValueError(f"Malformed KML coordinate token: {token!r}")
        pairs.append([float(parts[0]), float(parts[1])])
    return pairs


def _parse_kml_to_geojson(kml_bytes: bytes) -> dict:
    """Parse KML bytes and return a GeoJSON geometry dict."""
    root = ET.fromstring(kml_bytes)
    ns = _extract_kml_namespace(root.tag)
    prefix = f"{{{ns}}}" if ns else ""

    polygons = []
    for polygon_el in root.iter(f"{prefix}Polygon"):
        outer = _parse_ring_coords(polygon_el, ns, "outerBoundaryIs")
        if not outer:
            continue
        rings = [outer]
        inner = _parse_ring_coords(polygon_el, ns, "innerBoundaryIs")
        if inner:
            rings.append(inner)
        polygons.append(rings)

    if not polygons:
        raise ValueError("No Polygon elements found in KML file.")

    if len(polygons) == 1:
        return {"type": "Polygon", "coordinates": polygons[0]}
    return {"type": "MultiPolygon", "coordinates": polygons}


def _parse_kmz_to_geojson(kmz_bytes: bytes) -> dict:
    """Unzip a KMZ archive and parse the embedded KML."""
    with zipfile.ZipFile(io.BytesIO(kmz_bytes)) as zf:
        kml_names = [n for n in zf.namelist() if n.lower().endswith(".kml")]
        if not kml_names:
            raise ValueError("No .kml file found inside KMZ archive.")
        kml_bytes = zf.read(kml_names[0])
    return _parse_kml_to_geojson(kml_bytes)


def parse_boundary_file(filename: str, file_bytes: bytes) -> dict:
    """
    Parse a GeoJSON, KML, or KMZ boundary file and return a GeoJSON geometry dict.
    The returned dict can be passed directly to parse_geometry().
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in ("geojson", "json"):
        data = json.loads(file_bytes)
        if data.get("type") == "FeatureCollection":
            features = data.get("features") or []
            if not features:
                raise ValueError("GeoJSON FeatureCollection has no features.")
            data = features[0].get("geometry") or {}
        if "type" not in data or "coordinates" not in data:
            raise ValueError("GeoJSON must have 'type' and 'coordinates' fields.")
        return data

    if ext == "kml":
        return _parse_kml_to_geojson(file_bytes)

    if ext == "kmz":
        return _parse_kmz_to_geojson(file_bytes)

    raise ValueError(f"Unsupported file type: .{ext}. Accepted: .geojson, .json, .kml, .kmz")
