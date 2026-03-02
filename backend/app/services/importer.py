"""Transaction import service with deduplication."""

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.transaction import Transaction, Bank
from app.parsers.csv_parser import parse_csv
from app.schemas.transaction import UploadResponse


async def import_transactions(
    db: AsyncSession,
    file_content: bytes,
    bank: Bank,
) -> UploadResponse:
    """Parse CSV and import transactions, skipping duplicates."""
    parsed, parse_errors = parse_csv(file_content, bank)

    imported = 0
    duplicates = 0

    for txn_data in parsed:
        # Check for duplicate by bank + bank_transaction_id
        existing = await db.execute(
            select(Transaction.id).where(
                and_(
                    Transaction.bank == txn_data["bank"],
                    Transaction.bank_transaction_id == txn_data["bank_transaction_id"],
                )
            )
        )
        if existing.scalar_one_or_none() is not None:
            duplicates += 1
            continue

        txn = Transaction(**txn_data)
        db.add(txn)
        imported += 1

    await db.commit()

    return UploadResponse(
        imported=imported,
        duplicates_skipped=duplicates,
        errors=len(parse_errors),
        message=f"Imported {imported} transactions from {bank.value}. "
                f"Skipped {duplicates} duplicates. {len(parse_errors)} errors.",
    )
