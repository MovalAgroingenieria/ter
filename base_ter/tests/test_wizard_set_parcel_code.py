# pylint: disable=invalid-name
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestWizardSetParcelCode(TransactionCase):
    def setUp(self):
        super().setUp()
        self.parcel = self.env["ter.parcel"].create(
            {
                "alphanum_code": "PARCEL-01",
                "municipality_id": self.env["res.municipality"]
                .create(
                    {
                        "name": "Test Municipality",
                        "province_id": self.env["res.province"]
                        .create(
                            {
                                "name": "Test Province",
                                "region_id": self.env["res.admregion"]
                                .create({"name": "Test Region"})
                                .id,
                            }
                        )
                        .id,
                    }
                )
                .id,
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
