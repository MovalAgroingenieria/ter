# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerCatalogModels(TransactionCase):
    """Test creation and basic fields for ter.parceltag and ter.propertytag."""

    def test_parceltag_create_and_display(self):
        tag = self.env["ter.parceltag"].create(
            {"alphanum_code": "TAG-A", "color": 1}
        )
        self.assertTrue(tag.id)
        self.assertEqual(tag.alphanum_code, "TAG-A")
        self.assertEqual(tag.color, 1)
        self.assertFalse(tag.parcel_ids)

    def test_propertytag_create_and_display(self):
        tag = self.env["ter.propertytag"].create(
            {"alphanum_code": "PROP-X", "color": 2}
        )
        self.assertTrue(tag.id)
        self.assertEqual(tag.alphanum_code, "PROP-X")
        self.assertEqual(tag.color, 2)
        self.assertFalse(tag.property_ids)
