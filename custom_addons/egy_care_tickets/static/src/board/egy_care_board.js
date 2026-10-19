
/** @odoo-module **/

import {
    Component,
    onWillStart,
    proxy,
    useProps,
    xml,
} from "@odoo/owl";

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
import { View } from "@web/views/view";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

const QUEUED_DOMAIN = [
    ["queue_status", "in", ["waiting", "pending", "in_progress"]],
];

function buildCards(mode, uid) {
    if (mode === "queue") {
        const mine = [["user_id", "=", uid]];

        return [
            {
                key: "pending",
                label: "Pending",
                domain: [...mine, ["queue_status", "=", "pending"]],
            },
            {
                key: "assigned",
                label: "Assigned",
                domain: [...mine, ["state", "=", "draft"]],
            },
            {
                key: "in_progress",
                label: "In Progress",
                domain: [
                    ...mine,
                    "|",
                    ["queue_status", "=", "in_progress"],
                    ["state", "=", "in_progress"],
                ],
            },
            {
                key: "vip",
                label: "VIP",
                domain: [...mine, ["vip_ticket", "=", true]],
            },
            {
                key: "waiting",
                label: "Waiting",
                domain: [...mine, ["queue_status", "=", "waiting"]],
            },
        ];
    }

    return [
        {
            key: "total",
            label: "Total Queued",
            domain: [...QUEUED_DOMAIN],
        },
        {
            key: "pharmacy",
            label: "Pharmacy",
            domain: [
                ...QUEUED_DOMAIN,
                ["type_category", "=", "pharmacy"],
            ],
        },
        {
            key: "non_pharmacy",
            label: "Non-Pharmacy",
            domain: [
                ...QUEUED_DOMAIN,
                ["type_category", "=", "non_pharmacy"],
            ],
        },
        {
            key: "in_progress",
            label: "In Progress",
            domain: [
                ...QUEUED_DOMAIN,
                ["queue_status", "=", "in_progress"],
            ],
        },
        {
            key: "vip",
            label: "VIP",
            domain: [...QUEUED_DOMAIN, ["vip_ticket", "=", true]],
        },
        {
            key: "manual",
            label: "Manual",
            domain: [
                ...QUEUED_DOMAIN,
                ["source_id.code", "!=", "mobile_app"],
            ],
        },
        {
            key: "mobile_app",
            label: "Mobile App",
            domain: [
                ...QUEUED_DOMAIN,
                ["source_id.code", "=", "mobile_app"],
            ],
        },
    ];
}

export class EgyCareBoard extends Component {
    // OWL 3: explicitly expose the props received by the client action.
    props = useProps(standardActionServiceProps);

    static components = { View };

    static template = xml`
        <t t-name="egy_care.Board">
            <div class="o_egy_board">

                <div class="o_egy_board_head d-flex justify-content-between align-items-center">
                    <h4 class="o_egy_board_title" t-esc="this.title"/>

                    <button
                        type="button"
                        class="btn o_egy_btn_refresh"
                        t-on-click="this.refreshCounts"
                        t-att-disabled="this.state.loading"
                    >
                        Refresh
                    </button>
                </div>

                <div
                    t-if="this.state.error"
                    class="alert alert-danger o_egy_board_error"
                    role="alert"
                    t-esc="this.state.error"
                />

                <div class="o_egy_kpi_row">
                    <t
                        t-foreach="this.cards"
                        t-as="card"
                        t-key="card.key"
                    >
                        <div
                            t-att-class="this.cardClass(card)"
                            role="button"
                            tabindex="0"
                            t-on-click="() => this.onCardClick(card)"
                            t-att-title="
                                this.state.active === card.key
                                ? 'Click again to clear the filter'
                                : card.label
                            "
                        >
                            <div
                                class="o_egy_kpi_label"
                                t-esc="card.label"
                            />

                            <div
                                class="o_egy_kpi_value"
                                t-esc="this.countOf(card)"
                            />
                        </div>
                    </t>
                </div>

                <div class="o_egy_board_view_wrap">
                    <View
                        resModel="'egy.care.ticket'"
                        type="'list'"
                        views="this.viewDefs"
                        domain="this.listDomain"
                        context="this.viewContext"
                        className="'o_egy_board_view'"
                    />
                </div>

            </div>
        </t>
    `;

    setup() {
        this.orm = useService("orm");

        // The props are initialized by useProps() above.
        const action = this.props.action || {};
        const params = action.params || {};

        this.mode = params.mode === "queue" ? "queue" : "dashboard";

        this.title =
            action.name ||
            (this.mode === "queue" ? "My Queue" : "Dashboard");

        this.viewDefs = [
            [params.list_view_id || false, "list"],
            [params.search_view_id || false, "search"],
        ];

        this.cards = buildCards(this.mode, user.userId);

        this.baseDomain =
            this.mode === "queue"
                ? [["user_id", "=", user.userId]]
                : [...QUEUED_DOMAIN];

        this.viewContext = {
            ...user.context,
            ...(action.context || {}),
        };

        // OWL 3 reactive state.
        this.state = proxy({
            counts: {},
            active: false,
            loading: true,
            error: null,
        });

        onWillStart(() => this.refreshCounts());
    }

    async refreshCounts() {
        this.state.loading = true;
        this.state.error = null;

        try {
            const values = await Promise.all(
                this.cards.map((card) =>
                    this.orm.searchCount(
                        "egy.care.ticket",
                        card.domain
                    )
                )
            );

            const counts = {};

            this.cards.forEach((card, index) => {
                counts[card.key] = values[index];
            });

            this.state.counts = counts;
        } catch (error) {
            // Prevent failed ORM requests from leaving the board stuck.
            console.error(
                "[EgyCareBoard] Failed to load ticket counts:",
                error
            );

            this.state.error =
                "Unable to load ticket counts. Check the model access rights and browser console.";
        } finally {
            this.state.loading = false;
        }
    }

    countOf(card) {
        const value = this.state.counts[card.key];

        return typeof value === "number" ? value : 0;
    }

    cardClass(card) {
        let klass = "o_egy_kpi_card";

        if (this.state.active === card.key) {
            klass += " o_egy_kpi_active";
        }

        if (this.state.loading) {
            klass += " o_egy_kpi_loading";
        }

        return klass;
    }

    onCardClick(card) {
        this.state.active =
            this.state.active === card.key ? false : card.key;
    }

    get activeCard() {
        return (
            this.cards.find(
                (card) => card.key === this.state.active
            ) || null
        );
    }

    get listDomain() {
        return this.activeCard
            ? this.activeCard.domain
            : this.baseDomain;
    }
}

registry.category("actions").add("egy_care.board", EgyCareBoard);
