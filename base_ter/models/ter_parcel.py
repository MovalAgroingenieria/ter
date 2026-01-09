# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64

from odoo import _, api, exceptions, fields, models


class TerParcel(models.Model):
    _name = "ter.parcel"
    _description = "Parcel"
    _inherit = ["simple.model", "polygon.model", "gis.viewer", "mail.thread"]

    MAX_SIZE_OFFICIAL_CODE = 50

    _set_num_code = False
    _sequence_for_codes = ""
    _size_name = 20
    _minlength = 0
    _maxlength = 20
    _allowed_blanks_in_code = False
    _set_alphanum_code_to_lowercase = False
    _set_alphanum_code_to_uppercase = True
    _size_description = 75

    _gis_table = "ter_gis_parcel"
    _geom_field = "geom"
    _link_field = "name"

    _param_gis_selection = "idparcela"

    _aerial_image_size_big = 512
    _aerial_image_size_medium = 256
    _aerial_image_size_small = 128

    _aerial_image_zoom = 1.2
    _force_square_shape = True

    _area_fields = [("area_official", "Official Area")]
    _ha_name = "ha"

    alphanum_code = fields.Char(string="Parcel Code", required=True)

    municipality_id = fields.Many2one(
        string="Municipality",
        comodel_name="res.municipality",
        required=True,
        index=True,
        ondelete="restrict",
    )
    place_id = fields.Many2one(
        string="Place",
        comodel_name="res.place",
        index=True,
        ondelete="restrict",
    )

    area_official = fields.Float(
        string="Official Area",
        digits=(32, 4),
        default=0,
        required=True,
        index=True,
    )
    area_official_m2 = fields.Integer(
        string="Official Area (m²)",
        compute="_compute_area_official_m2",
    )

    diff_areas_threshold_exceeded = fields.Boolean(
        string="Threshold exceeded (difference between official and GIS areas)",
        compute="_compute_diff_areas_threshold_exceeded",
    )

    official_code = fields.Char(string="Official Code", size=MAX_SIZE_OFFICIAL_CODE, index=True)

    partner_id = fields.Many2one(
        string="Parcel Manager",
        comodel_name="res.partner",
        store=True,
        compute="_compute_partner_id",
        readonly=False,
        index=True,
    )

    property_id = fields.Many2one(
        string="Property",
        comodel_name="ter.property",
        index=True,
        ondelete="restrict",
    )

    aerial_image = fields.Image(
        string="Aerial Image",
        max_width=_aerial_image_size_big,
        max_height=_aerial_image_size_big,
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

    aerial_image_shown = fields.Image(
        string="Aerial Image (non-persistent)",
        max_width=_aerial_image_size_big,
        max_height=_aerial_image_size_big,
        compute="_compute_aerial_image_shown",
    )
    aerial_image_shown_256 = fields.Image(
        string="Aerial Image (medium size, non-persistent)",
        max_width=_aerial_image_size_medium,
        max_height=_aerial_image_size_medium,
        related="aerial_image_shown",
    )
    image_1920 = fields.Image(string="Aerial Image (zoom)", related="aerial_image_shown")

    tag_id = fields.Many2many(
        string="Tags",
        comodel_name="ter.parceltag",
        relation="ter_parcel_parceltag_rel",
        column1="parcel_id",
        column2="parceltag_id",
    )

    province_id = fields.Many2one(
        string="Province",
        comodel_name="res.province",
        store=True,
        index=True,
        compute="_compute_province_id",
    )
    region_id = fields.Many2one(
        string="Region",
        comodel_name="res.admregion",
        store=True,
        index=True,
        compute="_compute_region_id",
    )

    area_unit_name = fields.Char(string="Area unit name", compute="_compute_area_unit_name")

    property_data = fields.Char(string="Property Data", compute="_compute_property_data")
    address_data = fields.Char(string="Address Data", compute="_compute_address_data")

    partnerlink_ids = fields.One2many(
        string="Contacts of parcel",
        comodel_name="ter.parcel.partnerlink",
        inverse_name="parcel_id",
    )
    partner_code = fields.Integer(string="Partner Code", compute="_compute_partner_code")

    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("area_official_ok", "CHECK (area_official >= 0)", 'Incorrect value for "Official Area".'),
    ]

    @api.depends("area_official")
    def _compute_area_official_m2(self):
        config = self.env["ir.config_parameter"].sudo()
        area_unit_is_ha = bool(config.get_param("base_ter.area_unit_is_ha", False))
        factor = 10000.0
        if not area_unit_is_ha:
            value_in_ha = float(config.get_param("base_ter.area_unit_value_in_ha", 0) or 0)
            if value_in_ha and value_in_ha != 1:
                factor = value_in_ha * 10000.0

        for record in self:
            record.area_official_m2 = round((record.area_official or 0.0) * factor)

    @api.depends("mapped_to_polygon", "area_official_m2", "area_gis")
    def _compute_diff_areas_threshold_exceeded(self):
        config = self.env["ir.config_parameter"].sudo()
        warning = int(config.get_param("base_ter.warning_diff_areas", 0) or 0)

        for record in self:
            exceeded = False
            if warning > 0 and record.mapped_to_polygon:
                diff = abs((record.area_official_m2 or 0) - (record.area_gis or 0))
                threshold = int(round((record.area_official_m2 or 0) * (warning / 100.0)))
                exceeded = diff > threshold
            record.diff_areas_threshold_exceeded = exceeded

    @api.depends("partnerlink_ids.is_main", "partnerlink_ids.partner_id")
    def _compute_partner_id(self):
        for record in self:
            main = record.partnerlink_ids.filtered("is_main")[:1]
            record.partner_id = main.partner_id if main else False

    @api.depends("aerial_image", "mapped_to_polygon")
    def _compute_aerial_image_shown(self):
        config = self.env["ir.config_parameter"].sudo()

        wmsbase_url = config.get_param("base_ter.aerial_image_wmsbase_url", False)
        wmsbase_layers = config.get_param("base_ter.aerial_image_wmsbase_layers", False)
        wmsvec_url = config.get_param("base_ter.aerial_image_wmsvec_url", False)
        wmsvec_parcel_layer = config.get_param("base_ter.aerial_image_wmsvec_parcel_name", False)
        wmsvec_filter = bool(config.get_param("base_ter.aerial_image_wmsvec_parcel_filter", False))
        image_height = int(config.get_param("base_ter.aerial_image_height", 0) or 0)
        image_zoom = float(config.get_param("base_ter.aerial_image_zoom", 0) or 0)

        ogc_ok = bool(wmsbase_url and wmsbase_layers and image_height >= 0 and image_zoom >= 0)
        if image_height == 0:
            image_height = self._aerial_image_size_big
        if image_zoom == 0:
            image_zoom = self._aerial_image_zoom

        use_vec = bool(ogc_ok and wmsvec_url and wmsvec_parcel_layer)

        for record in self:
            shown = record.aerial_image or None
            if shown or not (ogc_ok and record.mapped_to_polygon):
                record.aerial_image_shown = shown
                continue

            if not use_vec:
                shown = record.get_aerial_image(
                    wms=wmsbase_url,
                    layers=wmsbase_layers,
                    image_height=image_height,
                    format="png",
                    zoom=image_zoom,
                    force_square_shape=self._force_square_shape,
                )
            else:
                base_raw = record.get_aerial_image(
                    wms=wmsbase_url,
                    layers=wmsbase_layers,
                    image_height=image_height,
                    format="png",
                    zoom=image_zoom,
                    get_raw=True,
                    filter=False,
                    force_square_shape=self._force_square_shape,
                )
                vec_raw = record.get_aerial_image(
                    wms=wmsvec_url,
                    layers=wmsvec_parcel_layer,
                    image_height=image_height,
                    format="png",
                    zoom=image_zoom,
                    get_raw=True,
                    filter=wmsvec_filter,
                    force_square_shape=self._force_square_shape,
                )
                if base_raw and vec_raw:
                    merged = self.env["common.image"].merge_img(base_raw, vec_raw)
                    if merged:
                        shown = base64.b64encode(merged.getvalue())

            if shown:
                record.aerial_image = shown
                self.env["common.log"].register_in_log(
                    _("Aerial image OK. Parcel: %s") % (record.name,),
                    source=self._name,
                    message_type="INFO",
                )
            else:
                self.env["common.log"].register_in_log(
                    _("Error getting aerial image (is the WMS url correct?)"),
                    source=self._name,
                    message_type="WARNING",
                )

            record.aerial_image_shown = shown

    @api.depends("municipality_id.province_id")
    def _compute_province_id(self):
        for record in self:
            record.province_id = record.municipality_id.province_id if record.municipality_id else False

    @api.depends("province_id.region_id")
    def _compute_region_id(self):
        for record in self:
            record.region_id = record.province_id.region_id if record.province_id else False

    @api.depends_context("lang")
    def _compute_area_unit_name(self):
        config = self.env["ir.config_parameter"].sudo()
        area_unit_is_ha = bool(config.get_param("base_ter.area_unit_is_ha", False))
        unit_name = _("ha") if area_unit_is_ha else (config.get_param("base_ter.area_unit_name", "") or "")
        for record in self:
            record.area_unit_name = unit_name

    @api.depends("property_id")
    def _compute_property_data(self):
        for record in self:
            record.property_data = record.property_id.name if record.property_id else _("not assigned")

    @api.depends("municipality_id", "place_id", "municipality_id.province_id")
    def _compute_address_data(self):
        for record in self:
            if not record.municipality_id or not record.municipality_id.province_id:
                record.address_data = ""
                continue

            base = "%s (%s)" % (record.municipality_id.name, record.municipality_id.province_id.name)
            if record.place_id and (record.place_id.name or "").lower() != (record.municipality_id.name or "").lower():
                base = "%s - %s" % (record.place_id.name, base)
            record.address_data = base

    @api.depends("partner_id.partner_code")
    def _compute_partner_code(self):
        for record in self:
            record.partner_code = record.partner_id.partner_code if record.partner_id and record.partner_id.partner_code > 0 else 0

    @api.constrains("municipality_id", "place_id")
    def _check_place_id(self):
        for record in self:
            if record.municipality_id and record.place_id and record.place_id.municipality_id != record.municipality_id:
                raise exceptions.ValidationError(_("The place is not in the municipality."))

    @api.constrains("partner_id", "property_id")
    def _check_property_id(self):
        config = self.env["ir.config_parameter"].sudo()
        same_owner = bool(config.get_param("base_ter.same_parcelmanager_propertyowner", False))
        if not same_owner:
            return

        for record in self:
            if record.partner_id and record.property_id and record.partner_id != record.property_id.partner_id:
                raise exceptions.ValidationError(
                    _("The parcel manager and the property manager must be the same person.")
                )

    @api.constrains("partner_id", "partnerlink_ids")
    def _check_partner_id(self):
        for record in self:
            if record.partner_id:
                if not record.partner_id.is_holder:
                    raise exceptions.ValidationError(_("The contact chosen as main is not a manager."))
                if not record.partnerlink_ids:
                    raise exceptions.ValidationError(
                        _("If a manager is assigned to the parcel, it is mandatory to configure the contact list.")
                    )

            main = record.partnerlink_ids.filtered("is_main")[:1]
            if main and record.partner_id and main.partner_id != record.partner_id:
                raise exceptions.ValidationError(
                    _("The parcel manager and the main contact must be the same person.")
                )

    @api.constrains("partner_id", "partnerlink_ids")
    def _check_partnerlink_ids(self):
        for record in self:
            if not record.partnerlink_ids:
                if record.partner_id:
                    raise exceptions.ValidationError(
                        _("The main contact exists, but the contact list of the parcel is empty.")
                    )
                continue

            if not record.partner_id:
                raise exceptions.ValidationError(_("It is mandatory to enter the parcel manager."))

            mains = record.partnerlink_ids.filtered("is_main")
            if len(mains) != 1:
                raise exceptions.ValidationError(
                    _("It is mandatory to enter the main contact of the parcel (only one).")
                )

            profiles = record.partnerlink_ids.mapped("profile_id")
            for profile in profiles:
                if not profile or not profile.requires_total:
                    continue
                links = record.partnerlink_ids.filtered(lambda l: l.profile_id == profile)
                total = sum(links.mapped("percentage"))
                if total != 100:
                    raise exceptions.ValidationError(
                        _("Review the profile percentages: there is a percentage profile that does not add up to 100%.")
                    )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if not self.partner_id:
            return

        if not self.partnerlink_ids or len(self.partnerlink_ids) == 1:
            profile_id, percentage = self._get_default_profile()
            self.partnerlink_ids = [
                (5,),
                (
                    0,
                    0,
                    self._get_default_first_partnerlink_vals(self.partner_id.id, profile_id, percentage),
                ),
            ]
            return

        main = self.partnerlink_ids.filtered("is_main")[:1]
        if main:
            self.partnerlink_ids = [(1, main.id, {"partner_id": self.partner_id.id})]

    def _get_default_profile(self):
        profile_id = self.env.ref("base_ter.ter_profile_01").id
        return profile_id, 100

    def _get_default_first_partnerlink_vals(self, partner_id, profile_id, percentage):
        return {
            "partner_id": partner_id,
            "profile_id": profile_id,
            "is_main": True,
            "percentage": percentage,
        }

    def name_get(self):
        show_archived = bool(self.env.context.get("show_archived_in_parcel_code", False))
        res = []
        for record in self:
            name = record.name
            if show_archived:
                name = _("Available") if record.active else _("ARCHIVED")
            res.append((record.id, name))
        return res

    def write(self, vals):
        res = super().write(vals)
        if "active" not in vals:
            return res

        partners = self.mapped("partnerlink_ids.partner_id").filtered("is_holder")
        for record in self.filtered("property_id"):
            record.property_id._refresh_computed_fields()

        if partners:
            partners._refresh_computed_fields()
        return res

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type not in ("form", "tree"):
            return arch, view

        area_fields = self._add_area_fields() or []
        if not area_fields:
            return arch, view

        # unique by field name
        area_map = {field_name: label for field_name, label in area_fields}

        config = self.env["ir.config_parameter"].sudo()
        area_unit_is_ha = bool(config.get_param("base_ter.area_unit_is_ha", False))
        area_unit_name = config.get_param("base_ter.area_unit_name", "") or ""
        value_in_ha = float(config.get_param("base_ter.area_unit_value_in_ha", 0) or 0)

        measure_name = _(self._ha_name)
        if not area_unit_is_ha and area_unit_name and value_in_ha and value_in_ha != 1 and area_unit_name != measure_name:
            measure_name = area_unit_name

        for field_name, label in area_map.items():
            for node in arch.xpath(f"//field[@name='{field_name}']"):
                node.set("string", "%s (%s)" % (_(label), measure_name))

        return arch, view

    def reset_aerial_image(self):
        if len(self) == 1:
            self.aerial_image = False
            self._compute_aerial_image_shown()
            return

        for record in self.with_progress(_("Getting the aerial images...")):
            record.aerial_image = False
            record._compute_aerial_image_shown()

    @api.model
    def action_reset_all_aerial_images(self, from_backend=False):
        self.search([]).reset_aerial_image()
        if from_backend:
            return {"type": "ir.actions.client", "tag": "reload"}

    def action_gis_preview(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "%s : %s" % (_("Parcel on the map"), self.alphanum_code),
            "res_model": "wizard.show.gis.preview",
            "view_mode": "form",
            "target": "new",
            "context": {"src_model": "ter.parcel"},
        }

    def action_set_parcel_code(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "%s : %s" % (_("Parcel"), self.alphanum_code),
            "res_model": "wizard.set.parcel.code",
            "view_mode": "form",
            "target": "new",
        }

    @api.model
    def _add_area_fields(self):
        return self._area_fields
