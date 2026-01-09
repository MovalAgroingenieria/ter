from unittest.mock import Mock, patch

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTerGisParcelModelCompute(TransactionCase):
    def _new_record(self):
        return self.env["ter.gis.parcel.model"].new({})

    def test_compute_threshold_str_empty_without_parcel(self):
        rec = self._new_record()
        rec._compute_diff_areas_threshold_exceeded_str()
        self.assertEqual(rec.diff_areas_threshold_exceeded_str, "")

    def test_compute_threshold_str_ok(self):
        rec = self._new_record()
        rec.parcel_id = Mock()
        rec.diff_areas_threshold_exceeded = False
        rec._compute_diff_areas_threshold_exceeded_str()
        self.assertEqual(rec.diff_areas_threshold_exceeded_str, "ok")

    def test_compute_threshold_str_check(self):
        rec = self._new_record()
        rec.parcel_id = Mock()
        rec.diff_areas_threshold_exceeded = True
        rec._compute_diff_areas_threshold_exceeded_str()
        self.assertEqual(rec.diff_areas_threshold_exceeded_str, "CHECK")

    def test_compute_gis_data_builds_expected_lines(self):
        rec = self._new_record()

        parcel = Mock()
        parcel.area_official_m2 = 100
        parcel.area_gis = 110
        parcel.perimeter_gis = 55
        parcel.bounding_box_str = "BOX(0 0,10 10)"
        rec.parcel_id = parcel

        formatter = Mock()
        formatter.transform_integer_to_locale.side_effect = lambda v: str(v)

        with patch.object(type(self.env["common.format"]), "transform_integer_to_locale",
                          side_effect=lambda self, v: str(v)):
            # easier: patch env service to our mock
            with patch.object(self.env, "__getitem__",
                              side_effect=lambda k: formatter if k == "common.format" else self.env[k]):
                rec._compute_gis_data()

        self.assertIn("⸰", rec.gis_data)
        self.assertIn("Official Area (m²): 100", rec.gis_data)
        self.assertIn("GIS Area (m²): 110", rec.gis_data)
        self.assertIn("GIS Perimeter (m): 55", rec.gis_data)
        self.assertIn("⸰ (0 0,10 10)", rec.gis_data)

    def test_compute_gis_data_empty_without_parcel(self):
        rec = self._new_record()
        rec._compute_gis_data()
        self.assertEqual(rec.gis_data, "")
