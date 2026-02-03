# Copyright 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .. import hooks as base_ter_hooks


class TerUnit(models.Model):
    _name = "ter.unit"
    _description = "Ter Unit"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name")
    geom_ewkt = fields.Text(
        string="Geometry (EWKT)",
        help="Geometry in EWKT format (e.g. SRID=25830;POLYGON(...)). "
        "If set, parcel is auto-assigned as the parcel with maximum overlap.",
    )
    partner_id = fields.Many2one("res.partner")
    description = fields.Html(help="Description to provide more information and context about this ter_unit")
    active = fields.Boolean(default=True, copy=False, export_string_translation=False)
    sequence = fields.Integer(default=10, export_string_translation=False)
    parcel_id = fields.Many2one(
        "ter.parcel", required=True, index=True
    )
    date_start = fields.Date(string="Start date", required=True, index=True)
    date_end = fields.Date(string="End date", required=True, index=True)
    #
    date_range_id = fields.Many2one('date.range', domain=[('is_unit_use_type', '=', True)], required=True)
    date_range_use_type_id = fields.Many2one(related="date_range_id.use_type_id", string="Campaign Type")
    #
    area_official = fields.Float(
        string="Official Area",
        digits=(32, 4),
        default=0,
        required=True,
        index=True,
    )
    account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
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
        Parcel = self.env["ter.parcel"]
        self.env.cr.execute(
            """
            SELECT tp.id
            FROM ter_gis_parcel gp
            INNER JOIN ter_parcel tp ON tp.name = gp.name
            WHERE tp.active = true
              AND gp.geom IS NOT NULL
              AND ST_Intersects(ST_GeomFromEWKT(%s)::geometry, gp.geom)
            ORDER BY ST_Area(ST_Intersection(ST_GeomFromEWKT(%s)::geometry, gp.geom))
                     DESC NULLS LAST
            LIMIT 1
            """,
            (ewkt, ewkt),
        )
        row = self.env.cr.fetchone()
        if row:
            return Parcel.browse(row[0])
        return Parcel

    def _sync_geom_to_gis_unit(self):
        """Sync geom_ewkt to ter_gis_unit table for PostGIS operations."""
        UnitTable = base_ter_hooks.UNIT_TABLE
        for unit in self:
            if not unit.geom_ewkt or not unit.geom_ewkt.strip():
                self.env.cr.execute(
                    "DELETE FROM %s WHERE unit_id = %%s" % UnitTable,
                    (unit.id,),
                )
                continue
            ewkt = unit._ensure_ewkt_srid(unit.geom_ewkt)
            self.env.cr.execute(
                """
                INSERT INTO %s (unit_id, geom)
                VALUES (%%s, ST_Multi(ST_GeomFromEWKT(%%s)::geometry)::geometry(MultiPolygon, 25830))
                ON CONFLICT (unit_id) DO UPDATE SET geom = EXCLUDED.geom
                """  # noqa: S608
                % UnitTable,
                (unit.id, ewkt),
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            geom = vals.get("geom_ewkt")
            if geom and not vals.get("parcel_id"):
                parcel = self._get_parcel_from_geometry(geom)
                if parcel:
                    vals["parcel_id"] = parcel.id
                else:
                    raise UserError(
                        _(
                            "No parcel found intersecting the unit geometry. "
                            "Ensure parcels exist with geometry in the same area."
                        )
                    )
        records = super().create(vals_list)
        records._sync_attribute_lines()
        to_sync = records.filtered(lambda r: r.geom_ewkt)
        if to_sync:
            to_sync._sync_geom_to_gis_unit()
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

    def _sync_attribute_lines(self):
        for unit in self:
            if not unit.use_type_id:
                continue

            required_attrs = unit.use_type_id.all_attribute_ids
            existing_attrs = unit.attribute_value_ids.mapped("attribute_id")
            missing_attrs = required_attrs - existing_attrs

            if missing_attrs:
                unit.write({
                    "attribute_value_ids": [(0, 0, {"attribute_id": attr.id}) for attr in missing_attrs]
                })

    def write(self, vals):
        if "geom_ewkt" in vals and "parcel_id" not in vals:
            geom = vals.get("geom_ewkt")
            if geom:
                parcel = self._get_parcel_from_geometry(geom)
                if parcel:
                    vals["parcel_id"] = parcel.id
        res = super().write(vals)
        if "use_type_id" in vals:
            self._sync_attribute_lines()
        if "geom_ewkt" in vals:
            self._sync_geom_to_gis_unit()
        return res

    def _check_domain_specific_rules(self):
        """
        Hook for modules extending ter.unit to add domain-specific validations.
        Override in inherited modules. Called before critical operations if needed.
        """
        pass

    def unlink(self):
        for unit in self:
            if unit.geom_ewkt and unit.geom_ewkt.strip():
                raise UserError(
                    _(
                        "Cannot delete a unit with GIS geometry. "
                        "Clear the geometry first or archive the record."
                    )
                )
        return super().unlink()

    @api.onchange("use_type_id")
    def _onchange_use_type_id(self):
        if not self.use_type_id:
            self.attribute_value_ids = [(5, 0, 0)]
            return
        allowed_attrs = self.use_type_id.all_attribute_ids
        commands = [(5, 0, 0)]
        for attr in allowed_attrs:
            commands.append((0, 0, {"attribute_id": attr.id}))
        self.attribute_value_ids = commands

    @api.constrains("attribute_value_ids")
    def _check_required_attributes(self):
        return True
        for unit in self:
            for line in unit.attribute_value_ids:
                print(line.value_id.id)
                if line.required and not line.value_id:
                    raise ValidationError(
                        _("Attribute '%s' is required.") % line.attribute_id.name
                    )

    @api.depends("date_start", "date_end")
    def _compute_is_current(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.date_start and record.date_end:
                record.is_current = (
                    record.date_start <= today <= record.date_end
                )
            else:
                record.is_current = False

    @api.depends("area_official")
    def _compute_area_official_m2(self):
        config = self.env["ir.config_parameter"].sudo()
        area_unit_is_ha = bool(config.get_param("base_ter.area_unit_is_ha", False))
        factor = 10000.0
        if not area_unit_is_ha:
            value_in_ha = float(
                config.get_param("base_ter.area_unit_value_in_ha", 0) or 0
            )
            if value_in_ha and value_in_ha != 1:
                factor = value_in_ha * 10000.0

        for record in self:
            record.area_official_m2 = round((record.area_official or 0.0) * factor)

