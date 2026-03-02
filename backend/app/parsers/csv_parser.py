"""
Bank CSV parsers.

Monzo CSV columns: Transaction ID, Date, Time, Type, Name, Emoji, Category,
                   Amount, Currency, Local amount, Local currency, Notes and #tags,
                   Address, Receipt, Description, Category split, Money Out, Money In

Starling CSV columns: Date, Counter Party, Reference, Type, Amount (GBP), Balance (GBP),
                      Spending Category
"""

import pandas as pd
import hashlib
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import List, Tuple
from app.models.transaction import Bank, Category


# ── Category mapping from bank categories to our standard categories ──

MONZO_CATEGORY_MAP = {
    "eating out": Category.EATING_OUT,
    "entertainment": Category.ENTERTAINMENT,
    "groceries": Category.GROCERIES,
    "shopping": Category.SHOPPING,
    "transport": Category.TRANSPORT,
    "bills": Category.UTILITIES,
    "personal care": Category.PERSONAL_CARE,
    "general": Category.UNCATEGORISED,
    "finances": Category.SAVINGS,
    "holidays": Category.TRAVEL,
    "family": Category.GIFTS,
    "charity": Category.GIFTS,
    "expenses": Category.UNCATEGORISED,
    "income": Category.SALARY,
}

STARLING_CATEGORY_MAP = {
    "eating out": Category.EATING_OUT,
    "entertainment": Category.ENTERTAINMENT,
    "groceries": Category.GROCERIES,
    "shopping": Category.SHOPPING,
    "transport": Category.TRANSPORT,
    "bills and services": Category.UTILITIES,
    "bills": Category.UTILITIES,
    "personal care": Category.PERSONAL_CARE,
    "general": Category.UNCATEGORISED,
    "saving": Category.SAVINGS,
    "savings": Category.SAVINGS,
    "holidays": Category.TRAVEL,
    "home": Category.HOUSING,
    "family": Category.GIFTS,
    "charity": Category.GIFTS,
    "income": Category.SALARY,
    "salary": Category.SALARY,
    "expenses": Category.UNCATEGORISED,
    "none": Category.UNCATEGORISED,
    "payments": Category.UNCATEGORISED,
    "lifestyle": Category.ENTERTAINMENT,
}

# Keyword-based fallback categorisation
KEYWORD_RULES = {
    Category.GROCERIES: [
        "tesco", "sainsbury", "asda", "aldi", "lidl", "morrisons", "waitrose",
        "co-op", "ocado", "iceland", "m&s food",
    ],
    Category.EATING_OUT: [
        "nandos", "mcdonald", "burger king", "kfc", "greggs", "pret",
        "starbucks", "costa", "deliveroo", "uber eats", "just eat",
    ],
    Category.TRANSPORT: [
        "tfl", "uber", "bolt", "trainline", "national rail", "citymapper",
        "bp", "shell", "esso", "petrol", "parking",
    ],
    Category.SUBSCRIPTIONS: [
        "netflix", "spotify", "amazon prime", "disney+", "apple.com/bill",
        "youtube", "gym", "puregym", "the gym",
    ],
    Category.UTILITIES: [
        "british gas", "edf", "octopus energy", "bulb", "thames water",
        "bt ", "vodafone", "ee ", "three", "o2 ",
        "council tax", "tv licence",
    ],
    Category.HOUSING: ["rent", "mortgage", "letting agent"],
    Category.SHOPPING: [
        "amazon", "ebay", "argos", "john lewis", "primark", "next ",
        "asos", "zara", "h&m",
    ],
    Category.SALARY: ["salary", "wages", "payroll"],
    Category.TRANSFER: ["transfer", "pot", "monzo", "starling"],
}


def _categorise_by_keywords(description: str, merchant: str | None) -> Category:
    text = f"{description} {merchant or ''}".lower()
    for category, keywords in KEYWORD_RULES.items():
        for keyword in keywords:
            if keyword in text:
                return category
    return Category.UNCATEGORISED


def _safe_decimal(value) -> Decimal:
    if pd.isna(value) or value == "":
        return Decimal("0.00")
    cleaned = str(value).replace("£", "").replace(",", "").strip()
    try:
        return Decimal(cleaned).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return Decimal("0.00")


