"""
Deflection ROI Calculator
==========================
Models the financial impact of automating deflectable support tickets.
Works standalone or imported by the analysis notebook.

Usage:
    python roi_model.py

Or import:
    from roi_model import calculate_roi, sensitivity_analysis
"""

import json
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CLASSIFIED_PATH = DATA_DIR / "tickets_classified.csv"
TAXONOMY_PATH   = DATA_DIR / "taxonomy.json"


# ─── Core ROI Calculator ──────────────────────────────────────────────────


def calculate_roi(
    df: pd.DataFrame = None,
    cost_per_human_ticket: float = 15.00,
    cost_per_automated_ticket: float = 1.50,
    monthly_ticket_volume: int = 5_000,
    deflection_multiplier: float = 1.0,
) -> dict:
    """
    Calculate ROI metrics for automated ticket deflection.

    Args:
        df: Classified tickets DataFrame (must have 'deflectable' column).
            If None, loads from data/tickets_classified.csv.
        cost_per_human_ticket: Fully-loaded cost per human-handled ticket ($).
        cost_per_automated_ticket: Cost per automated/deflected ticket ($).
        monthly_ticket_volume: Expected monthly ticket volume for the business.
        deflection_multiplier: Scale deflection rate (e.g., 0.8 = conservative).

    Returns:
        dict with full ROI metrics.
    """
    if df is None:
        if not CLASSIFIED_PATH.exists():
            raise FileNotFoundError(
                f"Classified tickets not found at {CLASSIFIED_PATH}.\n"
                "Run classifier.py first."
            )
        df = pd.read_csv(CLASSIFIED_PATH)

    if "deflectable" not in df.columns:
        raise ValueError("DataFrame must have a 'deflectable' column. Run classifier.py first.")

    total_sampled = len(df)
    deflectable_sampled = int(df["deflectable"].sum())
    deflection_rate_raw = deflectable_sampled / total_sampled

    # Apply multiplier (e.g., for conservative estimates)
    deflection_rate = deflection_rate_raw * deflection_multiplier

    # Monthly volumes
    monthly_deflected   = int(monthly_ticket_volume * deflection_rate)
    monthly_human       = monthly_ticket_volume - monthly_deflected

    # Monthly costs
    monthly_cost_current       = monthly_ticket_volume  * cost_per_human_ticket
    monthly_cost_automated     = (monthly_human         * cost_per_human_ticket
                                  + monthly_deflected   * cost_per_automated_ticket)
    monthly_savings            = monthly_cost_current - monthly_cost_automated

    # Annual
    annual_cost_current        = monthly_cost_current   * 12
    annual_cost_automated      = monthly_cost_automated * 12
    annual_savings             = monthly_savings        * 12

    # Savings per ticket
    savings_per_deflected_ticket = cost_per_human_ticket - cost_per_automated_ticket

    # Payback: assume $10K implementation cost (conservative)
    implementation_cost    = 10_000.0
    payback_period_months  = (
        implementation_cost / monthly_savings if monthly_savings > 0 else float("inf")
    )

    # Category-level breakdown
    category_breakdown = (
        df.groupby("predicted_category")["deflectable"]
        .agg(total="count", deflectable="sum")
        .assign(deflection_rate=lambda x: x["deflectable"] / x["total"])
        .sort_values("deflectable", ascending=False)
        .to_dict("index")
    )

    metrics = {
        # Sample stats
        "sample_size":                  total_sampled,
        "sample_deflectable":           deflectable_sampled,
        "deflection_rate_raw":          round(deflection_rate_raw, 4),
        "deflection_rate_applied":      round(deflection_rate, 4),

        # Volume
        "monthly_ticket_volume":        monthly_ticket_volume,
        "monthly_deflected":            monthly_deflected,
        "monthly_human_handled":        monthly_human,

        # Costs
        "cost_per_human_ticket":        cost_per_human_ticket,
        "cost_per_automated_ticket":    cost_per_automated_ticket,
        "savings_per_deflected_ticket": savings_per_deflected_ticket,

        "monthly_cost_current":         round(monthly_cost_current,    2),
        "monthly_cost_with_automation": round(monthly_cost_automated,  2),
        "monthly_savings":              round(monthly_savings,         2),

        "annual_cost_current":          round(annual_cost_current,     2),
        "annual_cost_with_automation":  round(annual_cost_automated,   2),
        "annual_savings":               round(annual_savings,          2),

        # Business case
        "implementation_cost_assumed":  implementation_cost,
        "payback_period_months":        round(payback_period_months, 1),
        "roi_year_1":                   round((annual_savings - implementation_cost) / implementation_cost * 100, 1),

        # Breakdown
        "category_breakdown":           category_breakdown,
    }

    return metrics


