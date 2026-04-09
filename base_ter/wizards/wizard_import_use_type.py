# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

import logging
import os

from odoo import fields, models, tools
from odoo.tools.translate import TranslationImporter

_logger = logging.getLogger(__name__)

_DATA_XML = "data/ter_use_type_data.xml"
_I18N_FILES = [
    ("data/i18n_use_type/es.po", "es_ES"),
    ("data/i18n_use_type/ca_ES.po", "ca_ES"),
]
# Synthetic module name used in ir_model_data so that use-type records
# are excluded from ``odoo-bin --i18n-export --modules=base_ter``.
_DATA_MODULE = "__base_ter_data__"
_SOURCE_MODULE = "base_ter"


class WizardImportUseType(models.TransientModel):
    _name = "wizard.import.use.type"
    _description = "Import Use Types"

    state = fields.Selection(
        [("confirm", "Confirm"), ("done", "Done")],
        default="confirm",
    )
    result_message = fields.Html(readonly=True)

    def _module_path(self):
        """Return the absolute path to the base_ter module root."""
        return os.path.dirname(os.path.dirname(__file__))

    def _restore_source_module(self):
        """Temporarily restore 'base_ter' as module in ir_model_data.

        On re-runs the entries may already be remapped to the synthetic
        module.  We need the original name so ``convert_xml_import`` can
        resolve existing XML IDs and skip already-loaded records.
        """
        self.env.cr.execute(
            "UPDATE ir_model_data SET module = %s "
            "WHERE module = %s AND model = 'ter.use_type'",
            (_SOURCE_MODULE, _DATA_MODULE),
        )

    def _remap_data_module(self):
        """Move ir_model_data to a synthetic module.

        After this, ``--i18n-export --modules=base_ter`` will no longer
        include ter.use_type name translations.
        """
        self.env.cr.execute(
            "UPDATE ir_model_data SET module = %s "
            "WHERE module = %s AND model = 'ter.use_type'",
            (_DATA_MODULE, _SOURCE_MODULE),
        )

    def _load_base_records(self):
        """Load base use-type records from XML (English source).

        Returns:
            str or None: Missing file path, or None on success.
        """
        abs_path = os.path.join(self._module_path(), _DATA_XML)
        if not os.path.isfile(abs_path):
            return abs_path
        self._restore_source_module()
        tools.convert.convert_xml_import(
            self.env,
            _SOURCE_MODULE,
            abs_path,
            idref={},
            mode="init",
            noupdate=True,
        )
        return None

    def _load_translations(self):
        """Load ES/CA translations from PO files."""
        module_path = self._module_path()
        importer = TranslationImporter(self.env.cr, verbose=True)
        for rel_path, lang in _I18N_FILES:
            abs_path = os.path.join(module_path, rel_path)
            if os.path.isfile(abs_path):
                importer.load_file(abs_path, lang)
                _logger.info("Loaded translations: %s (%s)", rel_path, lang)
        importer.save(overwrite=True)

    def action_import(self):
        """Load use-type records and translations."""
        self.ensure_one()

        count_before = self.env["ter.use_type"].search_count([])

        missing = self._load_base_records()
        if missing:
            self.write(
                {
                    "state": "done",
                    "result_message": self.env._(
                        "<p class='text-danger'>Data file not found:"
                        " <code>%(path)s</code></p>",
                        path=missing,
                    ),
                }
            )
            return self._reopen()

        self._load_translations()
        self._remap_data_module()
        self.env["ter.use_type"].invalidate_model()

        count_after = self.env["ter.use_type"].search_count([])
        created = count_after - count_before

        if created:
            msg = self.env._(
                "<p class='text-success'>"
                "<strong>%(created)d</strong> use types created"
                " (%(total)d total). Translations loaded.</p>",
                created=created,
                total=count_after,
            )
        else:
            msg = self.env._(
                "<p class='text-info'>All <strong>%(total)d</strong>"
                " use types were already loaded."
                " Translations refreshed.</p>",
                total=count_after,
            )

        self.write({"state": "done", "result_message": msg})
        return self._reopen()

    def _reopen(self):
        """Return an action that reopens this wizard (same record)."""
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
