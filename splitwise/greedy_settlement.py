"""Module 4: Fast Settlement — greedy heap-based matching, O(p log p). Always valid, not necessarily minimal."""
import heapq
from typing import Dict, List

from .models import Settlement


def greedy_settle(currency: str, cluster_id: str, balances: Dict[str, float]) -> List[Settlement]:
    creditors = []  # max-heap via negation: (-amount, member_id)
    debtors = []    # min-heap: (amount, member_id), amount is negative

    for member_id, amount in balances.items():
        if amount > 1e-9:
            heapq.heappush(creditors, (-amount, member_id))
        elif amount < -1e-9:
            heapq.heappush(debtors, (amount, member_id))

    settlements: List[Settlement] = []
    count = 0

    while creditors and debtors:
        neg_credit, creditor_id = heapq.heappop(creditors)
        debt, debtor_id = heapq.heappop(debtors)
        credit = -neg_credit
        pay = min(credit, -debt)

        settlements.append(Settlement(
            settlement_id=f"{cluster_id}-g{count}",
            from_member=debtor_id,
            to_member=creditor_id,
            amount=round(pay, 2),
            currency=currency,
        ))
        count += 1

        remaining_credit = credit - pay
        remaining_debt = debt + pay  # debt is negative

        if remaining_credit > 1e-9:
            heapq.heappush(creditors, (-remaining_credit, creditor_id))
        if remaining_debt < -1e-9:
            heapq.heappush(debtors, (remaining_debt, debtor_id))

    return settlements