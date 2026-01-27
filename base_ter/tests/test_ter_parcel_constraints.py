from odoo import exceptions
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerParcelConstraints(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Holder", "partner_code": 1}
        )

        region = cls.env["res.admregion"].create({"name": "R1"})
        province = cls.env["res.province"].create(
            {"name": "P1", "region_id": region.id}
        )
        cls.municipality = cls.env["res.municipality"].create(
            {"name": "M1", "province_id": province.id}
        )

        cls.profile = cls.env.ref("base_ter.ter_profile_01")
