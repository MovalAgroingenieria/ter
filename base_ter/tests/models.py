from odoo import fields, models


class GisViewerTestModel(models.Model):
    _name = "gis.viewer.test.model"
    _description = "GIS Viewer Test Model"
    _inherit = "gis.viewer"

    name = fields.Char()
    mapped_to_polygon = fields.Boolean(default=False)
    geom_ewkt = fields.Char()

    def extract_bounding_box(self, geom_ewkt, force_square_shape=False):
        return 4326, (0.0, 0.0, 10.0, 10.0)
