# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
import socket
import xmlrpc.client
from odoo import fields, models, exceptions, api, _


class ResPartner(models.Model):
    _inherit = ["res.partner"]

    mapped_to_base = fields.Boolean(
        string="Mapped to Base",
        default=False,
        help="Indicates that this partner has been mapped to base instance.",
    )

    base_connection_host = fields.Char(
        string="Host",
        help="Host or IP address of the base instance. It must begin with 'http://' or 'https://'.",
    )

    base_connection_port = fields.Integer(
        string="Port",
        help="Port of the base instance.",
    )

    base_connection_company_id = fields.Integer(
        string="Base company ID",
        default=1,
        help="Company ID used in the base instance.",
    )

    base_connection_database = fields.Char(
        string="Database",
        help="Database name of the base instance.",
    )

    base_connection_username = fields.Char(
        string="Username",
        help="Username of the base instance.",
    )

    base_connection_password = fields.Char(
        string="Password",
        help="Password of the base instance.",
    )

    _sql_constraints = [
        ("base_connection_company_id_ok",
         "CHECK (base_connection_company_id > 0)",
         "The company ID must be a positive integer."),
    ]

    @api.constrains("base_connection_host")
    def _check_base_connection_host(self):
        # Verify that the host begins with http:// or https://
        if self.base_connection_host and not (
            self.base_connection_host.startswith("http://")
            or self.base_connection_host.startswith("https://")
        ):
            raise exceptions.ValidationError(
                _("The host must begin with 'http://' or 'https://' [%s]") % self.base_connection_database)
        # Remove trailing slash if exists
        if self.base_connection_host.endswith("/"):
            self.base_connection_host = self.base_connection_host[:-1]

    @api.constrains("base_connection_port")
    def _check_base_connection_port(self):
        if self.base_connection_port and (
            self.base_connection_port < 1
            or self.base_connection_port > 65535
        ):
            raise exceptions.ValidationError(
                _("The port must be between 0 (no port) and 65535 [%s]") % self.base_connection_database)

    def _get_port(self, host, port):
        if port != 0:
            port = port
        elif host and port == 0:
            if host.startswith("http://"):
                port = 80
            elif host.startswith("https://"):
                port = 443
        else:
            port = False
        return port

    def _get_connection_params(self):
        host = self.base_connection_host
        port = self._get_port(host, self.base_connection_port)
        company_id = self.base_connection_company_id
        database = self.base_connection_database
        username = self.base_connection_username
        user_password = self.base_connection_password
        if not all([host, database, username, user_password]):
            raise exceptions.UserError(
                _("Connection parameters to %s are not fully configured.") % self.name.strip())
        return host, port, company_id, database, username, user_password

    def _check_odoo_rpc_connection(self, host, port, timeout=10):
        try:
            host_clean = host.replace("http://", "").replace("https://", "")
            with socket.create_connection((host_clean, port), timeout=timeout):
                return True
        except Exception:
            raise exceptions.ValidationError(
                _("There is no connection to %s.") % self.name.strip())

    def _check_connection(self):
        # Get connection parameters
        host, port, company_id, database, username, user_password = self._get_connection_params()

        # Check connection to host/port
        self._check_odoo_rpc_connection(host, port)

        # Connect to the remote base entity and set uid models
        url = f"{host}:{port}"
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        try:
            uid = common.authenticate(database, username, user_password, {})
        except Exception:
            raise exceptions.UserError(_("The database %s does not exist [%s]") % (database, self.name.strip()))
        if not uid:
            raise exceptions.UserError(_("Authentication into database %s failed.") % database)
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

        # Verify than field 'general_code' exists in res.company model (check installed base module)
        company_fields = models.execute_kw(
            database, uid, user_password,
            "res.company", "fields_get",
            [['general_code']],
            {"attributes": ["name"]}
        )
        assert isinstance(company_fields, dict)
        if "general_code" not in company_fields:
            raise exceptions.UserError(
                _("The base module does not appear to be installed in the database %s.") % database)

        # Verify that the company exists
        company_ids = models.execute_kw(
            database, uid, user_password,
            "res.company", "search",
            [[["id", "=", company_id]]],
            {"limit": 1}
        )
        assert isinstance(company_ids, list)
        if not company_ids:
            raise exceptions.UserError(
                _("The company ID %s was not found in the database %s.") % (company_id, database))
        company_id = company_ids[0]

        return models, uid, user_password, database, company_id

    def map_base_entity(self, cronjob=False):
        # Verify connections before start mapping
        for record in self:
            if not record.mapped_to_base:
                continue
            models, uid, user_password, database, company_id = record._check_connection()

        # Notification
        notification_message = ""
        if not cronjob:
            notification_title = _("Mapping results")
            notification_type = "info"
            notification_sticky = False
            if len(self) > 1:
                notification_sticky = True

        # Mapping process
        for record in self:
            # Get connection parameters
            if not record.mapped_to_base:
                continue
            models, uid, user_password, database, company_id = record._check_connection()

            # Get partner code
            partner_code = record.partner_code
            if not partner_code:
                raise exceptions.UserError(_("Partner code is not set. Can not be mapped to base entity."))

            # Get Jinja2 template
            config = self.env["ir.config_parameter"].sudo()
            jinja2_template = config.get_param("base_ter_general.jinja2_template", False)
            if not jinja2_template:
                raise exceptions.UserError(_("Jinja2 template not configured in Territory parameters."))

            # Set company general_code in base entity
            models.execute_kw(
                database, uid, user_password,
                "res.company", "write",
                [company_id, {"general_code": record.partner_code}]
            )

            # Get info of parcels from base entity (call remote method)
            parcels_info = models.execute_kw(
                database, uid, user_password,
                "wua.parcel", "get_parcels_info_from_base_entity",
                [[], jinja2_template]
            )
            assert isinstance(parcels_info, list)

            # Logging
            _logger = logging.getLogger(self.__class__.__name__)
            _logger.info("Mapping: Base entity %s [%s]", record.name.strip(), partner_code)
            num_of_parcels_found = len(parcels_info)
            success_mapped = 0
            success_mapped_property_mismatch = 0
            parcel_not_found = 0
            failed_mapped = 0
            _logger.info("Mapping: Number of parcels found: %d", num_of_parcels_found)

            # Get general partner parcels (detect property mismatch)
            TerParcel = self.env["ter.parcel"]
            general_partner_parcels = []
            general_partner_properties = self.env['ter.property'].search([('partner_id', '=', record.id)])
            for general_partner_property in general_partner_properties:
                general_partner_property_parcels = TerParcel.search(
                    [('property_id', '=', general_partner_property.id)])
                for parcel in general_partner_property_parcels:
                    general_partner_parcels.append(parcel.name)

            # Update general parcels info
            for parcel in parcels_info:
                if "parcel_code" not in parcel or not parcel["parcel_code"]:
                    failed_mapped += 1
                    continue
                existing_parcel = TerParcel.search([("name", "=", parcel["parcel_code"])], limit=1)
                if not existing_parcel:
                    parcel_not_found += 1
                    continue
                if existing_parcel:
                    # Only set as mapped if property match
                    if existing_parcel.name not in general_partner_parcels:
                        success_mapped_property_mismatch += 1
                    else:
                        # Process partner_info
                        partner_info = parcel.get("partner_info", "")
                        if partner_info and partner_info.find('|') != -1:
                            partner_info = partner_info.replace('|', '\n')
                        # Update parcel
                        parcel_data = {
                            "name": parcel.get("parcel_code", ""),
                            "is_secondary": True,
                            "mapped_from_base": True,
                            "last_update": fields.Datetime.now(),
                            "partner_info": partner_info,
                        }
                        existing_parcel.write(parcel_data)
                        success_mapped += 1

            # Summary logging
            _logger.info("Mapping: Parcels successfully mapped: %d", success_mapped)
            if success_mapped_property_mismatch > 0:
                _logger.info("Mapping: Parcels mapped property mismatch: %d", success_mapped_property_mismatch)
                notification_type = "info"
            if parcel_not_found > 0:
                _logger.info("Mapping: Parcels not found: %d", parcel_not_found)
            if failed_mapped > 0:
                _logger.info("Mapping: Parcels failed to map: %d", failed_mapped)

            # Get successfully mapped parcels of the partner
            success_mapped_parcels = []
            for general_partner_property in general_partner_properties:
                general_partner_property_parcels = self.env['ter.parcel'].search(
                    [('property_id', '=', general_partner_property.id), ('mapped_from_base', '=', 'True')])
                for parcel in general_partner_property_parcels:
                    success_mapped_parcels.append(parcel.name)

            # Update mapped successfully parcels in base entity (call remote method)
            base_mapping_results = models.execute_kw(
                database, uid, user_password,
                "wua.parcel", "set_parcel_info_to_base_entity",
                [[], success_mapped_parcels]
            )
            assert isinstance(base_mapping_results, list)
            if base_mapping_results:
                success_mapped_in_base_entity, failed_mapped_in_base_entity = base_mapping_results
            else:
                success_mapped_in_base_entity, failed_mapped_in_base_entity = 0, 0
            assert isinstance(success_mapped_in_base_entity, int)
            assert isinstance(failed_mapped_in_base_entity, int)
            _logger.info("Mapping: Parcels mapped in base entity: %d", success_mapped_in_base_entity)
            if failed_mapped_in_base_entity > 0:
                _logger.info("Mapping: Parcels failed to map in base entity: %d", failed_mapped_in_base_entity)

            # Post message in the partner chatter
            message_log = _("<b>Scan results</b>")
            message_log += _("<br/>· Parcels found in base entity: %d") % num_of_parcels_found
            if success_mapped > 0:
                message_log += _("<br/>· Parcels successfully mapped: %d") % success_mapped
            if success_mapped_property_mismatch > 0:
                message_log += _("<br/>· Parcels mapped property mismatch: %d") % success_mapped_property_mismatch
            if parcel_not_found > 0:
                message_log += _("<br/>· Parcels not found in general entity: %d") % parcel_not_found
            if failed_mapped > 0:
                message_log += _("<br/>· Parcels failed to scan: %d") % failed_mapped
            message_log += _("<br/><br/><b>Mapping results</b>")
            if success_mapped_in_base_entity > 0:
                message_log += _("<br/>· Parcels successfully mapped in base entity: %d") \
                    % success_mapped_in_base_entity
            if failed_mapped_in_base_entity > 0:
                message_log += _("<br/>· Parcels failed to map in base entity: %d") % failed_mapped_in_base_entity
            record.message_post(body=message_log)

            # Notification
            if not cronjob:
                big_space = "\u3000" * 10
                if len(self) > 1:
                    notification_message += "· "
                notification_message += f"%s [%d/%d]{big_space}" % \
                    (record.name, success_mapped_in_base_entity, num_of_parcels_found)

        # Notify user
        if not cronjob:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": notification_title,
                    "message": notification_message,
                    "sticky": notification_sticky,
                    "type": notification_type,
                }
            }
        else:
            return True

    def map_base_entity_cron(self):
        primary_partners = self.env["res.partner"].search([("mapped_to_base", "=", True)])
        admin_lang = self.env['res.users'].browse(2).lang or 'es_ES'
        for partner in primary_partners:
            job_description = _("Mapping %s") % partner.name
            partner.with_context(lang=admin_lang).with_delay(
                description=job_description).map_base_entity(cronjob=True)
