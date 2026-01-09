from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerGisParcelModelViews(TransactionCase):
    def test_search_view_uses_false_in_domains(self):
        view = self.env.ref("base_ter.ter_gis_parcel_model_view_search")
        self.assertNotIn("None", view.arch_db)
        self.assertIn("('partner_id', '!=', False)", view.arch_db)
        self.assertIn("('parcel_id', '!=', False)", view.arch_db)

    def test_tree_view_decorations_are_clean(self):
        view = self.env.ref("base_ter.ter_gis_parcel_model_view_tree")
        self.assertNotIn("== True", view.arch_db)
        self.assertIn('decoration-danger="diff_areas_threshold_exceeded"', view.arch_db)
        self.assertIn('decoration-bf="diff_areas_threshold_exceeded"', view.arch_db)
