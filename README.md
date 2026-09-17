# Splitwise — Group-Expense Settlement Optimization System

## Folder structure

```
splitwise_project/
├── requirements.txt
├── app.py                          # Streamlit web front-end
├── main.py                         # CLI demo (same backend, no UI)
├── splitwise/                      # backend library — one module per pipeline stage
│   ├── __init__.py
│   ├── models.py                    # Table 3.3 data model: Member, Transaction, Balance,
│   │                                 #   Cluster, Settlement, LedgerEntry
│   ├── aggregation.py                # Module 1 — Balance Aggregation (hash map, O(n))
│   ├── currency.py                   # Module 2 — Currency Partitioning (hash map bucketing)
│   ├── grouping.py                   # Module 3 — Group Partitioning (Union-Find / DSU)
│   ├── greedy_settlement.py          # Module 4 — Fast Settlement (heap-based greedy)
│   ├── optimal_settlement.py         # Module 5 — Optimal Settlement (DFS + backtracking + pruning)
│   ├── orchestrator.py               # Component-bounded routing (Section 3.3, threshold K)
│   ├── ledger.py                     # Module 6 — Settlement Ledger & Notification
│   ├── csv_io.py                     # NEW — parses an uploaded transactions CSV for the UI
│   └── sample_data.py                # NEW — built-in demo scenarios for the UI
└── tests/
    └── test_pipeline.py             # validation tests (Section 4.7)
```

Not built yet — next phase per Sections 4.6–4.9:

```
splitwise_project/
├── datasets/                        # PaySim + Personal Finance Tracker CSVs (download from Kaggle)
├── splitwise/
│   ├── fx.py                        # Frankfurter API client — display-only currency conversion
│   └── scenarios.py                 # synthetic group/membership scenario generator (evaluation-scale)
└── benchmarks/
    ├── run_benchmarks.py            # Module 7 — Performance Analysis: sweeps cluster size/
    │                                 #   density, logs the Table 4.3 metrics, picks K
    └── results/                     # benchmark CSVs + matplotlib plots
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running it

```bash
streamlit run app.py                  # web UI  ->  http://localhost:8501
python3 main.py                       # CLI demo
python3 tests/test_pipeline.py        # validation tests
# or, once pytest is installed:
pytest tests/
```

## Using the web app

1. **Load transactions** (sidebar) — pick a built-in demo scenario, upload a
   CSV (`transaction_id,payer_id,participant_ids,amount,currency`, with
   `participant_ids` joined by `;`), or add transactions one at a time.
2. **Set the threshold K** — clusters at or below K use the exact solver;
   larger clusters fall back to greedy. The exact solver is hard-capped at
   16 members regardless of K, so the UI never hangs on an exponential search.
3. The page then shows: the raw transaction log, aggregated net balances,
   each currency/connected-component cluster with its settlement plan
   (greedy vs optimal side by side), summary metrics (transaction-count
   reduction, optimal coverage), and the settlement ledger with per-member
   notifications.
