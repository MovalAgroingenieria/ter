# Copyright 2024-2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
from xml.etree import ElementTree

import requests
from psycopg2 import Error as PsycopgError

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

CADASTRE_WFS_NS = {
    "gml": "http://www.opengis.net/gml/3.2",
    "cp": "http://inspire.ec.europa.eu/schemas/cp/4.0",
}


class TerParcel(models.Model):
    _inherit = "ter.parcel"

    MAX_SIZE_OFFICIAL_CODE_URBAN = 50
    MAX_SIZE_CADASTRAL_FIELD = 10

    SIZE_RC1 = 7
    SIZE_RC2 = 7

    REQUEST_TIMEOUT = 5
    REQUEST_TIMEOUT_CADASTRE_WFS = 60

    _SIZE_MUNICIPALITY_CADASTRAL_CODE = 5
    _SIZE_CADASTRAL_SECTOR = 1
    _SIZE_CADASTRAL_POLYGON = 3
    _SIZE_CADASTRAL_PARCEL = 5

    _URL_CADASTRAL_DATA = (
        "http://ovc.catastro.meh.es/ovcservweb/"
        "OVCSWLocalizacionRC/OVCCallejero.asmx/Consulta_DNPRC?"
        "Provincia=&Municipio=&RC="
    )
    _URL_CADASTRAL_FORM = (
        "https://www1.sedecatastro.gob.es/"
        "CYCBienInmueble/OVCListaBienes.aspx?del=&muni=&rc1=rc1val&rc2=rc2val"
    )
    _URL_CADASTRE_WFS = "https://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx"
    _CADASTRE_WFS_SOURCE_SRID = 25830
    _CADASTRE_WFS_VERIFY_SSL = False

    _CADASTRE_WFS_USER_AGENT = "MovalAgro-Odoo-WFS/1.0"
    _CADASTRE_MATCH_TARGET_SRID = 25830
    _CADASTRE_REFCAT_LENGTH = 14

    _AUTOMATIC_UPDATE_CADASTRAL_DATA = True

    parcel_type = fields.Selection(
        selection=[
            ("01_R", "Rustic"),
            ("02_U", "Urban"),
        ],
        default="01_R",
        required=True,
        index=True,
    )

    official_code_urban = fields.Char(size=MAX_SIZE_OFFICIAL_CODE_URBAN)

    cadastral_sector = fields.Char(size=MAX_SIZE_CADASTRAL_FIELD, default="A")
    cadastral_polygon = fields.Char(size=MAX_SIZE_CADASTRAL_FIELD)
    cadastral_parcel = fields.Char(size=MAX_SIZE_CADASTRAL_FIELD)

    official_code = fields.Char(
        store=True,
        compute="_compute_official_code",
        readonly=True,
    )

    cadastral_area = fields.Integer(default=0)

    cadastral_subparcel = fields.Char(size=MAX_SIZE_CADASTRAL_FIELD)

    official_code_with_subparcel = fields.Char(
        store=True,
        index=True,
        compute="_compute_official_code_with_subparcel",
        readonly=True,
    )

    cadastre_gis_import_enabled = fields.Boolean(
        compute="_compute_cadastre_gis_import_enabled"
    )

    cadastre_match_state = fields.Selection(
        selection=[
            ("none", "Not scanned"),
            ("suggested", "Suggestion available"),
            ("no_match", "No cadastral match"),
            ("applied", "Applied"),
        ],
        default="none",
        copy=False,
        index=True,
        help="Result of the last background scan against the Cadastre WFS.",
    )
    cadastre_match_refcat = fields.Char(
        copy=False,
        help="Cadastral reference of the best overlapping cadastral parcel.",
    )
    cadastre_match_intersection = fields.Float(
        digits=(5, 2),
        copy=False,
        help="Overlap percentage of the best overlapping cadastral parcel.",
    )
    cadastre_match_date = fields.Datetime(copy=False)

    @api.depends_context("uid")
    def _compute_cadastre_gis_import_enabled(self):
        enabled = bool(self.env.company.cadastre_gis_import_enabled)
        for record in self:
            record.cadastre_gis_import_enabled = enabled

    @api.depends("official_code", "cadastral_subparcel")
    def _compute_official_code_with_subparcel(self):
        for record in self:
            if not record.official_code:
                record.official_code_with_subparcel = ""
                continue
            if record.cadastral_subparcel:
                record.official_code_with_subparcel = (
                    f"{record.official_code}-{record.cadastral_subparcel}"
                )
            else:
                record.official_code_with_subparcel = record.official_code

    @api.depends(
        "parcel_type",
        "municipality_id",
        "municipality_id.cadastral_code",
        "official_code_urban",
        "cadastral_sector",
        "cadastral_polygon",
        "cadastral_parcel",
    )
    def _compute_official_code(self):
        for record in self:
            record.official_code = record._get_official_code() or ""

    def _get_official_code(self):
        self.ensure_one()

        if self.parcel_type == "01_R":
            if not (
                self.municipality_id
                and self.municipality_id.cadastral_code
                and self.cadastral_sector
                and self.cadastral_polygon
                and self.cadastral_parcel
            ):
                return ""

            return (
                f"{self.municipality_id.cadastral_code}"
                f"{self.cadastral_sector}"
                f"{(self.cadastral_polygon or '').zfill(self._SIZE_CADASTRAL_POLYGON)}"
                f"{(self.cadastral_parcel or '').zfill(self._SIZE_CADASTRAL_PARCEL)}"
            )

        if self.official_code_urban:
            return (self.official_code_urban or "").strip()

        return ""

    @api.constrains("cadastral_area")
    def _check_cadastral_area_non_negative(self):
        for record in self:
            if record.cadastral_area is not None and record.cadastral_area < 0:
                raise ValidationError(
                    self.env._('Incorrect value for "Cadastral Area (m²)".')
                )

    @api.constrains("official_code")
    def _check_official_code_length(self):
        expected_len = (
            self._SIZE_MUNICIPALITY_CADASTRAL_CODE
            + self._SIZE_CADASTRAL_SECTOR
            + self._SIZE_CADASTRAL_POLYGON
            + self._SIZE_CADASTRAL_PARCEL
        )
        for record in self:
            if record.parcel_type != "01_R" or not record.official_code:
                continue
            if len(record.official_code) != expected_len:
                raise ValidationError(
                    self.env._("The length of the cadastral reference is not correct.")
                )

    @api.constrains("official_code_with_subparcel")
    def _check_official_code_with_subparcel_unique(self):
        for record in self:
            if not record.official_code_with_subparcel:
                continue
            if self.search_count(
                [
                    (
                        "official_code_with_subparcel",
                        "=",
                        record.official_code_with_subparcel,
                    ),
                    ("id", "!=", record.id),
                ]
            ):
                raise ValidationError(
                    self.env._(
                        "Repeated cadastral reference (with subparcel). "
                        "Check archived parcels."
                    )
                )

    def _sanitize_vals(self, vals):
        vals = dict(vals or {})

        if vals.get("cadastral_sector"):
            vals["cadastral_sector"] = (vals["cadastral_sector"] or "").strip().upper()

        if "cadastral_polygon" in vals:
            vals["cadastral_polygon"] = self._normalize_cadastral_numeric_field(
                vals.get("cadastral_polygon"),
                size=self._SIZE_CADASTRAL_POLYGON,
            )

        if "cadastral_parcel" in vals:
            vals["cadastral_parcel"] = self._normalize_cadastral_numeric_field(
                vals.get("cadastral_parcel"),
                size=self._SIZE_CADASTRAL_PARCEL,
            )

        if "parcel_type" in vals:
            if vals["parcel_type"] == "01_R":
                vals["official_code_urban"] = False
            else:
                vals["cadastral_sector"] = False
                vals["cadastral_polygon"] = False
                vals["cadastral_parcel"] = False

        if vals.get("cadastral_subparcel"):
            vals["cadastral_subparcel"] = (
                (vals["cadastral_subparcel"] or "").strip().upper()
            )

        return vals

    def _normalize_cadastral_numeric_field(self, value, size):
        if not value:
            return False
        try:
            number = int(str(value).strip())
        except (TypeError, ValueError):
            return False
        if number <= 0:
            return False
        return str(number).zfill(size)

    def _process_vals(self, vals):
        vals = self._sanitize_vals(vals)
        return super()._process_vals(vals)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._maybe_update_cadastral_area()
        return records

    def write(self, vals):
        vals = self._sanitize_vals(vals)
        tracked = {
            "parcel_type",
            "municipality_id",
            "official_code_urban",
            "cadastral_sector",
            "cadastral_polygon",
            "cadastral_parcel",
        }
        need_update = bool(tracked.intersection(vals.keys()))
        res = super().write(vals)
        if need_update:
            self._maybe_update_cadastral_area()
        return res

    def _maybe_update_cadastral_area(self):
        if not self._AUTOMATIC_UPDATE_CADASTRAL_DATA:
            return
        for record in self:
            if not record.official_code:
                continue
            if record.cadastral_area:
                continue
            record.cadastral_area = record._get_cadastral_area()

    def _get_cadastral_area(self):
        self.ensure_one()
        if not self.official_code:
            return 0

        try:
            resp = requests.get(
                f"{self._URL_CADASTRAL_DATA}{self.official_code}",
                timeout=self.REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.RequestException:
            return 0

        try:
            cadastral_data = ElementTree.fromstring(resp.content)
        except ElementTree.ParseError:
            return 0

        prefix = ""
        pos_closing = cadastral_data.tag.find("}")
        if pos_closing != -1:
            prefix = cadastral_data.tag[: pos_closing + 1]

        try:
            number_of_items = int(cadastral_data[0][0].text)
        except (IndexError, TypeError, ValueError):
            return 0

        if number_of_items != 1:
            return 0

        cadastral_area = 0
        for item in cadastral_data.iter(f"{prefix}ssp"):
            try:
                cadastral_area += int(item.text or 0)
            except (TypeError, ValueError):
                continue
        return cadastral_area

    def action_show_cadastral_form(self):
        self.ensure_one()
        if not self.official_code:
            return False

        expected_len = self.SIZE_RC1 + self.SIZE_RC2
        if len(self.official_code) != expected_len:
            return False

        rc1 = self.official_code[: self.SIZE_RC1]
        rc2 = self.official_code[self.SIZE_RC1 :]
        cadastral_link = self._URL_CADASTRAL_FORM.replace("rc1val", rc1).replace(
            "rc2val", rc2
        )
        return {
            "type": "ir.actions.act_url",
            "url": cadastral_link,
            "target": "new",
        }

    def _is_cadastre_gis_import_enabled(self):
        return bool(self.env.company.cadastre_gis_import_enabled)

    def _extract_cadastre_multisurface_gml(self, xml_content):
        try:
            root = ElementTree.fromstring(xml_content)
        except ElementTree.ParseError as exc:
            raise ValueError(
                self.env._("Malformed XML received from Cadastre service.")
            ) from exc

        namespaces = {
            "gml": "http://www.opengis.net/gml/3.2",
            "cp": "http://inspire.ec.europa.eu/schemas/cp/4.0",
        }

        for parcel in root.findall(".//cp:CadastralParcel", namespaces):
            geom = parcel.find(".//gml:MultiSurface", namespaces)
            if geom is None:
                continue
            geom_gml = ElementTree.tostring(geom, encoding="unicode")
            geom_gml = self._sanitize_cadastre_geometry_gml(geom_gml)
            if "posList" in geom_gml:
                return geom_gml

        raise ValueError(self.env._("No valid geometry found in Cadastre response."))

    def _sanitize_cadastre_geometry_gml(self, geometry_gml):
        """Remove embedded srsName values that PostGIS cannot resolve."""
        if not geometry_gml:
            return geometry_gml
        try:
            root = ElementTree.fromstring(geometry_gml)
        except ElementTree.ParseError:
            return geometry_gml

        for element in root.iter():
            attrs_to_remove = []
            for attr_name in element.attrib:
                if attr_name.rsplit("}", 1)[-1] == "srsName":
                    attrs_to_remove.append(attr_name)
            for attr_name in attrs_to_remove:
                del element.attrib[attr_name]

        return ElementTree.tostring(root, encoding="unicode")

    def _fetch_cadastre_geometry_gml(self, official_code):
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "STOREDQUERIE_ID": "GetParcel",
            "refcat": official_code,
            "srsname": "EPSG:%s" % self._CADASTRE_WFS_SOURCE_SRID,
        }
        response = requests.get(
            self._URL_CADASTRE_WFS,
            params=params,
            timeout=self.REQUEST_TIMEOUT_CADASTRE_WFS,
            verify=self._CADASTRE_WFS_VERIFY_SSL,
        )
        response.raise_for_status()
        return self._extract_cadastre_multisurface_gml(response.content)

    def _split_cadastre_import_candidates(self):
        candidates = self.browse()
        already_with_geometry = []
        without_official_code = []

        for record in self:
            if not record.official_code:
                without_official_code.append(record.display_name)
                continue
            if record.geom_ewkt:
                already_with_geometry.append(record.display_name)
                continue
            candidates |= record

        return candidates, already_with_geometry, without_official_code

    def _import_cadastre_geometry_candidates(self, candidates):
        created = []
        errors = []

        for record in candidates:
            try:
                geometry_gml = record._fetch_cadastre_geometry_gml(record.official_code)
                created_ok = record._set_gis_geometry_from_gml(  # pylint: disable=protected-access
                    geometry_gml,
                    source_srid=self._CADASTRE_WFS_SOURCE_SRID,
                    target_srid=25830,
                )
                if created_ok:
                    created.append(record.display_name)
                else:
                    errors.append(
                        self.env._(
                            "%(parcel)s: %(error)s",
                            parcel=record.display_name,
                            error=self.env._("Geometry could not be stored."),
                        )
                    )
            except (requests.RequestException, ValueError) as exc:
                errors.append(
                    self.env._(
                        "%(parcel)s: %(error)s",
                        parcel=record.display_name,
                        error=str(exc),
                    )
                )

        return created, errors

    def _build_cadastre_import_lines(
        self,
        created,
        already_with_geometry,
        without_official_code,
        errors,
    ):
        lines = [self.env._("Summary:")]
        lines.append(self.env._("- Created geometries: %(count)s", count=len(created)))
        lines.append(
            self.env._(
                "- Already had geometry: %(count)s",
                count=len(already_with_geometry),
            )
        )
        lines.append(
            self.env._(
                "- Without cadastral reference: %(count)s",
                count=len(without_official_code),
            )
        )
        lines.append(self.env._("- Errors: %(count)s", count=len(errors)))

        if created:
            lines.append(
                self.env._(
                    "Created geometry names: %(names)s",
                    names=self._format_summary_names(created),
                )
            )
        if already_with_geometry:
            lines.append(
                self.env._(
                    "Already with geometry names: %(names)s",
                    names=self._format_summary_names(already_with_geometry),
                )
            )
        if without_official_code:
            lines.append(
                self.env._(
                    "Without cadastral reference names: %(names)s",
                    names=self._format_summary_names(without_official_code),
                )
            )
        self._append_error_names_line(lines, errors)  # pylint: disable=protected-access
        return lines

    def action_get_gis_data_from_cadastre(self):
        if not self._is_cadastre_gis_import_enabled():
            raise UserError(
                self.env._(
                    "Cadastre GIS import is disabled in Territory settings. "
                    "Enable it to import parcel geometries."
                )
            )
        (
            candidates,
            already_with_geometry,
            without_official_code,
        ) = self._split_cadastre_import_candidates()
        created, errors = self._import_cadastre_geometry_candidates(candidates)
        lines = self._build_cadastre_import_lines(
            created,
            already_with_geometry,
            without_official_code,
            errors,
        )
        message_type = self._get_notification_type(bool(errors), bool(created))
        return self._build_result_message_action(
            self.env._("Cadastre GIS import"),
            lines,
            message_type,
        )

    def _cadastre_match_bbox(self):
        """Return the parcel geometry envelope in the WFS source SRID."""
        self.ensure_one()
        self.env.cr.execute(
            "SELECT ST_XMin(e), ST_YMin(e), ST_XMax(e), ST_YMax(e) FROM ("
            "SELECT ST_Envelope(geom) AS e FROM ter_gis_parcel "
            "WHERE name = %s AND geom IS NOT NULL) sub",
            (self.name,),
        )
        row = self.env.cr.fetchone()
        if not row or row[0] is None:
            return None
        return row

    def _cadastre_match_wfs_request(self, bbox):
        """Query the Cadastre WFS for cadastral parcels within ``bbox``."""
        srid = self._CADASTRE_WFS_SOURCE_SRID
        params = {
            "service": "wfs",
            "version": "2.0.0",
            "request": "getfeature",
            "typenames": "cp.cadastralparcel",
            "srsname": "EPSG::%s" % srid,
            "bbox": "%f,%f,%f,%f" % (bbox[0], bbox[1], bbox[2], bbox[3]),
        }
        response = requests.get(
            self._URL_CADASTRE_WFS,
            params=params,
            headers={"User-Agent": self._CADASTRE_WFS_USER_AGENT},
            timeout=self.REQUEST_TIMEOUT_CADASTRE_WFS,
            verify=self._CADASTRE_WFS_VERIFY_SSL,
        )
        response.raise_for_status()
        return response.content

    def _cadastre_match_parse_features(self, xml_content):
        """Return ``[{refcat, geom_gml}]`` from a WFS FeatureCollection."""
        try:
            root = ElementTree.fromstring(xml_content)
        except ElementTree.ParseError as exc:
            raise ValueError(
                self.env._("Malformed XML received from Cadastre service.")
            ) from exc
        features = []
        for parcel in root.findall(".//cp:CadastralParcel", CADASTRE_WFS_NS):
            ref_el = parcel.find(".//cp:nationalCadastralReference", CADASTRE_WFS_NS)
            refcat = (ref_el.text or "").strip() if ref_el is not None else ""
            geom = parcel.find(".//gml:MultiSurface", CADASTRE_WFS_NS)
            if not refcat or geom is None:
                continue
            geom_gml = self._sanitize_cadastre_geometry_gml(
                ElementTree.tostring(geom, encoding="unicode")
            )
            features.append({"refcat": refcat, "geom_gml": geom_gml})
        return features

    def _cadastre_match_geom_metrics(self, geom_gml):
        """Return ``(geojson_4326, intersection_pct)`` for a candidate GML."""
        self.ensure_one()
        try:
            self.env.cr.execute(
                "WITH cand AS ("
                "  SELECT ST_MakeValid(ST_SetSRID(ST_GeomFromGML(%s), %s)) AS g"
                "), par AS ("
                "  SELECT ST_MakeValid(geom) AS g FROM ter_gis_parcel WHERE name = %s"
                ") "
                "SELECT ST_AsGeoJSON(ST_Transform(cand.g, 4326)), "
                "CASE WHEN ST_Area(par.g) > 0 THEN "
                "100.0 * ST_Area(ST_Intersection(cand.g, par.g)) / ST_Area(par.g) "
                "ELSE 0 END "
                "FROM cand, par",
                (geom_gml, self._CADASTRE_WFS_SOURCE_SRID, self.name),
            )
            row = self.env.cr.fetchone()
        except PsycopgError as exc:
            raise ValueError(
                self.env._("Invalid cadastral geometry received from Cadastre.")
            ) from exc
        if not row:
            return "", 0.0
        return row[0] or "", float(row[1] or 0.0)

    def _cadastre_match_candidates(self):
        """Return overlapping candidates sorted by descending overlap.

        Each item is ``{refcat, intersection, geojson}`` where ``geojson`` is
        the candidate geometry projected to WGS84 for the comparison map.
        """
        self.ensure_one()
        bbox = self._cadastre_match_bbox()
        if not bbox:
            return []
        content = self._cadastre_match_wfs_request(bbox)
        candidates = []
        for feature in self._cadastre_match_parse_features(content):
            geojson, pct = self._cadastre_match_geom_metrics(feature["geom_gml"])
            if pct <= 0:
                continue
            candidates.append(
                {
                    "refcat": feature["refcat"],
                    "intersection": round(pct, 2),
                    "geojson": geojson,
                }
            )
        candidates.sort(key=lambda cand: cand["intersection"], reverse=True)
        return candidates

    def _cadastre_match_parcel_geojson(self):
        """Return the parcel geometry as WGS84 GeoJSON for the map."""
        self.ensure_one()
        self.env.cr.execute(
            "SELECT ST_AsGeoJSON(ST_Transform(geom, 4326)) FROM ter_gis_parcel "
            "WHERE name = %s AND geom IS NOT NULL",
            (self.name,),
        )
        row = self.env.cr.fetchone()
        return (row[0] if row else "") or ""

    def _cadastre_match_build_map_data(self):
        """Build the comparison payload consumed by the map widget."""
        self.ensure_one()
        return {
            "parcel": self._cadastre_match_parcel_geojson(),
            "candidates": self._cadastre_match_candidates(),
        }

    def _cadastre_match_suggest_one(self, threshold):
        """Scan one parcel and store the suggested match (never raises)."""
        self.ensure_one()
        vals = {"cadastre_match_date": fields.Datetime.now()}
        try:
            candidates = self._cadastre_match_candidates()
        except (requests.RequestException, ValueError) as exc:
            _logger.warning("Cadastre match failed for %s: %s", self.display_name, exc)
            vals.update(
                cadastre_match_state="no_match",
                cadastre_match_refcat=False,
                cadastre_match_intersection=0.0,
            )
            self.write(vals)
            return
        best = candidates[0] if candidates else {}
        intersection = best.get("intersection", 0.0)
        refcat = best.get("refcat") or False
        state = "suggested" if best and intersection >= threshold else "no_match"
        vals.update(
            cadastre_match_state=state,
            cadastre_match_refcat=refcat,
            cadastre_match_intersection=intersection,
        )
        self.write(vals)

    def cadastre_match_suggest(self):
        """Background-safe scan storing a suggested match per parcel.

        Meant to be enqueued as a queue job. Failures are logged and stored
        as ``no_match`` so the import/scan never crashes.
        """
        threshold = self.env.company.cadastre_match_min_intersection or 0.0
        for record in self:
            record._cadastre_match_suggest_one(threshold)
        return True

    def action_cadastre_match_suggest(self):
        """Enqueue a background cadastre scan for the parcels with geometry."""
        if not self._is_cadastre_gis_import_enabled():
            raise UserError(
                self.env._(
                    "Cadastre GIS import is disabled in Territory settings. "
                    "Enable it to scan parcels against the Cadastre."
                )
            )
        todo = self.filtered("mapped_to_polygon")
        for record in todo:
            record.with_delay(
                description=self.env._(
                    "Cadastre scan: %(parcel)s", parcel=record.display_name
                )
            ).cadastre_match_suggest()
        lines = [
            self.env._(
                "Queued background cadastre scan for %(count)s parcel(s).",
                count=len(todo),
            )
        ]
        skipped = len(self) - len(todo)
        if skipped:
            lines.append(
                self.env._(
                    "Skipped %(count)s parcel(s) without geometry.", count=skipped
                )
            )
        return self._build_display_notification(  # pylint: disable=protected-access
            self.env._("Cadastre scan"),
            lines,
            "success",
        )

    def cadastre_match_apply_geometry(self, refcat):
        """Overwrite the parcel geometry with the cadastral one for ``refcat``."""
        self.ensure_one()
        geometry_gml = self._fetch_cadastre_geometry_gml(refcat)
        applied = self._set_gis_geometry_from_gml(  # pylint: disable=protected-access
            geometry_gml,
            source_srid=self._CADASTRE_WFS_SOURCE_SRID,
            target_srid=self._CADASTRE_MATCH_TARGET_SRID,
        )
        if applied:
            self.cadastre_match_state = "applied"
        return applied

    def cadastre_match_fill_code(self, refcat):
        """Fill the cadastral reference components from ``refcat`` if empty.

        Only rustic references (14 characters) whose municipality cadastral
        code matches the parcel municipality are applied, so the computed
        ``official_code`` stays consistent.
        """
        self.ensure_one()
        if self.official_code:
            return False
        code = (refcat or "").strip().upper()
        if len(code) != self._CADASTRE_REFCAT_LENGTH:
            return False
        municipality_code = self.municipality_id.cadastral_code or ""
        if municipality_code and municipality_code != code[:5]:
            return False
        self.write(
            {
                "parcel_type": "01_R",
                "cadastral_sector": code[5],
                "cadastral_polygon": code[6:9],
                "cadastral_parcel": code[9:14],
            }
        )
        return True

    def action_open_cadastre_compare(self):
        """Open the wizard comparing this parcel with the Cadastre."""
        self.ensure_one()
        if not self._is_cadastre_gis_import_enabled():
            raise UserError(
                self.env._(
                    "Cadastre GIS import is disabled in Territory settings. "
                    "Enable it to compare parcels against the Cadastre."
                )
            )
        if not self.mapped_to_polygon:
            raise UserError(
                self.env._("This parcel has no geometry to compare with the Cadastre.")
            )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Compare with Cadastre"),
            "res_model": "ter.parcel.cadastre.compare.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"active_id": self.id, "active_model": "ter.parcel"},
        }
