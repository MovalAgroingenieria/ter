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

        province = cls.env["res.province"].create({"name": "P1"})
        cls.municipality = cls.env["res.municipality"].create(
            {"name": "M1", "province_id": province.id}
        )

        cls.profile = cls.env.ref("base_ter.ter_profile_01")

    def test_manager_requires_contact_list(self):
        parcel = self.env["ter.parcel"].create(
            {
                "alphanum_code": "PAR-002",
                "municipality_id": self.municipality.id,
                "area_official": 1.0,
            }
        )
        parcel.partner_id = self.partner
        with self.assertRaises(exceptions.ValidationError):
            parcel._check_partner_id()

    def test_single_main_contact_required(self):
        parcel = self.env["ter.parcel"].create(
            {
                "alphanum_code": "PAR-003",
                "municipality_id": self.municipality.id,
                "area_official": 1.0,
            }
        )
        self.env["ter.parcel.partnerlink"].create(
            {
                "parcel_id": parcel.id,
                "partner_id": self.partner.id,
                "profile_id": self.profile.id,
                "is_main": True,
                "percentage": 100,
            }
        )
        self.env["ter.parcel.partnerlink"].create(
            {
                "parcel_id": parcel.id,
                "partner_id": self.partner.id,
                "profile_id": self.profile.id,
                "is_main": False,
                "percentage": 0,
            }
        )
        parcel.partner_id = self.partner
        with self.assertRaises(exceptions.ValidationError):
            parcel._check_partnerlink_ids()
