# -*- coding: utf-8 -*-
{
    'name': 'Egy Care Tickets',
    'version': '20.0.2.3.0',
    'category': 'Egy Care',
    'summary': 'Egy Care ticketing system - Create Ticket, Ticket Details, My Queue, Dashboard and Manage Users',
    'description': """
Egy Care Tickets
================
Standalone ticketing application built for Egy Care on Odoo 20 (Community, no
Enterprise dependencies).

Screens implemented (UI phase, mapped 1:1 from the PDF mock-ups)
----------------------------------------------------------------
1. Create Ticket - 3-column creation form (labels above fields)
2. Ticket Details - info cards, tabs (details / attachments / queue & SLA /
   beneficiary history), workflow buttons
3. My Queue - KPI cards (Pending, Assigned, In Progress, VIP, Waiting) above a
   live queue list; cards act as filters
4. Dashboard - KPI cards (Total Queued, Pharmacy, Non-Pharmacy, In Progress,
   VIP, Manual, Mobile App) above the queued tickets list
5. Manage Users - agent roster with shifts, breaks and workload counters

Foundation
----------
- Beneficiary registry with auto-generated unique card numbers (EGC-xxxxx)
- Ticket sources and ticket types as editable master data (with Pharmacy /
  Non-Pharmacy categories)
- Round-robin auto assignment among active agents
- VIP handling (auto-detected from the beneficiary + manual override)
- Attachment limits (max 15, min 1) and Email CC limits (max 10)
- Full chatter / activity tracking on tickets and beneficiaries

The workflow buttons (Send To Co-Ordinator, Assign, Create Sub-Ticket, ...)
show a friendly placeholder notification: their business logic is planned for
the logic phase of the project.
""",
    'author': 'Egy Care',
    'website': 'https://www.egycare.com',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        # MUST stay first: refuses duplicate-copy installs (two folders = two
        # technical module names = crash on unique constraints) with a clear
        # error before any other data is loaded.
        'data/egy_care_install_guard.xml',
        'security/egy_care_security.xml',
        'security/ir.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_config_parameter_data.xml',
        'data/egy_care_source_data.xml',
        'data/egy_care_type_data.xml',
        'data/egy_care_master_data_update.xml',
        'views/egy_care_ticket_views.xml',
        'views/egy_care_beneficiary_views.xml',
        'views/egy_care_config_views.xml',
        'views/res_users_views.xml',
        'views/egy_care_menus.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'egy_care_tickets/static/src/board/egy_care_board.js',
            'egy_care_tickets/static/src/scss/egy_care.scss',
        ],
    },
    'application': True,
    'installable': True,
}
