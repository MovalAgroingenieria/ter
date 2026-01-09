from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestReportParcelPartner(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Partner Report", "partner_code": 1}
        )

    def test_report_action_exists(self):
        report = self.env.ref("base_ter.action_parcel_partner_report")
        self.assertEqual(report.model, "res.partner")
        self.assertEqual(report.report_type, "qweb-pdf")

    def test_report_renders_qweb(self):
        report = self.env.ref("base_ter.action_parcel_partner_report")
        # Render HTML to avoid wkhtml dependency in tests
        html, _ = report._render_qweb_html(self.partner.ids, data={})
        self.assertIn("Parcels Report", html)
        self.assertIn("Partner", html)
