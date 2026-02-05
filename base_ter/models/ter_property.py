# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
# pylint: disable=too-many-locals

import base64

from odoo import api, exceptions, fields, models
from odoo.http import request


class TerProperty(models.Model):
    _name = "ter.property"
    _description = "Property"
    _inherit = ["simple.model", "polygon.model", "gis.viewer", "mail.thread"]
    _rec_name = "alphanum_code"

    _set_num_code = False
    _sequence_for_codes = ""
    _size_name = 100
    _minlength = 0
    _maxlength = 100
    _allowed_blanks_in_code = True
    _set_alphanum_code_to_lowercase = False
    _set_alphanum_code_to_uppercase = False
    _size_description = 175

    _gis_table = "ter_gis_property"
    _geom_field = "geom"
    _link_field = "name"

    _param_gis_selection = "idfinca"

    _aerial_image_size_big = 512
    _aerial_image_size_medium = 256
    _aerial_image_size_small = 128

    _aerial_image_zoom = 1.2
    _force_square_shape = True

    _area_fields = [("area_official_parcels", "Official Area")]
    _ha_name = "ha"

    alphanum_code = fields.Char(string="Property Name", required=True)

    municipality_id = fields.Many2one(
        comodel_name="res.municipality",
        required=True,
        index=True,
        ondelete="restrict",
    )
    place_id = fields.Many2one(
        comodel_name="res.place",
        index=True,
        ondelete="restrict",
    )
    partner_id = fields.Many2one(
        string="Property Manager",
        comodel_name="res.partner",
        index=True,
        ondelete="restrict",
    )

    aerial_image = fields.Image(
        max_width=_aerial_image_size_big,
        max_height=_aerial_image_size_big,
    )
    aerial_image_key = fields.Char(index=True, readonly=True)

    aerial_image_medium = fields.Image(
        string="Aerial Image (medium)",
        max_width=_aerial_image_size_medium,
        max_height=_aerial_image_size_medium,
        store=True,
        related="aerial_image",
    )
    aerial_image_small = fields.Image(
        string="Aerial Image (small)",
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
    aerial_image_shown_b64 = fields.Char(
        string="Aerial Image shown (base64)",
        compute="_compute_aerial_image_shown",
    )
    aerial_image_shown_256 = fields.Image(
        string="Aerial Image (medium size, non-persistent)",
        max_width=_aerial_image_size_medium,
        max_height=_aerial_image_size_medium,
        related="aerial_image_shown",
    )
    image_1920 = fields.Image(
        string="Aerial Image (zoom)", related="aerial_image_shown"
    )

    tag_id = fields.Many2many(
        string="Tags",
        comodel_name="ter.propertytag",
        relation="ter_property_propertytag_rel",
        column1="property_id",
        column2="propertytag_id",
    )

    parcel_ids = fields.One2many(
        string="Parcels of the property",
        comodel_name="ter.parcel",
        inverse_name="property_id",
    )

    number_of_parcels = fields.Integer(
        string="Number of parcels",
        store=True,
        index=True,
        compute="_compute_number_of_parcels",
    )
    unit_count = fields.Integer(
        string="Units",
        compute="_compute_unit_count",
    )
    area_official_parcels = fields.Float(
        string="Parcel Area",
        digits=(32, 4),
        store=True,
        index=True,
        compute="_compute_area_official_parcels",
    )
    area_official_parcels_m2 = fields.Integer(
        string="Parcel Area (m²)",
        compute="_compute_area_official_parcels_m2",
    )
    diff_areas_threshold_exceeded = fields.Boolean(
        string="Threshold exceeded (difference between official and GIS areas)",
        compute="_compute_diff_areas_threshold_exceeded",
    )

    province_id = fields.Many2one(
        comodel_name="res.province",
        store=True,
        index=True,
        compute="_compute_province_id",
    )
    region_id = fields.Many2one(
        comodel_name="res.admregion",
        store=True,
        index=True,
        compute="_compute_region_id",
    )

    area_unit_name = fields.Char(
        string="Area unit name", compute="_compute_area_unit_name"
    )
    address_data = fields.Char(compute="_compute_address_data")

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
                - extra: Extra parameters
        """
        self.ensure_one()
        return self._make_wms_key(
            self.geom_ewkt or "",
            params.get("wms", ""),
            params.get("layers", ""),
            params.get("styles", ""),
            int(params.get("image_height", 0)),
            int(params.get("image_width", 0)),
            float(params.get("zoom", 0.0)),
            bool(params.get("force_square_shape", False)),
            bool(params.get("apply_filter", False)),
            params.get("extra", ""),
        )

    @api.depends("aerial_image", "mapped_to_polygon")
    def _compute_aerial_image_shown(self):  # pylint: disable=too-many-branches
        config = self.env["ir.config_parameter"].sudo()

        wmsbase_url = config.get_param("base_ter.aerial_image_wmsbase_url", False)
        wmsbase_layers = config.get_param("base_ter.aerial_image_wmsbase_layers", False)
        wmsvec_url = config.get_param("base_ter.aerial_image_wmsvec_url", False)
        wmsvec_layer = config.get_param(
            "base_ter.aerial_image_wmsvec_property_name", False
        )
        wmsvec_filter = bool(
            config.get_param("base_ter.aerial_image_wmsvec_property_filter", False)
        )
        image_height = int(config.get_param("base_ter.aerial_image_height", 0) or 0)
        image_zoom = float(config.get_param("base_ter.aerial_image_zoom", 0) or 0)

        ogc_ok = bool(
            wmsbase_url and wmsbase_layers and image_height >= 0 and image_zoom >= 0
        )
        if image_height == 0:
            image_height = self._aerial_image_size_big
        if image_zoom == 0:
            image_zoom = self._aerial_image_zoom

        use_vec = bool(ogc_ok and wmsvec_url and wmsvec_layer)

        for record in self:
            if not (ogc_ok and record.mapped_to_polygon):
                stored = record.aerial_image or False
                record.aerial_image_shown = stored
                record.aerial_image_shown_b64 = (
                    (stored or b"").decode("ascii", errors="ignore")
                    if isinstance(stored, (bytes, bytearray))
                    else (stored or "")
                )
                continue

            stored_b64 = None
            key = None
            if not use_vec:
                # pylint: disable=protected-access
                key = record._aerial_cache_key(
                    wms=wmsbase_url,
                    layers=wmsbase_layers,
                    styles="default",
                    image_height=image_height,
                    image_width=0,
                    zoom=image_zoom,
                    force_square_shape=self._force_square_shape,
                    apply_filter=False,
                    extra="base",
                )
                if record.aerial_image and record.aerial_image_key == key:
                    stored_b64 = record.aerial_image
                else:
                    stored_b64 = record.get_aerial_image(
                        wms=wmsbase_url,
                        layers=wmsbase_layers,
                        image_height=image_height,
                        image_format="png",
                        zoom=image_zoom,
                        force_square_shape=self._force_square_shape,
                    )
            else:
                # pylint: disable=protected-access
                key = record._aerial_cache_key(
                    wms=wmsbase_url,
                    layers=wmsbase_layers,
                    styles="default",
                    image_height=image_height,
                    image_width=0,
                    zoom=image_zoom,
                    force_square_shape=self._force_square_shape,
                    apply_filter=False,
                    extra="base+vec:%s:%s:%s"
                    % (wmsvec_url or "", wmsvec_layer or "", int(wmsvec_filter)),
                )
                if record.aerial_image and record.aerial_image_key == key:
                    stored_b64 = record.aerial_image
                else:
                    base_raw = record.get_aerial_image(
                        wms=wmsbase_url,
                        layers=wmsbase_layers,
                        image_height=image_height,
                        image_format="png",
                        zoom=image_zoom,
                        get_raw=True,
                        apply_filter=False,
                        force_square_shape=self._force_square_shape,
                    )
                    vec_raw = record.get_aerial_image(
                        wms=wmsvec_url,
                        layers=wmsvec_layer,
                        image_height=image_height,
                        image_format="png",
                        zoom=image_zoom,
                        get_raw=True,
                        apply_filter=wmsvec_filter,
                        force_square_shape=self._force_square_shape,
                    )
                    if base_raw and vec_raw:
                        merged_bytes = self.env["common.image"].merge_img(
                            base_raw,
                            vec_raw,
                            return_base64=False,
                        )
                        if merged_bytes:
                            stored_b64 = base64.b64encode(merged_bytes)

            if stored_b64:
                record.aerial_image = stored_b64
                record.aerial_image_key = key
                record.aerial_image_shown = stored_b64
                record.aerial_image_shown_b64 = (
                    stored_b64.decode("ascii", errors="ignore")
                    if isinstance(stored_b64, (bytes, bytearray))
                    else (stored_b64 or "")
                )
                self.env["common.log"].register_in_log(
                    self.env._(
                        "Aerial image OK. Property: %(name)s",
                        name=record.name,
                    ),
                    source=self._name,
                    message_type="INFO",
                )
            else:
                record.aerial_image_shown = False
                record.aerial_image_shown_b64 = ""
                self.env["common.log"].register_in_log(
                    self.env._("Error getting aerial image (is the WMS url correct?)"),
                    source=self._name,
                    message_type="WARNING",
                )

    @api.depends("parcel_ids")
    def _compute_number_of_parcels(self):
        for record in self:
            record.number_of_parcels = len(record.parcel_ids)

    @api.depends("parcel_ids.unit_ids")
    def _compute_unit_count(self):
        unit_model = self.env["ter.unit"]
        for record in self:
            count = unit_model.search_count([("farm_property_id", "=", record.id)])
            record.unit_count = count

    @api.depends("parcel_ids.area_official")
    def _compute_area_official_parcels(self):
        for record in self:
            record.area_official_parcels = sum(
                record.parcel_ids.mapped("area_official")
            )

    @api.depends("area_official_parcels")
    def _compute_area_official_parcels_m2(self):
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
            record.area_official_parcels_m2 = round(
                (record.area_official_parcels or 0.0) * factor
            )

    @api.depends(
        "mapped_to_polygon",
        "area_official_parcels_m2",
        "area_gis",
        "area_official_parcels",
    )
    def _compute_diff_areas_threshold_exceeded(self):
        config = self.env["ir.config_parameter"].sudo()
        warning = int(config.get_param("base_ter.warning_diff_areas", 0) or 0)

        for record in self:
            exceeded = False
            if (
                warning > 0
                and record.area_official_parcels > 0
                and record.mapped_to_polygon
            ):
                diff = abs(
                    (record.area_official_parcels_m2 or 0) - (record.area_gis or 0)
                )
                threshold = int(
                    round((record.area_official_parcels_m2 or 0) * (warning / 100.0))
                )
                exceeded = diff > threshold
            record.diff_areas_threshold_exceeded = exceeded

    @api.depends("municipality_id.province_id")
    def _compute_province_id(self):
        for record in self:
            record.province_id = (
                record.municipality_id.province_id if record.municipality_id else False
            )

    @api.depends("province_id.region_id")
    def _compute_region_id(self):
        for record in self:
            record.region_id = (
                record.province_id.region_id if record.province_id else False
            )

    @api.depends_context("lang")
    def _compute_area_unit_name(self):
        config = self.env["ir.config_parameter"].sudo()
        area_unit_is_ha = bool(config.get_param("base_ter.area_unit_is_ha", False))
        if area_unit_is_ha:
            unit_name = self.env._("ha")
        else:
            unit_name = config.get_param("base_ter.area_unit_name", "") or ""
        for record in self:
            record.area_unit_name = unit_name

    @api.depends("municipality_id", "place_id", "municipality_id.province_id")
    def _compute_address_data(self):
        for record in self:
            if not record.municipality_id or not record.municipality_id.province_id:
                record.address_data = ""
                continue

            base = "%s (%s)" % (
                record.municipality_id.name,
                record.municipality_id.province_id.name,
            )
            if (
                record.place_id
                and (record.place_id.name or "").lower()
                != (record.municipality_id.name or "").lower()
            ):
                base = "%s - %s" % (record.place_id.name, base)
            record.address_data = base

    @api.constrains("municipality_id", "place_id")
    def _check_place_id(self):
        for record in self:
            if (
                record.municipality_id
                and record.place_id
                and record.place_id.municipality_id != record.municipality_id
            ):
                raise exceptions.ValidationError(
                    self.env._("The place is not in the municipality.")
                )

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type not in ("form", "list"):
            return arch, view

        area_fields = self._add_area_fields() or []
        if not area_fields:
            return arch, view

        area_map = dict(area_fields)

        config = self.env["ir.config_parameter"].sudo()
        area_unit_is_ha = bool(config.get_param("base_ter.area_unit_is_ha", False))
        area_unit_name = config.get_param("base_ter.area_unit_name", "") or ""
        value_in_ha = float(config.get_param("base_ter.area_unit_value_in_ha", 0) or 0)

        measure_name = self.env._(self._ha_name)
        if (
            not area_unit_is_ha
            and area_unit_name
            and value_in_ha
            and value_in_ha != 1
            and area_unit_name != measure_name
        ):
            measure_name = area_unit_name

        for field_name, label in area_map.items():
            for node in arch.xpath(f"//field[@name='{field_name}']"):
                node.set(
                    "string",
                    "%s (%s)" % (self.env._(label), measure_name),
                )

        return arch, view

    def write(self, vals):
        old_partner = self.partner_id if len(self) == 1 else self.env["res.partner"]
        res = super().write(vals)

        config = self.env["ir.config_parameter"].sudo()
        same_owner = bool(
            config.get_param("base_ter.same_parcelmanager_propertyowner", False)
        )
        if not (same_owner and old_partner and vals.get("partner_id")):
            return res

        new_partner = self.env["res.partner"].browse(vals["partner_id"])
        for prop in self:
            for parcel in prop.parcel_ids:
                links = parcel.partnerlink_ids.filtered(
                    lambda link: link.partner_id == old_partner
                )
                links.write({"partner_id": new_partner.id})
                parcel.partner_id = new_partner

        return res

    @api.model
    def action_refresh_properties_layer(self, from_backend=False):
        config = self.env["ir.config_parameter"].sudo()
        epsg = int(config.get_param("base_ter.gis_viewer_epsg", 0) or 0) or 25830

        message_type = "INFO"
        message = self.env._("ter_gis_property layer recreated.")
        module = model = method = ""

        try:
            self.env.cr.execute("DROP TABLE IF EXISTS ter_gis_property")
            self.env.cr.execute(
                """
                CREATE TABLE ter_gis_property AS
                SELECT ROW_NUMBER() OVER (ORDER BY terpro.name) AS gid,
                       terpro.name,
                       ST_Multi(
                               ST_Union(
                                       ST_Transform(
                                           tergispar.geom::geometry, %s
                                       )
                               )
                       ) ::geometry(MultiPolygon,%s) AS geom
                FROM ter_gis_parcel tergispar
                    INNER JOIN ter_parcel terpar
                        ON tergispar.name = terpar.name
                    INNER JOIN ter_property terpro
                        ON terpro.id = terpar.property_id
                WHERE terpar.active = TRUE
                GROUP BY terpro.name
                """,
                (epsg, epsg),
            )
            self.env.cr.execute("ALTER TABLE ter_gis_property ADD PRIMARY KEY (gid)")
            self.env.cr.execute(
                "ALTER TABLE ter_gis_property ALTER COLUMN name SET NOT NULL"
            )
            self.env.cr.execute(
                "ALTER TABLE ter_gis_property "
                "ADD CONSTRAINT ter_gis_property_name_key UNIQUE(name)"
            )
            self.env.cr.execute(
                "ALTER TABLE ter_gis_property "
                "ADD CONSTRAINT ter_gis_property_name_check "
                "CHECK (name <> '')"
            )
            self.env.cr.execute(
                "CREATE INDEX IF NOT EXISTS ter_gis_property_idx "
                "ON public.ter_gis_property USING gist (geom)"
            )
        except RuntimeError as err:
            message_type = "ERROR"
            message = str(err)
            module = "base_ter"
            model = "ter.property"
            method = "action_refresh_properties_layer"

        self.env["common.log"].register_in_log(
            message,
            source=self._name,
            module=module,
            model=model,
            method=method,
            message_type=message_type,
        )
        if from_backend:
            return {"type": "ir.actions.client", "tag": "reload"}
        return None

    def delete_aerial_image(self):
        for record in self:
            record.aerial_image = False
            record.aerial_image_key = False
            record.aerial_image_medium = False
            record.aerial_image_small = False
            record.aerial_image_shown = False
            record.aerial_image_shown_256 = False
            record.aerial_image_shown_b64 = False
            record.image_1920 = False

    def reset_aerial_image(self):
        if len(self) == 1:
            self.aerial_image = False
            self.aerial_image_key = False
            self._compute_aerial_image_shown()  # pylint: disable=protected-access
            return

        progress_msg = request.env._("Getting the aerial images...")
        for record in self.with_progress(progress_msg):
            record.aerial_image = False
            record.aerial_image_key = False
            record._compute_aerial_image_shown()  # pylint: disable=protected-access

    @api.model
    def action_reset_all_aerial_images(self, from_backend=False):
        batch_size = 100
        offset = 0
        while True:
            batch = self.search([], limit=batch_size, offset=offset)
            if not batch:
                break
            batch.reset_aerial_image()
            offset += batch_size
        if from_backend:
            return {"type": "ir.actions.client", "tag": "reload"}
        return None

    def action_gis_preview(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "%s : %s"
            % (
                self.env._("Property on the map"),
                self.alphanum_code,
            ),
            "res_model": "wizard.show.gis.preview",
            "view_mode": "form",
            "target": "new",
            "context": {
                "src_model": "ter.property",
                "active_id": self.id,
            },
        }

    def action_show_units(self):
        self.ensure_one()
        list_view = self.env.ref("base_ter.c")
        form_view = self.env.ref("base_ter.view_ter_unit_form")
        search_view = self.env.ref("base_ter.view_ter_unit_filter")
        default_parcel = self.parcel_ids[:1].id if self.parcel_ids else False
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Territorial Units"),
            "res_model": "ter.unit",
            "view_mode": "list,form",
            "views": [
                (list_view.id, "list"),
                (form_view.id, "form"),
            ],
            "search_view_id": search_view.id,
            "target": "current",
            "domain": [("farm_property_id", "=", self.id)],
            "context": {"default_parcel_id": default_parcel},
        }

    def action_show_parcels(self):
        self.ensure_one()
        tree_view = self.env.ref("base_ter.ter_parcel_view_tree")
        form_view = self.env.ref("base_ter.ter_parcel_view_form")
        kanban_view = self.env.ref("base_ter.ter_parcel_view_kanban")
        search_view = self.env.ref("base_ter.ter_parcel_view_search")

        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Parcels"),
            "res_model": "ter.parcel",
            "view_mode": "list,form,kanban",
            "views": [
                (tree_view.id, "list"),
                (form_view.id, "form"),
                (kanban_view.id, "kanban"),
            ],
            "search_view_id": search_view.id,
            "target": "current",
            "domain": [("property_id", "=", self.id)],
            "context": {
                "default_partner_id": self.partner_id.id if self.partner_id else False,
                "default_property_id": self.id,
            },
        }

    def _refresh_computed_fields(self):
        self._compute_number_of_parcels()
        self._compute_area_official_parcels()

    @api.model
    def _add_area_fields(self):
        return self._area_fields
