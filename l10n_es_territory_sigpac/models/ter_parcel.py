# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64

from odoo import api, fields, models


class TerParcel(models.Model):
    _inherit = "ter.parcel"

    _aerial_img_sigpac_layers = ["pnoa", "sigpac_name", "parcel", "sigpac", "n_arrow"]
    _aerial_img_sigpac_layers_styles = ["default"] * 5

    sigpaclink_ids = fields.One2many(
        comodel_name="ter.parcel.sigpaclink",
        inverse_name="parcel_id",
    )
    number_of_sigpaclinks = fields.Integer(
        compute="_compute_number_of_sigpaclinks",
        store=False,
    )
    parcel_title_sigpac = fields.Char(
        compute="_compute_parcel_title_sigpac",
        store=False,
    )

    aerial_img_sigpac = fields.Binary(attachment=True)
    aerial_img_sigpac_shown = fields.Binary(
        compute="_compute_aerial_img_sigpac_shown",
        store=False,
    )
    aerial_img_sigpac_scale = fields.Integer(readonly=True)

    display_name = fields.Char(compute="_compute_display_name", store=False)

    def _compute_number_of_sigpaclinks(self):
        for record in self:
            record.number_of_sigpaclinks = len(record.sigpaclink_ids)

    def _compute_parcel_title_sigpac(self):
        for record in self:
            record.parcel_title_sigpac = record.env._(
                "PARCEL: %(name)s, SIGPAC ENCLOSURES", name=record.name or ""
            )

    def _compute_display_name(self):
        super()._compute_display_name()
        if not self.env.context.get("sigpac"):
            return
        for record in self:
            record.display_name = record.env._(
                "%(name)s (Sigpac)", name=record.display_name or ""
            )

    @api.depends("aerial_img_sigpac", "mapped_to_polygon")
    def _compute_aerial_img_sigpac_shown(self):
        params = self.env["ir.config_parameter"].sudo()

        wmsbase_url = params.get_param("base_ter.aerial_image_wmsbase_url") or False
        wmsbase_layers = params.get_param("base_ter.aerial_image_wmsbase_layers") or False
        wmsvec_url = params.get_param("base_ter.aerial_image_wmsvec_url") or False
        wmsvec_parcel_layer = (
            params.get_param("base_ter.aerial_image_wmsvec_parcel_name") or False
        )
        wmsvec_filter = bool(
            params.get_param("base_ter.aerial_image_wmsvec_parcel_filter") or False
        )
        image_height = int(params.get_param("base_ter.aerial_image_height", 0) or 0)
        image_zoom = float(params.get_param("base_ter.aerial_image_zoom", 0) or 0)

        wmssigpac_url = params.get_param("l10n_es_territory_sigpac.wms_sigpac_url") or False
        wmssigpac_layers = (
            params.get_param("l10n_es_territory_sigpac.wms_sigpac_layer") or False
        )

        ogc_ok = bool(
            wmsbase_url and wmsbase_layers and image_height >= 0 and image_zoom >= 0
        )
        if not image_height:
            image_height = getattr(self, "_aerial_image_size_big", 0) or 0
        if not image_zoom:
            image_zoom = getattr(self, "_aerial_image_zoom", 0) or 0.0

        use_vec = bool(ogc_ok and wmsvec_url and wmsvec_parcel_layer)
        use_sigpac = bool(ogc_ok and wmssigpac_url and wmssigpac_layers)

        for record in self:
            shown = record.aerial_img_sigpac or False
            if shown or not (ogc_ok and record.mapped_to_polygon):
                record.aerial_img_sigpac_shown = shown or False
                continue

            shown = record._get_aerial_img_sigpac_from_wms(
                wmsbase_url=wmsbase_url,
                wmsbase_layers=wmsbase_layers,
                wmsvec_url=wmsvec_url,
                wmsvec_parcel_layer=wmsvec_parcel_layer,
                wmsvec_filter=wmsvec_filter,
                wmssigpac_url=wmssigpac_url,
                wmssigpac_layers=wmssigpac_layers,
                image_height=image_height,
                image_zoom=image_zoom,
                use_vec=use_vec,
                use_sigpac=use_sigpac,
            )

            if shown:
                record.aerial_img_sigpac = shown
                self.env["common.log"].register_in_log(
                    record.env._(
                        "Aerial image OK. Parcel: %(name)s", name=record.name or ""
                    ),
                    source=record._name,
                    message_type="INFO",
                )
            else:
                self.env["common.log"].register_in_log(
                    record.env._("Error getting aerial image (is the WMS url correct?)"),
                    source=record._name,
                    message_type="WARNING",
                )

            record.aerial_img_sigpac_shown = shown or False

    def _get_aerial_img_sigpac_from_wms(
        self,
        *,
        wmsbase_url,
        wmsbase_layers,
        wmsvec_url,
        wmsvec_parcel_layer,
        wmsvec_filter,
        wmssigpac_url,
        wmssigpac_layers,
        image_height,
        image_zoom,
        use_vec,
        use_sigpac,
    ):
        self.ensure_one()
        force_square_shape = bool(getattr(self, "_force_square_shape", False))

        base_raw = self.get_aerial_image(
            wms=wmsbase_url,
            layers=wmsbase_layers,
            image_height=image_height,
            image_format="png",
            zoom=image_zoom,
            get_raw=True,
            apply_filter=False,
            force_square_shape=force_square_shape,
        )
        if not base_raw:
            return False

        merged_bytes = None

        if use_sigpac:
            sigpac_raw = self.get_aerial_image(
                wms=wmssigpac_url,
                layers=wmssigpac_layers,
                image_height=image_height,
                image_format="png",
                zoom=image_zoom,
                get_raw=True,
                apply_filter=False,
                force_square_shape=force_square_shape,
            )
            if sigpac_raw:
                merged_bytes = self.env["common.image"].merge_img(
                    base_raw, sigpac_raw, return_base64=False
                )

        if not merged_bytes:
            merged_bytes = base_raw.getvalue() if hasattr(base_raw, "getvalue") else False

        if use_vec:
            vec_raw = self.get_aerial_image(
                wms=wmsvec_url,
                layers=wmsvec_parcel_layer,
                image_height=image_height,
                image_format="png",
                zoom=image_zoom,
                get_raw=True,
                apply_filter=wmsvec_filter,
                force_square_shape=force_square_shape,
            )
            if vec_raw:
                merged_bytes = self.env["common.image"].merge_img(
                    merged_bytes, vec_raw, return_base64=False
                ) or merged_bytes

        if not merged_bytes:
            return False

        return base64.b64encode(merged_bytes)

    def _get_aerial_image_sigpac_layers(self, parcel):
        return self._aerial_img_sigpac_layers

    def _get_aerial_image_sigpac_layers_styles(self, parcel):
        return self._aerial_img_sigpac_layers_styles

    def action_get_enclosures(self):
        self.ensure_one()
        form_view = self.env.ref("l10n_es_territory_sigpac.ter_parcel_sigpac_view_form")
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("SIGPAC enclosures of the parcel"),
            "res_model": "ter.parcel",
            "view_mode": "form",
            "views": [(form_view.id, "form")],
            "target": "current",
            "res_id": self.id,
            "context": {"sigpac": True},
        }

    def action_regenerate_aerial_img_sigpac(self):
        parcels = self.search([("mapped_to_polygon", "=", True)])
        parcels._compute_aerial_img_sigpac_shown()


