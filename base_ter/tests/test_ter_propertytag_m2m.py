from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerPropertytagM2M(TransactionCase):
    def test_propertytag_m2m_uses_expected_relation(self):
        field = self.env["ter.propertytag"]._fields["property_ids"]
        self.assertEqual(field.relation, "ter_property_propertytag_rel")
        self.assertEqual(field.column1, "propertytag_id")
        self.assertEqual(field.column2, "property_id")
