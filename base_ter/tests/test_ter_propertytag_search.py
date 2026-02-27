# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerPropertytagSearch(TransactionCase):
    """Test ter.propertytag search by alphanum_code."""

    def test_propertytag_search_by_code(self):
        tag = self.env["ter.propertytag"].create(
            {"alphanum_code": "PROP-Y", "color": 3}
        )
        found = self.env["ter.propertytag"].search([("alphanum_code", "=", "PROP-Y")])
        self.assertEqual(len(found), 1)
        self.assertEqual(found, tag)
