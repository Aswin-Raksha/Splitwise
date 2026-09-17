"""Module 2: Currency Partitioning — bucket balances by currency, O(n).
See Section 3.2.2. Debts in different currencies are never netted directly."""
from collections import defaultdict
from typing import Dict, Tuple


def partition_by_currency(balances: Dict[Tuple[str, str], float]) -> Dict[str, Dict[str, float]]:
    """Group (member_id, currency) -> balance into currency -> {member_id: balance}."""
    buckets: Dict[str, Dict[str, float]] = defaultdict(dict)
    for (member_id, currency), amount in balances.items():
        buckets[currency][member_id] = amount
    return buckets