from odoo import fields, models


class GisViewerTestModel(models.Model):
    _name = "gis.viewer.test.model"
    _description = "GIS Viewer test model"

    name = fields.Char(required=True)
    mapped_to_polygon = fields.Boolean(default=True)

    # Minimal bbox used by tests
    bounding_box_str = fields.Char(default="BOX(0.0 0.0,10.0 10.0)")
