# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestTerParcelInvoicing(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env["res.partner"]
        cls.Parcel = cls.env["ter.parcel"]
        cls.Partnerlink = cls.env["ter.parcel.partnerlink"]

        cls.partner = cls.Partner.create({"name": "Test Partner"})

        cls.owner_profile = cls.env.ref("base_ter.ter_profile_01", raise_if_not_found=False)
        if not cls.owner_profile:
            # If the referenced profile is missing, tests relying on it must be skipped.
            # We keep a flag and assert accordingly in each test.
            cls._missing_owner_profile = True
        else:
            cls._missing_owner_profile = False

    def _create_parcel(self, extra=None):
        extra = extra or {}
        vals = {}

        # Try to satisfy required fields dynamically
        for name, field in self.Parcel._fields.items():
            if not field.required or name in extra:
                continue
            if name == "partner_id":
                vals[name] = self.partner.id
            elif name == "company_id":
                vals[name] = self.env.company.id
            elif field.type == "char":
                vals[name] = "TEST"
            elif field.type == "float":
                vals[name] = 1.0
            elif field.type == "integer":
                vals[name] = 1
            elif field.type == "boolean":
                vals[name] = True
            elif field.type == "many2one" and field.comodel_name == "res.partner":
                vals[name] = self.partner.id
            elif field.type == "many2one" and field.comodel_name == "res.company":
                vals[name] = self.env.company.id

        vals.update(extra)
        return self.Parcel.create(vals)

    def _create_partnerlink(self, parcel, extra=None):
        extra = extra or {}
        vals = {
            "parcel_id": parcel.id,
            "partner_id": self.partner.id,
            "percentage_overhead": 0.0,
        }

        # Fill mandatory fields for partnerlink dynamically
        for name, field in self.Partnerlink._fields.items():
            if not field.required or name in vals or name in extra:
                continue
            if name == "partner_id":
                vals[name] = self.partner.id
            elif name == "parcel_id":
                vals[name] = parcel.id
            elif name == "company_id":
                vals[name] = self.env.company.id
            elif name == "profile_id" and not self._missing_owner_profile:
                vals[name] = self.owner_profile.id
            elif field.type == "char":
                vals[name] = "TEST"
            elif field.type == "float":
                vals[name] = 1.0
            elif field.type == "integer":
                vals[name] = 1
            elif field.type == "boolean":
                vals[name] = True

        vals.update(extra)
        return self.Partnerlink.create(vals)

    def test_percentage_overhead_range_constraint(self):
        parcel = self._create_parcel()
        with self.assertRaises(exceptions.ValidationError):
            self._create_partnerlink(parcel, {"percentage_overhead": 101.0})

        with self.assertRaises(exceptions.ValidationError):
            self._create_partnerlink(parcel, {"percentage_overhead": -1.0})

        link = self._create_partnerlink(parcel, {"percentage_overhead": 50.0})
        self.assertEqual(link.percentage_overhead, 50.0)

    def test_is_owner_and_area_ownership(self):
        if self._missing_owner_profile:
            self.skipTest("Missing XML ID base_ter.ter_profile_01")

        parcel = self._create_parcel({"area_official": 100.0})
        link = self._create_partnerlink(
            parcel,
            {
                "profile_id": self.owner_profile.id,
                "percentage": 25.0,
                "percentage_overhead": 10.0,
            },
        )
        link.invalidate_recordset()
        self.assertTrue(link.is_owner)
        self.assertAlmostEqual(link.area_ownership, 25.0, places=4)
        self.assertAlmostEqual(link.area_overhead, 10.0, places=4)

    def test_parcel_overhead_total_must_be_100(self):
        parcel = self._create_parcel()
        # Create two links that sum != 100, should trigger parcel constraint
        self._create_partnerlink(parcel, {"percentage_overhead": 60.0})
        self._create_partnerlink(parcel, {"percentage_overhead": 30.0})

        with self.assertRaises(exceptions.ValidationError):
            parcel._check_partnerlink_ids()

        # Fix to 100 and check it passes
        links = parcel.partnerlink_ids
        links[0].percentage_overhead = 70.0
        links[1].percentage_overhead = 30.0
        parcel._check_partnerlink_ids()
