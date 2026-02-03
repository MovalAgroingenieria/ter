# Copyright 2024-2026 Moval Agroingeniería
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

import base64
import re
import xml.etree.ElementTree as ET

from odoo import _, api, fields, models
from odoo.exceptions import UserError

KML_NS = "http://www.opengis.net/kml/2.2"


def _find_recursive(parent, local_name):
    """Find first descendant with given local name (ignoring namespace)."""
    if parent is None:
        return None
    for child in parent.iter():
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == local_name:
            return child
    return None


def _parse_kml_coordinates(text):
    """Parse KML coordinates string (lon,lat[,alt] tuples) into list of (lon, lat)."""
    if not text or not text.strip():
        return []
    coords = []
    for part in re.split(r"[\s\n]+", text.strip()):
        part = part.strip()
        if not part:
            continue
        vals = part.split(",")
        if len(vals) >= 2:
            try:
                lon, lat = float(vals[0]), float(vals[1])
                coords.append((lon, lat))
            except (ValueError, TypeError):
                continue
    return coords


def _coords_to_wkt_polygon(coords):
    """Build WKT POLYGON from list of (lon, lat) - must be closed (first == last)."""
    if len(coords) < 3:
        return None
    if coords[0] != coords[-1]:
        coords = list(coords) + [coords[0]]
    inner = ", ".join("%s %s" % (c[0], c[1]) for c in coords)
    return "POLYGON((%s))" % inner


def _wkt_4326_to_ewkt_25830(env, wkt_4326):
    """Convert WKT in EPSG:4326 to EWKT in EPSG:25830 using PostGIS."""
    if not wkt_4326 or not wkt_4326.strip():
        return None
    env.cr.execute(
        """
        SELECT ST_AsText(ST_Transform(ST_GeomFromText(%s, 4326), 25830))
        """,
        (wkt_4326.strip(),),
    )
    row = env.cr.fetchone()
    if not row or not row[0]:
        return None
    return "SRID=25830;%s" % row[0]


class WizardImportKml(models.TransientModel):
    _name = "wizard.import.kml"
    _description = "Import KML file to Parcels or Properties"

    kml_file = fields.Binary(
        string="KML File",
        required=True,
        help="KML file with Placemarks containing Polygon geometries (WGS84).",
    )
    kml_filename = fields.Char(string="Filename")
    target_model = fields.Selection(
        [
            ("ter.parcel", "Parcels"),
            ("ter.property", "Properties"),
        ],
        string="Import to",
        default="ter.parcel",
        required=True,
    )
    municipality_id = fields.Many2one(
        "res.municipality",
        string="Municipality",
        required=True,
        help="Municipality assigned to all imported records.",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Manager / Holder",
        help="Optional: assign as manager (property) or use for parcel partner link.",
    )
    name_prefix = fields.Char(
        string="Name prefix",
        help="Optional prefix for record names (e.g. 'PARCEL-' or 'FINCA-').",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("done", "Done"),
        ],
        default="draft",
        readonly=True,
    )
    result_message = fields.Text(readonly=True)

    def _parse_kml_placemarks(self):
        """Parse KML file and yield (name, description, polygon_wkt_4326) for each Placemark."""
        self.ensure_one()
        if not self.kml_file:
            return
        raw = base64.b64decode(self.kml_file)
        try:
            root = ET.fromstring(raw)
        except ET.ParseError as e:
            raise UserError(_("Invalid KML XML: %s") % str(e)) from e

        def iter_placemarks(node):
            tag = node.tag.split("}")[-1] if "}" in node.tag else node.tag
            if tag == "Placemark":
                yield node
            for child in node:
                yield from iter_placemarks(child)

        for pm in iter_placemarks(root):
            name_elem = _find_recursive(pm, "name")
            desc_elem = _find_recursive(pm, "description")
            name = (name_elem.text or "").strip() if name_elem is not None else ""
            description = (desc_elem.text or "").strip() if desc_elem is not None else ""

            poly = _find_recursive(pm, "Polygon")
            if poly is None:
                continue
            outer = _find_recursive(poly, "outerBoundaryIs") or _find_recursive(poly, "outerBoundary")
            if outer is None:
                continue
            ring = _find_recursive(outer, "LinearRing") or _find_recursive(outer, "linearRing")
            if ring is None:
                continue
            coords_elem = _find_recursive(ring, "coordinates")
            if coords_elem is None or not (coords_elem.text or "").strip():
                continue

            coords = _parse_kml_coordinates(coords_elem.text or "")
            if len(coords) < 3:
                continue
            wkt = _wkt_4326_to_ewkt_25830(self.env, _coords_to_wkt_polygon(coords))
            if not wkt:
                continue
            yield (name or _("Unnamed"), description, wkt)

    def action_import(self):
        self.ensure_one()
        if not self.municipality_id:
            raise UserError(_("Municipality is required."))
        prefix = (self.name_prefix or "").strip()
        created = []
        errors = []
        used_codes = set()
        for i, (name, _desc, ewkt) in enumerate(self._parse_kml_placemarks()):
            base_code = (prefix + name) if prefix else (name or "KML-%s" % (i + 1))
            base_code = (base_code or "KML-%s" % (i + 1))[:45]
            code = base_code
            suffix = 1
            while code in used_codes:
                code = "%s-%s" % (base_code[:40], suffix)
                suffix += 1
            used_codes.add(code)
            code = code[:50]
            try:
                if self.target_model == "ter.parcel":
                    vals = {
                        "alphanum_code": code,
                        "municipality_id": self.municipality_id.id,
                        "area_official": 0,
                        "geom_ewkt": ewkt,
                    }
                    if self.partner_id and self.partner_id.is_holder:
                        profile = self.env.ref("base_ter.ter_profile_01")
                        vals["partnerlink_ids"] = [
                            (0, 0, {
                                "partner_id": self.partner_id.id,
                                "is_main": True,
                                "percentage": 100,
                                "profile_id": profile.id,
                            })
                        ]
                    parcel = self.env["ter.parcel"].create(vals)
                    created.append(parcel.display_name)
                else:
                    prop = self.env["ter.property"].create({
                        "alphanum_code": code,
                        "municipality_id": self.municipality_id.id,
                        "partner_id": self.partner_id.id if self.partner_id else False,
                        "geom_ewkt": ewkt,
                    })
                    created.append(prop.display_name)
            except Exception as e:
                errors.append("%s: %s" % (code, str(e)))
        msg_parts = []
        if created:
            msg_parts.append(_("Created %s record(s): %s") % (len(created), ", ".join(created[:10])))
            if len(created) > 10:
                msg_parts.append(_("... and %s more.") % (len(created) - 10))
        if errors:
            msg_parts.append(_("Errors: %s") % "; ".join(errors[:5]))
            if len(errors) > 5:
                msg_parts.append(_("... and %s more errors.") % (len(errors) - 5))
        self.write({
            "state": "done",
            "result_message": "\n".join(msg_parts) if msg_parts else _("No polygons found in KML."),
        })
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
