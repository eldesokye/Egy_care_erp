# -*- coding: utf-8 -*-
# Egy Care Tickets - Beneficiary registry.
# Every ticket belongs to a beneficiary. The beneficiary carries the unique
# Card No (auto-generated), the contact details and the VIP flag, and is
# reused by the remaining screens of the Egy Care suite.
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class EgyCareBeneficiary(models.Model):
    _name = 'egy.care.beneficiary'
    _description = 'Egy Care Beneficiary'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc, id desc'
    # Allow searching the beneficiary (Card No m2o dropdown) by name AND card no.
    _rec_names_search = ['name', 'card_no']

    card_no = fields.Char(
        string='Card No',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('New'),
        help='Unique membership card number. Generated automatically '
             '(EGC-00001, EGC-00002, ...).')
    name = fields.Char(string='Beneficiary Name', required=True, tracking=True)
    company_name = fields.Char(string='Company')
    phone = fields.Char(string='Phone / WhatsApp')
    email = fields.Char(string='Email')
    fax = fields.Char(string='Fax No')
    is_vip = fields.Boolean(
        string='VIP',
        tracking=True,
        help='VIP beneficiaries automatically create VIP tickets '
             '(high priority + gold badge). Agents can still override '
             'the flag on a specific ticket.')
    notes = fields.Text(string='Internal Notes')
    active = fields.Boolean(string='Active', default=True)

    ticket_ids = fields.One2many(
        'egy.care.ticket', 'beneficiary_id', string='Ticket History')
    ticket_count = fields.Integer(
        string='Tickets', compute='_compute_ticket_count')

    _card_no_unique = models.Constraint(
        'UNIQUE(card_no)',
        'The Card No must be unique per beneficiary!',
    )

    @api.depends('ticket_ids')
    def _compute_ticket_count(self):
        for beneficiary in self:
            beneficiary.ticket_count = len(beneficiary.ticket_ids)

    @api.depends('card_no', 'name')
    def _compute_display_name(self):
        """Show '[EGC-00001] Ahmed Hassan' everywhere the beneficiary is
        referenced, so agents can pick a beneficiary directly by Card No
        inside the 'Card No' dropdown of the Create Ticket screen."""
        for beneficiary in self:
            beneficiary.display_name = '[%s] %s' % (
                beneficiary.card_no or _('New'), beneficiary.name or '')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('card_no') or vals['card_no'] == _('New'):
                vals['card_no'] = self.env['ir.sequence'].sudo().next_by_code(
                    'egy.care.beneficiary.card') or _('New')
        return super().create(vals_list)

    def unlink(self):
        if any(b.ticket_ids for b in self):
            raise UserError(_(
                'You cannot delete a beneficiary that already has tickets. '
                'Archive it instead.'))
        return super().unlink()

    def action_view_tickets(self):
        """Smart button: open all tickets of this beneficiary."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'egy_care_tickets.action_egy_care_ticket')
        action['domain'] = [('beneficiary_id', '=', self.id)]
        action['context'] = {
            'default_beneficiary_id': self.id,
            'default_source_id': False,
        }
        return action
