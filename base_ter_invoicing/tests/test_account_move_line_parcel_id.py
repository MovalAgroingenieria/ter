# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase


class TestAccountMoveLineParcelId(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.account = cls.env["account.account"].create(
            {
                "name": "Test Expense",
                "code": "XTEST001",
                "account_type": "expense",
                "company_id": cls.env.company.id,
            }
        )
        cls.move = cls.env["account.move"].create(
            {
                "move_type": "entry",
                "date": cls.env["ir.fields.converter"]
                ._str_to_datetime("2025-01-01 00:00:00")
                .date(),
                "journal_id": cls.env["account.journal"]
                .search([("type", "=", "general")], limit=1)
                .id,
            }
        )

        cls.parcel = cls.env["ter.parcel"].create({"name": "P-001"})
        cls.partnerlink = cls.env["ter.parcel.partnerlink"].create(
            {
                "parcel_id": cls.parcel.id,
                "partner_id": cls.partner.id,
            }
        )

    def test_create_sets_parcel_id_from_partnerlink_billable_item(self):
        line = self.env["account.move.line"].create(
            {
                "move_id": self.move.id,
                "name": "Test",
                "account_id": self.account.id,
                "debit": 10.0,
                "credit": 0.0,
                "billable_item_model": "ter.parcel.partnerlink",
                "billable_item_res_id": self.partnerlink.id,
            }
        )
        self.assertEqual(line.parcel_id, self.parcel)

    def test_create_does_not_override_existing_parcel_id(self):
        other_parcel = self.env["ter.parcel"].create({"name": "P-002"})
        line = self.env["account.move.line"].create(
            {
                "move_id": self.move.id,
                "name": "Test",
                "account_id": self.account.id,
                "debit": 10.0,
                "credit": 0.0,
                "parcel_id": other_parcel.id,
                "billable_item_model": "ter.parcel.partnerlink",
                "billable_item_res_id": self.partnerlink.id,
            }
        )
        self.assertEqual(line.parcel_id, other_parcel)
