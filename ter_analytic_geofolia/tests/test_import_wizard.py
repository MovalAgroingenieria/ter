# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
# pylint: disable=protected-access

import base64
import json

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


def _encode(payload):
    return base64.b64encode(json.dumps(payload).encode("utf-8"))


@tagged("post_install", "-at_install")
class TestGeofoliaImportWizard(TransactionCase):
    def test_wizard_creates_job_and_parses(self):
        payload = {
            "Information": {"AppName": "Geofolia"},
            "Fields": [
                {"Id": "f1", "Code": "F1", "Name": "Field 1", "HarvestYear": 2026}
            ],
        }
        wizard = self.env["geofolia.import.wizard"].create(
            {
                "file_name": "test.json",
                "file_data": _encode(payload),
                "import_type": "fields",
            }
        )
        result = wizard.action_import()
        self.assertEqual(result["res_model"], "geofolia.import.job")
        job = self.env["geofolia.import.job"].browse(result["res_id"])
        self.assertEqual(job.state, "done")
        self.assertEqual(len(job.line_ids), 1)

    def test_wizard_autodetect_fields(self):
        payload = {
            "Information": {},
            "Fields": [{"Id": "f1", "Code": "F1", "Name": "F1", "HarvestYear": 2026}],
        }
        wizard = self.env["geofolia.import.wizard"].create(
            {
                "file_data": _encode(payload),
                "import_type": "auto",
            }
        )
        self.assertEqual(wizard._autodetect_type(), "fields")

    def test_wizard_autodetect_full(self):
        payload = {
            "Information": {},
            "Products": [{"SupplyId": "p1", "SupplyName": "P1"}],
            "Employees": [{"Id": "e1", "Name": "E1"}],
        }
        wizard = self.env["geofolia.import.wizard"].create(
            {
                "file_data": _encode(payload),
                "import_type": "auto",
            }
        )
        self.assertEqual(wizard._autodetect_type(), "full")

    def test_wizard_autodetect_products(self):
        payload = {
            "Information": {},
            "Products": [{"SupplyId": "p1", "SupplyName": "P1"}],
        }
        wizard = self.env["geofolia.import.wizard"].create(
            {
                "file_data": _encode(payload),
                "import_type": "auto",
            }
        )
        self.assertEqual(wizard._autodetect_type(), "products")

    def test_wizard_no_file_raises(self):
        wizard = self.env["geofolia.import.wizard"].create(
            {
                "file_data": _encode({"Information": {}, "Fields": []}),
                "import_type": "fields",
            }
        )
        wizard.write({"file_data": False})
        with self.assertRaises(UserError):
            wizard.action_import()

    def test_wizard_import_then_apply_full(self):
        payload = {
            "Information": {"AppName": "G"},
            "Products": [{"SupplyId": "s1", "Code": "S1", "SupplyName": "Supply 1"}],
            "Employees": [],
            "Partners": [{"Id": "p1", "Name": "Partner 1"}],
        }
        wizard = self.env["geofolia.import.wizard"].create(
            {
                "file_name": "full.json",
                "file_data": _encode(payload),
                "import_type": "full",
            }
        )
        result = wizard.action_import()
        job = self.env["geofolia.import.job"].browse(result["res_id"])
        self.assertEqual(job.state, "done")
        self.assertEqual(job.product_line_ids[0].sync_state, "created")
        self.assertEqual(job.partner_line_ids[0].sync_state, "created")
