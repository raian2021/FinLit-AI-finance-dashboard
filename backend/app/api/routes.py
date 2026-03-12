from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.ai_client import get_ai_client, FINANCIAL_EDUCATOR_PROMPT
from app.models.transaction import Transaction, Bank
from app.models.user import User
from app.schemas.transaction import (
    UploadResponse,
    CashFlowTruth,
    MonthlyOverview,
    SimulationRequest,
    SimulationResult,
    InsightRequest,
    InsightResponse,
)
from app.services.importer import import_transactions
from app.services.analytics import get_cashflow_truth, get_monthly_overview, run_simulation, build_ai_summary

router = APIRouter(prefix="/api/v1")


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/stats")
async def stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = await db.scalar(
        select(func.count()).select_from(Transaction).where(Transaction.user_id == current_user.id)
    )
    earliest = await db.scalar(
        select(func.min(Transaction.transaction_date)).where(Transaction.user_id == current_user.id)
    )
    latest = await db.scalar(
        select(func.max(Transaction.transaction_date)).where(Transaction.user_id == current_user.id)
    )
    return {
        "total_transactions": int(total or 0),
        "earliest_date": earliest.isoformat() if earliest else None,
        "latest_date": latest.isoformat() if latest else None,
    }


@router.post("/transactions/upload", response_model=UploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    bank: str = Form(..., description="monzo or starling"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only CSV files are supported")

    content = await file.read()
    if len(content) > 10_000_000:
        raise HTTPException(400, "File too large (max 10MB)")

    bank = bank.strip().lower()
    if bank not in ("monzo", "starling"):
        raise HTTPException(400, "bank must be 'monzo' or 'starling'")

    bank_enum = Bank.MONZO if bank == "monzo" else Bank.STARLING
    return await import_transactions(db, content, bank_enum, current_user.id)


@router.get("/analytics/cashflow", response_model=CashFlowTruth)
async def cashflow(
    months: int = Query(3, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    end = date.today()
    start = end - timedelta(days=30 * months)
    return await get_cashflow_truth(db, start, end, current_user.id)


@router.get("/analytics/periods")
async def periods(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (await db.execute(
        select(
            extract("year", Transaction.transaction_date).label("year"),
            extract("month", Transaction.transaction_date).label("month"),
            func.count().label("transaction_count"),
        )
        .where(Transaction.is_excluded == False)
        .where(Transaction.user_id == current_user.id)
        .group_by("year", "month")
        .order_by("year", "month")
    )).all()

    return [
        {"year": int(r.year), "month": int(r.month), "transaction_count": int(r.transaction_count)}
        for r in rows
    ]


@router.get("/analytics/monthly/{year}/{month}", response_model=MonthlyOverview)
async def monthly(
    year: int,
    month: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not (1 <= month <= 12) or not (2000 <= year <= 2100):
        raise HTTPException(400, "Invalid year/month")

    overview = await get_monthly_overview(db, year, month, current_user.id)
    if not overview:
        raise HTTPException(404, "No data for that period")
    return overview


@router.post("/simulate", response_model=SimulationResult)
async def simulate(
    req: SimulationRequest,
    current_user: User = Depends(get_current_user),
):
    return run_simulation(req)


@router.post("/insights", response_model=InsightResponse)
async def insights(
    req: InsightRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    summary = await build_ai_summary(db, months=req.months, user_id=current_user.id)

    client = get_ai_client()
    user_message = (
        "Create a short, structured financial education summary of this user's spending.\n\n"
        f"DATA (aggregated):\n{summary}"
    )
    text = await client.generate(FINANCIAL_EDUCATOR_PROMPT, user_message)

    return InsightResponse(
        insight=text,
        data_summary=summary,
        generated_at=datetime.utcnow(),
        model_used=f"{type(client).__name__}",
    )
