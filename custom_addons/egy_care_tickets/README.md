# Egy Care Tickets — Odoo 20 Module

Screens 1-5 of the Egy Care suite — **Create Ticket, Ticket Details, My Queue,
Dashboard and Manage Users** — implemented as a fully standalone Odoo 20
application (Community source, zero Enterprise dependencies), mapped 1:1 from
the PDF mock-ups. This module is the foundation the remaining 4 screens build
on.

---

## 1. Screens delivered (v2, version 20.0.2.0.0)

| PDF screen | Odoo implementation |
|---|---|
| **Create Ticket** | Dedicated creation form `view_egy_care_ticket_form`: row-wise 3-column grid (Card No / Beneficiary Name / Company → Source / Type / Fax → Phone / Email / Attachments → Email CC / Assign To / Auto Assign + VIP), labels above fields, full-width description, navy Create + outlined Cancel. After saving, the ticket opens on the Ticket Details screen. |
| **Ticket Details** | Default form view `view_egy_care_ticket_details_form`: header with **Create Approval** + status bar, info cards (Ticket Number, Approval Number, Ticket Source, From, Received At, Due Date, Ticket Aging `D:H:M:S`, Beneficiary), tabs **Ticket Details / Ticket Attachments / Queue & SLA / Beneficiary Ticket History**, bottom workflow bar **Send To Co-Ordinator, Re-Queue Ticket, Close Ticket, Pending Ticket, Assign, Create Sub-Ticket**. |
| **My Queue** | Client action `egy_care.board` (mode *queue*): KPI cards **Pending / Assigned / In Progress / VIP / Waiting** above a live native list (Ticket No, Current SLA, Current OLA, Status pill, Type, Source, From, Card No, **Open** button). Cards are clickable filters. |
| **Dashboard** | Same board component (mode *dashboard*): KPI cards **Total Queued / Pharmacy / Non-Pharmacy / In Progress / VIP / Manual / Mobile App** above the **Queued tickets** list (Ticket No, Current SLA, Agreed SLA, Agreed OLA, Current OLA, Status, Type, Source). |
| **Manage Users** | Agent roster `view_egy_care_users_list` (manager only): User Name, User Type, Start Shift Time, In Break, In Progress Ticket No., Assigned Tickets, Resolved Tickets, plus **Tickets** and **Profile** row buttons. |

Design notes (senior UX decisions):
- The board screens (My Queue / Dashboard) embed a **real Odoo list view**
  through the standard `View` component, so search, filters, sorting and
  record opening behave natively; the KPI cards act as one-click filters.
- Status pills match the mock-ups: Waiting = yellow, Pending = orange,
  In Progress = green.
- Odoo renders message history (the mock-up's *Ticket Log* and *Comments*
  tabs) in one unified chatter at the bottom of the Ticket Details screen —
  splitting them into separate tabs is a logic-phase customization.
- The workflow buttons are **UI-ready placeholders**: they show a friendly
  notification instead of failing, and will be wired to the workflow engine
  in the logic phase (Close Ticket and Re-Queue already use the real state
  machine).

## 2. Screen 1 deep mapping — Create Ticket (v1 foundations)

