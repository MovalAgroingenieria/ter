# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestIrCronDefault(TransactionCase):
    """Test ir.cron is_base_ter default value."""

    def test_ir_cron_is_base_ter_default_false(self):
        model = self.env.ref("base.model_res_partner")
        cron = self.env["ir.cron"].create(
            {
                "name": "Test cron default",
                "model_id": model.id,
                "state": "code",
                "code": "model.search([], limit=1)",
                "interval_number": 1,
                "interval_type": "days",
                "active": False,
            }
        )
        self.assertFalse(cron.is_base_ter)
