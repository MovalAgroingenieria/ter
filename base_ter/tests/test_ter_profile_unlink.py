from odoo import exceptions
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerProfileUnlink(TransactionCase):
    def test_unlink_forbidden_for_standard(self):
        profile = self.env["ter.profile"].create(
            {"alphanum_code": "STD", "is_standard": True, "requires_total": True}
        )
        with self.assertRaises(exceptions.UserError):
            profile.unlink()

    def test_unlink_allowed_for_non_standard(self):
        profile = self.env["ter.profile"].create(
            {"alphanum_code": "NSTD", "is_standard": False, "requires_total": True}
        )
        profile.unlink()
        self.assertFalse(profile.exists())