| PDF Element | Implementation |
|---|---|
| Sidebar: Egy Care Tickets | Root application menu with custom navy/teal icon |
| Dashboard | Menu + KPI board (client action `egy_care.board`, mode dashboard) — kanban still available from Manage Tickets |
| My Queue | Menu + KPI board (client action `egy_care.board`, mode queue), filtered to `user_id = current user` |
| Manage Users | Menu (manager only) + agents list with shifts, breaks and workload counters |
| Manage Tickets | Menu + list view with status badges, VIP flag, priority stars |
| Create Ticket | Dedicated menu opening a fresh form view (see below) |
| Card No * | `beneficiary_id` Many2one → beneficiary registry, searchable **by card no or name**, displays `[EGC-00001] Name` |
| Beneficiary Name * | Auto-filled readonly related field from the registry |
| Company | Auto-filled from the registry |
| Ticket Source * | `egy.care.ticket.source` model — editable master data (Mobile App, Phone, Email, WhatsApp, Fax, Walk-in, Portal, Direct). Default: Email |
| Ticket Type * | `egy.care.ticket.type` model — editable master data with **Pharmacy / Non-Pharmacy category** (Medication, Physiotherapy, Scan, Lab, Complaint, Inquiry, Service Request, Technical Support, Billing) |
| Fax No / Phone-WhatsApp / Email | Char fields, auto-filled from beneficiary on selection, still editable per ticket |
| Attachments * (max 15) | `ir.attachment` Many2many with **min 1 / max 15** validation, file-upload widget |
| Email CC (max 10) | Comma-separated text with count + format validation |
| Assign To | `res.users` Many2one restricted to Egy Care Agents |
| Auto Assign (default ✓) | **Round-robin** engine: active agent with oldest last-assignment pointer gets the ticket |
| VIP Ticket | Auto-checked when beneficiary is VIP → priority High + gold ribbon + badge; manual override allowed |
| Ticket Description * | Required Text field, wide textarea |
| Create Ticket / Cancel buttons | Bottom action bar — Create saves, validates and opens the ticket; Cancel discards |

**Bonus foundations** (needed by the next screens): full state machine
(New → In Progress → On Hold → Resolved → Closed / Cancelled) with header
buttons, chatter + activity tracking on tickets and beneficiaries, ticket
sequence `EC/2026/00001`, card sequence `EGC-00001`, security groups
(Agent / Manager), archived-ribbon support, automated tests.

## 3. Module structure

```
egy_care_tickets/
├── __manifest__.py              # Odoo 20 manifest (version 20.0.2.0.0)
├── __init__.py
├── models/
│   ├── egy_care_beneficiary.py  # Beneficiary registry (card no, VIP, contacts)
│   ├── egy_care_ticket.py       # Ticket model + business rules + UI fields
│   ├── egy_care_config.py       # Ticket Source / Ticket Type master data
│   └── res_users.py             # Round-robin pointer, agent flags, workload
├── security/
│   ├── egy_care_security.xml    # res.groups.privilege + Agent/Manager groups
│   └── ir.access.csv            # ACLs (Odoo 20 format - model ir.access)
├── data/
│   ├── ir_sequence_data.xml     # EC/... and EGC-... sequences
│   ├── ir_config_parameter_data.xml  # limits (15 / 1 / 10) as system params
│   ├── egy_care_source_data.xml # 6 base sources (noupdate)
│   ├── egy_care_type_data.xml   # 5 base types (noupdate)
│   └── egy_care_master_data_update.xml  # mock-up sources/types + categories
├── views/                       # forms / lists / kanban / search / menus
├── static/
│   ├── description/icon.png
│   └── src/
│       ├── board/egy_care_board.js  # KPI board OWL component (My Queue + Dashboard)
│       └── scss/egy_care.scss       # mock-up palette (navy #1f4e79, teal #2a9d8f)
├── demo/demo_data.xml           # 3 agents, 3 beneficiaries, 6 tickets
└── tests/test_egy_care_ticket.py
```

## 4. Installation / upgrade on your local Odoo 20 (VS Code)

### 4.1 Upgrade an already-installed module (your case for v2)

Copy the folder into a custom addons directory (recommended — keep it out of
the odoo source tree so `git pull` stays clean):

```
/home/<you>/odoo20/custom-addons/egy_care_tickets
```

Then restart the server and upgrade (v2 adds fields + views + a JS asset, so
an upgrade is required):

```bash
./odoo-bin -c odoo.conf -d your_db_name -u egy_care_tickets --stop-after-init
```

Or via UI after replacing the folder and restarting:
**Apps → Egy Care Tickets → Upgrade**.

