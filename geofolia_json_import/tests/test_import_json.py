import json
from pathlib import Path

from odoo.tests.common import TransactionCase


class TestGeofoliaJsonImport(TransactionCase):
    @classmethod
    def _load_data(cls, relpath):
        data_path = Path(__file__).parent / "data" / relpath
        return json.loads(data_path.read_text(encoding="utf-8"))

    def test_parse_fields(self):
        payload = self._load_data("field_sample.json")
        job = self.env["geofolia.import.job"].create(
            {
                "name": "Fields sample",
                "import_type": "fields",
                "file_data": self.env["ir.binary"]._base64_encode(
                    json.dumps(payload).encode("utf-8")
                ),
            }
        )
        job.action_parse()
        self.assertEqual(job.state, "done")
        self.assertTrue(job.info_json.get("AppName"))
        self.assertEqual(len(job.line_ids), 2)
        self.assertEqual(job.line_ids[0].import_type, "fields")

    def test_parse_products(self):
        payload = self._load_data("action_sample.json")
        job = self.env["geofolia.import.job"].create(
            {
                "name": "Products sample",
                "import_type": "products",
                "file_data": self.env["ir.binary"]._base64_encode(
                    json.dumps(payload).encode("utf-8")
                ),
            }
        )
        job.action_parse()
        self.assertEqual(job.state, "done")
        self.assertEqual(len(job.line_ids), 2)
        self.assertEqual(job.line_ids[0].import_type, "products")