class TerParcelSigpaclink(models.Model):
    _name = "ter.parcel.sigpaclink"
    _auto = False
    _description = "SIGPAC link of a parcel"
    _order = "name"

    name = fields.Char()
    parcel_id = fields.Many2one(comodel_name="ter.parcel")
    sigpac_id = fields.Many2one(comodel_name="ter.sigpac")

    enclosure_number = fields.Integer(compute="_compute_enclosure_number", store=False)

    municipality_id = fields.Many2one(comodel_name="res.municipality")

    parcel_area = fields.Float(digits=(32, 2))
    sigpac_area = fields.Float(digits=(32, 2))
    area_ha = fields.Float(digits=(32, 4))

    parcel_area_ha = fields.Float(
        compute="_compute_parcel_area_ha",
        digits=(32, 4),
        store=False,
    )

    intersection_percentage = fields.Float(digits=(32, 2))
    pend_media_porc = fields.Float(digits=(32, 2))
    coef_admis = fields.Integer()
    coef_rega = fields.Integer()

    uso_sigpac = fields.Selection(
        selection=[
            ("AG", "AG - CORRIENTES Y SUPERFICIES DE AGUA"),
            ("CA", "CA - VIALES"),
            ("CF", "CF - ASOCIACIÓN CÍTRICOS-FRUTALES"),
            ("CI", "CI - CITRICOS"),
            ("CS", "CS - ASOCIACIÓN CÍTRICOS-FRUTALES DE CÁSCARA"),
            ("CV", "CV - ASOCIACIÓN CÍTRICOS-VIÑEDO"),
            ("ED", "ED - EDIFICACIONES"),
            ("EP", "EP - ELEMENTO DEL PAISAJE"),
            ("FF", "FF - ASOCIACIÓN FRUTALES-FRUTALES DE CÁSCARA"),
            ("FL", "FL - FRUTOS SECOS Y OLIVAR"),
            ("FO", "FO - FORESTAL"),
            ("FS", "FS - FRUTOS SECOS"),
            ("FV", "FV - FRUTOS SECOS Y VIÑEDO"),
            ("FY", "FY - FRUTALES"),
            ("IM", "IM - IMPRODUCTIVOS"),
            ("IV", "IV - INVERNADEROS Y CULTIVOS BAJO PLASTICO"),
            ("MT", "MT - MATORRAL"),
            ("OC", "OC - ASOCIACIÓN OLIVAR-CÍTRICOS"),
            ("OF", "OF - OLIVAR - FRUTAL"),
            ("OV", "OV - OLIVAR"),
            ("PA", "PA - PASTO CON ARBOLADO"),
            ("PR", "PR - PASTO ARBUSTIVO"),
            ("PS", "PS - PASTIZAL"),
            ("TA", "TA - TIERRAS ARABLES"),
            ("TH", "TH - HUERTA"),
            ("VF", "VF - VIÑEDO - FRUTAL"),
            ("VI", "VI - VIÑEDO"),
            ("VO", "VO - VIÑEDO - OLIVAR"),
            ("ZC", "ZC - ZONA CONCENTRADA NO INCLUIDA EN LA ORTOFOTO"),
            ("ZU", "ZU - ZONA URBANA"),
            ("ZV", "ZV - ZONA CENSURADA"),
        ]
    )

    incidencia = fields.Char()
    region = fields.Char()

    gis_link_public = fields.Char(related="parcel_id.gis_link_public")
    gis_link_minimal = fields.Char(related="parcel_id.gis_link_minimal")
    gis_link_technical = fields.Char(related="parcel_id.gis_link_technical")

    sigpac_link = fields.Char(related="sigpac_id.sigpac_link")

    number_of_sigpaclinks = fields.Integer(related="parcel_id.number_of_sigpaclinks")

    irrigation_model_type = fields.Integer(
        compute="_compute_irrigation_model_type",
        store=False,
    )

    def _compute_enclosure_number(self):
        for record in self:
            enclosure_number = 0
            name = record.name or ""
            if len(name) > 3:
                suffix = name[-3:]
                if suffix.isdigit():
                    enclosure_number = int(suffix)
            record.enclosure_number = enclosure_number

    def _compute_parcel_area_ha(self):
        for record in self:
            record.parcel_area_ha = (record.parcel_area or 0.0) / 10000.0

    def _compute_irrigation_model_type(self):
        value = int(self.env.company.irrigation_model_type or 0)
        for record in self:
            record.irrigation_model_type = value

    @api.model
    def read_group(
        self,
        domain,
        fields,
        groupby,
        offset=0,
        limit=None,
        orderby=False,
        lazy=True,
    ):
        reduced_fields = [
            f
            for f in fields
            if f not in {"intersection_percentage", "pend_media_porc", "coef_rega"}
        ]
        return super().read_group(
            domain,
            reduced_fields,
            groupby,
            offset=offset,
            limit=limit,
            orderby=orderby,
            lazy=lazy,
        )

    def action_gis_viewer(self):
        self.ensure_one()
        if not self.gis_link_public:
            return False
        return {
            "type": "ir.actions.act_url",
            "url": self.gis_link_public,
            "target": "new",
        }

    def action_sigpac_viewer(self):
        self.ensure_one()
        if not self.sigpac_link:
            return False
        return {
            "type": "ir.actions.act_url",
            "url": self.sigpac_link,
            "target": "new",
        }

    @api.model
    def action_refresh_sigpac_intersections(self):
        self.sudo().env.cr.execute(
            "REFRESH MATERIALIZED VIEW CONCURRENTLY ter_parcel_sigpaclink"
        )
