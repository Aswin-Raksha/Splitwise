"""Built-in demo scenarios for the web front-end. Each returns a fresh list
of Transaction objects so repeated loads don't share mutable state."""

import random
from typing import List

from .models import Transaction


def scenario_figure_3_3() -> List[Transaction]:
    """Section 3.4 / Figure 3.3: A pays for B, B pays for C. B nets to zero
    but bridges A and C into one cluster, settled in a single payment."""
    return [
        Transaction("t1", "A", ["A", "B"], 40, "INR"),
        Transaction("t2", "B", ["B", "C"], 40, "INR"),
    ]


def scenario_small_trip_multi_currency() -> List[Transaction]:
    """A 6-person trip that splits into two independent clusters across
    two currencies — demonstrates currency + group partitioning together."""
    return [
        Transaction("t1", "Aditi", ["Aditi", "Ben", "Chen", "Dinesh"], 4000, "INR"),
        Transaction("t2", "Ben", ["Ben", "Chen", "Dinesh"], 1500, "INR"),
        Transaction("t3", "Chen", ["Chen", "Dinesh"], 800, "INR"),
        Transaction("t4", "Dinesh", ["Dinesh", "Aditi"], 600, "INR"),
        Transaction("t5", "Ella", ["Ella", "Farah"], 120, "USD"),
        Transaction("t6", "Farah", ["Farah", "Ella"], 45, "USD"),
    ]


def scenario_large_synthetic(num_members: int = 40, seed: int = 42) -> List[Transaction]:
    """A group split into several disjoint friend-circles of fixed size
    (3, 4, 6, and the remainder) — deliberately mirroring the 3/4/6/27
    fragmentation example in Section 3.3. A chain of transactions guarantees
    each circle is one connected component; a few extra random transactions
    per circle add realistic texture. Useful for seeing how the threshold K
    slider routes small clusters to the exact solver and the large one to
    greedy."""
    rng = random.Random(seed)
    group_sizes = [3, 4, 6, num_members - 13] if num_members > 13 else [num_members]
    member_ids = [f"M{i:02d}" for i in range(1, num_members + 1)]

    transactions = []
    idx = 0
    txn_id = 1
    for size in group_sizes:
        group = member_ids[idx: idx + size]
        idx += size

        # Chain transactions guarantee the whole circle is one connected component.
        for i in range(len(group) - 1):
            amount = round(rng.uniform(100, 1500), 2)
            transactions.append(Transaction(f"t{txn_id}", group[i], [group[i], group[i + 1]], amount, "INR"))
            txn_id += 1

        # A few extra random transactions within the circle for realistic texture.
        for _ in range(max(size, 3)):
            k = min(rng.randint(2, 4), size)
            participants = rng.sample(group, k=k)
            payer = rng.choice(participants)
            amount = round(rng.uniform(50, 2000), 2)
            transactions.append(Transaction(f"t{txn_id}", payer, participants, amount, "INR"))
            txn_id += 1

    return transactions


DEMO_SCENARIOS = {
    "Figure 3.3 — simple 3-person chain (A -> B -> C)": scenario_figure_3_3,
    "Small trip — 6 people, 2 currencies": scenario_small_trip_multi_currency,
    "Large synthetic group — 40 members": scenario_large_synthetic,
}
