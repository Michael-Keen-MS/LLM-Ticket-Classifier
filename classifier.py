"""
LLM Support Ticket Classifier
==============================
Classifies support tickets using Claude Haiku via the Anthropic API.
Outputs predicted category, priority, deflectable flag, confidence, and reasoning.

Usage:
    python classifier.py

Requires:
    ANTHROPIC_API_KEY environment variable set.
"""

import csv
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# ─── Auto-install anthropic if needed ──────────────────────────────────────
try:
    import anthropic
except ImportError:
    import subprocess
    print("Installing anthropic package...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "anthropic"])
    import anthropic

import pandas as pd

# ─── Paths ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TICKETS_PATH      = DATA_DIR / "tickets.csv"
TAXONOMY_PATH     = DATA_DIR / "taxonomy.json"
OUTPUT_PATH       = DATA_DIR / "tickets_classified.csv"

# ─── Load taxonomy ────────────────────────────────────────────────────────
with open(TAXONOMY_PATH, "r") as f:
    TAXONOMY = json.load(f)

CATEGORIES     = TAXONOMY["categories"]
PRIORITIES     = TAXONOMY["priority_levels"]
DEFLECTABLE    = set(TAXONOMY["deflectable"])

# ─── Model ────────────────────────────────────────────────────────────────
MODEL = "claude-haiku-4-5-20251001"

# ─── Prompt templates ────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a support ticket classifier for a fintech earned wage access company.
Your job is to classify each support ticket accurately and consistently.

You must respond with ONLY a valid JSON object — no markdown, no explanation, no extra text.

Classification rules:
- Category must be exactly one of the provided options
- Priority: Critical = fraud/security/funds at risk; High = can't access account or failed payment; Medium = billing/feature issue; Low = general question
- Deflectable = true if the ticket can be fully resolved by an automated system (FAQ, self-service, chatbot)
- Confidence: "high" if clear cut, "medium" if somewhat ambiguous, "low" if very unclear
- Reasoning: one sentence explaining the classification decision
"""

CLASSIFICATION_PROMPT = """Classify this support ticket:

Subject: {subject}
Body: {body}

Available categories: {categories}
Available priorities: {priorities}
Deflectable categories (can be automated): {deflectable}

Respond with this exact JSON structure:
{{
  "predicted_category": "<category>",
  "predicted_priority": "<priority>",
  "deflectable": <true or false>,
  "confidence": "<high|medium|low>",
  "reasoning": "<one sentence>"
}}"""


def get_client() -> anthropic.Anthropic:
    """Return an Anthropic client. Raises if API key is not set."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY environment variable is not set.\n"
            "Set it with:  $env:ANTHROPIC_API_KEY='your-key'  (PowerShell)\n"
            "         or:  export ANTHROPIC_API_KEY='your-key'  (bash)"
        )
    return anthropic.Anthropic(api_key=api_key)


