# -*- coding: utf-8 -*-
# Egy Care Tickets - automated tests.
# Run with:
#   ./odoo-bin -c odoo.conf -d <db> -i egy_care_tickets \
#       --test-tags /egy_care_tickets --stop-after-init
import base64
from datetime import timedelta

from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestEgyCareTicket(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users'].with_context(
            no_reset_password=True, mail_create_nosubscribe=True)
        agent_group = cls.env.ref('egy_care_tickets.group_egy_care_agent')
        cls.agent_a = Users.create({
            'name': 'Agent A',
            'login': 'agent_a_test',
            'email': 'agent_a@example.com',
            'group_ids': [Command.link(agent_group.id)],
        })
        cls.agent_b = Users.create({
            'name': 'Agent B',
            'login': 'agent_b_test',
            'email': 'agent_b@example.com',
            'group_ids': [Command.link(agent_group.id)],
        })
        cls.beneficiary = cls.env['egy.care.beneficiary'].create({
            'name': 'Ahmed Test',
            'is_vip': True,
        })

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _attachment(self, name='test-file.txt'):
        return Command.create({
            'name': name,
            'datas': base64.b64encode(b'Egy Care test file content'),
        })

    def _ticket_vals(self, **kwargs):
        vals = {
            'beneficiary_id': self.beneficiary.id,
            'source_id': self.env.ref('egy_care_tickets.source_email').id,
            'type_id': self.env.ref('egy_care_tickets.type_complaint').id,
            'description': 'Test ticket description',
            'auto_assign': False,
            'attachment_ids': [self._attachment()],
        }
        vals.update(kwargs)
        return vals

    # ------------------------------------------------------------------
    # Sequences
    # ------------------------------------------------------------------
    def test_beneficiary_card_sequence(self):
        self.assertTrue(
            self.beneficiary.card_no.startswith('EGC-'),
            'Beneficiary card no must be auto-generated with the EGC- prefix')
        other = self.env['egy.care.beneficiary'].create({'name': 'Second'})
        self.assertNotEqual(other.card_no, self.beneficiary.card_no)

    def test_ticket_number_sequence(self):
        ticket = self.env['egy.care.ticket'].create(self._ticket_vals())
        self.assertTrue(ticket.ticket_no.startswith('EC/'))
        self.assertIn(str(fields.Date.today().year), ticket.ticket_no)

    # ------------------------------------------------------------------
    # Auto assignment (round-robin)
    # ------------------------------------------------------------------
    def test_auto_assign_round_robin(self):
        Ticket = self.env['egy.care.ticket']
        t1 = Ticket.create(self._ticket_vals(auto_assign=True))
        t2 = Ticket.create(self._ticket_vals(auto_assign=True))
        t3 = Ticket.create(self._ticket_vals(auto_assign=True))
        self.assertEqual(t1.user_id, self.agent_a)
        self.assertEqual(t2.user_id, self.agent_b)
        self.assertEqual(t3.user_id, self.agent_a)
        self.assertTrue(t1.assigned_on)

    def test_auto_assign_no_agent(self):
        # Remove both agents from the group: auto-assign must not crash.
        group = self.env.ref('egy_care_tickets.group_egy_care_agent')
        group.write({'user_ids': [Command.unlink(self.agent_a.id),
                                  Command.unlink(self.agent_b.id)]})
        try:
            ticket = self.env['egy.care.ticket'].create(
                self._ticket_vals(auto_assign=True))
            self.assertFalse(ticket.user_id)
        finally:
            group.write({'user_ids': [Command.link(self.agent_a.id),
                                      Command.link(self.agent_b.id)]})

    # ------------------------------------------------------------------
    # Attachment limits (min 1 / max 15 by default)
    # ------------------------------------------------------------------
    def test_attachments_required(self):
        with self.assertRaises(ValidationError):
            self.env['egy.care.ticket'].create(
                self._ticket_vals(attachment_ids=[]))

    def test_attachments_max_15(self):
        with self.assertRaises(ValidationError):
            self.env['egy.care.ticket'].create(self._ticket_vals(
                attachment_ids=[self._attachment('f%s.txt' % i)
                                for i in range(16)]))
        ticket = self.env['egy.care.ticket'].create(self._ticket_vals(
            attachment_ids=[self._attachment('f%s.txt' % i)
                            for i in range(15)]))
        self.assertEqual(len(ticket.attachment_ids), 15)

    # ------------------------------------------------------------------
    # Email / Email CC limits
    # ------------------------------------------------------------------
    def test_email_cc_max_10(self):
        ten = ', '.join('cc%s@mail.com' % i for i in range(10))
        eleven = ', '.join('cc%s@mail.com' % i for i in range(11))
        ticket = self.env['egy.care.ticket'].create(
            self._ticket_vals(email_cc=ten))
        self.assertTrue(ticket.email_cc)
        with self.assertRaises(ValidationError):
            self.env['egy.care.ticket'].create(
                self._ticket_vals(email_cc=eleven))

    def test_invalid_email(self):
        with self.assertRaises(ValidationError):
            self.env['egy.care.ticket'].create(
                self._ticket_vals(email='not-an-email'))

    # ------------------------------------------------------------------
    # VIP handling
    # ------------------------------------------------------------------
    def test_vip_from_beneficiary(self):
        # Beneficiary is VIP: API-created tickets inherit the flag + priority.
        ticket = self.env['egy.care.ticket'].create(self._ticket_vals())
        self.assertTrue(ticket.vip_ticket)
        self.assertEqual(ticket.priority, '1')

    def test_vip_manual_override(self):
        ticket = self.env['egy.care.ticket'].create(self._ticket_vals(
            vip_ticket=False))
        self.assertFalse(ticket.vip_ticket)

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------
    def test_state_workflow(self):
        ticket = self.env['egy.care.ticket'].create(self._ticket_vals())
        self.assertEqual(ticket.state, 'draft')

        ticket.action_start()
        self.assertEqual(ticket.state, 'in_progress')

        ticket.action_hold()
        self.assertEqual(ticket.state, 'on_hold')

        ticket.action_resolve()
        self.assertEqual(ticket.state, 'resolved')

        ticket.action_close()
        self.assertEqual(ticket.state, 'closed')
        self.assertTrue(ticket.closed_on)

        ticket.action_reopen()
        self.assertEqual(ticket.state, 'in_progress')
        self.assertFalse(ticket.closed_on)

    def test_illegal_transition(self):
        ticket = self.env['egy.care.ticket'].create(self._ticket_vals())
        # Cannot close a draft ticket directly.
        with self.assertRaises(Exception):
            ticket.action_close()

    # ------------------------------------------------------------------
    # Screens 2-5 UI fields (v2)
    # ------------------------------------------------------------------
    def test_queue_status_default(self):
        ticket = self.env['egy.care.ticket'].create(self._ticket_vals())
        self.assertEqual(ticket.queue_status, 'pending')
        self.assertEqual(ticket.agreed_sla, 120)
        self.assertEqual(ticket.agreed_ola, 15)
        self.assertTrue(ticket.received_at)
        self.assertEqual(ticket.card_no, self.beneficiary.card_no)

    def test_ticket_aging(self):
        Ticket = self.env['egy.care.ticket']
        ticket = Ticket.create(self._ticket_vals(
            received_at=fields.Datetime.now()))
        self.assertEqual(ticket.ticket_aging, '0:0:0:0')
        eighty_five_min_ago = fields.Datetime.now() - timedelta(minutes=85)
        ticket.received_at = eighty_five_min_ago
        self.assertTrue(ticket.ticket_aging.startswith('0:1:2'),
                        'Aging for 85 minutes must be 0:1:2x:x, got %s'
                        % ticket.ticket_aging)

    def test_due_date_from_agreed_sla(self):
        Ticket = self.env['egy.care.ticket']
        ticket = Ticket.new(self._ticket_vals())
        ticket.received_at = fields.Datetime.now()
        ticket.agreed_sla = 120
        ticket._onchange_due_date()
        self.assertTrue(ticket.due_date)
        delta = ticket.due_date - ticket.received_at
        self.assertAlmostEqual(delta.total_seconds(), 120 * 60, delta=60)

    def test_ui_todo_notification(self):
        ticket = self.env['egy.care.ticket'].create(self._ticket_vals())
        action = ticket.action_assign_ticket()
        self.assertEqual(action['type'], 'ir.actions.client')
        self.assertEqual(action['tag'], 'display_notification')
