# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models

CATALOG_PARAM = "base_ter_data_import.show_catalog_import_wizard"


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    show_catalog_import_wizard = fields.Boolean(
        string="Show catalog import wizard",
        compute="_compute_show_catalog_import_wizard",
    )

    @api.depends()
    def _compute_show_catalog_import_wizard(self):
        val = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(CATALOG_PARAM, "False")
        )
        for rec in self:
            rec.show_catalog_import_wizard = val == "True"

    def action_open_import_catalog_csv_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Import Territory Catalogs from CSV"),
            "res_model": "wizard.import.catalog.csv",
            "view_mode": "form",
            "target": "new",
        }