> Demo data note: `-u` does **not** re-load demo records. To see the new demo
> users/tickets, create a database with demo data enabled, or load them
> manually.

### 4.2 Register the addons path — `odoo.conf`

```ini
[options]
admin_passwd = YOUR_MASTER_PASSWORD
db_host = localhost
db_port = 5432
db_user = odoo
db_password = YOUR_DB_PASSWORD
addons_path = /home/<you>/odoo20/odoo/addons, /home/<you>/odoo20/custom-addons
```

### 4.3 Install (fresh databases)

```bash
# from your odoo source root
./odoo-bin -c odoo.conf -d your_db_name -i egy_care_tickets --stop-after-init
# then start the server
./odoo-bin -c odoo.conf -d your_db_name
```

Or via UI: **Apps → Update Apps List → search "Egy Care Tickets" → Install**.

### 4.4 VS Code debug configuration — `.vscode/launch.json`

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Odoo 20 (Egy Care)",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/odoo-bin",
            "args": [
                "-c", "${workspaceFolder}/odoo.conf",
                "-d", "your_db_name",
                "--limit-time-real=120000",
                "--dev=xml,qweb,Reload"
            ],
            "console": "integratedTerminal"
        }
    ]
}
```

`--dev=xml` hot-reloads view XML so you can iterate on the screens without
restarting; upgrade a module after model changes with `-u egy_care_tickets`.

### 4.5 First-run checklist

1. Log in as admin (already an Egy Care **Manager**).
2. Settings → Users: add colleagues to **Egy Care / Agent** (auto-assign pool).
3. Egy Care Tickets → Configuration: adjust Sources / Types if needed.
4. Optional limits: Settings → Technical → System Parameters:
   `egy_care.max_attachments` (15), `egy_care.min_attachments` (1),
   `egy_care.max_email_cc` (10).
5. To see demo records, create the DB with demo data enabled.

## 5. Business rules implemented

- **Round-robin auto-assign**: on save with Auto Assign ✓ and no manual
  Assign To, the ticket goes to the active, non-shared member of
  *Egy Care / Agent* with the oldest `Last Ticket Auto-Assigned On` pointer
  (never-assigned agents first). Manual re-assignment updates the pointer too,
  so the workload stays even. If the group is empty, a note is logged on the
  ticket instead of failing.
- **VIP**: beneficiary `is_vip` → new tickets are VIP + High priority
  (auto, overridable). VIP tickets show a gold ribbon and a badge in lists.
- **Attachments**: 1–15 files (configurable). The count is enforced on
  create and edit.
- **Email CC**: max 10 valid addresses; ticket Email must be valid.
- **Sequences**: tickets `EC/<year>/00001`, cards `EGC-00001`. Both unique
  (SQL constraints via the new Odoo 19/20 `models.Constraint` API).
- **Delete protection**: tickets only deletable when New/Cancelled;
  beneficiaries with tickets must be archived, not deleted.

## 6. Security matrix

| Model | Agent | Manager |
|---|---|---|
| Ticket | create / read / write | + delete |
| Beneficiary | create / read / write | + delete |
| Ticket Source / Type | read | full |
| Manage Users menu | — | ✓ |
| Configuration menu | — | ✓ |
| Administrators (`Settings` group) | — | auto-manager |

## 7. Run the automated tests

```bash
./odoo-bin -c odoo.conf -d your_db_name -i egy_care_tickets \
    --test-tags /egy_care_tickets --stop-after-init