def _generate_txn_id(bank: Bank, row_data: str) -> str:
    return hashlib.sha256(f"{bank.value}:{row_data}".encode()).hexdigest()[:32]


def parse_monzo_csv(file_content: bytes) -> Tuple[List[dict], List[str]]:
    import io
    df = pd.read_csv(io.BytesIO(file_content))
    transactions, errors = [], []

    for idx, row in df.iterrows():
        try:
            bank_txn_id = str(row.get("Transaction ID", "")).strip()
            if not bank_txn_id or bank_txn_id == "nan":
                bank_txn_id = _generate_txn_id(
                    Bank.MONZO,
                    f"{row.get('Date', '')}{row.get('Amount', '')}{row.get('Name', '')}"
                )

            date_str = str(row.get("Date", "")).strip()
            try:
                txn_date = pd.to_datetime(date_str, dayfirst=True).date()
            except Exception:
                txn_date = pd.to_datetime(date_str).date()

            amount = _safe_decimal(row.get("Amount", 0))
            name = str(row.get("Name", "")).strip()
            description = str(row.get("Description", name)).strip()
            if description == "nan":
                description = name
            merchant = name if name != "nan" else None

            monzo_cat = str(row.get("Category", "")).strip().lower()
            category = MONZO_CATEGORY_MAP.get(monzo_cat, Category.UNCATEGORISED)
            if category == Category.UNCATEGORISED:
                category = _categorise_by_keywords(description, merchant)
            if amount > 0 and category == Category.UNCATEGORISED:
                category = Category.OTHER_INCOME

            transactions.append({
                "bank": Bank.MONZO,
                "bank_transaction_id": bank_txn_id,
                "transaction_date": txn_date,
                "amount": amount,
                "currency": str(row.get("Currency", "GBP")).strip(),
                "description": description[:500],
                "merchant": merchant[:255] if merchant else None,
                "category": category,
            })
        except Exception as e:
            errors.append(f"Row {idx}: {str(e)}")

    return transactions, errors


def parse_starling_csv(file_content: bytes) -> Tuple[List[dict], List[str]]:
    import io
    df = pd.read_csv(io.BytesIO(file_content))
    transactions, errors = [], []

    for idx, row in df.iterrows():
        try:
            date_str = str(row.get("Date", "")).strip()
            try:
                txn_date = pd.to_datetime(date_str, dayfirst=True).date()
            except Exception:
                txn_date = pd.to_datetime(date_str).date()

            amount = _safe_decimal(row.get("Amount (GBP)", row.get("Amount", 0)))
            counter_party = str(row.get("Counter Party", "")).strip()
            reference = str(row.get("Reference", "")).strip()
            description = counter_party if counter_party != "nan" else reference
            if description == "nan":
                description = str(row.get("Type", "Unknown"))
            merchant = counter_party if counter_party != "nan" else None

            bank_txn_id = _generate_txn_id(
                Bank.STARLING,
                f"{date_str}{amount}{counter_party}{reference}"
            )

            starling_cat = str(row.get("Spending Category", "")).strip().lower()
            category = STARLING_CATEGORY_MAP.get(starling_cat, Category.UNCATEGORISED)
            if category == Category.UNCATEGORISED:
                category = _categorise_by_keywords(description, merchant)
            if amount > 0 and category == Category.UNCATEGORISED:
                category = Category.OTHER_INCOME

            transactions.append({
                "bank": Bank.STARLING,
                "bank_transaction_id": bank_txn_id,
                "transaction_date": txn_date,
                "amount": amount,
                "currency": "GBP",
                "description": description[:500],
                "merchant": merchant[:255] if merchant else None,
                "category": category,
            })
        except Exception as e:
            errors.append(f"Row {idx}: {str(e)}")

    return transactions, errors


def parse_csv(file_content: bytes, bank: Bank) -> Tuple[List[dict], List[str]]:
    if bank == Bank.MONZO:
        return parse_monzo_csv(file_content)
    elif bank == Bank.STARLING:
        return parse_starling_csv(file_content)
    else:
        raise ValueError(f"Unsupported bank: {bank}")
