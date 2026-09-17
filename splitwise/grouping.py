"""Module 3: Group Partitioning — Disjoint Set Union with path compression
and union by rank, splitting a currency bucket into independent settlement
clusters (connected components of the debt graph)."""
from collections import defaultdict
from typing import Dict, List

from .models import Cluster, Transaction


class DisjointSetUnion:
    def __init__(self):
        self.parent: Dict[str, str] = {}
        self.rank: Dict[str, int] = {}

    def make_set(self, x: str) -> None:
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def find(self, x: str) -> str:
        self.make_set(x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # path compression
        return self.parent[x]

    def union(self, x: str, y: str) -> None:
        root_x, root_y = self.find(x), self.find(y)
        if root_x == root_y:
            return
        if self.rank[root_x] < self.rank[root_y]:
            root_x, root_y = root_y, root_x
        self.parent[root_y] = root_x
        if self.rank[root_x] == self.rank[root_y]:
            self.rank[root_x] += 1


def partition_into_clusters(
    currency: str,
    member_balances: Dict[str, float],
    transactions: List[Transaction],
) -> List[Cluster]:
    """Partition one currency bucket's members into connected components,
    using the transaction log restricted to this currency.

    Union-Find runs over ALL members touched by a transaction, including
    ones whose net balance has since dropped to zero. A zero-balance member
    can still be the only link between two non-zero members (e.g. A pays for
    B, B pays for C: B nets to zero but is the bridge between A and C), so
    excluding them from unioning would wrongly split one cluster into two
    unsettleable singletons.
    """
    dsu = DisjointSetUnion()
    for txn in transactions:
        if txn.currency != currency:
            continue
        dsu.make_set(txn.payer_id)
        for participant_id in txn.participant_ids:
            dsu.union(txn.payer_id, participant_id)

    for member_id in member_balances:
        dsu.make_set(member_id)  # isolated non-zero members with no txns in this bucket

    groups: Dict[str, List[str]] = defaultdict(list)
    for member_id in member_balances:  # only report clusters for non-zero members
        groups[dsu.find(member_id)].append(member_id)

    return [
        Cluster(cluster_id=f"{currency}-{i}", currency=currency, member_ids=members)
        for i, members in enumerate(groups.values())
    ]
