# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, api, _


class TerProperty(models.Model):
    _name = 'ter.property'
    _description = 'Property'
    _inherit = ['simple.model', 'polygon.model',
                'common.log', 'mail.thread']
    _rec_name = 'alphanum_code'

    # Static variables inherited from "simple.model"
    _set_num_code = False
    _sequence_for_codes = ''
    _size_name = 30
    _minlength = 0
    _maxlength = 30
    _allowed_blanks_in_code = True
    _set_alphanum_code_to_lowercase = False
    _set_alphanum_code_to_uppercase = False
    _size_description = 75

    # Static variables inherited from "polygon.model"
    _gis_table = 'ter_gis_property'
    _geom_field = 'geom'
    _link_field = 'name'

    alphanum_code = fields.Char(
        string='Property Name',
        required=True,)

    partner_id = fields.Many2one(
        string='Property Manager',
        comodel_name='res.partner',
        index=True,
        ondelete='restrict',)

    parcel_ids = fields.One2many(
        string='Parcels of the property',
        comodel_name='ter.parcel',
        inverse_name='property_id',)

    area_official_parcels = fields.Float(
        string='Managed Area (parcels)',
        digits=(32, 4),
        default=0,
        index=True,)

    @api.model
    def action_refresh_properties_layer(self):
        config = self.env['ir.config_parameter'].sudo()
        gis_viewer_epsg = config.get_param(
            'base_ter.gis_viewer_epsg', False)
        if not gis_viewer_epsg:
            gis_viewer_epsg = 25830
        message_type = 'INFO'
        message = _('ter_gis_property layer recreated.')
        module = ''
        model = ''
        method = ''
        try:
            self.env.cr.execute(
                'DROP TABLE IF EXISTS ter_gis_property')
            self.env.cr.execute(
                'CREATE TABLE ter_gis_property AS '
                'SELECT ROW_NUMBER() OVER (ORDER BY terpro.name) AS gid, terpro.name, '
                'ST_UNION(tergispar.geom)::Geometry(MultiPolygon,%s) AS geom '
                'FROM ter_gis_parcel tergispar '
                'INNER JOIN ter_parcel terpar ON tergispar.name = terpar.name '
                'INNER JOIN ter_property terpro ON terpro.id = terpar.property_id '
                'GROUP BY terpro.name', tuple((gis_viewer_epsg,)))
            self.env.cr.execute(
                'ALTER TABLE ter_gis_property '
                'ADD PRIMARY KEY (gid)')
            self.env.cr.execute(
                'ALTER TABLE ter_gis_property '
                'ALTER COLUMN name SET NOT NULL')
            self.env.cr.execute(
                'ALTER TABLE ter_gis_property '
                'ADD CONSTRAINT ter_gis_property_name_key UNIQUE(name)')
            self.env.cr.execute(
                'ALTER TABLE ter_gis_property '
                'ADD CONSTRAINT ter_gis_property_name_check CHECK (name <> \'\')')
            self.env.cr.execute(
                'CREATE INDEX IF NOT EXISTS ter_gis_property_idx '
                'ON public.ter_gis_property USING gist (geom)')
        except Exception as error:
            message_type = 'ERROR'
            message = str(error)
            module = 'base_ter'
            model = 'ter.property'
            method = 'action_refresh_properties_layer'
        self.register_in_log(message, source=self._name, module=module,
                             model=model, method=method,
                             message_type=message_type)
