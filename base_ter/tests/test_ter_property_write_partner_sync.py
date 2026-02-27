# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
# pylint: disable=invalid-name
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerPropertyWritePartnerSync(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.write({"same_parcelmanager_propertyowner": True})

        cls.old_partner = cls.env["res.partner"].create(
            {"name": "Old", "partner_code": 12}
        )
        cls.new_partner = cls.env["res.partner"].create(
            {"name": "New", "partner_code": 20}
        )

        region = cls.env["res.admregion"].create({"name": "R1"})
        province = cls.env["res.province"].create(
            {"name": "P1", "region_id": region.id}
        )
        cls.municipality = cls.env["res.municipality"].create(
            {"name": "M1", "province_id": province.id}
        )

        cls.profile = cls.env.ref("base_ter.ter_profile_01")

    def test_write_updates_parcel_partner_and_partnerlinks(self):
        prop = self.env["ter.property"].create(
            {
                "alphanum_code": "F-001",
                "municipality_id": self.municipality.id,
                "partner_id": self.old_partner.id,
            }
        )
        parcel = self.env["ter.parcel"].create(
            {
                "alphanum_code": "PAR-001",
                "municipality_id": self.municipality.id,
                "area_official": 1.0,
                "property_id": prop.id,
            }
        )
        link = self.env["ter.parcel.partnerlink"].create(
            {
                "parcel_id": parcel.id,
                "partner_id": self.old_partner.id,
                "profile_id": self.profile.id,
                "is_main": True,
                "percentage": 100,
            }
        )
        parcel.partner_id = self.old_partner

        prop.write({"partner_id": self.new_partner.id})

        parcel.invalidate_recordset()
        link.invalidate_recordset()
        self.assertEqual(parcel.partner_id.id, self.new_partner.id)
        self.assertEqual(link.partner_id.id, self.new_partner.id)
