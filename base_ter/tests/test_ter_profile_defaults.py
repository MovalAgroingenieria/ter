# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerProfileDefaults(TransactionCase):
    """Test ter.profile default values and creation."""

    def test_profile_defaults(self):
        profile = self.env["ter.profile"].create(
            {"alphanum_code": "CUSTOM", "requires_total": False}
        )
        self.assertTrue(profile.id)
        self.assertEqual(profile.alphanum_code, "CUSTOM")
        self.assertFalse(profile.requires_total)
        self.assertFalse(profile.is_standard)
        self.assertTrue(profile.active)

    def test_profile_standard_flag_stored(self):
        profile = self.env["ter.profile"].create(
            {
                "alphanum_code": "STD-PROFILE",
                "is_standard": True,
                "requires_total": True,
            }
        )
        self.assertTrue(profile.is_standard)
        self.assertTrue(profile.requires_total)
