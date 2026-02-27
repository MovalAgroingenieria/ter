# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
# pylint: disable=invalid-name
from unittest.mock import patch

from odoo import exceptions
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestResConfigSettingsGeometry(TransactionCase):
    def setUp(self):
        super().setUp()
        self.env.company.write({"gis_viewer_epsg": 4326})

    def test_set_values_calls_update_geometry_on_epsg_change(self):
        settings = self.env["res.config.settings"].create({"gis_viewer_epsg": 25830})

        with patch.object(
            type(settings), "update_geometry", return_value=(True, "")
        ) as mocked:
            settings.set_values()
            mocked.assert_called_once_with(4326, 25830)

    def test_set_values_raises_usererror_on_failed_update(self):
        settings = self.env["res.config.settings"].create({"gis_viewer_epsg": 25830})

        with patch.object(
            type(settings), "update_geometry", return_value=(False, "ter_gis_parcel")
        ):
            with self.assertRaises(exceptions.UserError):
                settings.set_values()

    def test_update_geometry_stops_on_first_failure(self):
        settings = self.env["res.config.settings"].create({"gis_viewer_epsg": 25830})

        with patch.object(
            type(settings), "_set_layers_to_update_geometry", return_value=["a", "b"]
        ):
            with patch.object(
                type(settings),
                "_update_layer_geometry",
                side_effect=[(False, "a\n\nERROR:\n\nboom"), (True, "")],
            ) as mocked:
                ok, details = settings.update_geometry(4326, 25830)
                self.assertFalse(ok)
                self.assertIn("boom", details)
                self.assertEqual(mocked.call_count, 1)
