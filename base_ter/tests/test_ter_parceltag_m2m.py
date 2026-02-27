# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerParceltagM2M(TransactionCase):
    def test_parceltag_m2m_uses_expected_relation(self):
        field = self.env["ter.parceltag"]._fields["parcel_ids"]
        self.assertEqual(field.relation, "ter_parcel_parceltag_rel")
        self.assertEqual(field.column1, "parceltag_id")
        self.assertEqual(field.column2, "parcel_id")
