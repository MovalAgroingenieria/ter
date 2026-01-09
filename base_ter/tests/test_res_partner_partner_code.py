from odoo import exceptions
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestResPartnerPartnerCode(TransactionCase):
    def test_partner_code_asstr_padding(self):
        partner = self.env["res.partner"].create(
            {"name": "P1", "partner_code": 12}
        )
        self.assertEqual(partner.partner_code_asstr, "000012")

    def test_is_holder(self):
        p0 = self.env["res.partner"].create({"name": "P0", "partner_code": 0})
        p1 = self.env["res.partner"].create({"name": "P1", "partner_code": 1})
        self.assertFalse(p0.is_holder)
        self.assertTrue(p1.is_holder)

    def test_child_contact_forces_partner_code_zero(self):
        parent = self.env["res.partner"].create({"name": "Parent", "partner_code": 10})
        child = self.env["res.partner"].create(
            {"name": "Child", "parent_id": parent.id, "partner_code": 99}
        )
        self.assertEqual(child.partner_code, 0)

    def test_partner_code_unique_when_positive(self):
        self.env["res.partner"].create({"name": "P1", "partner_code": 25})
        with self.assertRaises(exceptions.ValidationError):
            self.env["res.partner"].create({"name": "P2", "partner_code": 25})
