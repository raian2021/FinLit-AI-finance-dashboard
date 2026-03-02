"""Generate sample Monzo and Starling CSV files for testing."""

import csv
import random
from datetime import datetime, timedelta
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sample")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Sample data pools ──

MERCHANTS = {
    "eating_out": [
        ("Nando's", -15.50), ("Greggs", -4.20), ("Pret A Manger", -6.80),
        ("Deliveroo", -22.40), ("McDonald's", -8.90), ("Costa Coffee", -4.50),
        ("Uber Eats", -18.60), ("Wagamama", -14.30),
    ],
    "groceries": [
        ("Tesco", -45.60), ("Sainsbury's", -38.20), ("Aldi", -28.90),
        ("Lidl", -22.40), ("Co-op", -12.50), ("Ocado", -85.30),
    ],
    "transport": [
        ("TfL", -7.20), ("Uber", -12.80), ("Bolt", -9.40),
        ("Trainline", -35.60), ("Shell Petrol", -55.00),
    ],
    "shopping": [
        ("Amazon", -29.99), ("ASOS", -45.00), ("Primark", -32.00),
        ("Argos", -19.99), ("John Lewis", -65.00),
    ],
    "subscriptions": [
        ("Netflix", -15.99), ("Spotify", -10.99), ("Amazon Prime", -8.99),
        ("PureGym", -24.99), ("Disney+", -7.99), ("YouTube Premium", -12.99),
    ],
    "bills": [
        ("Octopus Energy", -95.00), ("Thames Water", -35.00),
        ("Council Tax", -145.00), ("Vodafone", -28.00), ("BT Broadband", -32.00),
    ],
    "housing": [
        ("Rent - Letting Agent", -850.00),
    ],
    "income": [
        ("Salary - Odgers", 2800.00),
    ],
    "savings": [
        ("Transfer to Savings Pot", -200.00), ("ISA Contribution", -100.00),
    ],
}


def generate_monzo_csv(months: int = 3):
    """Generate a realistic Monzo CSV export."""
    filepath = os.path.join(OUTPUT_DIR, "monzo_sample.csv")

    headers = [
        "Transaction ID", "Date", "Time", "Type", "Name", "Emoji", "Category",
        "Amount", "Currency", "Local amount", "Local currency", "Notes and #tags",
        "Address", "Receipt", "Description", "Category split", "Money Out", "Money In",
    ]

    rows = []
    base_date = datetime.now() - timedelta(days=30 * months)

    for day_offset in range(30 * months):
        current_date = base_date + timedelta(days=day_offset)
        date_str = current_date.strftime("%d/%m/%Y")

        # Salary on 28th
        if current_date.day == 28:
            name, amount = MERCHANTS["income"][0]
            rows.append([
                f"tx_monzo_{len(rows):04d}", date_str, "09:00:00", "Faster payment",
                name, "", "income", f"{amount:.2f}", "GBP", f"{amount:.2f}", "GBP",
                "", "", "", f"SALARY {name}", "", "", f"{amount:.2f}",
            ])

        # Rent on 1st
        if current_date.day == 1:
            name, amount = MERCHANTS["housing"][0]
            rows.append([
                f"tx_monzo_{len(rows):04d}", date_str, "08:00:00", "Direct debit",
                name, "🏠", "bills", f"{amount:.2f}", "GBP", f"{amount:.2f}", "GBP",
                "", "", "", name, "", f"{abs(amount):.2f}", "",
            ])

        # Savings on 1st
        if current_date.day == 1:
            for name, amount in MERCHANTS["savings"]:
                rows.append([
                    f"tx_monzo_{len(rows):04d}", date_str, "10:00:00", "Pot transfer",
                    name, "💰", "finances", f"{amount:.2f}", "GBP", f"{amount:.2f}",
                    "GBP", "", "", "", name, "", f"{abs(amount):.2f}", "",
                ])

        # Bills spread through month
        if current_date.day in [3, 5, 8, 12, 15]:
            bill_idx = current_date.day % len(MERCHANTS["bills"])
            name, amount = MERCHANTS["bills"][bill_idx]
            rows.append([
                f"tx_monzo_{len(rows):04d}", date_str, "07:00:00", "Direct debit",
                name, "📄", "bills", f"{amount:.2f}", "GBP", f"{amount:.2f}", "GBP",
                "", "", "", name, "", f"{abs(amount):.2f}", "",
            ])

        # Daily spending (1-4 transactions per day)
        daily_txns = random.randint(1, 4)
        for _ in range(daily_txns):
            cat = random.choice(["eating_out", "groceries", "transport", "shopping", "subscriptions"])

            # Subscriptions only once a month
            if cat == "subscriptions" and current_date.day != 15:
                cat = "eating_out"

            name, base_amount = random.choice(MERCHANTS[cat])
            # Add some variance
            amount = round(base_amount * random.uniform(0.8, 1.3), 2)
            time_str = f"{random.randint(7, 22):02d}:{random.randint(0, 59):02d}:00"

            monzo_cat = cat.replace("_", " ")
            if cat == "subscriptions":
                monzo_cat = "bills"

            rows.append([
                f"tx_monzo_{len(rows):04d}", date_str, time_str, "Card payment",
                name, "", monzo_cat, f"{amount:.2f}", "GBP", f"{amount:.2f}", "GBP",
                "", "", "", f"Card payment to {name}", "", f"{abs(amount):.2f}", "",
            ])

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"✓ Generated {len(rows)} Monzo transactions → {filepath}")
    return filepath


def generate_starling_csv(months: int = 3):
    """Generate a realistic Starling Bank CSV export."""
    filepath = os.path.join(OUTPUT_DIR, "starling_sample.csv")

    headers = ["Date", "Counter Party", "Reference", "Type", "Amount (GBP)", "Balance (GBP)", "Spending Category"]

    rows = []
    balance = 1500.00
    base_date = datetime.now() - timedelta(days=30 * months)

    for day_offset in range(30 * months):
        current_date = base_date + timedelta(days=day_offset)
        date_str = current_date.strftime("%d/%m/%Y")

        # Salary
        if current_date.day == 28:
            name, amount = "Odgers Berndtson", 2800.00
            balance += amount
            rows.append([date_str, name, "SALARY", "FASTER PAYMENT", f"{amount:.2f}", f"{balance:.2f}", "INCOME"])

        # Rent
        if current_date.day == 1:
            balance -= 850
            rows.append([date_str, "Letting Agent Ltd", "RENT", "DIRECT DEBIT", "-850.00", f"{balance:.2f}", "HOME"])

        # Daily transactions
        for _ in range(random.randint(1, 3)):
            cat = random.choice(["eating_out", "groceries", "transport", "shopping"])
            name, base_amount = random.choice(MERCHANTS[cat])
            amount = round(base_amount * random.uniform(0.8, 1.3), 2)
            balance += amount  # amount is negative

            starling_cat_map = {
                "eating_out": "EATING OUT",
                "groceries": "GROCERIES",
                "transport": "TRANSPORT",
                "shopping": "SHOPPING",
                "subscriptions": "BILLS AND SERVICES",
            }

            rows.append([
                date_str, name, f"CARD PAYMENT", "CARD",
                f"{amount:.2f}", f"{balance:.2f}", starling_cat_map.get(cat, "GENERAL"),
            ])

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"✓ Generated {len(rows)} Starling transactions → {filepath}")
    return filepath


if __name__ == "__main__":
    generate_monzo_csv(3)
    generate_starling_csv(3)
    print("\n✓ Sample data ready in data/sample/")
