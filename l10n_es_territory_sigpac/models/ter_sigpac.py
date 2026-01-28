# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments
# pylint: disable=duplicate-code

import logging

from jinja2 import Template
from jinja2.exceptions import TemplateError
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class TerSigpac(models.Model):
    _name = "ter.sigpac"
    _auto = False
    _description = "SIGPAC Enclosure"
    _order = "name"

    name = fields.Char()

    dn_oid = fields.Integer()

    provincia = fields.Integer()

    municipio = fields.Integer()

    agregado = fields.Integer()

    zona = fields.Integer()

    poligono = fields.Integer()

    parcela = fields.Integer()

    recinto = fields.Integer()

    dn_surface = fields.Float(digits=(32, 2))

    dn_surface_ha = fields.Float(digits=(32, 4))

    dn_perim = fields.Float(digits=(32, 2))

    pend_media = fields.Integer()

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

    sigpac_link = fields.Char(
        compute="_compute_sigpac_link",
        store=False,
    )

    sigpaclink_ids = fields.One2many(
        comodel_name="ter.parcel.sigpaclink",
        inverse_name="sigpac_id",
    )

    number_of_sigpaclinks = fields.Integer(
        compute="_compute_number_of_sigpaclinks",
        store=False,
    )

    def _compute_sigpac_link(self):
        params = self.env["ir.config_parameter"].sudo()
        template_value = (
            params.get_param("l10n_es_territory_sigpac.sigpac_viewer_url") or ""
        )

        for record in self:
            if not template_value:
                record.sigpac_link = ""
                continue

            try:
                record.sigpac_link = Template(template_value).render({"object": record})
            except TemplateError as err:
                _logger.warning(
                    "Invalid SIGPAC viewer URL template. Using raw value. Error: %s",
                    err,
                )
                record.sigpac_link = template_value

    def _compute_number_of_sigpaclinks(self):
        for record in self:
            record.number_of_sigpaclinks = len(record.sigpaclink_ids)

    # pylint: disable=redefined-outer-name
    @api.model
    def read_group(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):
        reduced_fields = [
            f for f in fields if f not in {"dn_oid", "pend_media_porc", "coef_rega"}
        ]
        return super().read_group(
            domain, reduced_fields, groupby, offset, limit, orderby, lazy
        )

    def action_sigpac_viewer(self):
        self.ensure_one()
        if not self.sigpac_link:
            return False
        return {"type": "ir.actions.act_url", "url": self.sigpac_link, "target": "new"}

    def action_get_parcels(self):
        self.ensure_one()
        if not self.sigpaclink_ids:
            return False

        list_view = self.env.ref(
            "l10n_es_territory_sigpac.ter_parcel_sigpaclink_only_parcels_view_tree"
        )
        search_view = self.env.ref(
            "l10n_es_territory_sigpac.ter_parcel_sigpaclink_only_parcels_view_search"
        )

        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Parcels of the enclosure"),
            "res_model": "ter.parcel.sigpaclink",
            "view_mode": "list",
            "views": [(list_view.id, "list")],
            "search_view_id": (search_view.id, search_view.name),
            "target": "current",
            "domain": [("id", "in", self.sigpaclink_ids.ids)],
        }