def sensitivity_analysis(
    df: pd.DataFrame = None,
    cost_per_human_ticket: float = 15.00,
    cost_per_automated_ticket: float = 1.50,
    volume_min: int = 1_000,
    volume_max: int = 20_000,
    volume_step: int = 1_000,
) -> pd.DataFrame:
    """
    Run ROI sensitivity analysis across a range of monthly ticket volumes.

    Returns:
        DataFrame with columns: monthly_volume, annual_savings, deflection_rate,
                                 payback_months
    """
    if df is None:
        if CLASSIFIED_PATH.exists():
            df = pd.read_csv(CLASSIFIED_PATH)
        else:
            # Use placeholder deflection rate if no classified data yet
            df = None

    rows = []
    volumes = range(volume_min, volume_max + volume_step, volume_step)
    for vol in volumes:
        try:
            m = calculate_roi(
                df=df,
                cost_per_human_ticket=cost_per_human_ticket,
                cost_per_automated_ticket=cost_per_automated_ticket,
                monthly_ticket_volume=vol,
            )
            rows.append({
                "monthly_volume":   vol,
                "annual_savings":   m["annual_savings"],
                "deflection_rate":  m["deflection_rate_applied"],
                "payback_months":   m["payback_period_months"],
                "monthly_savings":  m["monthly_savings"],
                "annual_cost_current":       m["annual_cost_current"],
                "annual_cost_with_automation": m["annual_cost_with_automation"],
            })
        except Exception as e:
            print(f"  [WARN] Volume {vol}: {e}")

    return pd.DataFrame(rows)


def print_roi_report(metrics: dict):
    """Print a formatted ROI summary report."""
    sep = "=" * 60

    print(f"\n{sep}")
    print("DEFLECTION ROI REPORT")
    print(sep)

    print(f"\n{'CLASSIFICATION SAMPLE':}")
    print(f"  Tickets classified:     {metrics['sample_size']:,}")
    print(f"  Deflectable tickets:    {metrics['sample_deflectable']:,} "
          f"({metrics['deflection_rate_raw']:.1%})")

    print(f"\n{'VOLUME PROJECTIONS (at {n:,}/mo)'.format(n=metrics['monthly_ticket_volume']):}")
    print(f"  Monthly ticket volume:  {metrics['monthly_ticket_volume']:,}")
    print(f"  Deflected (automated):  {metrics['monthly_deflected']:,} tickets/mo")
    print(f"  Human-handled:          {metrics['monthly_human_handled']:,} tickets/mo")

    print(f"\n{'COST ASSUMPTIONS':}")
    print(f"  Cost per human ticket:     ${metrics['cost_per_human_ticket']:.2f}")
    print(f"  Cost per automated ticket: ${metrics['cost_per_automated_ticket']:.2f}")
    print(f"  Savings per deflection:    ${metrics['savings_per_deflected_ticket']:.2f}")

    print(f"\n{'FINANCIAL IMPACT':}")
    print(f"  Monthly cost (current):    ${metrics['monthly_cost_current']:>10,.2f}")
    print(f"  Monthly cost (automated):  ${metrics['monthly_cost_with_automation']:>10,.2f}")
    print(f"  Monthly savings:           ${metrics['monthly_savings']:>10,.2f}")
    print(f"  Annual savings:            ${metrics['annual_savings']:>10,.2f}")

    print(f"\n{'BUSINESS CASE':}")
    print(f"  Implementation cost:       ${metrics['implementation_cost_assumed']:>10,.2f}")
    print(f"  Payback period:            {metrics['payback_period_months']:.1f} months")
    print(f"  Year-1 ROI:                {metrics['roi_year_1']:.0f}%")

    print(f"\n{'DEFLECTION BY CATEGORY':}")
    for cat, data in metrics["category_breakdown"].items():
        rate = data.get("deflection_rate", 0)
        total = data.get("total", 0)
        deflectable = data.get("deflectable", 0)
        bar = "#" * int(rate * 20)
        print(f"  {cat:<26} {rate:>5.1%}  {bar}")

    print(f"\n{sep}")


def main():
    print("\nCalculating ROI...")
    df_to_use = None
    try:
        metrics = calculate_roi()
        if CLASSIFIED_PATH.exists():
            df_to_use = pd.read_csv(CLASSIFIED_PATH)
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        print("\nUsing sample deflection rate of 45% for demonstration.")
        # Create a minimal mock df for demonstration
        mock_data = [{"predicted_category": "Billing & Payments", "deflectable": True}] * 45
        mock_data += [{"predicted_category": "Technical Issue", "deflectable": False}] * 55
        df_to_use = pd.DataFrame(mock_data)
        metrics = calculate_roi(df=df_to_use)

    print_roi_report(metrics)

    print("\nSensitivity Analysis (Annual Savings by Ticket Volume):")
    print("-" * 50)

    try:
        sa = sensitivity_analysis(df=df_to_use)
        if not sa.empty:
            print(f"\n{'Volume/mo':<12} {'Annual Savings':<16} {'Payback':}")
            print("-" * 40)
            for _, row in sa.iterrows():
                vol = int(row["monthly_volume"])
                sav = row["annual_savings"]
                pb  = row["payback_months"]
                print(f"  {vol:>6,}      ${sav:>12,.0f}     {pb:.1f} mo")
    except Exception as e:
        print(f"  Could not run sensitivity analysis: {e}")

    return metrics


if __name__ == "__main__":
    main()
