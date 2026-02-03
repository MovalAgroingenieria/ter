import json
from pathlib import Path

from odoo.tests.common import TransactionCase


class TestGeofoliaJsonImport(TransactionCase):
    @classmethod
    def _load_data(cls, relpath):
        data_path = Path(__file__).parent / "data" / relpath
        return json.loads(data_path.read_text(encoding="utf-8"))

    def _create_job(self, relpath, import_type, name=None):
        payload = self._load_data(relpath)
        return self.env["geofolia.import.job"].create(
            {
                "name": name or relpath,
                "import_type": import_type,
                "file_data": self.env["ir.binary"]._base64_encode(
                    json.dumps(payload).encode("utf-8")
                ),
            }
        )

    def test_parse_fields(self):
        job = self._create_job("field_sample.json", "fields", "Fields sample")
        job.action_parse()
        self.assertEqual(job.state, "done")
        self.assertTrue(job.info_json.get("AppName"))
        self.assertEqual(len(job.line_ids), 2)
        self.assertEqual(job.line_ids[0].import_type, "fields")

    def test_parse_products(self):
        job = self._create_job("action_sample.json", "products", "Products sample")
        job.action_parse()
        self.assertEqual(job.state, "done")
        self.assertEqual(len(job.line_ids), 2)
        self.assertEqual(job.line_ids[0].import_type, "products")

    def test_parse_full_with_activities(self):
        job = self._create_job(
            "action_sample_with_activities.json", "full", "Full with Activities"
        )
        job.action_parse()
        self.assertEqual(job.state, "done")
        self.assertEqual(len(job.product_line_ids), 1)
        self.assertEqual(len(job.activity_line_ids), 1)
        self.assertEqual(len(job.activity_line_ids.employee_line_ids), 1)
        emp_line = job.activity_line_ids.employee_line_ids[0]
        self.assertEqual(emp_line.plot_code, "1216")
        self.assertEqual(emp_line.worked_surface, 8000)

    def test_parse_full_sample_minimal(self):
        job = self._create_job("full_sample_minimal.json", "full", "Full minimal")
        job.action_parse()
        self.assertEqual(job.state, "done")
        self.assertEqual(len(job.line_ids), 0)
        self.assertGreaterEqual(len(job.product_line_ids), 0)
        self.assertEqual(len(job.activity_line_ids), 1)
        self.assertEqual(len(job.activity_line_ids.employee_line_ids), 1)
