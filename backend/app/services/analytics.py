"""
Analytics service.

Handles:
1. Monthly aggregation (computing snapshots from raw transactions)
2. Cash-flow truth screen (income vs essential vs discretionary vs savings)
3. Compound growth simulation (the core "opportunity cost" engine)
"""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import select, func, extract, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import (
    Transaction, MonthlySnapshot, Category,
    ESSENTIAL_CATEGORIES, DISCRETIONARY_CATEGORIES,
    INCOME_CATEGORIES, SAVINGS_CATEGORIES,
)
from app.schemas.transaction import (
    CategoryBreakdown, MonthlyOverview, CashFlowTruth,
    SimulationRequest, SimulationResult, SimulationYear,
)


async def compute_monthly_snapshot(
    db: AsyncSession, year: int, month: int
) -> MonthlySnapshot:
    """Compute and cache monthly aggregates from raw transactions."""

    # Fetch all non-excluded transactions for the month
    stmt = select(Transaction).where(
        and_(
            extract("year", Transaction.transaction_date) == year,
            extract("month", Transaction.transaction_date) == month,
            Transaction.is_excluded == False,
        )
    )
    result = await db.execute(stmt)
    transactions = result.scalars().all()

    if not transactions:
        return None

    # Compute totals
    total_income = sum(t.amount for t in transactions if t.amount > 0)
    total_expenses = abs(sum(t.amount for t in transactions if t.amount < 0))
    total_essential = abs(sum(
        t.amount for t in transactions
        if t.amount < 0 and t.category in ESSENTIAL_CATEGORIES
    ))
    total_discretionary = abs(sum(
        t.amount for t in transactions
        if t.amount < 0 and t.category in DISCRETIONARY_CATEGORIES
    ))
    total_savings = abs(sum(
        t.amount for t in transactions
        if t.amount < 0 and t.category in SAVINGS_CATEGORIES
    ))

    net_cashflow = total_income - total_expenses
    savings_rate = (
        float(total_savings / total_income * 100) if total_income > 0 else 0.0
    )

    # Category breakdown
    category_totals = {}
    for t in transactions:
        if t.amount < 0:  # Only expenses
            cat = t.category.value
            if cat not in category_totals:
                category_totals[cat] = {"total": 0, "count": 0}
            category_totals[cat]["total"] += float(abs(t.amount))
            category_totals[cat]["count"] += 1

    # Upsert snapshot
    existing = await db.execute(
        select(MonthlySnapshot).where(
            and_(MonthlySnapshot.year == year, MonthlySnapshot.month == month)
        )
    )
    snapshot = existing.scalar_one_or_none()

    if snapshot:
        snapshot.total_income = total_income
        snapshot.total_expenses = total_expenses
        snapshot.total_essential = total_essential
        snapshot.total_discretionary = total_discretionary
        snapshot.total_savings = total_savings
        snapshot.net_cashflow = net_cashflow
        snapshot.savings_rate = Decimal(str(round(savings_rate, 2)))
        snapshot.category_totals = json.dumps(category_totals)
        snapshot.transaction_count = len(transactions)
        snapshot.computed_at = datetime.utcnow()
    else:
        snapshot = MonthlySnapshot(
            year=year,
            month=month,
            total_income=total_income,
            total_expenses=total_expenses,
            total_essential=total_essential,
            total_discretionary=total_discretionary,
            total_savings=total_savings,
            net_cashflow=net_cashflow,
            savings_rate=Decimal(str(round(savings_rate, 2))),
            category_totals=json.dumps(category_totals),
            transaction_count=len(transactions),
        )
        db.add(snapshot)

    await db.commit()
    await db.refresh(snapshot)
    return snapshot


async def get_monthly_overview(
    db: AsyncSession, year: int, month: int
) -> Optional[MonthlyOverview]:
    """Get or compute a monthly overview."""
    snapshot = await compute_monthly_snapshot(db, year, month)
    if not snapshot:
        return None

    category_totals = json.loads(snapshot.category_totals or "{}")
    total_exp = float(snapshot.total_expenses) if snapshot.total_expenses else 1

    categories = [
        CategoryBreakdown(
            category=cat,
            total=Decimal(str(round(data["total"], 2))),
            percentage=round(data["total"] / total_exp * 100, 1),
            transaction_count=data["count"],
        )
        for cat, data in sorted(
            category_totals.items(), key=lambda x: x[1]["total"], reverse=True
        )
    ]

    return MonthlyOverview(
        year=snapshot.year,
        month=snapshot.month,
        total_income=snapshot.total_income,
        total_expenses=snapshot.total_expenses,
        total_essential=snapshot.total_essential,
        total_discretionary=snapshot.total_discretionary,
        total_savings=snapshot.total_savings,
        net_cashflow=snapshot.net_cashflow,
        savings_rate=float(snapshot.savings_rate) if snapshot.savings_rate else 0,
        categories=categories,
    )


