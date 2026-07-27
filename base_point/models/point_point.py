# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, exceptions, fields, models


class PointPoint(models.Model):
    _name = "point.point"
    _description = "Point"
    _inherit = ["simple.model", "point.model", "gis.viewer", "mail.thread"]

    size_name = 20
    minlength = 0
    maxlength = 20
    allowed_blanks_in_code = False
    set_alphanum_code_to_uppercase = True
    sequence_for_codes = ""

    _gis_table = "point_gis_point"
    _geom_field = "geom"
    _link_field = "name"

    _param_gis_selection = "idpunto"
    _gis_mapped_field = "mapped_to_point"

    _aerial_image_size_big = 512
    _aerial_image_size_medium = 256
    _aerial_image_size_small = 128
    _aerial_image_zoom = 1.2

    alphanum_code = fields.Char(string="Point Code", required=True)

    partner_id = fields.Many2one(
        "res.partner",
        string="Point Manager",
        store=True,
        compute="_compute_partner_id",
        readonly=False,
        index=True,
    )
    municipality_id = fields.Many2one(
        "res.municipality", ondelete="restrict", index=True
    )
    place_id = fields.Many2one("res.place", ondelete="restrict", index=True)
    tag_id = fields.Many2many("point.pointtag", relation="point_point_pointtag_rel")
    province_id = fields.Many2one(
        "res.province", compute="_compute_province_id", store=True
    )
    region_id = fields.Many2one(
        "res.admregion", compute="_compute_region_id", store=True
    )
    partnerlink_ids = fields.One2many(
        "point.point.partnerlink",
        "point_id",
        string="Contacts",
    )
    address_data = fields.Char(compute="_compute_address_data")
    altitude = fields.Float(string="Altitude (m)", digits=(32, 2))
    aerial_image = fields.Image(max_width=512, max_height=512)
    aerial_image_key = fields.Char(index=True, readonly=True)
    aerial_image_medium = fields.Image(
        string="Aerial Image (Medium)",
        related="aerial_image",
        store=True,
        max_width=256,
        max_height=256,
    )
    aerial_image_small = fields.Image(
        string="Aerial Image (Small)",
        related="aerial_image",
        store=True,
        max_width=128,
        max_height=128,
    )
    aerial_image_shown = fields.Image(
        compute="_compute_aerial_image_shown", max_width=512, max_height=512
    )
    aerial_image_shown_b64 = fields.Char(compute="_compute_aerial_image_shown_b64")
    image_1920 = fields.Image(string="Aerial Image (Large)", related="aerial_image_shown")
    active = fields.Boolean(default=True)

    @api.constrains("municipality_id", "place_id")
    def _check_geographic_coherence(self):
        for record in self:
            if record.municipality_id and record.place_id:
                if record.place_id.municipality_id != record.municipality_id:
                    raise exceptions.ValidationError(
                        record.env._(
                            "The place '%(place)s' does not belong to "
                            "municipality '%(municipality)s'.",
                            place=record.place_id.description,
                            municipality=record.municipality_id.description,
                        )
                    )

    @api.constrains("partner_id", "partnerlink_ids")
    def _check_partner_is_main(self):
        for record in self:
            if not record.partner_id:
                continue
            main_links = record.partnerlink_ids.filtered("is_main")
            if not main_links or record.partner_id not in main_links.mapped("partner_id"):
                raise exceptions.ValidationError(
                    record.env._(
                        "The manager must appear as a main contact in the partner links."
                    )
                )

    @api.depends("partnerlink_ids.is_main", "partnerlink_ids.partner_id")
    def _compute_partner_id(self):
        for record in self:
            main = record.partnerlink_ids.filtered("is_main")[:1]
            record.partner_id = main.partner_id if main else False

    @api.depends("municipality_id")
    def _compute_province_id(self):
        for record in self:
            record.province_id = record.municipality_id.province_id

    @api.depends("province_id")
    def _compute_region_id(self):
        for record in self:
            record.region_id = record.province_id.region_id

    @api.depends("municipality_id", "place_id")
    def _compute_address_data(self):
        for record in self:
            parts = [
                record.municipality_id.description or "",
                record.place_id.description or "",
            ]
            record.address_data = " · ".join([part for part in parts if part])

    def _compute_aerial_image_shown(self):
        for record in self:
            record.aerial_image_shown = record.aerial_image

    @api.depends("aerial_image_shown")
    def _compute_aerial_image_shown_b64(self):
        for record in self:
            record.aerial_image_shown_b64 = record.aerial_image_shown or False

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._auto_assign_main_partner()  # pylint: disable=protected-access
        return records

    def write(self, vals):
        res = super().write(vals)
        if "partnerlink_ids" in vals:
            self._auto_assign_main_partner()  # pylint: disable=protected-access
        return res

    def _auto_assign_main_partner(self):
        for record in self:
            links = record.partnerlink_ids
            if len(links) == 1 and not links.is_main:
                links.is_main = True

    def action_set_point_code(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Set Point Code"),
            "res_model": "wizard.set.point.code",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_id": self.id,
                "active_ids": [self.id],
                "active_model": "point.point",
            },
        }

    def action_gis_preview(self):
        self.ensure_one()
        if not self.env["ir.model"].sudo().search(
            [("model", "=", "wizard.show.gis.preview")], limit=1
        ):
            raise exceptions.UserError(
                self.env._("GIS preview wizard is not available in this database.")
            )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("GIS Preview"),
            "res_model": "wizard.show.gis.preview",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_centerx": self.coord_x,
                "default_centery": self.coord_y,
            },
        }

    def reset_aerial_image(self):
        for record in self:
            record.aerial_image = False
            record.aerial_image_key = False

    def action_reset_all_aerial_images(self):
        batch_size = 100
        offset = 0
        while True:
            batch = self.search([], limit=batch_size, offset=offset)
            if not batch:
                break
            batch.reset_aerial_image()
            offset += batch_size
        return None
