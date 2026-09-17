"""Module 1: Balance Aggregation — hash-map based, O(n). See Section 3.2.1."""
from collections import defaultdict
from typing import Dict, List, Tuple

from .models import Transaction


def aggregate_balances(transactions: List[Transaction]) -> Dict[Tuple[str, str], float]:
    """Fold raw transactions into net balances keyed by (member_id, currency).

    The payer is credited the full amount; each participant (the payer
    included, if also a participant) is debited an equal share. Members
    whose net balance nets to zero are dropped from the result, since they
    neither owe nor are owed anything.
    """
    balances: Dict[Tuple[str, str], float] = defaultdict(float)

    for txn in transactions:
        share = txn.amount / len(txn.participant_ids)
        balances[(txn.payer_id, txn.currency)] += txn.amount
        for participant_id in txn.participant_ids:
            balances[(participant_id, txn.currency)] -= share

    return {k: round(v, 2) for k, v in balances.items() if abs(v) > 1e-9}