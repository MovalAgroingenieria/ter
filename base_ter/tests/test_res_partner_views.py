from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestResPartnerViews(TransactionCase):
    def test_partner_form_view_has_no_deprecated_attrs(self):
        view = self.env.ref("base_ter.view_partner_form")
        self.assertNotIn("attrs=", view.arch_db)
        self.assertIn("context_no_ter", view.arch_db)
        self.assertIn("partner_code", view.arch_db)

    def test_partner_kanban_view_uses_qweb_conditions(self):
        view = self.env.ref("base_ter.res_partner_kanban_view")
        self.assertNotIn("attrs=", view.arch_db)
        self.assertIn("t-if", view.arch_db)
        self.assertIn("is_holder", view.arch_db)

    def test_partner_tree_view_button_invisible_modifier(self):
        view = self.env.ref("base_ter.res_partner_view_tree")
        self.assertIn('invisible="number_of_parcels == 0"', view.arch_db)