```

Covers: card/ticket sequences, round-robin rotation, empty-agent fallback,
attachment min/max, Email CC limits, invalid email, VIP propagation and
override, full state machine, illegal transitions, queue-status defaults,
ticket aging, due-date-from-SLA and the UI placeholder actions.

## 8. Odoo 20 API notes used (keep for the remaining screens)

This module is written **natively for Odoo 19/20** — do not copy patterns
from older tutorials:

- `<list>` (not `<tree>`), `view_mode="list,form,kanban"` (not `tree`)
- No `attrs`/`states` — use `invisible="state != 'draft'"` Python expressions
- SQL constraints: `_name_unique = models.Constraint('UNIQUE(name)', 'msg')`
  (the old `_sql_constraints` list is legacy)
- Security groups: `res.groups.privilege` + `privilege_id` (not `category_id`)
- Access rights: `ir.model.access` is **gone** — the model is now `ir.access`
  and the CSV file must be named **`ir.access.csv`** with the new columns:
  `id,name,model_id,group_id/id,operation,domain`
  - `model_id` takes the **technical model name** (`egy.care.ticket`), not an xml_id
  - `operation` is a string of letters: `c` create, `r` read, `u` write, `d` delete
    (e.g. `cru` = create/read/write, `crud` = all) — no more perm_ columns
  - `domain` replaces the removed record rules (`ir.rule` does not exist in 20)
- `res.users.group_ids` (renamed from `groups_id`), `res.groups.user_ids`
- `ir.config_parameter`: `get_param()` / `set_param()` were **removed** — use
  the typed helpers `get_int() / get_str() / get_bool() / get_float()` and
  `set_int() / set_str() / ...`. For seeding parameters in data XML use
  `<function model="ir.config_parameter" name="set_int">` (create-or-update,
  so it can never crash on the unique key constraint), inside a
  `noupdate="1"` block so upgrades never overwrite admin-tuned values
- Record rules (`ir.rule`) no longer exist in 20 — use ACL domains instead
- Kanban cards: `<t t-name="card">` (not `kanban-box`)
- Chatter: `<chatter/>` tag
- No Font Awesome icons (replaced by Material Symbols in 20)
- Search views: `<group expand="0" string="Group By">` is **rejected** by the
  `search_view.rng` schema since 20 — write a plain `<group>`; the web client
  automatically collects every `context="{'group_by': ...}"` filter into the
  Group By dropdown
- List badge widget emits bootstrap classes: decorations map to
  `text-bg-warning` / `text-bg-info` / `text-bg-success` / `text-bg-300`
  (muted) — NOT `decoration-*` CSS classes
- `banner_route` on actions **no longer exists** — KPI banners are done with a
  client action + OWL component (see `static/src/board/egy_care_board.js`)
- Client action pattern (verified in the 20.0 source):
  `ir.actions.client` with `tag` + `params` (Json field, set via `eval` with
  `ref()`); register the component with
  `registry.category("actions").add(tag, Component)`; the component receives
  props `{ action, actionId, updateActionState }` and can embed a real view
  with `<View resModel type views domain context/>` from `@web/views/view`
- Current user in JS: `import { user } from "@web/core/user"` → `user.userId`,
  `user.context`; ORM from JS: `useService("orm")` → `orm.searchCount(...)`

## 9. Roadmap — the remaining screens and their dependencies

| # | Screen | Builds on | Notes |
|---|---|---|---|
| 1 | Create Ticket | ✅ this module | done |
| 2 | Manage Tickets | ✅ UI delivered (v2) | logic phase: bulk actions, SLA columns, export |
| 3 | My Queue (full) | ✅ UI delivered (v2) | logic phase: activity scheduling, due timers, computed SLA/OLA |
| 4 | Dashboard | ✅ UI delivered (v2) | logic phase: computed KPIs, graph/pivot tab |
| 5 | Manage Users (full) | ✅ UI delivered (v2) | logic phase: agent profiles, skills, load rules |
| 6 | Beneficiary 360 | beneficiary registry | history, linked tickets, notes timeline |
| 7 | SLA / Escalations | states + assignment | new model `egy.care.sla`, cron |
| 8 | Notifications | chatter + email_cc | mail templates, CC routing |
| 9 | Reports / Integrations | everything | QWeb reports, REST endpoints |

Recommended build order: 2 → 3 → 6 → 4 → 5 → 7 → 8 → 9 (each row above lists
the objects it reuses — nothing else needs to be re-created). Screens 1-5 are
delivered (UI phase); the workflow buttons and computed SLA/OLA/aging values
are ready to be wired during the logic phase.

## 10. Troubleshooting

**Golden rule — one folder, one name, forever.** Odoo uses the add-ons
*folder name* as the module's technical name. `egy_care_tickets` and
`egy_care_tickets111` are two DIFFERENT modules to Odoo, never "versions".
To update the module: replace the files inside the same folder, restart,
press **Upgrade**. Never install a second copy.

- **Module not in Apps list** → check `addons_path`, restart with
  `-u base --stop-after-init` once, ensure *Apps* filter shows "Apps".
- **"Unable to add constraint" on install** → existing duplicate data; clean
  duplicates and upgrade again (only applies to pre-existing DBs).
- **Attachment error on programmatic ticket creation** → by design min 1
  attachment is required; lower `egy_care.min_attachments` to 0 if your
  import flow has no files.
- **Record rules / ir.rule missing** → they no longer exist in Odoo 20; put the
  domain in the `domain` column of `ir.access.csv` instead.
- **KeyError: 'ir.model.access' on install** → the ACL CSV was still named
  `ir.model.access.csv` (Odoo ≤19 format). This module ships the corrected
  `security/ir.access.csv` — make sure you copied the updated module folder.
- **ParseError: Invalid view ... definition on install** → usually an arch that
  fails the Odoo 20 RNG schemas. Known 20-breaking case: `<group expand="0"
  string="Group By">` inside a search view — use a plain `<group>` instead.
  To catch these before installing, validate the module locally with
  `scripts/validate_views_rng.py` (runs the real `base/rng/*.rng` schemas
  against every view arch).
- **UniqueViolation: ir_config_parameter_key_uniq (key egy_care....) on
  install** → the database already contains that system parameter, and the
  folder being installed is a *different technical module* (Odoo uses the
  folder name as the module name, so `egy_care_tickets111` is NOT "version 2
  of egy_care_tickets" — it is a second module that re-creates the same
  records). Never keep two copies of this module under two folder names:
  keep ONE folder (`egy_care_tickets`), copy the updated files into it, and
  press **Upgrade** (an installed module never needs Install again). The
  module itself is now immune: system parameters are seeded with the
  idempotent `set_int()` helper (create-or-update) instead of `<record>`
  inserts. The failed install rolls back automatically — no DB cleanup
  needed.
- **UniqueViolation: egy_care_ticket_source_source_name_unique /
  egy_care_ticket_type_type_name_unique (Key (name)=(Phone) ...) on install**
  → same root cause as above: a second copy of the module is being installed
  while the original one is still installed, so the master-data rows already
  exist. As of v20.0.2.2.0 the module carries an **install guard**
  (`data/egy_care_install_guard.xml`): any duplicate-copy install now stops
  immediately with a plain-English `UserError` listing the conflicting
  module names, before any data is touched. Follow the steps in the error:
  delete the duplicate folder, restart, **Upgrade** the installed module.
- **Auto-assign does nothing** → no user is in the *Egy Care / Agent* group.
- **KPI cards show 0 / empty list on My Queue or Dashboard** → the board needs
  the JS asset: make sure `static/src/board/egy_care_board.js` was copied and
  the module was **upgraded** (not just restarted), then hard-refresh the
  browser (Ctrl+Shift+R) so the assets bundle rebuilds.
- **Old Dashboard / My Queue menus still show a plain list** → the menu
  actions changed to the board client actions; run the upgrade and refresh.
- **Workflow buttons show "...logic phase" notifications** → by design; the
  buttons are wired in the logic phase.
- **Aging / Current SLA / Current OLA show 0 or do not move** → these are
  computed by the workflow engine in the logic phase; today they are plain
  fields (demo data pre-fills them).
