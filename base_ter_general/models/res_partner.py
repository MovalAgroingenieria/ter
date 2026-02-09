# 2024-2026 Moval Agroingeniería
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
# pylint: disable=translation-not-lazy

import logging
import socket
import xmlrpc.client

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    mapped_to_base = fields.Boolean(
        default=False,
        help="Indicates whether this partner is mapped to the base instance.",
    )
    base_connection_host = fields.Char(
        help="Base instance host or IP. It must start with http:// or https://.",
    )
    base_connection_port = fields.Integer(
        help="Base instance port. Use 0 to rely on the scheme default.",
    )
    base_connection_company_id = fields.Integer(
        default=1,
        help="Company ID used in the base instance.",
    )
    base_connection_database = fields.Char(
        help="Base instance database name.",
    )
    base_connection_username = fields.Char(
        help="Base instance username.",
    )
    base_connection_password = fields.Char(
        help="Base instance password.",
    )

    _sql_constraints = [
        (
            "base_connection_company_id_ok",
            "CHECK (base_connection_company_id > 0)",
            "The company ID must be a positive integer.",
        ),
    ]

    @api.constrains("base_connection_host")
    def _check_base_connection_host(self):
        for record in self:
            if not record.base_connection_host:
                continue
            host = record.base_connection_host.strip()
            if not (host.startswith("http://") or host.startswith("https://")):
                raise ValidationError(
                    record.env._(
                        "The host must start with 'http://' or 'https://' [%(db)s]"
                    )
                    % {"db": record.base_connection_database or ""}
                )

    def write(self, vals):
        if "base_connection_host" in vals and vals["base_connection_host"]:
            host = vals["base_connection_host"].strip()
            vals["base_connection_host"] = host.rstrip("/")
        return super().write(vals)

    @api.constrains("base_connection_port")
    def _check_base_connection_port(self):
        for record in self:
            if record.base_connection_port and not (
                1 <= record.base_connection_port <= 65535
            ):
                raise ValidationError(
                    record.env._("The port must be between 1 and 65535 [%(db)s]")
                    % {"db": record.base_connection_database or ""}
                )

    def _get_port(self, host, port):
        if port:
            return port
        if not host:
            return False
        if host.startswith("http://"):
            return 80
        if host.startswith("https://"):
            return 443
        return False

    def _get_connection_params(self):
        self.ensure_one()
        host = self.base_connection_host
        port = self._get_port(host, self.base_connection_port or 0)
        company_id = self.base_connection_company_id
        database = self.base_connection_database
        username = self.base_connection_username
        password = self.base_connection_password
        if not all([host, database, username, password]):
            raise UserError(
                self.env._(
                    "Connection parameters to %(name)s are not fully configured."
                )
                % {"name": self.display_name.strip()}
            )
        return host, port, company_id, database, username, password

    def _check_odoo_rpc_connection(self, host, port, timeout=10):
        self.ensure_one()
        try:
            host_clean = host.replace("http://", "").replace("https://", "")
            with socket.create_connection((host_clean, port), timeout=timeout):
                return True
        except OSError as exc:
            raise ValidationError(
                self.env._("There is no connection to %(name)s.")
                % {"name": self.display_name.strip()}
            ) from exc

    def _check_connection(self):
        self.ensure_one()

        host, port, company_id, database, username, password = (
            self._get_connection_params()
        )

        self._check_odoo_rpc_connection(host, port)

        url = f"{host}:{port}"
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")

        try:
            uid = common.authenticate(database, username, password, {})
        except Exception as exc:
            raise UserError(
                self.env._("The database %(database)s does not exist [%(name)s]")
                % {"database": database, "name": self.display_name.strip()}
            ) from exc

        if not uid:
            raise UserError(
                self.env._("Authentication into database %(database)s failed.")
                % {"database": database}
            )

        rpc_models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

        company_fields = rpc_models.execute_kw(
            database,
            uid,
            password,
            "res.company",
            "fields_get",
            [["general_code"]],
            {"attributes": ["name"]},
        )
        if "general_code" not in company_fields:
            raise UserError(
                self.env._(
                    "The base module does not appear to be installed "
                    "in the database %(database)s."
                )
                % {"database": database}
            )

        company_ids = rpc_models.execute_kw(
            database,
            uid,
            password,
            "res.company",
            "search",
            [[["id", "=", company_id]]],
            {"limit": 1},
        )
        if not company_ids:
            raise UserError(
                self.env._(
                    "The company ID %(company_id)s was not found "
                    "in the database %(database)s."
                )
                % {"company_id": company_id, "database": database}
            )

        return rpc_models, uid, password, database, company_ids[0]

    def map_base_entity(  # noqa: C901
        self, cronjob=False
    ):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        for record in self:
            if record.mapped_to_base:
                record._check_connection()  # pylint: disable=protected-access

        notification_message = ""
        notification_title = self.env._("Mapping results")
        notification_type = "info"
        notification_sticky = len(self) > 1

        ter_parcel_model = self.env["ter.parcel"]
        config = self.env["ir.config_parameter"].sudo()

        for record in self:
            if not record.mapped_to_base:
                continue

            rpc_models, uid, password, database, company_id = (
                record._check_connection()  # pylint: disable=protected-access
            )

            partner_code = record.partner_code
            if not partner_code:
                raise UserError(
                    record.env._("Partner code is not set. It cannot be mapped.")
                )

            jinja2_template = config.get_param("base_ter_general.jinja2_template") or ""
            if not jinja2_template:
                raise UserError(record.env._("Jinja2 template is not configured."))

            rpc_models.execute_kw(
                database,
                uid,
                password,
                "res.company",
                "write",
                [company_id, {"general_code": partner_code}],
            )

            parcels_info = (
                rpc_models.execute_kw(
                    database,
                    uid,
                    password,
                    "wua.parcel",
                    "get_parcels_info_from_base_entity",
                    [[], jinja2_template],
                )
                or []
            )
            num_of_parcels_found = len(parcels_info)

            _logger.info(
                "Mapping base entity %s [%s] - parcels found: %d",
                record.display_name.strip(),
                partner_code,
                num_of_parcels_found,
            )

            general_partner_properties = self.env["ter.property"].search(
                [("partner_id", "=", record.id)]
            )
            general_partner_parcels = set(
                ter_parcel_model.search(
                    [("property_id", "in", general_partner_properties.ids)]
                ).mapped("name")
            )

            success_mapped = 0
            success_mapped_property_mismatch = 0
            parcel_not_found = 0
            failed_mapped = 0

            for parcel in parcels_info:
                parcel_code = parcel.get("parcel_code") or ""
                if not parcel_code:
                    failed_mapped += 1
                    continue

                existing_parcel = ter_parcel_model.search(
                    [("name", "=", parcel_code)], limit=1
                )
                if not existing_parcel:
                    parcel_not_found += 1
                    continue

                if existing_parcel.name not in general_partner_parcels:
                    success_mapped_property_mismatch += 1
                    continue

                partner_info = parcel.get("partner_info") or ""
                if "|" in partner_info:
                    partner_info = partner_info.replace("|", "\n")

                existing_parcel.write(
                    {
                        "is_secondary": True,
                        "mapped_from_base": True,
                        "last_update": fields.Datetime.now(),
                        "partner_info": partner_info,
                    }
                )
                success_mapped += 1

            _logger.info("Mapping parcels successfully mapped: %d", success_mapped)
            if success_mapped_property_mismatch:
                _logger.info(
                    "Mapping parcels property mismatch: %d",
                    success_mapped_property_mismatch,
                )
            if parcel_not_found:
                _logger.info("Mapping parcels not found: %d", parcel_not_found)
            if failed_mapped:
                _logger.info("Mapping parcels failed: %d", failed_mapped)

            success_mapped_parcels = ter_parcel_model.search(
                [
                    ("property_id", "in", general_partner_properties.ids),
                    ("mapped_from_base", "=", True),
                ]
            ).mapped("name")

            base_mapping_results = (
                rpc_models.execute_kw(
                    database,
                    uid,
                    password,
                    "wua.parcel",
                    "set_parcel_info_to_base_entity",
                    [[], success_mapped_parcels],
                )
                or []
            )

            if base_mapping_results:
                success_mapped_in_base, failed_mapped_in_base = base_mapping_results
            else:
                success_mapped_in_base, failed_mapped_in_base = 0, 0

            _logger.info(
                "Mapping parcels mapped in base entity: %d", success_mapped_in_base
            )
            if failed_mapped_in_base:
                _logger.info(
                    "Mapping parcels failed to map in base entity: %d",
                    failed_mapped_in_base,
                )

            message_log = record.env._("<b>Scan results</b>")
            message_log += record.env._(
                "<br/>· Parcels found in base entity: %(n)d"
            ) % {"n": num_of_parcels_found}
            if success_mapped:
                message_log += record.env._(
                    "<br/>· Parcels successfully mapped: %(n)d"
                ) % {"n": success_mapped}
            if success_mapped_property_mismatch:
                message_log += record.env._(
                    "<br/>· Parcels property mismatch: %(n)d"
                ) % {"n": success_mapped_property_mismatch}
            if parcel_not_found:
                message_log += record.env._(
                    "<br/>· Parcels not found in general entity: %(n)d"
                ) % {"n": parcel_not_found}
            if failed_mapped:
                message_log += record.env._("<br/>· Parcels failed to scan: %(n)d") % {
                    "n": failed_mapped
                }
            message_log += record.env._("<br/><br/><b>Mapping results</b>")
            if success_mapped_in_base:
                message_log += record.env._(
                    "<br/>· Parcels mapped in base entity: %(n)d"
                ) % {"n": success_mapped_in_base}
            if failed_mapped_in_base:
                message_log += record.env._(
                    "<br/>· Parcels failed to map in base entity: %(n)d"
                ) % {"n": failed_mapped_in_base}
            record.message_post(body=message_log)

            if not cronjob:
                if len(self) > 1:
                    notification_message += "· "
                notification_message += "%s [%d/%d]    " % (
                    record.display_name,
                    success_mapped_in_base,
                    num_of_parcels_found,
                )

        if cronjob:
            return True

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": notification_title,
                "message": notification_message,
                "sticky": notification_sticky,
                "type": notification_type,
            },
        }

    def map_base_entity_cron(self):
        partners = self.search([("mapped_to_base", "=", True)])
        admin_lang = self.env.ref("base.user_admin").lang or "en_US"
        for partner in partners:
            job_desc_tpl = partner.env._("Mapping %(name)s")
            job_description = job_desc_tpl % {"name": partner.display_name}
            partner.with_context(lang=admin_lang).with_delay(
                description=job_description
            ).map_base_entity(cronjob=True)
