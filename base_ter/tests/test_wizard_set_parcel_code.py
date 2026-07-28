# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
# pylint: disable=invalid-name
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestWizardSetParcelCode(TransactionCase):
    def setUp(self):
        super().setUp()
        region = self.env["res.admregion"].create({"name": "Test Region"})
        province_vals = {"name": "Test Province", "region_id": region.id}
        # Modules installed on top of base_ter (e.g. l10n_es_territory) may add
        # required fields to these administrative models; populate them only
        # when present so this test works with or without those modules.
        if "cadastral_code" in self.env["res.province"]._fields:
            province_vals["cadastral_code"] = 99
        province = self.env["res.province"].create(province_vals)
        municipality_vals = {
            "name": "Test Municipality",
            "province_id": province.id,
        }
        if "municipality_number" in self.env["res.municipality"]._fields:
            municipality_vals["municipality_number"] = 999
        municipality = self.env["res.municipality"].create(municipality_vals)
        self.parcel = self.env["ter.parcel"].create(
            {
                "alphanum_code": "PARCEL-01",
                "municipality_id": municipality.id,
                "area_official": 1.0,
            }
        )

    def test_default_get_sets_parcel_code(self):
        wiz = (
            self.env["wizard.set.parcel.code"]
            .with_context(active_id=self.parcel.id)
            .create({})
        )
        defaults = wiz.default_get(["parcel_code"])
        self.assertEqual(defaults.get("parcel_code"), "PARCEL-01")

    def test_set_parcel_code_upper_and_strip(self):
        wiz = (
            self.env["wizard.set.parcel.code"]
            .with_context(active_id=self.parcel.id)
            .create({"parcel_code": "  abc-99  "})
        )
        wiz.set_parcel_code()
        self.assertEqual(self.parcel.alphanum_code, "ABC-99")

    def test_set_parcel_code_empty_clears(self):
        wiz = (
            self.env["wizard.set.parcel.code"]
            .with_context(active_id=self.parcel.id)
            .create({"parcel_code": "   "})
        )
        wiz.set_parcel_code()
        self.assertFalse(self.parcel.alphanum_code)
