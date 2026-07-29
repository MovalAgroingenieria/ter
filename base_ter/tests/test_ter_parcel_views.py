from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerParcelViews(TransactionCase):
    def test_parcel_search_view_uses_false_in_domains(self):
        view = self.env.ref("base_ter.ter_parcel_view_search")
        self.assertNotIn("None", view.arch_db)
        self.assertIn("('partner_id', '!=', False)", view.arch_db)
        self.assertIn("('partner_id', '=', False)", view.arch_db)

    def test_partnerlink_tree_view_disables_create_delete(self):
        view = self.env.ref("base_ter.ter_parcel_partnerlink_view_list")
        self.assertIn('create="false"', view.arch_db)
        self.assertIn('delete="false"', view.arch_db)
        self.assertNotIn('edit="false"', view.arch_db)
