# -*- coding: utf-8 -*-

from odoo import fields, models


class GeofoliaImportLine(models.Model):
    _name = "geofolia.import.line"
    _description = "Geofolia Import Line"
    _order = "id asc"

    job_id = fields.Many2one("geofolia.import.job", required=True, ondelete="cascade")
    import_type = fields.Selection(related="job_id.import_type", store=True, readonly=True)

    external_uuid = fields.Char()
    code = fields.Char()
    name = fields.Char()
    raw_json = fields.Json()
    raw_json_text = fields.Text()

    # Fields (plots)
    harvest_year = fields.Integer()
    area = fields.Float()
    city = fields.Char()
    crop_name = fields.Char()
    geography_wkt = fields.Text()

    # Products (supplies)
    supply_id = fields.Char()
    category_enum = fields.Integer()
    product_type_enum = fields.Integer()
    unit_symbol = fields.Char()
    botanical_species = fields.Char()
    variety_name = fields.Char()


class GeofoliaImportProductLine(models.Model):
    _name = "geofolia.import.product.line"
    _description = "Geofolia Import Product Line"
    _order = "id asc"

    job_id = fields.Many2one("geofolia.import.job", required=True, ondelete="cascade")
    farm_identification_code = fields.Char()
    external_id = fields.Char()
    code = fields.Char()
    name = fields.Char()
    category_enum = fields.Integer()
    product_type_enum = fields.Integer()
    unit_symbol = fields.Char()
    raw_json = fields.Json()
    raw_json_text = fields.Text()


class GeofoliaImportEmployeeLine(models.Model):
    _name = "geofolia.import.employee.line"
    _description = "Geofolia Import Employee Line"
    _order = "id asc"

    job_id = fields.Many2one("geofolia.import.job", required=True, ondelete="cascade")
    external_id = fields.Char()
    code = fields.Char()
    name = fields.Char()
    email = fields.Char()
    phone = fields.Char()
    raw_json = fields.Json()
    raw_json_text = fields.Text()


class GeofoliaImportPartnerLine(models.Model):
    _name = "geofolia.import.partner.line"
    _description = "Geofolia Import Partner Line"
    _order = "id asc"

    job_id = fields.Many2one("geofolia.import.job", required=True, ondelete="cascade")
    external_id = fields.Char()
    code = fields.Char()
    name = fields.Char()
    vat = fields.Char()
    raw_json = fields.Json()
    raw_json_text = fields.Text()


class GeofoliaImportHarvestedProductLine(models.Model):
    _name = "geofolia.import.harvested.product.line"
    _description = "Geofolia Import Harvested Product Line"
    _order = "id asc"

    job_id = fields.Many2one("geofolia.import.job", required=True, ondelete="cascade")
    external_id = fields.Char()
    code = fields.Char()
    name = fields.Char()
    unit_symbol = fields.Char()
    raw_json = fields.Json()
    raw_json_text = fields.Text()


class GeofoliaImportEquipmentLine(models.Model):
    _name = "geofolia.import.equipment.line"
    _description = "Geofolia Import Equipment Line"
    _order = "id asc"

    job_id = fields.Many2one("geofolia.import.job", required=True, ondelete="cascade")
    external_id = fields.Char()
    code = fields.Char()
    name = fields.Char()
    category = fields.Char()
    raw_json = fields.Json()
    raw_json_text = fields.Text()


class GeofoliaImportActivityLine(models.Model):
    _name = "geofolia.import.activity.line"
    _description = "Geofolia Import Activity Line"
    _order = "id asc"

    job_id = fields.Many2one("geofolia.import.job", required=True, ondelete="cascade")

    farm_identification_code = fields.Char()
    external_id = fields.Char()
    harvest_year = fields.Integer()

    operation_name = fields.Char()
    operation_category = fields.Char()

    status_name = fields.Char()
    status_code = fields.Char()

    starting_date = fields.Date()
    ending_date = fields.Date()
    start_time = fields.Char()
    finish_time = fields.Char()
    duration_minutes = fields.Integer()

    last_modification_dt = fields.Datetime()
    comment = fields.Text()

    raw_json = fields.Json()
    raw_json_text = fields.Text()
