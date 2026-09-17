"""Streamlit front-end for the Splitwise group-expense settlement system.

Run with:  streamlit run app.py

This file is UI only — every algorithmic step (aggregation, currency and
group partitioning, greedy/optimal settlement, ledger) lives in the
splitwise/ package and is unchanged from the CLI version.
"""
import time

import pandas as pd
import streamlit as st

from splitwise.aggregation import aggregate_balances
from splitwise.csv_io import SAMPLE_CSV_TEXT, parse_transactions_csv
from splitwise.currency import partition_by_currency
from splitwise.greedy_settlement import greedy_settle
from splitwise.grouping import partition_into_clusters
from splitwise.ledger import new_ledger, record_settlement
from splitwise.models import Transaction
from splitwise.optimal_settlement import optimal_settle
from splitwise.orchestrator import DEFAULT_THRESHOLD_K
from splitwise.sample_data import DEMO_SCENARIOS

# Hard safety cap: the exact solver is O(2^p). Even if the user sets K above
# this, clusters larger than it fall back to greedy so the UI never hangs.
SAFE_OPTIMAL_LIMIT = 16

st.set_page_config(page_title="Splitwise Settlement Optimizer", layout="wide")

if "transactions" not in st.session_state:
    st.session_state.transactions = []

st.title("💸 Group-Expense Settlement Optimizer")
st.caption(
    "Balance aggregation → currency partitioning → connected-component clustering "
    "→ greedy / optimal settlement, routed by cluster size."
)

with st.expander("How this works", expanded=False):
    st.markdown(
        "1. **Aggregate** every transaction into each member's net balance.\n"
        "2. **Partition by currency** — balances in different currencies never mix.\n"
        "3. **Partition by connected component** (Union–Find) — members who never "
        "transacted, directly or transitively, are settled independently.\n"
        "4. **Settle each cluster.** Clusters at or below the threshold **K** use an "
        "exact DFS + backtracking + pruning solver (guaranteed minimum transactions); "
        "larger clusters use a fast greedy heap-based matcher (always valid, not "
        "always minimal)."
    )

# ---------------------------------------------------------------- Sidebar --
st.sidebar.header("1. Load transactions")
source = st.sidebar.radio("Source", ["Demo scenario", "Upload CSV", "Manual entry"])

if source == "Demo scenario":
    scenario_name = st.sidebar.selectbox("Pick a scenario", list(DEMO_SCENARIOS.keys()))
    if st.sidebar.button("Load scenario", width='stretch'):
        st.session_state.transactions = DEMO_SCENARIOS[scenario_name]()

elif source == "Upload CSV":
    st.sidebar.download_button(
        "⬇ Download sample CSV", SAMPLE_CSV_TEXT,
        file_name="sample_transactions.csv", width='stretch',
    )
    uploaded = st.sidebar.file_uploader("transactions.csv", type="csv")
    if uploaded is not None:
        try:
            st.session_state.transactions = parse_transactions_csv(uploaded)
            st.sidebar.success(f"Loaded {len(st.session_state.transactions)} transactions.")
        except ValueError as exc:
            st.sidebar.error(str(exc))

else:  # Manual entry
    with st.sidebar.form("manual_txn_form", clear_on_submit=True):
        payer = st.text_input("Payer ID")
        participants = st.text_input("Participant IDs (comma-separated, include payer if they share)")
        amount = st.number_input("Amount", min_value=0.0, step=10.0)
        currency = st.text_input("Currency", value="INR")
        if st.form_submit_button("Add transaction", width='stretch'):
            if payer and participants and amount > 0:
                st.session_state.transactions.append(Transaction(
                    transaction_id=f"t{len(st.session_state.transactions) + 1}",
                    payer_id=payer.strip(),
                    participant_ids=[p.strip() for p in participants.split(",") if p.strip()],
                    amount=amount,
                    currency=currency.strip().upper() or "INR",
                ))
            else:
                st.sidebar.warning("Payer, participants and a positive amount are all required.")

if st.sidebar.button("🗑 Clear all transactions"):
    st.session_state.transactions = []

st.sidebar.header("2. Settlement threshold")
threshold_k = st.sidebar.slider(
    "Cluster size threshold K", min_value=0, max_value=20, value=DEFAULT_THRESHOLD_K,
    help="Clusters at or below K use the exact (optimal) solver; larger clusters use greedy.",
)
st.sidebar.caption(f"Exact solver is capped at {SAFE_OPTIMAL_LIMIT} members regardless of K, for responsiveness.")

transactions = st.session_state.transactions

if not transactions:
    st.info("Load a demo scenario, upload a CSV, or add a transaction manually from the sidebar to get started.")
    st.stop()

# -------------------------------------------------------- Raw transactions --
st.subheader("Raw transaction log")
st.dataframe(
    pd.DataFrame([{
        "id": t.transaction_id, "payer": t.payer_id,
        "participants": ", ".join(t.participant_ids),
        "amount": t.amount, "currency": t.currency,
    } for t in transactions]),
    width='stretch', hide_index=True,
)

