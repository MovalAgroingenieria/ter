from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerParcel(TransactionCase):
    @classmethod
    def setUpClass(cls):  # pylint: disable=invalid-name
        super().setUpClass()
        region = cls.env["res.admregion"].create({"name": "R1"})
        province = cls.env["res.province"].create(
            {"name": "P1", "region_id": region.id}
        )

        cls.municipality = cls.env["res.municipality"].create(
            {"name": "M1", "province_id": province.id}
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Partner Property", "partner_code": 19990009}
        )

        cls.property = cls.env["ter.property"].create(
            {
                "alphanum_code": "PROP-001",
                "municipality_id": cls.municipality.id,
                "partner_id": cls.partner.id,
            }
        )
        cls.parcel = cls.env["ter.parcel"].create(
            {
                "name": "PARCEL-001",
                "property_id": cls.property.id,
                "is_secondary": True,
                "mapped_from_base": True,
                "municipality_id": cls.municipality.id,
                "last_update": fields.Datetime.to_datetime("2025-01-01 00:00:00"),
                "partner_info": "X",
            }
        )

    def test_compute_clears_base_fields_when_not_secondary(self):
        self.parcel.write(
            {
                "is_secondary": False,
                "mapped_from_base": True,
                "partner_info": "Y",
            }
        )
        self.parcel.invalidate_recordset()
        self.assertFalse(self.parcel.mapped_from_base)
        self.assertFalse(self.parcel.last_update)
        self.assertFalse(self.parcel.partner_info)

    def test_compute_keeps_values_when_secondary(self):
        self.parcel.write(
            {
                "is_secondary": True,
                "mapped_from_base": True,
                "partner_info": "OK",
            }
        )
        self.parcel.invalidate_recordset()
        self.assertTrue(self.parcel.is_secondary)
        self.assertTrue(self.parcel.mapped_from_base)
        self.assertEqual(self.parcel.partner_info, "OK")
