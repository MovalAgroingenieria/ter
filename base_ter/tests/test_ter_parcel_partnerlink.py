# Copyright 2026 Moval Agroingeniería S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
# pylint: disable=invalid-name
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerParcelPartnerlink(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Holder", "partner_code": 1}
        )

        # Minimal geo hierarchy (adjust if your models require extra fields)
        region = (
            cls.env["res.admregion"].create({"name": "R1"})
            if "res.admregion" in cls.env
            else None
        )
        province_vals = {"name": "P1"}
        if region:
            province_vals["region_id"] = region.id
        province = cls.env["res.province"].create(province_vals)

        municipality_vals = {"name": "M1", "province_id": province.id}
        cls.municipality = cls.env["res.municipality"].create(municipality_vals)

        cls.profile = cls.env.ref("base_ter.ter_profile_01")

        cls.parcel = cls.env["ter.parcel"].create(
            {
                "alphanum_code": "PAR-001",
                "municipality_id": cls.municipality.id,
                "area_official": 1.0,
            }
        )

    def test_profile_without_total_forces_percentage_zero(self):
        profile = self.env["ter.profile"].create(
            {"name": "NoTotal", "requires_total": False}
        )
        link = self.env["ter.parcel.partnerlink"].create(
            {
                "parcel_id": self.parcel.id,
                "partner_id": self.partner.id,
                "profile_id": profile.id,
                "is_main": True,
                "percentage": 75,
            }
        )
        self.assertEqual(link.percentage, 0)

        link.write({"percentage": 80})
        self.assertEqual(link.percentage, 0)
