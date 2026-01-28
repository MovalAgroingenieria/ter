# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=protected-access

import os
import tempfile
from unittest import mock

import psycopg2
from odoo import exceptions
from odoo.addons.l10n_es_territory_sigpac.models.res_config_settings import DEF_INT_PERC
from odoo.tests.common import TransactionCase


class TestResConfigSettings(TransactionCase):
    def setUp(self):  # pylint: disable=invalid-name
        super().setUp()
        self.settings = self.env["res.config.settings"].create({})

    def test_check_minimum_intersection_percentage_ok(self):
        self.settings.sigpac_minimum_intersection_percentage = 0
        self.settings._check_sigpac_minimum_intersection_percentage()

        self.settings.sigpac_minimum_intersection_percentage = 100
        self.settings._check_sigpac_minimum_intersection_percentage()

    def test_check_minimum_intersection_percentage_invalid(self):
        with self.assertRaises(exceptions.ValidationError):
            self.settings.sigpac_minimum_intersection_percentage = -0.1
            self.settings._check_sigpac_minimum_intersection_percentage()

        with self.assertRaises(exceptions.ValidationError):
            self.settings.sigpac_minimum_intersection_percentage = 100.1
            self.settings._check_sigpac_minimum_intersection_percentage()

    def test_get_shp_list_empty_names_glob(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p1 = os.path.join(tmpdir, "a.shp")
            p2 = os.path.join(tmpdir, "b.shp")
            with open(p1, "w", encoding="utf-8"):
                pass
            with open(p2, "w", encoding="utf-8"):
                pass

            shp_list = self.settings._get_shp_list(tmpdir, "")
            self.assertEqual(len(shp_list), 2)
            self.assertTrue(any(x["shapefile"].endswith("a.shp") for x in shp_list))
            self.assertTrue(any(x["shapefile"].endswith("b.shp") for x in shp_list))

    def test_get_shp_list_with_conditions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p1 = os.path.join(tmpdir, "x.shp")
            p2 = os.path.join(tmpdir, "y.shp")
            with open(p1, "w", encoding="utf-8"):
                pass
            with open(p2, "w", encoding="utf-8"):
                pass

            shp_list = self.settings._get_shp_list(tmpdir, "x.shp(FOO=1), y.shp")
            self.assertEqual(
                shp_list,
                [
                    {"shapefile": f"{tmpdir}/x.shp", "condition": "FOO=1"},
                    {"shapefile": f"{tmpdir}/y.shp", "condition": ""},
                ],
            )

    def test_get_shp_list_missing_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shp_list = self.settings._get_shp_list(tmpdir, "missing.shp")
            self.assertEqual(shp_list, [])

    def test_build_shapefiles_argument(self):
        shp_list = [
            {"shapefile": "/a/x.shp", "condition": ""},
            {"shapefile": "/a/y.shp", "condition": "FOO=1"},
        ]
        arg = self.settings._build_shapefiles_argument(shp_list)
        self.assertEqual(arg, "/a/x.shp#/a/y.shp(FOO=1)")

    def test_update_geometry_drop_view_error(self):
        with mock.patch.object(self.settings.env, "cr") as cr:
            cr.execute.side_effect = psycopg2.Error("boom")
            resp = self.settings.update_geometry(25830, 4326)
            self.assertEqual(resp[0], False)

    def test_update_geometry_rebuild_called_with_default(self):
        with mock.patch.object(self.settings.env, "cr") as cr:
            cr.execute.return_value = True
            with mock.patch.object(
                type(self.settings.env["ir.config_parameter"].sudo()),
                "get_param",
                return_value="",
            ):
                with mock.patch.object(
                    type(self.settings), "_rebuild_ter_parcel_sigpaclink_view"
                ) as rebuild:
                    resp = self.settings.update_geometry(25830, 4326)
                    self.assertEqual(resp[0], True)
                    rebuild.assert_called_once_with(DEF_INT_PERC)
