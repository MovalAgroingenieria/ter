# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models

from ..load_catalog_csv import load_catalogs_from_csv


class WizardImportCatalogCsv(models.TransientModel):
    _name = "wizard.import.catalog.csv"
    _description = "Import Territory Catalogs from Local CSV"

    state = fields.Selection(
        [("draft", "Draft"), ("done", "Done")],
        default="draft",
        required=True,
    )
    message = fields.Html(compute="_compute_message", readonly=True)
    result_message = fields.Html(readonly=True)

    @api.depends()
    def _compute_message(self):
        for wiz in self:
            wiz.message = _(
                "<p>Territory catalogs (profiles, use types, attributes and "
                "values) are imported from <strong>local CSV files</strong> "
                "included in the <em>Base Territory</em> module.</p>"
                "<p>Files must be in the module's <code>catalogos_csv</code> "
                "folder, with UTF-8 encoding and semicolon (;) as separator.</p>"
                "<p>Click <strong>Import now</strong> to load or update data "
                "from those files.</p>"
            )

    def action_import(self):
        self.ensure_one()
        env = self.env
        try:
            counts = load_catalogs_from_csv(env)
        except Exception as exc:
            self.result_message = _(
                "<p class='text-danger'><strong>Import error:</strong></p>"
                "<pre>%s</pre>"
            ) % (exc,)
            self.state = "done"
            return self._reopen_wizard()

        env["ir.config_parameter"].sudo().set_param(
            "base_ter.show_catalog_import_wizard",
            "False",
        )
        self.result_message = (
            _(
                "<p class='text-success'><strong>Import completed.</strong></p>"
                "<ul>"
                "<li>Profiles: %(profiles)s</li>"
                "<li>Use types: %(use_types)s</li>"
                "<li>Attributes: %(attributes)s</li>"
                "<li>Attribute values: %(values)s</li>"
                "</ul>"
            )
            % counts
        )
        self.state = "done"
        return self._reopen_wizard()

    def _reopen_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
