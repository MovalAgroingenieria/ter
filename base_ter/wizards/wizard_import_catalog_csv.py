# Copyright 2026 Moval Agroingeniería S.L.
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
                "<p>Los catálogos del territorio (perfiles, tipos de uso, "
                "atributos y valores) se importan desde <strong>ficheros CSV "
                "locales</strong> incluidos en el módulo <em>Base Territory</em>.</p>"
                "<p>Los ficheros deben estar en la carpeta <code>catalogos_csv</code> "
                "del módulo, con codificación UTF-8 y separador punto y coma (;).</p>"
                "<p>Pulse <strong>Importar ahora</strong> para cargar o actualizar "
                "los datos desde esos ficheros.</p>"
            )

    def action_import(self):
        self.ensure_one()
        env = self.env
        try:
            counts = load_catalogs_from_csv(env)
        except Exception as exc:
            self.result_message = _(
                "<p class='text-danger'><strong>Error al importar:</strong></p><pre>%s</pre>"
            ) % (exc,)
            self.state = "done"
            return

        # Clear "show wizard" flag so banner is hidden after user runs import
        env["ir.config_parameter"].sudo().set_param(
            "base_ter.show_catalog_import_wizard",
            "False",
        )

        self.result_message = (
            _(
                "<p class='text-success'><strong>Importación completada.</strong></p>"
                "<ul>"
                "<li>Perfiles: %(profiles)s</li>"
                "<li>Tipos de uso: %(use_types)s</li>"
                "<li>Atributos: %(attributes)s</li>"
                "<li>Valores de atributos: %(values)s</li>"
                "</ul>"
            )
            % counts
        )
        self.state = "done"
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
