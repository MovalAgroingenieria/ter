from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestIrCronExtension(TransactionCase):
    def test_ir_cron_has_is_base_ter_field(self):
        cron = self.env["ir.cron"].create(
            {
                "name": "Test cron",
                "model_id": self.env.ref("base.model_res_partner").id,
                "state": "code",
                "code": "model.search([])[:1]",
                "interval_number": 1,
                "interval_type": "days",
                "numbercall": 1,
                "active": False,
                "is_base_ter": True,
            }
        )
        self.assertTrue(cron.is_base_ter)
