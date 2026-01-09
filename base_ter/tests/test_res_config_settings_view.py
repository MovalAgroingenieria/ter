from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestResConfigSettingsView(TransactionCase):
    def test_settings_block_is_inherited(self):
        view = self.env.ref("base_ter.res_config_settings_view_form")
        self.assertIn('data-key="base_ter"', view.arch_db)
        self.assertIn("area_unit_is_ha", view.arch_db)
        self.assertIn("gis_viewer_url", view.arch_db)
