# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestIrCronExtension(TransactionCase):
    def test_ir_cron_has_is_base_ter_field(self):
        model = self.env.ref("base.model_res_partner")

        cron = self.env["ir.cron"].create(
            {
                "name": "Test cron",
                "model_id": model.id,
                "state": "code",
                "code": "model.search([], limit=1)",
                "interval_number": 1,
                "interval_type": "days",
                "active": False,
                "is_base_ter": True,
            }
        )
        self.assertTrue(cron.is_base_ter)
