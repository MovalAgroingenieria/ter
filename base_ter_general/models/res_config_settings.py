# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    jinja2_template = fields.Char(
        string="Jinja2 Template",
        config_parameter="base_ter_general.jinja2_template",
    )