async def get_cashflow_truth(
    db: AsyncSession,
    start_date: date,
    end_date: date,
) -> CashFlowTruth:
    """The core truth screen — where does your money actually go?"""
    stmt = select(Transaction).where(
        and_(
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
            Transaction.is_excluded == False,
        )
    )
    result = await db.execute(stmt)
    transactions = result.scalars().all()

    income = sum(t.amount for t in transactions if t.amount > 0)
    essential = abs(sum(
        t.amount for t in transactions
        if t.amount < 0 and t.category in ESSENTIAL_CATEGORIES
    ))
    discretionary = abs(sum(
        t.amount for t in transactions
        if t.amount < 0 and t.category in DISCRETIONARY_CATEGORIES
    ))
    savings = abs(sum(
        t.amount for t in transactions
        if t.amount < 0 and t.category in SAVINGS_CATEGORIES
    ))
    total_accounted = essential + discretionary + savings
    total_expenses = abs(sum(t.amount for t in transactions if t.amount < 0))
    unaccounted = total_expenses - total_accounted

    income_f = float(income) if income > 0 else 1

    # Top discretionary categories
    disc_breakdown = {}
    for t in transactions:
        if t.amount < 0 and t.category in DISCRETIONARY_CATEGORIES:
            cat = t.category.value
            if cat not in disc_breakdown:
                disc_breakdown[cat] = {"total": 0, "count": 0}
            disc_breakdown[cat]["total"] += float(abs(t.amount))
            disc_breakdown[cat]["count"] += 1

    top_disc = [
        CategoryBreakdown(
            category=cat,
            total=Decimal(str(round(data["total"], 2))),
            percentage=round(data["total"] / income_f * 100, 1),
            transaction_count=data["count"],
        )
        for cat, data in sorted(
            disc_breakdown.items(), key=lambda x: x[1]["total"], reverse=True
        )[:5]
    ]

    return CashFlowTruth(
        period_start=start_date,
        period_end=end_date,
        income=income,
        essential_spend=essential,
        discretionary_spend=discretionary,
        savings_outflows=savings,
        unaccounted=Decimal(str(round(float(unaccounted), 2))),
        essential_pct=round(float(essential) / income_f * 100, 1),
        discretionary_pct=round(float(discretionary) / income_f * 100, 1),
        savings_pct=round(float(savings) / income_f * 100, 1),
        top_discretionary=top_disc,
    )


def run_simulation(req: SimulationRequest) -> SimulationResult:
    """
    Deterministic compound growth simulation.

    This is the CORE of the product — showing opportunity cost:
    "If you redirected £X/month, here's what it could grow to."

    Uses simple compound interest with monthly contributions.
    Formula: FV = P * ((1+r)^n - 1) / r  (future value of annuity)
    But we compute year-by-year for the projection table.
    """
    monthly = float(req.monthly_amount)
    annual_return = req.annual_return
    monthly_return = annual_return / 12
    inflation = req.inflation_rate
    years = req.years

    projections = []
    nominal_balance = 0.0
    total_contributed = 0.0

    for year in range(1, years + 1):
        # Simulate 12 months of contributions + growth
        for _ in range(12):
            nominal_balance = (nominal_balance + monthly) * (1 + monthly_return)
            total_contributed += monthly

        # Real value adjusted for inflation
        real_value = nominal_balance / ((1 + inflation) ** year)
        growth = nominal_balance - total_contributed

        projections.append(SimulationYear(
            year=year,
            nominal_value=Decimal(str(round(nominal_balance, 2))),
            real_value=Decimal(str(round(real_value, 2))),
            total_contributed=Decimal(str(round(total_contributed, 2))),
            growth=Decimal(str(round(growth, 2))),
        ))

    final = projections[-1]

    return SimulationResult(
        monthly_amount=req.monthly_amount,
        annual_return=annual_return,
        years=years,
        inflation_rate=inflation,
        projections=projections,
        final_nominal=final.nominal_value,
        final_real=final.real_value,
        total_contributed=final.total_contributed,
        total_growth_nominal=final.growth,
    )


async def build_ai_summary(db: AsyncSession, months: int = 3) -> dict:
    """
    Build an AGGREGATED summary safe to send to AI.
    NO raw transactions, NO merchant names, NO personal identifiers.
    """
    today = date.today()
    start_month = today.month - months
    start_year = today.year
    if start_month <= 0:
        start_month += 12
        start_year -= 1

    snapshots = []
    for i in range(months):
        m = start_month + i
        y = start_year
        if m > 12:
            m -= 12
            y += 1
        overview = await get_monthly_overview(db, y, m)
        if overview:
            snapshots.append({
                "period": f"{y}-{m:02d}",
                "income": str(overview.total_income),
                "expenses": str(overview.total_expenses),
                "essential": str(overview.total_essential),
                "discretionary": str(overview.total_discretionary),
                "savings": str(overview.total_savings),
                "savings_rate": f"{overview.savings_rate:.1f}%",
                "top_categories": [
                    {"name": c.category, "amount": str(c.total), "pct": f"{c.percentage}%"}
                    for c in overview.categories[:6]
                ],
            })

    return {
        "months_analysed": len(snapshots),
        "monthly_data": snapshots,
        "currency": "GBP",
    }
