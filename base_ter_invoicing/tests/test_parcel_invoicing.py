# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.exceptions import ValidationError
from odoo.tests.common import SavepointCase


class TestParcelInvoicing(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.parcel = cls.env["ter.parcel"].create({"name": "P-001"})

        cls.owner_profile = cls.env.ref("base_ter.ter_profile_01", raise_if_not_found=False)
        if not cls.owner_profile:
            cls.owner_profile = cls.env["ter.profile"].create({"name": "Owner"})

        cls.account = cls.env["account.account"].create(
            {
                "name": "Test Income",
                "code": "XTEST100",
                "account_type": "income",
                "company_id": cls.env.company.id,
            }
        )
        cls.journal = cls.env["account.journal"].search([("type", "=", "general")], limit=1)
        if not cls.journal:
            cls.journal = cls.env["account.journal"].create(
                {
                    "name": "Misc",
                    "code": "MISC",
                    "type": "general",
                    "company_id": cls.env.company.id,
                }
            )

    def test_overhead_percentages_must_sum_100(self):
        self.env["ter.parcel.partnerlink"].create(
            {
                "parcel_id": self.parcel.id,
                "partner_id": self.partner.id,
                "profile_id": self.owner_profile.id,
                "percentage": 100.0,
                "percentage_overhead": 60.0,
            }
        )
        self.env["ter.parcel.partnerlink"].create(
            {
                "parcel_id": self.parcel.id,
                "partner_id": self.partner.id,
                "profile_id": self.owner_profile.id,
                "percentage": 0.0,
                "percentage_overhead": 30.0,
            }
        )
        with self.assertRaises(ValidationError):
            self.parcel._check_partnerlink_ids()

    def test_total_invoiced_computed_from_posted_move_lines(self):
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.journal.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Line",
                            "account_id": self.account.id,
                            "debit": 0.0,
                            "credit": 10.0,
                            "quantity": 1.0,
                            "price_unit": 10.0,
                            "parcel_id": self.parcel.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Counterpart",
                            "account_id": self.account.id,
                            "debit": 10.0,
                            "credit": 0.0,
                            "quantity": 1.0,
                            "price_unit": 10.0,
                        },
                    ),
                ],
            }
        )
        move.action_post()
        self.parcel.invalidate_recordset(["total_invoiced"])
        self.assertEqual(self.parcel.total_invoiced, 10.0)
