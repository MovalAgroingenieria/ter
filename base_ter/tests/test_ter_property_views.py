from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerPropertyViews(TransactionCase):
    def test_property_action_views_exist(self):
        action = self.env.ref("base_ter.ter_property_action")
        tree_view = self.env.ref("base_ter.ter_property_view_tree")
        form_view = self.env.ref("base_ter.ter_property_view_form")
        kanban_view = self.env.ref("base_ter.ter_property_view_kanban")
        pivot_view = self.env.ref("base_ter.ter_property_view_pivot")

        view_ids = action.view_ids.mapped("view_id").ids
        self.assertIn(tree_view.id, view_ids)
        self.assertIn(form_view.id, view_ids)
        self.assertIn(kanban_view.id, view_ids)
        self.assertIn(pivot_view.id, view_ids)

    def test_property_form_view_no_commented_blocks(self):
        view = self.env.ref("base_ter.ter_property_view_form")
        self.assertNotIn("<!--", view.arch_db)

    def test_property_kanban_js_class(self):
        view = self.env.ref("base_ter.ter_property_view_kanban")
        self.assertIn('js_class="ter_property_view_kanban"', view.arch_db)