def classify_single(subject: str, body: str, client: anthropic.Anthropic = None) -> dict:
    """
    Classify a single ticket.

    Args:
        subject: Ticket subject line
        body: Ticket body text
        client: Optional pre-created Anthropic client

    Returns:
        dict with keys: predicted_category, predicted_priority, deflectable,
                        confidence, reasoning
    """
    if client is None:
        client = get_client()

    prompt = CLASSIFICATION_PROMPT.format(
        subject=subject,
        body=body,
        categories=", ".join(CATEGORIES),
        priorities=", ".join(PRIORITIES),
        deflectable=", ".join(DEFLECTABLE),
    )

    message = client.messages.create(
        model=MODEL,
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Parse JSON — be tolerant of minor formatting issues
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON from the response if there's extra text
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
        else:
            # Return a fallback with raw text logged
            print(f"  [WARN] Could not parse JSON: {raw[:100]}")
            result = {
                "predicted_category": "General Inquiry",
                "predicted_priority": "Low",
                "deflectable": False,
                "confidence": "low",
                "reasoning": "Parse error — could not extract structured response.",
            }

    # Validate and normalize
    if result.get("predicted_category") not in CATEGORIES:
        result["predicted_category"] = "General Inquiry"
    if result.get("predicted_priority") not in PRIORITIES:
        result["predicted_priority"] = "Medium"
    result["deflectable"] = bool(result.get("deflectable", False))

    return result


def classify_batch(df: pd.DataFrame, client: anthropic.Anthropic,
                   rate_limit_delay: float = 1.5) -> pd.DataFrame:
    """
    Classify all tickets in a DataFrame.

    Args:
        df: DataFrame with 'subject' and 'body' columns
        client: Anthropic client
        rate_limit_delay: Seconds to sleep between API calls

    Returns:
        DataFrame with classification columns added
    """
    results = []
    total = len(df)

    print(f"\nClassifying {total} tickets using {MODEL}...")
    print("─" * 60)

    for idx, row in df.iterrows():
        ticket_num = idx + 1
        if ticket_num % 25 == 0 or ticket_num == 1:
            print(f"  [{ticket_num}/{total}] Classifying...")

        try:
            result = classify_single(row["subject"], row["body"], client=client)
        except Exception as e:
            print(f"  [ERROR] Ticket {row.get('ticket_id', idx)}: {e}")
            result = {
                "predicted_category": "General Inquiry",
                "predicted_priority": "Low",
                "deflectable": False,
                "confidence": "low",
                "reasoning": f"Classification error: {str(e)[:80]}",
            }

        result["ticket_id"] = row.get("ticket_id", f"TKT-{idx}")
        results.append(result)

        # Respect rate limits
        if rate_limit_delay > 0:
            time.sleep(rate_limit_delay)

    print(f"  [{total}/{total}] Done.\n")

    results_df = pd.DataFrame(results)
    return df.merge(results_df, on="ticket_id", how="left")


def print_classification_report(df: pd.DataFrame):
    """Print accuracy metrics comparing predicted vs actual labels."""
    from sklearn.metrics import classification_report, accuracy_score

    print("\n" + "=" * 60)
    print("CLASSIFICATION REPORT")
    print("=" * 60)

    # Category accuracy
    cat_acc = accuracy_score(df["category_actual"], df["predicted_category"])
    print(f"\nCategory Accuracy:  {cat_acc:.1%}")

    pri_acc = accuracy_score(df["priority_actual"], df["predicted_priority"])
    print(f"Priority Accuracy:  {pri_acc:.1%}")

    print("\n--- Category Classification Report ---")
    print(classification_report(
        df["category_actual"],
        df["predicted_category"],
        labels=CATEGORIES,
        zero_division=0,
    ))

    print("--- Priority Classification Report ---")
    print(classification_report(
        df["priority_actual"],
        df["predicted_priority"],
        labels=PRIORITIES,
        zero_division=0,
    ))

    # Deflection summary
    deflectable_count = df["deflectable"].sum()
    total = len(df)
    print(f"--- Deflection Summary ---")
    print(f"  Deflectable tickets: {deflectable_count} / {total} ({deflectable_count/total:.1%})")
    print(f"  Non-deflectable:     {total - deflectable_count} / {total} ({(total - deflectable_count)/total:.1%})")

    # Confidence distribution
    conf_dist = df["confidence"].value_counts()
    print(f"\n--- Confidence Distribution ---")
    for level in ["high", "medium", "low"]:
        count = conf_dist.get(level, 0)
        print(f"  {level.capitalize():<8}: {count} ({count/total:.1%})")

    print("=" * 60)


def main():
    print("\n" + "=" * 60)
    print("LLM SUPPORT TICKET CLASSIFIER")
    print("=" * 60)

    # Load tickets
    if not TICKETS_PATH.exists():
        print(f"Tickets file not found at {TICKETS_PATH}")
        print("Run: python data/generate_tickets.py")
        sys.exit(1)

    df = pd.read_csv(TICKETS_PATH)
    print(f"\nLoaded {len(df)} tickets from {TICKETS_PATH.name}")
    print(f"Categories in data: {df['category_actual'].nunique()}")
    print(f"Priority breakdown: {dict(df['priority_actual'].value_counts())}")

    # Initialize client
    client = get_client()
    print(f"\nUsing model: {MODEL}")

    # Run classification
    start_time = time.time()
    df_classified = classify_batch(df, client, rate_limit_delay=1.5)
    elapsed = time.time() - start_time

    print(f"Classification complete in {elapsed:.1f}s "
          f"({elapsed/len(df):.2f}s per ticket)")

    # Save results
    df_classified.to_csv(OUTPUT_PATH, index=False)
    print(f"\nResults saved to: {OUTPUT_PATH}")

    # Print report
    print_classification_report(df_classified)

    return df_classified


if __name__ == "__main__":
    main()
