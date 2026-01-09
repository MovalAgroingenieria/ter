from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestReportParcel(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        province = cls.env["res.province"].create({"name": "P1"})
        cls.municipality = cls.env["res.municipality"].create(
            {"name": "M1", "province_id": province.id}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Partner Report", "partner_code": 1})

        cls.parcel = cls.env["ter.parcel"].create(
            {
                "alphanum_code": "PAR-001",
                "municipality_id": cls.municipality.id,
                "area_official": 1.0,
                "partner_id": cls.partner.id,
            }
        )

    def test_report_action_exists(self):
        report = self.env.ref("base_ter.action_parcel_report")
        self.assertEqual(report.model, "ter.parcel")
        self.assertEqual(report.report_type, "qweb-pdf")

    def test_report_renders_qweb(self):
        report = self.env.ref("base_ter.action_parcel_report")
        html, _ = report._render_qweb_html(self.parcel.ids, data={})
        self.assertIn("Parcel Report", html)
        self.assertIn("Aerial Image", html)
