# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerParceltagSearch(TransactionCase):
    """Test ter.parceltag search by alphanum_code."""

    def test_parceltag_search_by_code(self):
        tag = self.env["ter.parceltag"].create(
            {"alphanum_code": "SEARCH-TAG", "color": 5}
        )
        found = self.env["ter.parceltag"].search(
            [("alphanum_code", "=", "SEARCH-TAG")]
        )
        self.assertEqual(len(found), 1)
        self.assertEqual(found, tag)
