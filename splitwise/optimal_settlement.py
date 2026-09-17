"""Module 5: Optimal Settlement — DFS with backtracking and pruning,
guarantees the minimum number of transactions. O(2^p) worst case, so only
ever called on size-bounded clusters (see orchestrator.py)."""
from typing import Dict, List, Tuple

from .models import Settlement


def optimal_settle(currency: str, cluster_id: str, balances: Dict[str, float]) -> List[Settlement]:
    members = list(balances.keys())
    amounts = [balances[m] for m in members]
    n = len(amounts)

    best_count = [n]  # safe upper bound: at most one txn per member
    best_plan: List[Tuple[int, int, float]] = []
    current_plan: List[Tuple[int, int, float]] = []

    def dfs(i: int, txn_count: int) -> None:
        while i < n and abs(amounts[i]) < 1e-9:
            i += 1

        if i == n:
            if txn_count < best_count[0]:
                best_count[0] = txn_count
                best_plan[:] = current_plan[:]
            return

        if txn_count >= best_count[0]:
            return  # prune: this branch can't beat the best found so far

        for j in range(i + 1, n):
            if amounts[j] * amounts[i] < 0:  # opposite signs only
                amounts[j] += amounts[i]
                current_plan.append((i, j, amounts[i]))
                dfs(i + 1, txn_count + 1)
                current_plan.pop()
                amounts[j] -= amounts[i]

    dfs(0, 0)

    settlements: List[Settlement] = []
    for count, (i, j, amt) in enumerate(best_plan):
        if amt > 0:
            from_m, to_m = members[j], members[i]  # j pays i
        else:
            from_m, to_m = members[i], members[j]  # i pays j
        settlements.append(Settlement(
            settlement_id=f"{cluster_id}-o{count}",
            from_member=from_m,
            to_member=to_m,
            amount=round(abs(amt), 2),
            currency=currency,
        ))
    return settlements
