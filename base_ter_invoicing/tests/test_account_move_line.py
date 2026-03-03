# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
# pylint: disable=invalid-name

from datetime import date

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAccountMoveLineTerInvoicing(TransactionCase):
    """Tests for account.move.line parcel_id sync and total_invoiced invalidation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create({"name": "Test Holder", "partner_code": 1})

        # Geo hierarchy
        region = (
            cls.env["res.admregion"].create({"name": "R1"})
            if "res.admregion" in cls.env
            else None
        )
        province_vals = {"name": "P1"}
        if region:
            province_vals["region_id"] = region.id
        province = cls.env["res.province"].create(province_vals)
        cls.municipality = cls.env["res.municipality"].create(
            {"name": "M1", "province_id": province.id}
        )

        cls.profile = cls.env.ref("base_ter.ter_profile_01")

        # Parcels and partnerlinks
        cls.parcel_a = cls.env["ter.parcel"].create(
            {
                "alphanum_code": "PAR-A",
                "municipality_id": cls.municipality.id,
                "area_official": 1.0,
            }
        )
        cls.partnerlink_a = cls.env["ter.parcel.partnerlink"].create(
            {
                "parcel_id": cls.parcel_a.id,
                "partner_id": cls.partner.id,
                "profile_id": cls.profile.id,
                "is_main": True,
                "percentage": 100,
                "percentage_overhead": 100,
            }
        )

        cls.parcel_b = cls.env["ter.parcel"].create(
            {
                "alphanum_code": "PAR-B",
                "municipality_id": cls.municipality.id,
                "area_official": 2.0,
            }
        )
        cls.partnerlink_b = cls.env["ter.parcel.partnerlink"].create(
            {
                "parcel_id": cls.parcel_b.id,
                "partner_id": cls.partner.id,
                "profile_id": cls.profile.id,
                "is_main": True,
                "percentage": 100,
                "percentage_overhead": 100,
            }
        )

        # Accounting
        cls.acc_income = cls.env["account.account"].create(
            {
                "name": "Test Income",
                "code": "TINCOME",
                "account_type": "income",
                "company_ids": [(6, 0, [cls.company.id])],
            }
        )
        cls.acc_recv = cls.env["account.account"].create(
            {
                "name": "Test Receivable",
                "code": "TRECV",
                "account_type": "asset_receivable",
                "company_ids": [(6, 0, [cls.company.id])],
            }
        )
        cls.sale_journal = cls.env["account.journal"].search(
            [("company_id", "=", cls.company.id), ("type", "=", "sale")], limit=1
        )
        if not cls.sale_journal:
            cls.sale_journal = cls.env["account.journal"].create(
                {
                    "name": "Test Sale",
                    "code": "TSAL",
                    "type": "sale",
                    "company_id": cls.company.id,
                    "default_account_id": cls.acc_income.id,
                }
            )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Service",
                "type": "service",
                "list_price": 50.0,
                "property_account_income_id": cls.acc_income.id,
            }
        )

    def _create_invoice_with_partnerlink_line(self, partnerlink, amount=100.0):
        """Create draft out_invoice with one line linked to the given partnerlink."""
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_date": date.today(),
                "journal_id": self.sale_journal.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line",
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": amount,
                            "account_id": self.acc_income.id,
                            "billable_item_model": "ter.parcel.partnerlink",
                            "billable_item_res_id": partnerlink.id,
                        },
                    )
                ],
            }
        )
        return move

    def test_parcel_id_set_on_create_when_billable_item_is_partnerlink(self):
        """parcel_id is set from partnerlink when creating a line with billable_item."""
        move = self._create_invoice_with_partnerlink_line(self.partnerlink_a, amount=50.0)
        line = move.invoice_line_ids[0]
        self.assertEqual(
            line.parcel_id,
            self.parcel_a,
            "parcel_id should be set from ter.parcel.partnerlink on create",
        )

    def test_parcel_id_synced_on_write_when_billable_item_changes(self):
        """parcel_id is updated when billable_item_model / billable_item_res_id change."""
        move = self._create_invoice_with_partnerlink_line(self.partnerlink_a)
        line = move.invoice_line_ids[0]
        self.assertEqual(line.parcel_id, self.parcel_a)

        line.write(
            {
                "billable_item_model": "ter.parcel.partnerlink",
                "billable_item_res_id": self.partnerlink_b.id,
            }
        )
        self.assertEqual(
            line.parcel_id,
            self.parcel_b,
            "parcel_id should sync to parcel_b after write",
        )

    def test_total_invoiced_invalidated_after_create_and_post(self):
        """total_invoiced is invalidated after create and recomputes correctly when posted."""
        self.parcel_a.invalidate_recordset(["total_invoiced"])
        self.assertEqual(self.parcel_a.total_invoiced, 0.0)

        move = self._create_invoice_with_partnerlink_line(self.partnerlink_a, amount=75.0)
        move.action_post()
        self.parcel_a.invalidate_recordset(["total_invoiced"])
        self.assertEqual(
            self.parcel_a.total_invoiced,
            75.0,
            "total_invoiced should include posted line amount",
        )

    def test_total_invoiced_invalidated_after_unlink(self):
        """total_invoiced is invalidated after unlink and recomputes to 0."""
        move = self._create_invoice_with_partnerlink_line(self.partnerlink_a, amount=30.0)
        move.action_post()
        self.parcel_a.invalidate_recordset(["total_invoiced"])
        self.assertEqual(self.parcel_a.total_invoiced, 30.0)

        move.invoice_line_ids.unlink()
        self.parcel_a.invalidate_recordset(["total_invoiced"])
        self.assertEqual(
            self.parcel_a.total_invoiced,
            0.0,
            "total_invoiced should be 0 after line unlink",
        )

    def test_billable_item_non_existent_partnerlink(self):
        """Line with non-existent partnerlink res_id does not set parcel_id and does not crash."""
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_date": date.today(),
                "journal_id": self.sale_journal.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Orphan line",
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": 10.0,
                            "account_id": self.acc_income.id,
                            "billable_item_model": "ter.parcel.partnerlink",
                            "billable_item_res_id": 999999999,
                        },
                    )
                ],
            }
        )
        line = move.invoice_line_ids[0]
        self.assertFalse(
            line.parcel_id,
            "parcel_id should be False when billable_item points to non-existent id",
        )

    def test_write_parcel_id_via_internal_write_no_double_invalidation(self):
        """Changing billable_item uses _write() for parcel_id; invalidation runs once."""
        move = self._create_invoice_with_partnerlink_line(self.partnerlink_a, amount=20.0)
        line = move.invoice_line_ids[0]
        self.assertEqual(line.parcel_id, self.parcel_a)

        line.write(
            {
                "billable_item_model": "ter.parcel.partnerlink",
                "billable_item_res_id": self.partnerlink_b.id,
            }
        )
        self.assertEqual(line.parcel_id, self.parcel_b)
        move.action_post()
        self.parcel_a.invalidate_recordset(["total_invoiced"])
        self.parcel_b.invalidate_recordset(["total_invoiced"])
        self.assertEqual(self.parcel_a.total_invoiced, 0.0)
        self.assertEqual(self.parcel_b.total_invoiced, 20.0)
