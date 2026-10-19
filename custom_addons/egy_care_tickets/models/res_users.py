# -*- coding: utf-8 -*-
# Egy Care Tickets - res.users extensions.
# - egy_ticket_last_assigned_on: round-robin pointer used by the auto-assign
#   engine (agent with the oldest pointer receives the next ticket).
# - is_egy_agent / egy_open_ticket_count: used by the Assign To dropdown and
#   the Manage Users screen.
from odoo import api, fields, models

EPOCH = fields.Datetime.to_datetime('1970-01-01')


class ResUsers(models.Model):
    _inherit = 'res.users'

    egy_ticket_last_assigned_on = fields.Datetime(
        string='Last Ticket Auto-Assigned On',
        copy=False,
        default=False,
        help='Round-robin pointer: the auto-assign engine gives the next '
             'ticket to the agent with the oldest value.')

    is_egy_agent = fields.Boolean(
        string='Egy Care Agent',
        compute='_compute_is_egy_agent',
        search='_search_is_egy_agent',
        help='Technical field: user belongs to the Egy Care Agent group.')

    egy_open_ticket_count = fields.Integer(
        string='Open Tickets',
        compute='_compute_egy_open_ticket_count')

    # ------------------------------------------------------------------
    # Manage Users screen (UI phase - fields displayed on the mock-up)
    # ------------------------------------------------------------------
    egy_user_type = fields.Selection(
        [('doctor', 'Doctor'),
         ('coordinator', 'Co-Ordinator'),
         ('pharmacist', 'Pharmacist'),
         ('agent', 'Agent'),
         ('other', 'Other')],
        string='User Type',
        default='agent',
        help='Role of the user inside the Egy Care ticketing flow.')
    egy_shift_start = fields.Datetime(
        string='Start Shift Time',
        help='Start date and time of the current shift.')
    egy_on_break = fields.Boolean(
        string='On Break',
        help='Displayed as "In Break" on the Manage Users screen.')
    egy_in_progress_ticket_no = fields.Char(
        string='In Progress Ticket No.',
        compute='_compute_egy_workload')
    egy_assigned_ticket_count = fields.Integer(
        string='Assigned Tickets',
        compute='_compute_egy_workload')
    egy_resolved_ticket_count = fields.Integer(
        string='Resolved Tickets',
        compute='_compute_egy_workload')

    def _compute_is_egy_agent(self):
        group = self.env.ref('egy_care_tickets.group_egy_care_agent')
        group_user_ids = group.user_ids.ids if group else []
        for user in self:
            user.is_egy_agent = user.id in group_user_ids

    def _search_is_egy_agent(self, operator, value):
        group = self.env.ref('egy_care_tickets.group_egy_care_agent')
        positive = (
            (operator in ('=', 'in') and value)
            or (operator in ('!=', 'not in') and not value)
        )
        if positive:
            return [('group_ids', 'in', group.ids)]
        return ['!', ('group_ids', 'in', group.ids)]

    def _compute_egy_open_ticket_count(self):
        for user in self:
            user.egy_open_ticket_count = self.env['egy.care.ticket'].search_count([
                ('user_id', '=', user.id),
                ('state', 'in', ('draft', 'in_progress', 'on_hold')),
            ])

    def _compute_egy_workload(self):
        """Workload figures displayed on the Manage Users screen."""
        Ticket = self.env['egy.care.ticket']
        for user in self:
            in_progress = Ticket.search(
                [('user_id', '=', user.id), ('state', '=', 'in_progress')],
                limit=1, order='id desc')
            user.egy_in_progress_ticket_no = in_progress.ticket_no
            user.egy_assigned_ticket_count = Ticket.search_count([
                ('user_id', '=', user.id),
                ('state', 'in', ('draft', 'in_progress', 'on_hold')),
            ])
            user.egy_resolved_ticket_count = Ticket.search_count([
                ('user_id', '=', user.id),
                ('state', 'in', ('resolved', 'closed')),
            ])

    # ------------------------------------------------------------------
    # Manage Users screen actions (the two buttons of each row)
    # ------------------------------------------------------------------
    def action_view_egy_tickets(self):
        """"Tickets" action button: open the tickets handled by this user."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'egy_care_tickets.action_egy_care_ticket')
        action['name'] = _('%s Tickets', self.name or _('User'))
        action['domain'] = [('user_id', '=', self.id)]
        action['context'] = {'default_user_id': self.id}
        return action

    def action_open_egy_profile(self):
        """"Profile" action button: open the user form."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name or _('User'),
            'res_model': 'res.users',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def _egy_care_get_next_agent(self):
        """Round-robin: return the active agent whose last auto-assignment
        is the oldest (never-assigned agents first, then by user id)."""
        group = self.env.ref('egy_care_tickets.group_egy_care_agent')
        agents = group.user_ids.filtered(
            lambda u: u.active and not u.share) if group else self.browse()
        if not agents:
            return self.browse()
        return min(
            agents,
            key=lambda u: (u.egy_ticket_last_assigned_on or EPOCH, u.id))
