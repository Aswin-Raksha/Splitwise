"""Core data model for the Splitwise settlement system."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Member:
    member_id: str
    display_name: str = ""
    group_memberships: List[str] = field(default_factory=list)


@dataclass
class Transaction:
    transaction_id: str
    payer_id: str
    participant_ids: List[str]
    amount: float
    currency: str
    timestamp: str = ""


@dataclass
class Balance:
    member_id: str
    currency: str
    net_balance: float


@dataclass
class Cluster:
    cluster_id: str
    currency: str
    member_ids: List[str]

    @property
    def size(self) -> int:
        return len(self.member_ids)


@dataclass
class Settlement:
    settlement_id: str
    from_member: str
    to_member: str
    amount: float
    currency: str
    status: str = "pending"


@dataclass
class LedgerEntry:
    event_id: str
    settlement_id: str
    event_type: str
    event_time: str
