"""Demo: run the full pipeline end-to-end on the worked examples from the
project report (Figure 3.3 and Sections 3.2.4/3.2.5)."""
from splitwise.aggregation import aggregate_balances
from splitwise.currency import partition_by_currency
from splitwise.grouping import partition_into_clusters
from splitwise.ledger import new_ledger, record_settlement
from splitwise.models import Cluster, Transaction
from splitwise.orchestrator import settle_all, settle_cluster


def run_pipeline(transactions):
    balances = aggregate_balances(transactions)
    print("Net balances:", balances)

    buckets = partition_by_currency(balances)
    ledger = new_ledger()

    for currency, member_balances in buckets.items():
        clusters = partition_into_clusters(currency, member_balances, transactions)
        print(f"Currency {currency}: {len(clusters)} cluster(s)")

        settlements = settle_all(clusters, {currency: member_balances})
        for s in settlements:
            print(f"  {s.from_member} -> {s.to_member}: {s.amount} {s.currency}")
            record_settlement(ledger, s)

    print("Ledger entries recorded:", len(ledger["entries"]))


def demo_three_member_example():
    print("=== Figure 3.3: A pays for B, B pays for C -> single net payment ===")
    transactions = [
        Transaction("t1", payer_id="A", participant_ids=["A", "B"], amount=40, currency="INR"),
        Transaction("t2", payer_id="B", participant_ids=["B", "C"], amount=40, currency="INR"),
    ]
    run_pipeline(transactions)


def demo_greedy_vs_optimal_example():
    print("\n=== Section 3.2.4/3.2.5 example: greedy vs optimal ===")
    balances = {"A": 130, "B": 150, "C": 20, "D": -15, "E": -125, "F": -160}
    cluster = Cluster(cluster_id="demo", currency="INR", member_ids=list(balances.keys()))

    for label, k in [("greedy  (K=0)", 0), ("optimal (K=10)", 10)]:
        settlements = settle_cluster(cluster, balances, threshold_k=k)
        print(f"{label}: {len(settlements)} transactions")
        for s in settlements:
            print(f"  {s.from_member} -> {s.to_member}: {s.amount}")


if __name__ == "__main__":
    demo_three_member_example()
    demo_greedy_vs_optimal_example()