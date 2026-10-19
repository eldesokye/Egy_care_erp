# -*- coding: utf-8 -*-
# Egy Care Tickets - editable master data models (Ticket Source / Ticket Type).
# Stored as models (not hardcoded Selections) so the lists can be maintained
# from the Configuration menu without any code change.
from odoo import fields, models


class EgyCareTicketSource(models.Model):
    _name = 'egy.care.ticket.source'
    _description = 'Egy Care Ticket Source'
    _order = 'sequence, name'

    name = fields.Char(string='Source Name', required=True)
    code = fields.Char(
        string='Code',
        help='Technical code used by integrations and imports (phone, email, ...).')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Internal Description')

    _source_name_unique = models.Constraint(
        'UNIQUE(name)',
        'The ticket source name must be unique!',
    )


class EgyCareTicketType(models.Model):
    _name = 'egy.care.ticket.type'
    _description = 'Egy Care Ticket Type'
    _order = 'sequence, name'

    name = fields.Char(string='Type Name', required=True)
    code = fields.Char(
        string='Code',
        help='Technical code used by integrations and imports.')
    category = fields.Selection(
        [('pharmacy', 'Pharmacy'),
         ('non_pharmacy', 'Non-Pharmacy')],
        string='Category',
        default='non_pharmacy',
        index=True,
        required=True,
        help='Used by the Dashboard KPI cards (Pharmacy / Non-Pharmacy).')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Internal Description')

    _type_name_unique = models.Constraint(
        'UNIQUE(name)',
        'The ticket type name must be unique!',
    )
