from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerParceltagViews(TransactionCase):
    def test_parceltag_action_view_ids_has_no_trailing_comma(self):
        action = self.env.ref("base_ter.ter_parceltag_action")
        self.assertIn(
            "ter_parceltag_view_tree",
            action.view_ids.mapped("view_id").mapped("xml_id"),
        )
        self.assertIn(
            "ter_parceltag_view_form",
            action.view_ids.mapped("view_id").mapped("xml_id"),
        )

    def test_parceltag_form_view_has_no_bad_spacing(self):
        view = self.env.ref("base_ter.ter_parceltag_view_form")
        self.assertNotIn('string = "', view.arch_db)
