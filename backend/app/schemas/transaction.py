from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from app.models.transaction import Bank, Category


# ── Transaction schemas ──

class TransactionOut(BaseModel):
    id: int
    bank: Bank
    transaction_date: date
    amount: Decimal
    currency: str
    description: str
    merchant: Optional[str]
    category: Category
    category_confirmed: bool
    is_excluded: bool

    model_config = {"from_attributes": True}


class TransactionUpdate(BaseModel):
    category: Optional[Category] = None
    category_confirmed: Optional[bool] = None
    is_excluded: Optional[bool] = None
    notes: Optional[str] = None


class UploadResponse(BaseModel):
    imported: int
    duplicates_skipped: int
    errors: int
    message: str


# ── Snapshot / Analytics schemas ──

class CategoryBreakdown(BaseModel):
    category: str
    total: Decimal
    percentage: float
    transaction_count: int


class MonthlyOverview(BaseModel):
    year: int
    month: int
    total_income: Decimal
    total_expenses: Decimal
    total_essential: Decimal
    total_discretionary: Decimal
    total_savings: Decimal
    net_cashflow: Decimal
    savings_rate: Optional[float]
    categories: list[CategoryBreakdown]


class CashFlowTruth(BaseModel):
    """The core 'truth screen' — where does your money actually go?"""
    period_start: date
    period_end: date
    income: Decimal
    essential_spend: Decimal
    discretionary_spend: Decimal
    savings_outflows: Decimal
    unaccounted: Decimal
    essential_pct: float
    discretionary_pct: float
    savings_pct: float
    top_discretionary: list[CategoryBreakdown]


# ── Simulation schemas ──

class SimulationRequest(BaseModel):
    monthly_amount: Decimal = Field(..., gt=0, description="Monthly redirect amount in GBP")
    annual_return: float = Field(default=0.07, ge=0, le=0.30)
    years: int = Field(default=10, ge=1, le=50)
    inflation_rate: float = Field(default=0.025, ge=0, le=0.15)


class SimulationYear(BaseModel):
    year: int
    nominal_value: Decimal
    real_value: Decimal
    total_contributed: Decimal
    growth: Decimal


class SimulationResult(BaseModel):
    monthly_amount: Decimal
    annual_return: float
    years: int
    inflation_rate: float
    projections: list[SimulationYear]
    final_nominal: Decimal
    final_real: Decimal
    total_contributed: Decimal
    total_growth_nominal: Decimal
    disclaimer: str = (
        "This is a hypothetical illustration using assumed constant returns. "
        "Actual investment returns vary and can be negative. "
        "Past performance is not a guide to future performance. "
        "This is not financial advice."
    )


# ── AI Insight schemas ──

class InsightRequest(BaseModel):
    months: int = Field(default=3, ge=1, le=12, description="Months of data to analyse")


class InsightResponse(BaseModel):
    insight: str
    data_summary: dict
    generated_at: datetime
    model_used: str
    disclaimer: str = (
        "This is AI-generated financial education, not personalised financial advice. "
        "For advice tailored to your circumstances, consult a qualified financial adviser."
    )
