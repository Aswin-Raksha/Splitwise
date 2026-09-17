"""Basic validation tests per Section 4.7 of the report.
Run with: python3 tests/test_pipeline.py   (from the project root)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from splitwise.aggregation import aggregate_balances
from splitwise.currency import partition_by_currency
from splitwise.grouping import DisjointSetUnion, partition_into_clusters
from splitwise.greedy_settlement import greedy_settle
from splitwise.models import Transaction
from splitwise.optimal_settlement import optimal_settle


def test_balances_sum_to_zero():
    transactions = [
        Transaction("t1", "A", ["A", "B", "C"], 90, "INR"),
        Transaction("t2", "B", ["A", "B"], 20, "INR"),
    ]
    balances = aggregate_balances(transactions)
    total = sum(balances.values())
    assert abs(total) < 1e-6, f"Balances should sum to zero, got {total}"
    print("PASS: aggregated balances sum to zero")


def test_dsu_connected_components():
    dsu = DisjointSetUnion()
    dsu.union("A", "B")
    dsu.union("B", "C")
    dsu.union("D", "E")
    assert dsu.find("A") == dsu.find("C")
    assert dsu.find("A") != dsu.find("D")
    assert dsu.find("D") == dsu.find("E")
    print("PASS: DSU connected components")


def test_greedy_produces_feasible_plan():
    balances = {"A": 130, "B": 150, "C": 20, "D": -15, "E": -125, "F": -160}
    settlements = greedy_settle("INR", "c1", dict(balances))
    net = dict(balances)
    for s in settlements:
        net[s.from_member] += s.amount
        net[s.to_member] -= s.amount
    for m, amt in net.items():
        assert abs(amt) < 1e-6, f"{m} not fully settled: {amt}"
    print(f"PASS: greedy plan is feasible ({len(settlements)} transactions)")


def test_optimal_matches_paper_example():
    # NOTE: Section 2.1 of the report claims this example settles optimally in
    # 4 transactions. A brute-force check of every subset of these six balances
    # finds none that sums to zero, which means the group cannot be split and
    # the true minimum for pairwise transactions is n-1 = 5, not 4. This test
    # asserts the mathematically correct value; see the chat reply for detail.
    balances = {"A": 130, "B": 150, "C": 20, "D": -15, "E": -125, "F": -160}
    settlements = optimal_settle("INR", "c1", dict(balances))
    assert len(settlements) == 5, f"Expected 5 transactions, got {len(settlements)}"
    print("PASS: optimal solver finds the true minimum (5 transactions)")


def test_optimal_never_worse_than_greedy():
    balances = {"A": 130, "B": 150, "C": 20, "D": -15, "E": -125, "F": -160}
    greedy_count = len(greedy_settle("INR", "c1", dict(balances)))
    optimal_count = len(optimal_settle("INR", "c1", dict(balances)))
    assert optimal_count <= greedy_count
    print(f"PASS: optimal ({optimal_count}) never worse than greedy ({greedy_count})")


def test_clustering_survives_zero_balance_bridge():
    # Figure 3.3: A pays for B, B pays for C. B nets to zero but is the only
    # link between A and C — they must end up in ONE cluster, not two.
    transactions = [
        Transaction("t1", "A", ["A", "B"], 40, "INR"),
        Transaction("t2", "B", ["B", "C"], 40, "INR"),
    ]
    balances = aggregate_balances(transactions)
    buckets = partition_by_currency(balances)
    clusters = partition_into_clusters("INR", buckets["INR"], transactions)
    assert len(clusters) == 1, f"Expected 1 cluster (A and C bridged via B), got {len(clusters)}"
    assert set(clusters[0].member_ids) == {"A", "C"}
    print("PASS: zero-balance bridge member (B) keeps A and C in one cluster")


if __name__ == "__main__":
    test_balances_sum_to_zero()
    test_dsu_connected_components()
    test_greedy_produces_feasible_plan()
    test_optimal_matches_paper_example()
    test_optimal_never_worse_than_greedy()
    test_clustering_survives_zero_balance_bridge()
    print("\nAll tests passed.")
