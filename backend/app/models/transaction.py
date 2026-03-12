"""
Database models.

Design decisions:
- Transactions store category as enum, not FK — simpler for MVP, easy to migrate later
- We store original merchant name for your own reference but NEVER send it to AI
- Monthly snapshots cache aggregated data to avoid recomputing on every request
"""

import enum
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    String, Numeric, Date, DateTime, Enum, Text, Integer, Boolean, Index, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Bank(str, enum.Enum):
    MONZO = "monzo"
    STARLING = "starling"


class Category(str, enum.Enum):
    # Essentials
    HOUSING = "housing"
    UTILITIES = "utilities"
    GROCERIES = "groceries"
    TRANSPORT = "transport"
    INSURANCE = "insurance"
    HEALTHCARE = "healthcare"

    # Discretionary
    EATING_OUT = "eating_out"
    ENTERTAINMENT = "entertainment"
    SHOPPING = "shopping"
    SUBSCRIPTIONS = "subscriptions"
    PERSONAL_CARE = "personal_care"
    TRAVEL = "travel"
    GIFTS = "gifts"

    # Financial
    SAVINGS = "savings"
    INVESTMENTS = "investments"
    DEBT_REPAYMENT = "debt_repayment"

    # Income
    SALARY = "salary"
    FREELANCE = "freelance"
    OTHER_INCOME = "other_income"

    # Meta
    TRANSFER = "transfer"
    CASH = "cash"
    UNCATEGORISED = "uncategorised"


# Which categories are essential vs discretionary
ESSENTIAL_CATEGORIES = {
    Category.HOUSING, Category.UTILITIES, Category.GROCERIES,
    Category.TRANSPORT, Category.INSURANCE, Category.HEALTHCARE,
}

DISCRETIONARY_CATEGORIES = {
    Category.EATING_OUT, Category.ENTERTAINMENT, Category.SHOPPING,
    Category.SUBSCRIPTIONS, Category.PERSONAL_CARE, Category.TRAVEL,
    Category.GIFTS,
}

INCOME_CATEGORIES = {
    Category.SALARY, Category.FREELANCE, Category.OTHER_INCOME,
}

SAVINGS_CATEGORIES = {
    Category.SAVINGS, Category.INVESTMENTS, Category.DEBT_REPAYMENT,
}


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Source
    bank: Mapped[Bank] = mapped_column(Enum(Bank), nullable=False)
    bank_transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Core fields
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="GBP")
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    merchant: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Categorisation
    category: Mapped[Category] = mapped_column(
        Enum(Category), default=Category.UNCATEGORISED
    )
    category_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_excluded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_txn_date", "transaction_date"),
        Index("ix_txn_category", "category"),
        Index("ix_txn_bank_id", "user_id", "bank", "bank_transaction_id", unique=True),
    )

    @property
    def is_income(self) -> bool:
        return self.amount > 0

    @property
    def is_expense(self) -> bool:
        return self.amount < 0


class MonthlySnapshot(Base):
    """Pre-computed monthly aggregates. This is what gets sent to AI — never raw transactions."""
    __tablename__ = "monthly_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)

    # Totals
    total_income: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_expenses: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_essential: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_discretionary: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_savings: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    net_cashflow: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    # Category breakdown (JSON-like text for flexibility)
    category_totals: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Stats
    transaction_count: Mapped[int] = mapped_column(Integer, default=0)
    savings_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Metadata
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_snapshot_period", "user_id", "year", "month", unique=True),
    )
