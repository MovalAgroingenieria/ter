# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from psycopg2 import sql

from .. import hooks as base_ter_hooks


class TerUnit(models.Model):
    _name = "ter.use_unit"
    _description = "Ter Use Unit"
    _inherit = ["mail.thread", "mail.activity.mixin", "gis.viewer"]

    _param_gis_selection = "idunidad"

    _sql_constraints = [
        (
            "area_official_non_negative",
            "CHECK (area_official >= 0)",
            "Official area must be greater than or equal to 0.",
        ),
    ]

    name = fields.Char(
        copy=False,
        help="Auto-generated as {parcel_code}-{start_YY}/{end_YY}-{seq} when left empty.",
    )
    geom_ewkt = fields.Text(
        string="Geometry (EWKT)",
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
        string="Code",
        related="parcel_id.alphanum_code",
    )
    parcel_aerial_image_shown_256 = fields.Image(
        string="Aerial Image (GIS preview)",
        related="parcel_id.aerial_image_shown_256",
    )
    parcel_image_1920 = fields.Image(
        string="Aerial Image (zoom)",
        related="parcel_id.image_1920",
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
        for unit in self:
            if not unit.geom_ewkt or not unit.geom_ewkt.strip():
                self.env.cr.execute(
                    sql.SQL("DELETE FROM {} WHERE unit_id = %s").format(qual),
                    (unit.id,),
                )
                continue
            ewkt = unit._ensure_ewkt_srid(  # pylint: disable=protected-access
                unit.geom_ewkt
            )
            self.env.cr.execute(
                sql.SQL(
                    "INSERT INTO {} (unit_id, geom) "
                    "VALUES (%s, ST_Multi("
                    "ST_GeomFromEWKT(%s)::geometry"
                    ")::geometry(MultiPolygon, 25830)) "
                    "ON CONFLICT (unit_id) DO UPDATE "
                    "SET geom = EXCLUDED.geom"
                ).format(qual),
                (unit.id, ewkt),
            )

    def _build_ter_unit_name(self, params):
        """Build name as {parcel_code}-{start_YY}/{end_YY}-{seq:02d}."""
        parcel_code = (params.get("parcel_code") or "?").strip() or "?"
        date_start = params.get("date_start")
        date_end = params.get("date_end")
        if isinstance(date_start, str):
            date_start = fields.Date.from_string(date_start)
        if isinstance(date_end, str):
            date_end = fields.Date.from_string(date_end)
        start_yy = str(date_start.year)[-2:] if date_start else "??"
        end_yy = str(date_end.year)[-2:] if date_end else "??"
        seq = params.get("seq", 1)
        return f"{parcel_code}-{start_yy}/{end_yy}-{seq:02d}"

    @api.model
    def _get_next_ter_unit_name(self, vals, company=None):
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
        seq = self.search_count(domain) + 1

        return self._build_ter_unit_name(  # pylint: disable=protected-access
            {
                "parcel_code": parcel_code,
                "date_start": date_start,
                "date_end": date_end,
                "seq": seq,
            }
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self._get_next_ter_unit_name(vals)
            geom = vals.get("geom_ewkt")
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
        for unit in self:
            if not unit.use_type_id:
                continue

            required_attrs = unit.use_type_id.all_attribute_ids
            existing_attrs = unit.attribute_value_ids.mapped("attribute_id")
            missing_attrs = required_attrs - existing_attrs

            if missing_attrs:
                cmds = []
                for attr in missing_attrs:
                    line_vals = {"attribute_id": attr.id}
                    value_id = unit._get_cultivable_default_value_id(attr)
                    if value_id:
                        line_vals["value_id"] = value_id
                    cmds.append((0, 0, line_vals))
                unit.write({"attribute_value_ids": cmds})

    def write(self, vals):
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
        return res

    def _check_domain_specific_rules(self):
        """Hook for modules extending ter.use_unit to add domain-specific validations.

        Override in inherited modules. Called before critical operations if needed.
        """

    @api.ondelete(at_uninstall=False)
    def _unlink_check_geometry(self):
        for unit in self:
            if unit.geom_ewkt and unit.geom_ewkt.strip():
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
        for unit in self:
            for line in unit.attribute_value_ids:
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

    def action_regenerate_image(self):
        """Regenerate aerial image on the main parcel."""
        self.ensure_one()
        if self.parcel_id:
            self.parcel_id.reset_aerial_image()

    @api.model
    def action_reset_all_aerial_images(self, from_backend=False):
        """Reset aerial images for all parcels linked to territorial units."""
        batch_size = 100
        offset = 0
        while True:
            batch = self.search([], limit=batch_size, offset=offset)
            if not batch:
                break
            parcels = batch.mapped("parcel_id")
            parcels.reset_aerial_image()
            offset += batch_size
        if from_backend:
            return {"type": "ir.actions.client", "tag": "reload"}
        return None

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
            "base_ter.view_ter_unit_attribute_value_list", raise_if_not_found=False
        )
        form_view = self.env.ref(
            "base_ter.view_ter_unit_attribute_value_form", raise_if_not_found=False
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