# ------------------------------------------------------------- Aggregation --
balances = aggregate_balances(transactions)
buckets = partition_by_currency(balances)

st.subheader("Net balances (after aggregation)")
if balances:
    bal_df = pd.DataFrame(
        [{"member": m, "currency": c, "net_balance": amt} for (m, c), amt in balances.items()]
    ).sort_values(["currency", "net_balance"], ascending=[True, False])
    st.dataframe(bal_df, width='stretch', hide_index=True)
else:
    st.write("Every balance nets to zero — nothing to settle.")
    st.stop()

# ------------------------------------------------------- Clustering + settle --
st.subheader("Clusters & settlement plans")

ledger = new_ledger()
total_naive_txns = len(transactions)
total_greedy_baseline = 0
total_actual_txns = 0
optimal_members = 0
total_members = 0

for currency, member_balances in buckets.items():
    clusters = partition_into_clusters(currency, member_balances, transactions)
    st.markdown(f"#### Currency: {currency} — {len(clusters)} cluster(s)")

    for cluster in clusters:
        cluster_balances = {m: member_balances[m] for m in cluster.member_ids}
        total_members += cluster.size

        t0 = time.perf_counter()
        greedy_plan = greedy_settle(currency, cluster.cluster_id, dict(cluster_balances))
        greedy_time_ms = (time.perf_counter() - t0) * 1000
        total_greedy_baseline += len(greedy_plan)

        eligible = cluster.size <= threshold_k
        capped = eligible and cluster.size > SAFE_OPTIMAL_LIMIT
        use_optimal = eligible and not capped

        if use_optimal:
            t0 = time.perf_counter()
            optimal_plan = optimal_settle(currency, cluster.cluster_id, dict(cluster_balances))
            optimal_time_ms = (time.perf_counter() - t0) * 1000
            optimal_members += cluster.size
            chosen_plan, engine = optimal_plan, "optimal"
        else:
            optimal_plan, optimal_time_ms = None, None
            chosen_plan, engine = greedy_plan, "greedy"

        total_actual_txns += len(chosen_plan)

        with st.expander(
            f"Cluster `{cluster.cluster_id}` — {cluster.size} member(s) — "
            f"{engine} path, {len(chosen_plan)} transaction(s)",
            expanded=cluster.size <= 8,
        ):
            if capped:
                st.warning(
                    f"Cluster size {cluster.size} exceeds the {SAFE_OPTIMAL_LIMIT}-member "
                    f"safety cap for the exact solver in this UI — using greedy instead."
                )

            m1, m2, m3 = st.columns(3)
            m1.metric("Members", cluster.size)
            m2.metric("Greedy transactions", len(greedy_plan), help=f"{greedy_time_ms:.2f} ms")
            if use_optimal:
                m3.metric(
                    "Optimal transactions", len(optimal_plan),
                    delta=len(optimal_plan) - len(greedy_plan), delta_color="inverse",
                    help=f"{optimal_time_ms:.2f} ms",
                )
            else:
                m3.metric("Optimal transactions", "skipped")

            st.dataframe(
                pd.DataFrame([
                    {"from": s.from_member, "to": s.to_member, "amount": s.amount, "currency": s.currency}
                    for s in chosen_plan
                ]),
                width='stretch', hide_index=True,
            )

            for s in chosen_plan:
                record_settlement(ledger, s)

# ------------------------------------------------------------------ Summary --
st.subheader("Summary")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Naive transactions (1 per logged expense)", total_naive_txns)
c2.metric("Transactions after settlement", total_actual_txns)
reduction_pct = 100 * (1 - total_actual_txns / total_naive_txns) if total_naive_txns else 0
c3.metric("Reduction vs naive", f"{reduction_pct:.0f}%")
coverage_pct = 100 * optimal_members / total_members if total_members else 0
c4.metric("Optimal coverage", f"{coverage_pct:.0f}%")

st.bar_chart(
    pd.DataFrame({
        "engine": ["Greedy-only baseline", "Component-bounded (this run)"],
        "transactions": [total_greedy_baseline, total_actual_txns],
    }).set_index("engine")
)

# ------------------------------------------------------------------- Ledger --
st.subheader("Settlement ledger & notifications")
if ledger["entries"]:
    st.dataframe(
        pd.DataFrame([
            {"event_id": e.event_id, "settlement_id": e.settlement_id, "type": e.event_type, "time": e.event_time}
            for e in ledger["entries"]
        ]),
        width='stretch', hide_index=True,
    )
    who = st.selectbox("View notifications for member", sorted(ledger["notifications"].keys()))
    for msg in ledger["notifications"][who]:
        st.write("• " + msg)
else:
    st.write("No settlements recorded.")