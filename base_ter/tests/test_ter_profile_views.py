# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerProfileViews(TransactionCase):
    def test_profile_action_views_exist(self):
        action = self.env.ref("base_ter.ter_profile_action")
        tree_view = self.env.ref("base_ter.ter_profile_view_list")
        form_view = self.env.ref("base_ter.ter_profile_view_form")

        view_ids = action.view_ids.mapped("view_id").ids
        self.assertIn(tree_view.id, view_ids)
        self.assertIn(form_view.id, view_ids)

    def test_profile_form_view_no_large_commented_blocks(self):
        view = self.env.ref("base_ter.ter_profile_view_form")
        self.assertNotIn("<!--", view.arch_db)
