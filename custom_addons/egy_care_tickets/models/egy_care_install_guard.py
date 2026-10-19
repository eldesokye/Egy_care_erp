# -*- coding: utf-8 -*-
# Egy Care Tickets - duplicate-install guard.
#
# Odoo uses the add-ons FOLDER name as the technical module name. Keeping two
# copies of this suite in custom_addons under two folder names therefore
# creates two different modules that re-declare the same models, menus and
# master data: the second install always ends in unique-constraint crashes
# (ir_config_parameter_key_uniq, egy_care_ticket_source_source_name_unique,
# ...) or in silently duplicated menus, groups and sequences.
#
# This guard runs as the FIRST data file of the module and turns that
# situation into one clear, actionable error message before any other data
# is loaded.
#
# NOTE: the name pattern intentionally covers the whole "egy_care_tickets*"
# family. If the suite is ever split into several add-on modules, adjust the
# pattern (e.g. 'egy_care%') together with this comment.
from odoo import api, models
from odoo.exceptions import UserError

_SUITE_PATTERN = 'egy_care_tickets%'


class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    @api.model
    def _egy_guard_single_install(self):
        """Refuse to load when a sibling copy of the suite is already
        installed or queued in this database.

        Exactly one ``egy_care_tickets*`` module record may be in an active
        state (to install / to upgrade / installed): the one being loaded
        right now. More than one means a duplicate folder copy is being
        installed over an existing one. Merely having an extra uninstalled
        folder on disk is harmless and does not trigger the guard.
        """
        copies = self.sudo().search([
            ('name', '=ilike', _SUITE_PATTERN),
            ('state', 'in', ('installed', 'to upgrade', 'to install')),
        ])
        if len(copies) < 2:
            return
        names = ', '.join(sorted(copies.mapped('name')))
        raise UserError(self.env._(
            'Two copies of the Egy Care Tickets suite are active in this '
            'database: %s.\n'
            'Odoo treats every folder in your add-ons path as a separate '
            'module, so the same module can never be installed twice under '
            'two folder names.\n\n'
            'How to fix:\n'
            '1. Keep ONE folder (recommended: custom_addons/egy_care_tickets) '
            'and delete the duplicate folder.\n'
            '2. Restart the Odoo server and press "Update Apps List".\n'
            '3. Open Egy Care Tickets in Apps and press Upgrade - an '
            'installed module never needs Install again.',
            names,
        ))
