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
class TestGeofoliaImportJob(
    TransactionCase
):  # pylint: disable=too-many-public-methods,W0212
    def _minimal_payload_fields(self):
        return {
            "Information": {"AppName": "Geofolia", "CountryCode": "ES"},
            "Fields": [
                {
                    "Id": "field-uuid-1",
                    "Code": "F001",
                    "Name": "Test Field",
                    "HarvestYear": 2026,
                    "Area": 1.5,
                    "City": "TestCity",
                }
            ],
        }

    def _minimal_payload_products(self):
        return {
            "Information": {"AppName": "Geofolia"},
            "Products": [
                {
                    "SupplyId": "supply-1",
                    "Code": "P001",
                    "SupplyName": "Test Supply",
                }
            ],
        }

    def _minimal_payload_full(self):
        return {
            "Information": {"AppName": "Geofolia"},
            "Products": [
                {"SupplyId": "prod-1", "Code": "P1", "SupplyName": "Product One"}
            ],
            "Employees": [
                {
                    "Id": "emp-1",
                    "FirstName": "John",
                    "Name": "Doe",
                    "FarmIdentificationCode": "F1",
                }
            ],
            "Partners": [
                {
                    "Id": "part-1",
                    "Name": "Partner One",
                    "FarmIdentificationCode": "F1",
                }
            ],
            "HarvestedProducts": [
                {"HarvestId": "h1", "Code": "H1", "Name": "Harvest One"}
            ],
            "Equipments": [
                {
                    "EquipmentId": "equip-1",
                    "Code": "E1",
                    "Name": "Tractor",
                }
            ],
            "Activities": [
                {
                    "ActionId": "act-1",
                    "OperationName": "Sowing",
                    "StartingDate": "2026-02-01",
                    "EndingDate": "2026-02-01",
                    "ActionEmployees": [
                        {
                            "EmployeeActionId": "act-1",
                            "EmployeeId": "emp-1",
                            "EmployeeName": "John Doe",
                            "EmployeeTime": 120,
                        }
                    ],
                }
            ],
        }

    def test_create_job(self):
        job_obj = self.env["geofolia.import.job"]
        job = job_obj.create(
            {
                "name": "Test Job",
                "import_type": "full",
                "file_data": _encode({"Information": {}, "Fields": []}),
            }
        )
        self.assertEqual(job.state, "draft")
        self.assertEqual(job.apply_state, "draft")

    def test_load_json_payload(self):
        payload = {"Information": {}, "Fields": []}
        job = self.env["geofolia.import.job"].create(
            {
                "name": "J",
                "import_type": "fields",
                "file_data": _encode(payload),
            }
        )
        self.assertEqual(job._load_json_payload(), payload)

    def test_load_json_payload_invalid_raises(self):
        job = self.env["geofolia.import.job"].create(
            {
                "name": "J",
                "import_type": "fields",
                "file_data": base64.b64encode(b"not json"),
            }
        )
        with self.assertRaises(UserError):
            job._load_json_payload()

    def test_parse_payload_missing_information_raises(self):
        job = self.env["geofolia.import.job"].create(
            {
                "name": "J",
                "import_type": "fields",
                "file_data": _encode({"Fields": []}),
            }
        )
        payload = {"Fields": []}
        with self.assertRaises(UserError):
            job._parse_payload(payload)

    def test_parse_fields_creates_lines(self):
        payload = self._minimal_payload_fields()
        job = self.env["geofolia.import.job"].create(
            {
                "name": "Fields Job",
                "import_type": "fields",
                "file_data": _encode(payload),
            }
        )
        job._parse_payload(payload)
        self.assertEqual(len(job.line_ids), 1)
        line = job.line_ids[0]
        self.assertEqual(line.external_uuid, "field-uuid-1")
        self.assertEqual(line.code, "F001")
        self.assertEqual(line.name, "Test Field")
        self.assertEqual(line.harvest_year, 2026)
        self.assertEqual(line.sync_state, "pending")

    def test_parse_products_creates_lines(self):
        payload = self._minimal_payload_products()
        job = self.env["geofolia.import.job"].create(
            {
                "name": "Products Job",
                "import_type": "products",
                "file_data": _encode(payload),
            }
        )
        job._parse_payload(payload)
        self.assertEqual(len(job.line_ids), 1)
        line = job.line_ids[0]
        self.assertEqual(line.supply_id, "supply-1")
        self.assertEqual(line.code, "P001")

    def test_parse_full_creates_all_line_types(self):
        payload = self._minimal_payload_full()
        job = self.env["geofolia.import.job"].create(
            {
                "name": "Full Job",
                "import_type": "full",
                "file_data": _encode(payload),
            }
        )
        job._parse_payload(payload)
        self.assertEqual(len(job.product_line_ids), 1)
        self.assertEqual(len(job.employee_line_ids), 1)
        self.assertEqual(len(job.partner_line_ids), 1)
        self.assertEqual(len(job.harvested_product_line_ids), 1)
        self.assertEqual(len(job.equipment_line_ids), 1)
        self.assertEqual(len(job.activity_line_ids), 1)
        self.assertEqual(len(job.activity_employee_line_ids), 1)

    def test_action_parse_sets_state(self):
        payload = self._minimal_payload_full()
        job = self.env["geofolia.import.job"].create(
            {
                "name": "Full Job",
                "import_type": "full",
                "file_data": _encode(payload),
            }
        )
        job.action_parse()
        self.assertEqual(job.state, "done")
        self.assertEqual(job.apply_state, "ready")
        self.assertFalse(job.error)

    def test_apply_product_line_creates_product(self):
        payload = self._minimal_payload_full()
        job = self.env["geofolia.import.job"].create(
            {
                "name": "Full",
                "import_type": "full",
                "file_data": _encode(payload),
            }
        )
        job.action_parse()
        job._apply_product_line(job.product_line_ids[0])
        line = job.product_line_ids[0]
        self.assertEqual(line.sync_state, "created")
        self.assertTrue(line.product_id)
        self.assertEqual(line.product_id.geofolia_external_id, "prod-1")
        self.assertEqual(line.product_id.default_code, "P1")

    def test_apply_product_line_idempotent(self):
        payload = self._minimal_payload_full()
        job = self.env["geofolia.import.job"].create(
            {
                "name": "Full",
                "import_type": "full",
                "file_data": _encode(payload),
            }
        )
        job.action_parse()
        job._apply_product_line(job.product_line_ids[0])
        job._apply_product_line(job.product_line_ids[0])
        self.assertEqual(job.product_line_ids[0].sync_state, "no_action")

    def test_apply_partner_line_creates_partner(self):
        payload = self._minimal_payload_full()
        job = self.env["geofolia.import.job"].create(
            {
                "name": "Full",
                "import_type": "full",
                "file_data": _encode(payload),
            }
        )
        job.action_parse()
        job._apply_partner_line(job.partner_line_ids[0])
        line = job.partner_line_ids[0]
        self.assertEqual(line.sync_state, "created")
        self.assertTrue(line.partner_id)
        self.assertEqual(line.partner_id.geofolia_external_id, "part-1")

    def test_apply_employee_line_creates_person(self):
        payload = self._minimal_payload_full()
        job = self.env["geofolia.import.job"].create(
            {
                "name": "Full",
                "import_type": "full",
                "file_data": _encode(payload),
            }
        )
        job.action_parse()
        job._apply_employee_line(job.employee_line_ids[0])
        line = job.employee_line_ids[0]
        self.assertEqual(line.sync_state, "created")
        self.assertTrue(line.person_id)
        self.assertEqual(line.person_id.geofolia_external_id, "emp-1")

    def test_apply_harvested_product_line_creates_product(self):
        payload = self._minimal_payload_full()
        job = self.env["geofolia.import.job"].create(
            {
                "name": "Full",
                "import_type": "full",
                "file_data": _encode(payload),
            }
        )
        job.action_parse()
        job._apply_product_like(job.harvested_product_line_ids[0], "harvested")
        line = job.harvested_product_line_ids[0]
        self.assertEqual(line.sync_state, "created")
        self.assertTrue(line.product_id)
        self.assertEqual(line.product_id.geofolia_external_id, "h1")

    def test_apply_equipment_line_creates_fsm_equipment(self):
        payload = self._minimal_payload_full()
        job = self.env["geofolia.import.job"].create(
            {
                "name": "Full",
                "import_type": "full",
                "file_data": _encode(payload),
            }
        )
        job.action_parse()
        job._apply_equipment_line(job.equipment_line_ids[0])
        line = job.equipment_line_ids[0]
        self.assertEqual(line.sync_state, "created")
        self.assertTrue(line.equipment_id)
        self.assertEqual(line.equipment_id.geofolia_external_id, "equip-1")

    def test_apply_activity_employee_line_creates_analytic_line(self):
        payload = self._minimal_payload_full()
        job = self.env["geofolia.import.job"].create(
            {
                "name": "Full",
                "import_type": "full",
                "file_data": _encode(payload),
            }
        )
        job.action_parse()
        job._apply_employee_line(job.employee_line_ids[0])
        job._apply_activity_employee_line(job.activity_employee_line_ids[0])
        line = job.activity_employee_line_ids[0]
        self.assertEqual(line.sync_state, "created")
        self.assertTrue(line.analytic_line_id)
        self.assertEqual(line.analytic_line_id.unit_amount, 2.0)
        self.assertEqual(line.person_id, job.employee_line_ids[0].person_id)

    def test_apply_activity_employee_skipped_when_employee_missing(self):
        payload = {
            "Information": {"AppName": "G"},
            "Employees": [],
            "Activities": [
                {
                    "ActionId": "a1",
                    "OperationName": "Work",
                    "ActionEmployees": [
                        {
                            "EmployeeActionId": "a1",
                            "EmployeeId": "nonexistent",
                            "EmployeeName": "Nobody",
                            "EmployeeTime": 60,
                        }
                    ],
                }
            ],
        }
        job = self.env["geofolia.import.job"].create(
            {
                "name": "Job",
                "import_type": "full",
                "file_data": _encode(payload),
            }
        )
        job.action_parse()
        job._apply_activity_employee_line(job.activity_employee_line_ids[0])
        self.assertEqual(job.activity_employee_line_ids[0].sync_state, "skipped")

    def test_apply_full_export(self):
        payload = self._minimal_payload_full()
        job = self.env["geofolia.import.job"].create(
            {
                "name": "Full",
                "import_type": "full",
                "file_data": _encode(payload),
            }
        )
        job.action_parse()
        job.action_apply()
        self.assertEqual(job.product_line_ids[0].sync_state, "created")
        self.assertEqual(job.partner_line_ids[0].sync_state, "created")
        self.assertEqual(job.employee_line_ids[0].sync_state, "created")
        self.assertEqual(job.harvested_product_line_ids[0].sync_state, "created")
        self.assertEqual(job.equipment_line_ids[0].sync_state, "created")
        self.assertEqual(job.activity_employee_line_ids[0].sync_state, "created")
        self.assertIn(job.apply_state, ("done", "partial"))

    def test_action_reprocess_reapplies_pending(self):
        payload = self._minimal_payload_full()
        job = self.env["geofolia.import.job"].create(
            {
                "name": "Full",
                "import_type": "full",
                "file_data": _encode(payload),
            }
        )
        job.action_parse()
        job.action_apply()
        job.action_reprocess()
        self.assertIn(job.apply_state, ("done", "partial"))

    def test_product_line_missing_id_skipped(self):
        payload = {
            "Information": {"AppName": "G"},
            "Products": [{"Code": "X", "SupplyName": "Y"}],
        }
        job = self.env["geofolia.import.job"].create(
            {
                "name": "J",
                "import_type": "full",
                "file_data": _encode(payload),
            }
        )
        job.action_parse()
        job._apply_product_line(job.product_line_ids[0])
        self.assertEqual(job.product_line_ids[0].sync_state, "skipped")

    def test_to_date_and_to_datetime(self):
        job = self.env["geofolia.import.job"].create(
            {
                "name": "J",
                "import_type": "full",
                "file_data": _encode({"Information": {}, "Fields": []}),
            }
        )
        self.assertFalse(job._to_date(None))
        self.assertEqual(
            str(job._to_date("2026-02-01")),
            "2026-02-01",
        )
        self.assertFalse(job._to_datetime(None))
        dt = job._to_datetime("2026-02-01T10:00:00Z")
        self.assertIsNotNone(dt)

    def test_parse_fields_then_apply_fields_needs_parcel_or_geometry(self):
        payload = self._minimal_payload_fields()
        job = self.env["geofolia.import.job"].create(
            {
                "name": "Fields Job",
                "import_type": "fields",
                "file_data": _encode(payload),
            }
        )
        job.action_parse()
        self.assertEqual(job.state, "done")
        job.action_apply()
        line = job.line_ids[0]
        self.assertIn(
            line.sync_state,
            ("error", "skipped"),
            "Without parcel/date range or geometry, apply should not create location",
        )
