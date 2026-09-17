"""
Component-bounded settlement: route each cluster to the exact solver if
it's small enough (size <= K), otherwise fall back to the greedy engine.
"""
from typing import Dict, List

from .models import Cluster, Settlement
from .greedy_settlement import greedy_settle
from .optimal_settlement import optimal_settle

DEFAULT_THRESHOLD_K = 12  # clusters at or below this size use the exact solver


def settle_cluster(cluster: Cluster, balances: Dict[str, float], threshold_k: int = DEFAULT_THRESHOLD_K) -> List[Settlement]:
    cluster_balances = {m: balances[m] for m in cluster.member_ids}
    if cluster.size <= threshold_k:
        return optimal_settle(cluster.currency, cluster.cluster_id, cluster_balances)
    return greedy_settle(cluster.currency, cluster.cluster_id, cluster_balances)


def settle_all(
    clusters: List[Cluster],
    balances_by_currency: Dict[str, Dict[str, float]],
    threshold_k: int = DEFAULT_THRESHOLD_K,
) -> List[Settlement]:
    all_settlements: List[Settlement] = []
    for cluster in clusters:
        balances = balances_by_currency[cluster.currency]
        all_settlements.extend(settle_cluster(cluster, balances, threshold_k))
    return all_settlements