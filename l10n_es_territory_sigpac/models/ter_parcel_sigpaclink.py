# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models

from ..hooks import ensure_l10n_es_territory_sigpac_schema


class TerParcelSigpaclink(models.Model):
    _name = "ter.parcel.sigpaclink"
    _auto = False
    _table = "ter_parcel_sigpaclink"
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
            ("AG", "AG - Water streams and surfaces"),
            ("CA", "CA - Roads"),
            ("CF", "CF - Citrus-stone fruit association"),
            ("CI", "CI - Citrus"),
            ("CS", "CS - Citrus-nut tree association"),
            ("CV", "CV - Citrus-vineyard association"),
            ("ED", "ED - Buildings"),
            ("EP", "EP - Landscape element"),
            ("FF", "FF - Stone fruit-nut tree association"),
            ("FL", "FL - Nut trees and olive grove"),
            ("FO", "FO - Forest"),
            ("FS", "FS - Nut trees"),
            ("FV", "FV - Nut trees and vineyard"),
            ("FY", "FY - Stone fruit"),
            ("IM", "IM - Unproductive land"),
            ("IV", "IV - Greenhouses and plastic-covered crops"),
            ("MT", "MT - Shrubland"),
            ("OC", "OC - Olive-citrus association"),
            ("OF", "OF - Olive grove - stone fruit"),
            ("OV", "OV - Olive grove"),
            ("PA", "PA - Pasture with trees"),
            ("PR", "PR - Shrub pasture"),
            ("PS", "PS - Grassland"),
            ("TA", "TA - Arable land"),
            ("TH", "TH - Vegetable garden"),
            ("VF", "VF - Vineyard - stone fruit"),
            ("VI", "VI - Vineyard"),
            ("VO", "VO - Vineyard - olive grove"),
            ("ZC", "ZC - Concentrated area not included in orthophoto"),
            ("ZU", "ZU - Urban area"),
            ("ZV", "ZV - Censored area"),
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

    def init(self):
        ensure_l10n_es_territory_sigpac_schema(self.env)

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
    def read_group(  # pylint: disable=too-many-arguments,too-many-positional-arguments,redefined-outer-name
        self,
        domain,
        fields,
        groupby,
        offset=0,
        limit=None,
        orderby=False,
        lazy=True,
    ):
        fields_list = fields
        reduced_fields = [
            field_name
            for field_name in fields_list
            if field_name
            not in {"intersection_percentage", "pend_media_porc", "coef_rega"}
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
