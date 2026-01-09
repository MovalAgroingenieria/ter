from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestReportProperty(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        province = cls.env["res.province"].create({"name": "P1"})
        cls.municipality = cls.env["res.municipality"].create(
            {"name": "M1", "province_id": province.id}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Partner Property", "partner_code": 1})

        cls.prop = cls.env["ter.property"].create(
            {
                "alphanum_code": "PROP-001",
                "municipality_id": cls.municipality.id,
                "partner_id": cls.partner.id,
            }
        )

    def test_report_action_exists(self):
        report = self.env.ref("base_ter.action_property_report")
        self.assertEqual(report.model, "ter.property")
        self.assertEqual(report.report_type, "qweb-pdf")

    def test_report_renders_qweb(self):
        report = self.env.ref("base_ter.action_property_report")
        html, _ = report._render_qweb_html(self.prop.ids, data={})
        self.assertIn("Property Report", html)
        self.assertIn("Aerial Image", html)
