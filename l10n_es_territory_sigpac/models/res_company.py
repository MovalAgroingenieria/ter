# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

DEF_INT_PERC = 5.0


class ResCompany(models.Model):
    _inherit = "res.company"

    sigpac_path = fields.Char(
        help="Path of the official shapefiles of SIGPAC, in the server.",
    )
    sigpac_names = fields.Char(
        help="Names of the official shapefiles of SIGPAC (comma-separated).",
    )
    sigpac_minimum_intersection_percentage = fields.Float(
        digits=(32, 4),
        default=DEF_INT_PERC,
        help="Minimum intersection percentage "
        "allowed for parcels and SIGPAC enclosures.",
    )
    wms_sigpac_url = fields.Char(
        default="https://wms.mapa.gob.es/sigpac/wms",
    )
    wms_sigpac_layer = fields.Char(
        default="recinto",
    )
    sigpac_viewer_url = fields.Char(
        help="URL template for SIGPAC viewer (Jinja2).",
    )
    python_venv_url = fields.Char(
        default="/home/odoo18/venv3.10/bin/python",
        help="Python interpreter path for the SIGPAC import helper.",
    )
    irrigation_model_type = fields.Integer()

    url_gis_viewer_epsg_code = fields.Integer("URL Gist viewer", default=25830)
