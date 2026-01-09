from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerPropertyTagViews(TransactionCase):
    def test_propertytag_action_views_exist(self):
        action = self.env.ref("base_ter.ter_propertytag_action")
        tree_view = self.env.ref("base_ter.ter_propertytag_view_tree")
        form_view = self.env.ref("base_ter.ter_propertytag_view_form")

        view_ids = action.view_ids.mapped("view_id").ids
        self.assertIn(tree_view.id, view_ids)
        self.assertIn(form_view.id, view_ids)

    def test_propertytag_form_view_no_commented_blocks(self):
        view = self.env.ref("base_ter.ter_propertytag_view_form")
        self.assertNotIn("<!--", view.arch_db)
