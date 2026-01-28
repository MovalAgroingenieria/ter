# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=protected-access
# pylint: disable=too-many-arguments
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-locals
# pylint: disable=unused-argument
# pylint: disable=too-many-positional-arguments

import base64
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class TerParcel(models.Model):
    _inherit = "ter.parcel"

    _aerial_img_sigpac_layers = ["pnoa", "sigpac_name", "parcel", "sigpac", "n_arrow"]
    _aerial_img_sigpac_layers_styles = [
        "default",
        "default",
        "default",
        "default",
        "default",
    ]

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

    aerial_img_sigpac = fields.Binary(
        attachment=True,
    )

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

    def _compute_aerial_img_sigpac_shown(self):
        params = self.env["ir.config_parameter"].sudo()

        aerial_image_wmsbase_url = (
            params.get_param("base_ter.aerial_image_wmsbase_url") or False
        )
        aerial_image_wmsbase_layers = (
            params.get_param("base_ter.aerial_image_wmsbase_layers") or False
        )
        aerial_image_wmsvec_url = (
            params.get_param("base_ter.aerial_image_wmsvec_url") or False
        )
        aerial_image_wmsvec_parcel_name = (
            params.get_param("base_ter.aerial_image_wmsvec_parcel_name") or False
        )
        aerial_image_wmsvec_parcel_filter = (
            params.get_param("base_ter.aerial_image_wmsvec_parcel_filter") or False
        )
        aerial_image_height = int(
            params.get_param("base_ter.aerial_image_height", 0) or 0
        )
        aerial_image_zoom = float(
            params.get_param("base_ter.aerial_image_zoom", 0) or 0
        )

        aerial_image_wmssigpac_url = (
            params.get_param("l10n_es_territory_sigpac.wms_sigpac_url") or False
        )
        aerial_image_wmssigpac_layers = (
            params.get_param("l10n_es_territory_sigpac.wms_sigpac_layer") or False
        )

        ogc_data_ok = bool(
            aerial_image_wmsbase_url
            and aerial_image_wmsbase_layers
            and aerial_image_height >= 0
            and aerial_image_zoom >= 0
        )

        if aerial_image_height == 0:
            aerial_image_height = getattr(self, "_aerial_image_size_big", 0) or 0
        if aerial_image_zoom == 0:
            aerial_image_zoom = getattr(self, "_aerial_image_zoom", 0) or 0.0

        ogc_vec_layer = bool(
            aerial_image_wmsvec_url and aerial_image_wmsvec_parcel_name
        )

        for record in self:
            shown = record.aerial_img_sigpac or False

            if not shown and ogc_data_ok and record.mapped_to_polygon:
                shown = record._compute_aerial_sigpac_from_wms(
                    aerial_image_wmsbase_url=aerial_image_wmsbase_url,
                    aerial_image_wmsbase_layers=aerial_image_wmsbase_layers,
                    aerial_image_wmsvec_url=aerial_image_wmsvec_url,
                    aerial_image_wmsvec_parcel_name=aerial_image_wmsvec_parcel_name,
                    aerial_image_wmsvec_parcel_filter=aerial_image_wmsvec_parcel_filter,
                    aerial_image_wmssigpac_url=aerial_image_wmssigpac_url,
                    aerial_image_wmssigpac_layers=aerial_image_wmssigpac_layers,
                    aerial_image_height=aerial_image_height,
                    aerial_image_zoom=aerial_image_zoom,
                    ogc_vec_layer=ogc_vec_layer,
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
                        record.env._(
                            "Error getting aerial image (is the WMS url correct?)"
                        ),
                        source=record._name,
                        message_type="WARNING",
                    )

            record.aerial_img_sigpac_shown = shown or False

    def _compute_aerial_sigpac_from_wms(
        self,
        *,
        aerial_image_wmsbase_url,
        aerial_image_wmsbase_layers,
        aerial_image_wmsvec_url,
        aerial_image_wmsvec_parcel_name,
        aerial_image_wmsvec_parcel_filter,
        aerial_image_wmssigpac_url,
        aerial_image_wmssigpac_layers,
        aerial_image_height,
        aerial_image_zoom,
        ogc_vec_layer,
    ):
        self.ensure_one()
        force_square_shape = getattr(self, "_force_square_shape", False)

        if not ogc_vec_layer:
            return self.get_aerial_image(
                wms=aerial_image_wmsbase_url,
                layers=aerial_image_wmsbase_layers,
                image_height=aerial_image_height,
                format="png",
                zoom=aerial_image_zoom,
                force_square_shape=force_square_shape,
            )

        aerial_image_base_raw = self.get_aerial_image(
            wms=aerial_image_wmsbase_url,
            layers=aerial_image_wmsbase_layers,
            image_height=aerial_image_height,
            format="png",
            zoom=aerial_image_zoom,
            get_raw=True,
            filter=False,
            force_square_shape=force_square_shape,
        )
        aerial_image_vec_raw = self.get_aerial_image(
            wms=aerial_image_wmsvec_url,
            layers=aerial_image_wmsvec_parcel_name,
            image_height=aerial_image_height,
            format="png",
            zoom=aerial_image_zoom,
            get_raw=True,
            filter=aerial_image_wmsvec_parcel_filter,
            force_square_shape=force_square_shape,
        )
        aerial_image_sigpac_raw = self.get_aerial_image(
            wms=aerial_image_wmssigpac_url,
            layers=aerial_image_wmssigpac_layers,
            image_height=aerial_image_height,
            format="png",
            zoom=aerial_image_zoom,
            get_raw=True,
            filter=False,
            styles="recinto",
            force_square_shape=force_square_shape,
        )

        if not (
            aerial_image_base_raw and aerial_image_vec_raw and aerial_image_sigpac_raw
        ):
            return False

        merged = self.env["common.image"].merge_img(
            aerial_image_base_raw, aerial_image_sigpac_raw
        )
        merged = (
            self.env["common.image"].merge_img(merged, aerial_image_vec_raw)
            if merged
            else False
        )
        if not merged:
            return False
        return base64.b64encode(merged.getvalue())

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
        compute="_compute_parcel_area_ha", digits=(32, 4), store=False
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
        compute="_compute_irrigation_model_type", store=False
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
            record.parcel_area_ha = (record.parcel_area or 0.0) / 10000

    def _compute_irrigation_model_type(self):
        irrigation_model_type = self.env["ir.default"].get(
            "ter.infrastructure.configuration", "irrigation_model_type"
        )
        for record in self:
            record.irrigation_model_type = irrigation_model_type

    @api.model
    def read_group(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):
        reduced_fields = [
            f
            for f in fields
            if f not in {"intersection_percentage", "pend_media_porc", "coef_rega"}
        ]
        return super().read_group(
            domain, reduced_fields, groupby, offset, limit, orderby, lazy
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
        return {"type": "ir.actions.act_url", "url": self.sigpac_link, "target": "new"}

    @api.model
    def action_refresh_sigpac_intersections(self):
        self.sudo().env.cr.execute(
            "REFRESH MATERIALIZED VIEW CONCURRENTLY ter_parcel_sigpaclink"
        )
