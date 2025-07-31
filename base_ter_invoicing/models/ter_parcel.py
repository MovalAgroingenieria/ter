# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models, api, exceptions, _


class TerParcel(models.Model):
    _name = 'ter.parcel'
    _inherit = ['ter.parcel']

    @api.constrains('partner_id', 'partnerlink_ids')
    def _check_partnerlink_ids(self):
        super(TerParcel, self)._check_partnerlink_ids()
        for record in self:
            if record.partnerlink_ids:
                total_percentage_overhead = \
                    sum(partnerlink.percentage_overhead
                        for partnerlink in record.partnerlink_ids)
                if total_percentage_overhead != 100:
                    raise exceptions.ValidationError(
                        _('Review the overhead percentages: '
                          'the total must be 100%.'))

    def _get_default_first_partnerlink_vals(self, partner_id, profile_id,
                                            percentage):
        resp = super(TerParcel, self)._get_default_first_partnerlink_vals(
            partner_id, profile_id, percentage)
        resp['percentage_overhead'] = 100
        return resp

    def _add_area_fields(self):
        area_fields = super(TerParcel, self)._add_area_fields()
        area_fields.append(('area_ownership', _('🡸 Area')))
        area_fields.append(('area_overhead', _('🡸 Area')))
        return area_fields


class TerParcelPartnerlink(models.Model):
    _name = 'ter.parcel.partnerlink'
    _inherit = ['ter.parcel.partnerlink', 'account.billable.item']

    _billing_partner_id_name = 'partner_id'
    _billing_quantity_name = ''

    area_ownership = fields.Float(
        string='Area (ownership)',
        digits=(32, 4),
        store=True,
        compute='_compute_area_ownership',
        index=True,)

    percentage_overhead = fields.Float(
        string='% Overhead',
        digits=(32, 2),
        default=0,
        required=True,)

    area_overhead = fields.Float(
        string='Area (overhead)',
        digits=(32, 4),
        store=True,
        compute='_compute_area_overhead',
        index=True,)

    is_owner = fields.Boolean(
        string='Owner (y/n)',
        store=True,
        compute='_compute_is_owner',)

    parcel_code = fields.Char(
        string='Parcel Code',
        store=True,
        related='parcel_id.alphanum_code')

    parcel_area_official = fields.Float(
        string='Total Area',
        digits=(32, 4),
        store=True,
        related='parcel_id.area_official',)

    parcel_official_code = fields.Char(
        string='Official Code',
        store=True,
        related='parcel_id.official_code',)

    property_name = fields.Char(
        string='Property',
        store=True,
        related='parcel_id.property_id.alphanum_code',)

    partner_is_company = fields.Boolean(
        string='Company (y/n)',
        store=True,
        related='partner_id.is_company',)

    _sql_constraints = [
        ('overhead_percentage',
         'CHECK (percentage_overhead >= 0 and percentage_overhead <= 100)',
         'Incorrect value of "Overhead Percentage".'),
        ]

    @api.depends('parcel_id.area_official', 'profile_id', 'percentage')
    def _compute_area_ownership(self):
        for record in self:
            area_ownership = 0
            if (record.parcel_id and record.parcel_id.area_official > 0 and
               record.percentage and record.profile_id and
               record.profile_id == self.env.ref('base_ter.ter_profile_01')):
                area_ownership = \
                    record.parcel_id.area_official * record.percentage / 100
            record.area_ownership = area_ownership

    @api.depends('parcel_id.area_official', 'percentage_overhead')
    def _compute_area_overhead(self):
        for record in self:
            area_overhead = 0
            if (record.parcel_id and record.parcel_id.area_official > 0 and
               record.percentage_overhead):
                area_overhead = \
                    (record.parcel_id.area_official *
                     record.percentage_overhead / 100)
            record.area_overhead = area_overhead

    @api.depends('profile_id')
    def _compute_is_owner(self):
        for record in self:
            is_owner = False
            if (record.profile_id and
               record.profile_id == self.env.ref('base_ter.ter_profile_01')):
                is_owner = True
            record.is_owner = is_owner
