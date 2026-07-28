# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
# pylint: disable=too-many-lines

import base64
import logging

import requests
from odoo import api, fields, models
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.queue_job.job import identity_exact
from odoo.exceptions import UserError, ValidationError
from psycopg2 import sql

from .. import hooks as base_ter_hooks

_logger = logging.getLogger(__name__)


class TerUnit(models.Model):
    _name = "ter.use_unit"
    _description = "Ter Use Unit"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "polygon.model",
        "gis.viewer",
        "common.background.job",
    ]

    _param_gis_selection = "unituseid"

    _gis_table = "ter_gis_unit"
    _geom_field = "geom"
    _link_field = "name"

    _aerial_image_size_big = 512
    _aerial_image_size_medium = 256
    _aerial_image_size_small = 128
    _aerial_image_zoom = 1.2
    _force_square_shape = True

    _sql_constraints = [
        (
            "area_official_non_negative",
            "CHECK (area_official >= 0)",
            "Official area must be greater than or equal to 0.",
        ),
    ]

    name = fields.Char(
        copy=False,
        help=(
            "Auto-generated as {parcel_code}-{start_YYMM}-{end_YYMM}-{seq} "
            "when left empty."
        ),
    )
    geom_ewkt = fields.Text(
        string="Geometry (EWKT)",
        compute=False,
        store=True,
        readonly=False,
        help="Geometry in EWKT format (e.g. SRID=25830;POLYGON(...)). "
        "If set, parcel is auto-assigned as the parcel with maximum overlap.",
    )
    partner_id = fields.Many2one(
        string="Holder",
        comodel_name="res.partner",
        compute="_compute_partner_id",
        store=True,
        readonly=False,
        required=False,
        index=True,
        tracking=True,
    )
    partner_code = fields.Integer(
        related="partner_id.partner_code",
    )
    description = fields.Html(
        help="Description to provide more information "
        "and context about this ter_unit"
    )
    active = fields.Boolean(default=True, copy=False, export_string_translation=False)
    sequence = fields.Integer(default=10, export_string_translation=False)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("validated", "Validated"),
        ],
        default="draft",
        required=True,
        copy=False,
        index=True,
    )
    validity_state = fields.Selection(
        selection=[
            ("not_started", "Not Started"),
            ("in_range", "In Range"),
            ("out_of_range", "Out of Range"),
        ],
        compute="_compute_validity_state",
        store=True,
        search="_search_validity_state",
    )
    parcel_id = fields.Many2one(
        "ter.parcel",
        string="Main Parcel",
        required=True,
        index=True,
    )

    farm_property_id = fields.Many2one(
        "ter.property",
        string="Farm/Property",
        related="parcel_id.property_id",
        readonly=True,
    )
    municipality_id = fields.Many2one(
        "res.municipality",
        related="parcel_id.municipality_id",
        readonly=True,
    )
    area_gis_ha = fields.Float(
        string="Area GIS",
        digits=(32, 4),
        compute="_compute_area_gis_ha",
    )
    area_parcels = fields.Float(
        digits=(32, 4),
        compute="_compute_area_parcels",
    )
    note = fields.Html()
    date_start = fields.Date(string="Start date", required=True, index=True)
    date_end = fields.Date(string="End date", required=True, index=True)
    #
    date_range_id = fields.Many2one(
        "date.range",
        domain=[("is_unit_use_type", "=", True)],
        required=True,
    )
    date_range_use_type_id = fields.Many2one(
        related="date_range_id.use_type_id", string="Campaign Type"
    )
    #
    area_official = fields.Float(
        string="Official Area",
        digits=(32, 4),
        default=0,
        required=True,
        index=True,
        help="Official area of the territorial use unit, always in hectares (ha).",
    )
    area_official_m2 = fields.Integer(
        string="Official Area (m²)",
        compute="_compute_area_official_m2",
    )
    use_type_id = fields.Many2one("ter.use_type", index=True)
    is_current = fields.Boolean(
        string="In Range",
        compute="_compute_is_current",
        store=True,
        index=True,
        help="True if today is within date_start and date_end.",
    )
    attribute_value_ids = fields.One2many(
        comodel_name="ter.unit.attribute.value",
        inverse_name="unit_id",
        string="Attributes",
        copy=True,
    )
    attribute_value_count = fields.Integer(
        string="Attribute count",
        compute="_compute_attribute_value_count",
    )
    parcel_alphanum_code = fields.Char(
        string="Parcel Code",
        related="parcel_id.alphanum_code",
    )
    alphanum_code = fields.Char(
        string="Parcel Code",
        related="parcel_id.alphanum_code",
    )
    parcel_aerial_image_medium = fields.Image(
        string="Aerial Image (GIS preview)",
        related="parcel_id.aerial_image_medium",
    )
    parcel_aerial_image = fields.Image(
        string="Aerial Image (zoom)",
        related="parcel_id.aerial_image",
    )
    mapped_to_polygon = fields.Boolean(
        string="Mapped to polygon",
        compute="_compute_mapped_to_polygon",
        store=True,
    )
    area_unit_name = fields.Char(
        string="Area unit",
        compute="_compute_area_unit_name",
    )

    aerial_image = fields.Image(
        max_width=_aerial_image_size_big,
        max_height=_aerial_image_size_big,
    )
    aerial_image_key = fields.Char(index=True, readonly=True)
    aerial_image_last_refresh = fields.Datetime(
        readonly=True,
        index=True,
        copy=False,
    )
    aerial_image_medium = fields.Image(
        string="Aerial Image (medium size)",
        max_width=_aerial_image_size_medium,
        max_height=_aerial_image_size_medium,
        store=True,
        related="aerial_image",
    )
    aerial_image_small = fields.Image(
        string="Aerial Image (small size)",
        max_width=_aerial_image_size_small,
        max_height=_aerial_image_size_small,
        store=True,
        related="aerial_image",
    )

    @api.depends("parcel_id")
    def _compute_parcel_count(self):
        for record in self:
            parcels = record.parcel_id
            record.parcel_count = len(parcels) if parcels else 0

    @api.depends("geom_ewkt")
    def _compute_area_gis_ha(self):
        for record in self:
            area = 0.0
            if record.geom_ewkt and record.geom_ewkt.strip():
                try:
                    self.env.cr.execute(
                        sql.SQL(
                            "SELECT ST_Area(ST_Transform(geom, 25830)) / 10000.0 "
                            "FROM {}.{} WHERE unit_id = %s"
                        ).format(
                            sql.Identifier(base_ter_hooks.GIS_SCHEMA),
                            sql.Identifier(base_ter_hooks.UNIT_TABLE),
                        ),
                        (record.id,),
                    )
                    row = self.env.cr.fetchone()
                    area = float(row[0]) if row and row[0] else 0.0
                except RuntimeError:
                    area = 0.0
            record.area_gis_ha = area

    @api.depends("parcel_id.area_official")
    def _compute_area_parcels(self):
        for record in self:
            parcels = record.parcel_id
            record.area_parcels = (
                sum(parcels.mapped("area_official")) if parcels else 0.0
            )

    @api.depends_context("lang")
    def _compute_area_unit_name(self):
        company = self.env.company
        is_ha, unit_name, _ = company._get_area_unit_params()
        if is_ha:
            unit_name = self.env._("ha")
        for record in self:
            record.area_unit_name = unit_name

    @api.depends("geom_ewkt")
    def _compute_mapped_to_polygon(self):
        qual = sql.SQL("{}.{}").format(
            sql.Identifier(base_ter_hooks.GIS_SCHEMA),
            sql.Identifier(base_ter_hooks.UNIT_TABLE),
        )
        for record in self:
            if not record.geom_ewkt or not record.geom_ewkt.strip():
                record.mapped_to_polygon = False
                continue
            self.env.cr.execute(
                sql.SQL("SELECT 1 FROM {} WHERE unit_id = %s LIMIT 1").format(qual),
                (record.id,),
            )
            record.mapped_to_polygon = bool(self.env.cr.fetchone())

    def _get_bounding_box(self):
        xmin = ymin = xmax = ymax = 0.0
        first = True
        qual = sql.SQL("{}.{}").format(
            sql.Identifier(base_ter_hooks.GIS_SCHEMA),
            sql.Identifier(base_ter_hooks.UNIT_TABLE),
        )
        for record in self:
            if not record.mapped_to_polygon:
                continue
            try:
                self.env.cr.execute(
                    sql.SQL(
                        "SELECT ST_XMin(ST_Envelope(geom)), ST_YMin(ST_Envelope(geom)),"
                        " ST_XMax(ST_Envelope(geom)), ST_YMax(ST_Envelope(geom))"
                        " FROM {} WHERE unit_id = %s"
                    ).format(qual),
                    (record.id,),
                )
                row = self.env.cr.fetchone()
                if not row or any(v is None for v in row):
                    continue
                bxmin, bymin, bxmax, bymax = [float(v) for v in row]
                if first:
                    first = False
                    xmin, ymin, xmax, ymax = bxmin, bymin, bxmax, bymax
                else:
                    xmin = min(xmin, bxmin)
                    ymin = min(ymin, bymin)
                    xmax = max(xmax, bxmax)
                    ymax = max(ymax, bymax)
            except Exception:  # pylint: disable=broad-except
                continue
        return xmin, ymin, xmax, ymax

    def _ensure_ewkt_srid(self, wkt, default_srid=25830):
        """Ensure WKT has SRID prefix for PostGIS. Returns EWKT string."""
        if not wkt or not (wkt or "").strip():
            return ""
        wkt = (wkt or "").strip()
        if wkt.upper().startswith("SRID="):
            return wkt
        return "SRID=%s;%s" % (default_srid, wkt)

    def _get_parcel_from_geometry(self, geom_ewkt, srid=25830):
        """
        Find the parcel with maximum overlap with the given geometry.
        Uses PostGIS ST_Intersects and ST_Area(ST_Intersection(...)).
        """
        ewkt = self._ensure_ewkt_srid(geom_ewkt, srid)
        if not ewkt:
            return self.env["ter.parcel"]
        parcel_model = self.env["ter.parcel"]
        self.env.cr.execute(
            sql.SQL(
                "SELECT tp.id "
                "FROM {}.{} gp "
                "INNER JOIN ter_parcel tp ON tp.name = gp.name "
                "WHERE tp.active = true "
                "  AND gp.geom IS NOT NULL "
                "  AND ST_Intersects(ST_GeomFromEWKT(%s)::geometry, gp.geom) "
                "ORDER BY ST_Area("
                "ST_Intersection(ST_GeomFromEWKT(%s)::geometry, gp.geom)"
                ") DESC NULLS LAST "
                "LIMIT 1"
            ).format(
                sql.Identifier(base_ter_hooks.GIS_SCHEMA),
                sql.Identifier(base_ter_hooks.PARCEL_TABLE),
            ),
            (ewkt, ewkt),
        )
        row = self.env.cr.fetchone()
        if row:
            return parcel_model.browse(row[0])
        return parcel_model

    def _sync_geom_to_gis_unit(self):
        """Sync geom_ewkt to ter_gis_unit table for PostGIS operations."""
        base_ter_hooks._ensure_gis_unit_table(  # pylint: disable=protected-access
            self.env
        )
        qual = sql.SQL("{}.{}").format(
            sql.Identifier(base_ter_hooks.GIS_SCHEMA),
            sql.Identifier(base_ter_hooks.UNIT_TABLE),
        )
        for record in self:
            if not record.geom_ewkt or not record.geom_ewkt.strip():
                self.env.cr.execute(
                    sql.SQL("DELETE FROM {} WHERE unit_id = %s").format(qual),
                    (record.id,),
                )
                continue
            ewkt = record._ensure_ewkt_srid(  # pylint: disable=protected-access
                record.geom_ewkt
            )
            self.env.cr.execute(
                sql.SQL(
                    "INSERT INTO {} (unit_id, name, geom) "
                    "VALUES (%s, %s, ST_Multi("
                    "ST_GeomFromEWKT(%s)::geometry"
                    ")::geometry(MultiPolygon, 25830)) "
                    "ON CONFLICT (unit_id) DO UPDATE "
                    "SET name = EXCLUDED.name, geom = EXCLUDED.geom"
                ).format(qual),
                (record.id, record.name, ewkt),
            )

    def _sync_name_to_gis_unit(self):
        """Keep the denormalized ``ter_gis_unit.name`` in sync on rename."""
        qual = sql.SQL("{}.{}").format(
            sql.Identifier(base_ter_hooks.GIS_SCHEMA),
            sql.Identifier(base_ter_hooks.UNIT_TABLE),
        )
        for record in self:
            self.env.cr.execute(
                sql.SQL("UPDATE {} SET name = %s WHERE unit_id = %s").format(qual),
                (record.name, record.id),
            )

    def _build_ter_unit_name(self, params):
        """Build the use unit name.

        Format: ``{parcel_code}-{start_YYMM}-{end_YYMM}-{seq:02d}``. When an
        ``extra_code`` param is given (e.g. a crop code) it is inserted right
        before the sequence: ``{parcel}-{YYMM}-{YYMM}-{EXTRA}-{seq:02d}``.
        Year-month is used (not just the year) so units planted in different
        months of the same year stay distinct.
        """
        parcel_code = (params.get("parcel_code") or "?").strip() or "?"
        start_code = self._ter_unit_period_code(params.get("date_start"))
        end_code = self._ter_unit_period_code(params.get("date_end"))
        seq = params.get("seq", 0)
        parts = [parcel_code, start_code, end_code]
        extra_code = (params.get("extra_code") or "").strip()
        if extra_code:
            parts.append(extra_code)
        parts.append("%02d" % seq)
        return "-".join(parts)

    def _ter_unit_period_code(self, date_value):
        """Return the YYMM code of a date (e.g. 2511), ``0000`` if empty."""
        if isinstance(date_value, str):
            date_value = fields.Date.from_string(date_value)
        if not date_value:
            return "0000"
        return date_value.strftime("%y%m")

    def _ter_unit_name_extra_code(self, _vals):
        """Return an optional code inserted before the sequence in the name.

        Empty in the base model; sub-modules (e.g. Geofolia) override it to
        add a crop code.
        """
        return ""

    @api.model
    def _get_next_ter_unit_name(self, vals, _company=None):
        parcel_code = ""
        parcel_id = vals.get("parcel_id")
        if parcel_id:
            parcel = self.env["ter.parcel"].browse(parcel_id)
            if parcel.exists():
                parcel_code = parcel.alphanum_code or ""

        date_start = vals.get("date_start")
        date_end = vals.get("date_end")
        if (not date_start or not date_end) and vals.get("date_range_id"):
            dr = self.env["date.range"].browse(vals["date_range_id"])
            if dr.exists():
                date_start = date_start or dr.date_start
                date_end = date_end or dr.date_end

        domain = [("parcel_id", "=", parcel_id)] if parcel_id else []
        if date_start and date_end:
            domain += [("date_start", "=", date_start), ("date_end", "=", date_end)]
        elif vals.get("date_range_id"):
            domain += [("date_range_id", "=", vals["date_range_id"])]
        seq = self.search_count(domain)

        return self._build_ter_unit_name(  # pylint: disable=protected-access
            {
                "parcel_code": parcel_code,
                "date_start": date_start,
                "date_end": date_end,
                "extra_code": self._ter_unit_name_extra_code(vals),
                "seq": seq,
            }
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self._get_next_ter_unit_name(vals)
            geom = vals.get("geom_ewkt")
            if geom:
                geom = self._ensure_ewkt_srid(geom)
                vals["geom_ewkt"] = geom
            if geom and not vals.get("parcel_id"):
                parcel = self._get_parcel_from_geometry(geom)
                if parcel:
                    vals["parcel_id"] = parcel.id
                else:
                    raise UserError(
                        self.env._(
                            "No parcel found intersecting the unit geometry. "
                            "Ensure parcels exist with geometry in the same area."
                        )
                    )
        records = super().create(vals_list)
        records._sync_attribute_lines()  # pylint: disable=protected-access
        to_sync = records.filtered(lambda r: r.geom_ewkt)
        if to_sync:
            to_sync._sync_geom_to_gis_unit()  # pylint: disable=protected-access
        return records

    def _sanitize_attribute_value_commands(self, commands):
        sanitized = []
        for cmd in commands or []:
            if not isinstance(cmd, (list, tuple)) or len(cmd) < 1:
                continue
            if cmd[0] == 0:
                vals = cmd[2] or {}
                if not vals.get("attribute_id"):
                    continue
            sanitized.append(cmd)
        return sanitized

    def _get_cultivable_default_value_id(self, attribute):
        """
        Return default value_id for the 'Cultivable' attribute.
        Yes for Farming use type, No otherwise.
        """
        if not attribute or attribute.name != "Cultivable":
            return False
        farming_type = self.env.ref(
            "base_ter.ter_use_type_farming", raise_if_not_found=False
        )
        use_type = attribute.use_type_id
        if farming_type and use_type and use_type == farming_type:
            yes_val = attribute.value_ids.filtered(lambda v: v.name == "Yes")
            return yes_val[:1].id if yes_val else False
        no_val = attribute.value_ids.filtered(lambda v: v.name == "No")
        return no_val[:1].id if no_val else False

    def _sync_attribute_lines(self):
        for record in self:
            if not record.use_type_id:
                continue

            required_attrs = record.use_type_id.all_attribute_ids
            existing_attrs = record.attribute_value_ids.mapped("attribute_id")
            missing_attrs = required_attrs - existing_attrs

            if missing_attrs:
                cmds = []
                for attr in missing_attrs:
                    line_vals = {"attribute_id": attr.id}
                    value_id = record._get_cultivable_default_value_id(attr)
                    if value_id:
                        line_vals["value_id"] = value_id
                    cmds.append((0, 0, line_vals))
                record.write({"attribute_value_ids": cmds})

    def write(self, vals):
        if vals.get("geom_ewkt"):
            vals["geom_ewkt"] = self._ensure_ewkt_srid(vals["geom_ewkt"])
        if "geom_ewkt" in vals and "parcel_id" not in vals:
            geom = vals.get("geom_ewkt")
            if geom:
                parcel = self._get_parcel_from_geometry(
                    geom
                )  # pylint: disable=protected-access
                if parcel:
                    vals["parcel_id"] = parcel.id
        res = super().write(vals)
        if "use_type_id" in vals:
            self._sync_attribute_lines()  # pylint: disable=protected-access
        if "geom_ewkt" in vals:
            self._sync_geom_to_gis_unit()  # pylint: disable=protected-access
        elif "name" in vals:
            self._sync_name_to_gis_unit()  # pylint: disable=protected-access
        return res

    def _check_domain_specific_rules(self):
        """Hook for modules extending ter.use_unit to add domain-specific validations.

        Override in inherited modules. Called before critical operations if needed.
        """

    @api.ondelete(at_uninstall=False)
    def _unlink_check_geometry(self):
        for record in self:
            if record.geom_ewkt and record.geom_ewkt.strip():
                raise UserError(
                    self.env._(
                        "Cannot delete a unit with GIS geometry. "
                        "Clear the geometry first or archive the record."
                    )
                )

    @api.depends("parcel_id", "parcel_id.partner_id")
    def _compute_partner_id(self):
        """Set holder from parcel's manager (partner_id)."""
        for record in self:
            if record.parcel_id and record.parcel_id.partner_id:
                record.partner_id = record.parcel_id.partner_id

    @api.constrains("partner_id", "parcel_id")
    def _check_holder_is_parcel_manager(self):
        for record in self:
            if record.partner_id and record.parcel_id:
                if record.partner_id != record.parcel_id.partner_id:
                    raise ValidationError(
                        self.env._(
                            "The holder must be the manager (main contact) "
                            "of the main parcel."
                        )
                    )

    @api.constrains("date_start", "date_end")
    def _check_date_start_before_date_end(self):
        for record in self:
            if record.date_start and record.date_end:
                if record.date_start > record.date_end:
                    raise ValidationError(
                        self.env._("Start date must be before or equal to end date.")
                    )

    @api.constrains("date_start", "date_end", "date_range_id")
    def _check_dates_within_date_range(self):
        for record in self:
            if not record.date_range_id:
                continue
            dr = record.date_range_id
            if (
                record.date_start
                and dr.date_start
                and record.date_start < dr.date_start
            ):
                raise ValidationError(
                    self.env._(
                        "Start date must be within the date range "
                        "(%(start)s – %(end)s).",
                        start=dr.date_start,
                        end=dr.date_end,
                    )
                )
            if record.date_end and dr.date_end and record.date_end > dr.date_end:
                raise ValidationError(
                    self.env._(
                        "End date must be within the date range "
                        "(%(start)s – %(end)s).",
                        start=dr.date_start,
                        end=dr.date_end,
                    )
                )

    @api.onchange("use_type_id")
    def _onchange_use_type_id(self):
        if not self.use_type_id:
            self.attribute_value_ids = [(5, 0, 0)]
            return
        allowed_attrs = self.use_type_id.all_attribute_ids
        commands = [(5, 0, 0)]
        for attr in allowed_attrs:
            line_vals = {"attribute_id": attr.id}
            value_id = self._get_cultivable_default_value_id(attr)
            if value_id:
                line_vals["value_id"] = value_id
            commands.append((0, 0, line_vals))
        self.attribute_value_ids = commands

    @api.onchange("date_range_id")
    def _onchange_date_range_id(self):
        if self.date_range_id:
            self.date_start = self.date_range_id.date_start
            self.date_end = self.date_range_id.date_end

    @api.constrains("attribute_value_ids")
    def _check_required_attributes(self):
        for record in self:
            for line in record.attribute_value_ids:
                if line.required and not line.value_id:
                    raise ValidationError(
                        self.env._(
                            "Attribute '%(attr)s' is required.",
                            attr=line.attribute_id.name,
                        )
                    )

    def _search_validity_state(self, operator, value):
        today = fields.Date.context_today(self)
        if operator not in ("=", "!="):
            return []
        domains = {
            "not_started": [("date_start", ">", today)],
            "in_range": [
                ("date_start", "<=", today),
                ("date_end", ">=", today),
            ],
            "out_of_range": [("date_end", "<", today)],
        }
        domain = domains.get(value, [])
        if operator == "!=":
            return [("id", "not in", self.search(domain).ids)]
        return domain

    @api.depends("date_start", "date_end")
    def _compute_validity_state(self):
        today = fields.Date.context_today(self)
        for record in self:
            validity = "not_started"
            if record.date_start and record.date_end:
                if today < record.date_start:
                    validity = "not_started"
                elif record.date_start <= today <= record.date_end:
                    validity = "in_range"
                else:
                    validity = "out_of_range"
            record.validity_state = validity

    def _cron_recompute_validity_state(self):
        """Recompute validity_state for all ter.unit records (run daily)."""
        records = self.search([("date_start", "!=", False), ("date_end", "!=", False)])
        records.invalidate_recordset(["validity_state"])
        records.mapped("validity_state")

    @api.depends("date_start", "date_end")
    def _compute_is_current(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.date_start and record.date_end:
                record.is_current = record.date_start <= today <= record.date_end
            else:
                record.is_current = False

    @api.depends("attribute_value_ids")
    def _compute_attribute_value_count(self):
        for record in self:
            record.attribute_value_count = len(record.attribute_value_ids)

    @api.depends("area_official")
    def _compute_area_official_m2(self):
        # Official area in ter.use_unit is always in hectares (company area_unit_is_ha).
        # 1 ha = 10000 m².
        factor = 10000.0
        for record in self:
            record.area_official_m2 = round((record.area_official or 0.0) * factor)

    @api.constrains("state", "parcel_id", "date_start", "date_end")
    def _check_validated_state_requirements(self):
        for record in self:
            if record.state == "validated":
                if not record.parcel_id:
                    raise ValidationError(
                        self.env._("Cannot validate: Main parcel is required.")
                    )
                if not record.date_start or not record.date_end:
                    raise ValidationError(
                        self.env._("Cannot validate: Date range is required.")
                    )

    def action_validate(self):
        """Validate the unit use."""
        return self.write({"state": "validated"})

    def action_set_to_draft(self):
        """Set the unit use back to draft."""
        return self.write({"state": "draft"})

    def action_gis_preview(self):
        """Open GIS preview wizard for the main parcel."""
        self.ensure_one()
        if not self.parcel_id:
            return None
        return self.parcel_id.action_gis_preview()

    def _aerial_cache_key(self, params):
        """Generate cache key for aerial image.

        Args:
            params (dict): Dictionary with keys:
                - wms: WMS URL
                - layers: WMS layers
                - styles: WMS styles
                - image_height: Image height
                - image_width: Image width
                - zoom: Zoom level
                - force_square_shape: Force square shape
                - apply_filter: Apply filter
                - extra: Extra parameters (optional)
        """
        self.ensure_one()
        return self._make_wms_key(
            self.geom_ewkt or "",
            params.get("wms") or "",
            params.get("layers") or "",
            params.get("styles") or "",
            int(params.get("image_height") or 0),
            int(params.get("image_width") or 0),
            float(params.get("zoom") or 0.0),
            bool(params.get("force_square_shape")),
            bool(params.get("apply_filter")),
            params.get("extra") or "",
        )

    def _get_wms_config(self):
        """Load WMS configuration from current company (unit-use layer)."""
        company = self.env.company
        return {
            "wmsbase_url": company.aerial_image_wmsbase_url or False,
            "wmsbase_layers": company.aerial_image_wmsbase_layers or False,
            "wmsvec_url": company.aerial_image_wmsvec_url or False,
            "wmsvec_unit_layer": company.aerial_image_wmsvec_unit_name or False,
            "wmsvec_filter": bool(company.aerial_image_wmsvec_unit_filter),
            "image_height": int(company.aerial_image_height or 0),
            "image_zoom": float(company.aerial_image_zoom or 0),
        }

    @api.model
    def extract_bounding_box(self, geom_ewkt, force_square_shape=True):
        """Extract the bounding box from the unit geometry.

        The unit ``geom_ewkt`` is stored as user/import input and may lack
        the ``SRID=...;`` prefix that the polygon parser needs, so normalize
        it first (the geometry is always stored in EPSG:25830).
        """
        if geom_ewkt:
            geom_ewkt = self._ensure_ewkt_srid(geom_ewkt)
        return super().extract_bounding_box(
            geom_ewkt, force_square_shape=force_square_shape
        )

    def _fetch_and_store_aerial_image(self):
        """Fetch the aerial image from the WMS service and persist it.

        This performs the actual network call(s) and must only be
        triggered by an explicit action: the "Regenerate Image" button
        (``reset_aerial_image``), a mass generation action, or the
        background queue_job (``_job_generate_aerial_image``).
        """
        self.ensure_one()
        wms_cfg = self._get_wms_config()  # pylint: disable=protected-access
        image_height = wms_cfg["image_height"] or self._aerial_image_size_big
        image_zoom = wms_cfg["image_zoom"] or self._aerial_image_zoom
        is_ogc_ok = bool(
            wms_cfg["wmsbase_url"]
            and wms_cfg["wmsbase_layers"]
            and image_height >= 0
            and image_zoom >= 0
        )
        if not (is_ogc_ok and self.mapped_to_polygon):
            return False

        use_vector = bool(
            is_ogc_ok and wms_cfg["wmsvec_url"] and wms_cfg["wmsvec_unit_layer"]
        )
        stored_base64 = None
        if not use_vector:
            key = self._aerial_cache_key(  # pylint: disable=protected-access
                {
                    "wms": wms_cfg["wmsbase_url"],
                    "layers": wms_cfg["wmsbase_layers"],
                    "styles": "default",
                    "image_height": image_height,
                    "image_width": 0,
                    "zoom": image_zoom,
                    "force_square_shape": self._force_square_shape,
                    "apply_filter": False,
                    "extra": "base",
                }
            )
            if self.aerial_image and self.aerial_image_key == key:
                stored_base64 = self.aerial_image
            else:
                stored_base64 = self.get_aerial_image(
                    wms=wms_cfg["wmsbase_url"],
                    layers=wms_cfg["wmsbase_layers"],
                    image_height=image_height,
                    image_format="png",
                    zoom=image_zoom,
                    force_square_shape=self._force_square_shape,
                )
        else:
            key = self._aerial_cache_key(  # pylint: disable=protected-access
                {
                    "wms": wms_cfg["wmsbase_url"],
                    "layers": wms_cfg["wmsbase_layers"],
                    "styles": "default",
                    "image_height": image_height,
                    "image_width": 0,
                    "zoom": image_zoom,
                    "force_square_shape": self._force_square_shape,
                    "apply_filter": False,
                    "extra": "base+vec:%s:%s:%s"
                    % (
                        wms_cfg["wmsvec_url"] or "",
                        wms_cfg["wmsvec_unit_layer"] or "",
                        int(wms_cfg["wmsvec_filter"]),
                    ),
                }
            )
            if self.aerial_image and self.aerial_image_key == key:
                stored_base64 = self.aerial_image
            else:
                base_image_raw = self.get_aerial_image(
                    wms=wms_cfg["wmsbase_url"],
                    layers=wms_cfg["wmsbase_layers"],
                    image_height=image_height,
                    image_format="png",
                    zoom=image_zoom,
                    get_raw=True,
                    apply_filter=False,
                    force_square_shape=self._force_square_shape,
                )
                vector_image_raw = self.get_aerial_image(
                    wms=wms_cfg["wmsvec_url"],
                    layers=wms_cfg["wmsvec_unit_layer"],
                    image_height=image_height,
                    image_format="png",
                    zoom=image_zoom,
                    get_raw=True,
                    apply_filter=wms_cfg["wmsvec_filter"],
                    force_square_shape=self._force_square_shape,
                )
                if base_image_raw and vector_image_raw:
                    merged_bytes = self.env["common.image"].merge_img(
                        base_image_raw,
                        vector_image_raw,
                        return_base64=False,
                    )
                    if merged_bytes:
                        stored_base64 = base64.b64encode(merged_bytes)

        if stored_base64:
            self.aerial_image = stored_base64
            self.aerial_image_key = key
            self.aerial_image_last_refresh = fields.Datetime.now()
            self.env["common.log"].register_in_log(
                self.env._(
                    "Aerial image OK. Territorial unit: %(name)s", name=self.name
                ),
                source=self._name,
                message_type="INFO",
            )
            return True

        self.env["common.log"].register_in_log(
            self.env._("Error getting aerial image (is the WMS url correct?)"),
            source=self._name,
            message_type="WARNING",
        )
        return False

    def delete_aerial_image(self):
        for record in self:
            record.aerial_image = False
            record.aerial_image_key = False
            record.aerial_image_medium = False
            record.aerial_image_small = False

    def reset_aerial_image(self):
        if len(self) == 1:
            self.aerial_image = False
            self.aerial_image_key = False
            self._fetch_and_store_aerial_image()  # pylint: disable=protected-access
            return
        for record in self:
            try:
                record.aerial_image = False
                record.aerial_image_key = False
                record._fetch_and_store_aerial_image()  # pylint: disable=protected-access
            except Exception as e:  # noqa: BLE001  # pylint: disable=W0718
                # Never let a single bad record (e.g. a corrupt/degenerate
                # geometry) abort the rest of the batch.
                self.env.cr.rollback()
                self.env.invalidate_all()
                _logger.exception(
                    "Unexpected error generating aerial image for unit %s: %s",
                    record.name,
                    e,
                )

    def _job_generate_aerial_image(self):
        """Queue_job entry point used by the background refresh cron."""
        self.ensure_one()
        wms_errors = (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            OSError,
        )
        try:
            self._fetch_and_store_aerial_image()  # pylint: disable=protected-access
        except wms_errors as exc:
            raise RetryableJobError(
                self.env._(
                    "WMS temporarily unavailable for unit %(name)s: %(error)s",
                    name=self.name,
                    error=str(exc),
                )
            ) from exc

    @api.model
    def cron_generate_pending_aerial_images(self, batch_size=200):
        """Incrementally (re)generate aerial images via queue_job.

        Each run picks a batch of units with GIS geometry, giving
        priority to those that never had a successful refresh
        (``aerial_image_last_refresh`` is null) and then to the ones
        refreshed longest ago. Each unit is delayed as its own job, so
        every job commits independently, and ``identity_exact`` prevents
        enqueuing a duplicate job for a unit that already has one
        pending/enqueued.
        """
        records = self.search(
            [("mapped_to_polygon", "=", True)],
            order="aerial_image_last_refresh asc nulls first, create_date asc",
            limit=batch_size,
        )
        for record in records:
            record.with_delay(
                channel="root.ter_gis_aerial_image",
                identity_key=identity_exact,
                description=self.env._(
                    "Generate aerial image: %(name)s", name=record.name
                ),
            )._job_generate_aerial_image()  # pylint: disable=protected-access
        return len(records)

    def action_regenerate_image(self):
        """Regenerate the territorial unit's own aerial image."""
        self.ensure_one()
        self.reset_aerial_image()

    _MASS_AERIAL_IMAGE_BATCH_NAME = (
        "base_ter.ter_use_unit.action_reset_all_aerial_images"
    )
    _MASS_AERIAL_IMAGE_CHUNK_SIZE = 50

    @api.model
    def action_reset_all_aerial_images(self, from_backend=False):
        """Enqueue a background job batch to regenerate every unit's image.

        The work is split into small chunks, each delayed as its own
        queue_job tagged to a ``queue.job.batch``, so progress can be
        tracked via the batch's ``completeness`` percentage. If a
        previous batch is still running, no duplicate is created; the
        user is notified instead.
        """
        launched = not self._is_background_batch_running(
            self._MASS_AERIAL_IMAGE_BATCH_NAME
        )
        if launched:
            batch = self._new_background_batch(self._MASS_AERIAL_IMAGE_BATCH_NAME)
            chunk_size = self._MASS_AERIAL_IMAGE_CHUNK_SIZE
            offset = 0
            while True:
                chunk_ids = self.search([], limit=chunk_size, offset=offset).ids
                if not chunk_ids:
                    break
                self.browse(chunk_ids).with_context(job_batch=batch).with_delay(
                    channel="root.ter_gis_aerial_image",
                    description=self.env._(
                        "Generate aerial images (territorial units), "
                        "records %(offset)s+",
                        offset=offset,
                    ),
                )._job_reset_all_aerial_images_chunk()  # pylint: disable=protected-access
                offset += chunk_size
        return self._background_job_notification(launched, from_backend)

    def _job_reset_all_aerial_images_chunk(self):
        """Queue_job entry point: regenerate this chunk's aerial images."""
        self.reset_aerial_image()

    def action_show_parcels(self):
        """Open parcels linked to this unit."""
        self.ensure_one()
        parcel_ids = self.parcel_id
        if not parcel_ids:
            return None
        tree_view = self.env.ref("base_ter.ter_parcel_view_tree")
        form_view = self.env.ref("base_ter.ter_parcel_view_form")
        search_view = self.env.ref("base_ter.ter_parcel_view_search")
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Parcels"),
            "res_model": "ter.parcel",
            "view_mode": "list,form",
            "views": [(tree_view.id, "list"), (form_view.id, "form")],
            "search_view_id": search_view.id,
            "domain": [("id", "in", parcel_ids)],
        }

    def action_show_attribute_values(self):
        self.ensure_one()
        list_view = self.env.ref(
            "base_ter.ter_unit_attribute_value_view_list", raise_if_not_found=False
        )
        form_view = self.env.ref(
            "base_ter.ter_unit_attribute_value_view_form", raise_if_not_found=False
        )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Attributes"),
            "res_model": "ter.unit.attribute.value",
            "view_mode": "list,form",
            "views": [
                (list_view.id if list_view else False, "list"),
                (form_view.id if form_view else False, "form"),
            ],
            "domain": [("unit_id", "=", self.id)],
            "context": {"default_unit_id": self.id},
        }
