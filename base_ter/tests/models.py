from odoo import fields, models


class GisViewerTestModel(models.Model):
    _name = "gis.viewer.test.model"
    _description = "GIS Viewer test model"
    _inherit = "gis.viewer"

    name = fields.Char(required=True)
    mapped_to_polygon = fields.Boolean(default=True)

    # Minimal bbox used by tests
    bounding_box_str = fields.Char(default="BOX(0.0 0.0,10.0 10.0)")

    geom_ewkt = fields.Char(default="SRID=4326;POLYGON((0 0,10 0,10 10,0 10,0 0))")

    def extract_bounding_box(self, _ewkt, force_square_shape=False):
        bbox = (0.0, 0.0, 10.0, 10.0)
        return 4326, bbox
