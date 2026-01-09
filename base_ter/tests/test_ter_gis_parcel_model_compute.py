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

    def test_compute_gis_data_empty_without_parcel(self):
        rec = self._new_record()
        rec._compute_gis_data()
        self.assertEqual(rec.gis_data, "")
