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

    @api.depends("aerial_img_sigpac")
    def _compute_aerial_img_sigpac_shown(self):
        """Mirror the stored SIGPAC overlay image, never fetch it.

        Fetching is an explicit, potentially slow, network operation. It
        must only happen via ``reset_aerial_img_sigpac`` (button/action),
        never as a side effect of reading/opening a record.
        """
        for record in self:
            record.aerial_img_sigpac_shown = record.aerial_img_sigpac or False

    def _fetch_and_store_aerial_img_sigpac(self):
        """Fetch the SIGPAC overlay aerial image from the WMS and store it.

        This performs the actual network call(s) and must only be
        triggered by an explicit action (``reset_aerial_img_sigpac``).
        """
        self.ensure_one()
        params = self.env["ir.config_parameter"].sudo()

        wmsbase_url = params.get_param("base_ter.aerial_image_wmsbase_url") or False
        wmsbase_layers = (
            params.get_param("base_ter.aerial_image_wmsbase_layers") or False
        )
        wmsvec_url = params.get_param("base_ter.aerial_image_wmsvec_url") or False
        wmsvec_parcel_layer = (
            params.get_param("base_ter.aerial_image_wmsvec_parcel_name") or False
        )
        wmsvec_filter = bool(
            params.get_param("base_ter.aerial_image_wmsvec_parcel_filter")
        )
        image_height = int(params.get_param("base_ter.aerial_image_height", 0) or 0)
        image_zoom = float(params.get_param("base_ter.aerial_image_zoom", 0) or 0)

        wmssigpac_url = (
            params.get_param("l10n_es_territory_sigpac.wms_sigpac_url") or False
        )
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

        if not (ogc_ok and self.mapped_to_polygon):
            return False

        shown = (
            self._get_aerial_img_sigpac_from_wms(  # pylint: disable=protected-access
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
        )

        if shown:
            self.aerial_img_sigpac = shown
            self.env["common.log"].register_in_log(
                self.env._("Aerial image OK. Parcel: %(name)s", name=self.name or ""),
                source="ter.parcel",
                message_type="INFO",
            )
            return True

        self.env["common.log"].register_in_log(
            self.env._("Error getting aerial image (is the WMS url correct?)"),
            source="ter.parcel",
            message_type="WARNING",
        )
        return False

    def reset_aerial_img_sigpac(self):
        """Explicitly (re)generate the SIGPAC overlay aerial image."""
        for record in self:
            record.aerial_img_sigpac = False
            record._fetch_and_store_aerial_img_sigpac()  # pylint: disable=protected-access

    def _get_aerial_img_sigpac_from_wms(  # pylint: disable=too-many-arguments,too-many-locals
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
            merged_bytes = (
                base_raw.getvalue() if hasattr(base_raw, "getvalue") else False
            )

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
                merged_bytes = (
                    self.env["common.image"].merge_img(
                        merged_bytes, vec_raw, return_base64=False
                    )
                    or merged_bytes
                )

        if not merged_bytes:
            return False

        return base64.b64encode(merged_bytes)

    def _get_aerial_image_sigpac_layers(
        self, parcel
    ):  # pylint: disable=unused-argument
        return self._aerial_img_sigpac_layers

    def _get_aerial_image_sigpac_layers_styles(
        self, parcel
    ):  # pylint: disable=unused-argument
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
        parcels.reset_aerial_img_sigpac()
