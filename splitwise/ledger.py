"""Module 6: Settlement Ledger and Notification — append-only event log.


Function-based version: instead of a SettlementLedger class, the ledger's
state is a plain dict you create once with new_ledger() and pass into
record_settlement() every time you record a payment. This avoids importing
a class at all — everything here is a function plus a dict.
"""
from collections import defaultdict
from typing import Dict, List

from .models import LedgerEntry, Settlement


def new_ledger() -> dict:
    """Creates a fresh, empty ledger state. Pass this into record_settlement()."""
    return {
        "entries": [],           # List[LedgerEntry], in the order they were recorded
        "notifications": defaultdict(list),  # member_id -> List[str] messages
        "counter": 0,
    }


def record_settlement(ledger: dict, settlement: Settlement) -> LedgerEntry:
    """Records one settlement into the ledger, in place, and returns the
    LedgerEntry that was created for it."""
    ledger["counter"] += 1
    entry = LedgerEntry(
        event_id=f"evt{ledger['counter']}",
        settlement_id=settlement.settlement_id,
        event_type="settlement_recorded",
        event_time=f"t{ledger['counter']}",
    )
    ledger["entries"].append(entry)

    ledger["notifications"][settlement.from_member].append(
        f"Pay {settlement.amount} {settlement.currency} to {settlement.to_member}"
    )
    ledger["notifications"][settlement.to_member].append(
        f"Receive {settlement.amount} {settlement.currency} from {settlement.from_member}"
    )
    return entry


def get_entries(ledger: dict) -> List[LedgerEntry]:
    return ledger["entries"]


def get_notifications(ledger: dict, member_id: str) -> List[str]:
    return ledger["notifications"].get(member_id, [])


def all_members_with_notifications(ledger: dict) -> List[str]:
    return sorted(ledger["notifications"].keys())