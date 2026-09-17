"""CSV helpers for the web front-end: parse an uploaded transactions CSV
into Transaction objects, and provide a sample CSV for the user to download
as a template."""
import csv
import io
from typing import List

from .models import Transaction

REQUIRED_COLUMNS = ["transaction_id", "payer_id", "participant_ids", "amount", "currency"]

SAMPLE_CSV_TEXT = """transaction_id,payer_id,participant_ids,amount,currency
t1,Aditi,Aditi;Ben;Chen;Dinesh,4000,INR
t2,Ben,Ben;Chen;Dinesh,1500,INR
t3,Chen,Chen;Dinesh,800,INR
t4,Dinesh,Dinesh;Aditi,600,INR
t5,Ella,Ella;Farah,120,USD
t6,Farah,Farah;Ella,45,USD
"""


def parse_transactions_csv(uploaded_file) -> List[Transaction]:
    """Parse an uploaded CSV into Transaction objects.

    Expected columns: transaction_id, payer_id, participant_ids (member IDs
    joined with ';'), amount, currency. Raises ValueError with a readable
    message if required columns are missing or a row is malformed.
    """
    text = uploaded_file.getvalue().decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise ValueError(f"CSV is missing required column(s): {', '.join(missing)}")

    transactions = []
    for line_no, row in enumerate(reader, start=2):  # header is line 1
        try:
            transactions.append(Transaction(
                transaction_id=row["transaction_id"].strip(),
                payer_id=row["payer_id"].strip(),
                participant_ids=[p.strip() for p in row["participant_ids"].split(";") if p.strip()],
                amount=float(row["amount"]),
                currency=row["currency"].strip().upper(),
            ))
        except (ValueError, AttributeError) as exc:
            raise ValueError(f"Row {line_no} is malformed: {exc}") from exc

    if not transactions:
        raise ValueError("CSV has no data rows.")
    return transactions
