# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerUseType(TransactionCase):
    """Test ter.use_type creation and hierarchy."""

    def test_use_type_create_root(self):
        use_type = self.env["ter.use_type"].create(
            {"name": "Agriculture", "sequence": 1, "color": 1}
        )
        self.assertTrue(use_type.id)
        self.assertEqual(use_type.name, "Agriculture")
        self.assertFalse(use_type.parent_id)
        self.assertTrue(use_type.active)

    def test_use_type_create_child(self):
        parent = self.env["ter.use_type"].create({"name": "Crops", "sequence": 10})
        child = self.env["ter.use_type"].create(
            {"name": "Cereal", "parent_id": parent.id, "sequence": 1}
        )
        self.assertEqual(child.parent_id, parent)
        self.assertIn(child, parent.child_ids)
