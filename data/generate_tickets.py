"""
Generate 300 synthetic support tickets for a fintech/payments company.
Produces realistic subject + body text using pools of phrases and templates.
"""
import csv
import random
from datetime import datetime, timedelta

random.seed(42)

# ─── Category distributions ──────────────────────────────────────────────────
CATEGORY_WEIGHTS = {
    "Billing & Payments":     0.22,
    "Account Access":         0.18,
    "Technical Issue":        0.15,
    "Product Question":       0.16,
    "Cancellation Request":   0.07,
    "Refund Request":         0.10,
    "General Inquiry":        0.08,
    "Compliance & Legal":     0.04,
}

PRIORITY_BY_CATEGORY = {
    "Billing & Payments":     {"Low": 0.15, "Medium": 0.50, "High": 0.30, "Critical": 0.05},
    "Account Access":         {"Low": 0.10, "Medium": 0.35, "High": 0.40, "Critical": 0.15},
    "Technical Issue":        {"Low": 0.20, "Medium": 0.40, "High": 0.30, "Critical": 0.10},
    "Product Question":       {"Low": 0.45, "Medium": 0.45, "High": 0.08, "Critical": 0.02},
    "Cancellation Request":   {"Low": 0.10, "Medium": 0.55, "High": 0.30, "Critical": 0.05},
    "Refund Request":         {"Low": 0.10, "Medium": 0.45, "High": 0.35, "Critical": 0.10},
    "General Inquiry":        {"Low": 0.60, "Medium": 0.35, "High": 0.05, "Critical": 0.00},
    "Compliance & Legal":     {"Low": 0.05, "Medium": 0.30, "High": 0.40, "Critical": 0.25},
}

HANDLE_TIME_BY_PRIORITY = {
    "Low":      (4, 10),
    "Medium":   (8, 20),
    "High":     (15, 35),
    "Critical": (25, 60),
}

FCR_BY_PRIORITY = {
    "Low": 0.85, "Medium": 0.72, "High": 0.55, "Critical": 0.40,
}

CSAT_BY_PRIORITY = {
    "Low":      [5, 5, 5, 4, 4],
    "Medium":   [5, 4, 4, 4, 3],
    "High":     [4, 4, 3, 3, 2],
    "Critical": [4, 3, 3, 2, 1],
}

CHANNELS = ["email", "chat", "phone", "web"]
CHANNEL_WEIGHTS = [0.35, 0.30, 0.20, 0.15]

# ─── Ticket content templates per category ────────────────────────────────────

TICKETS = {
    "Billing & Payments": [
        {
            "subject": "Unexpected charge on my account",
            "body": "Hi, I just noticed a charge of ${amount} on my account that I don't recognize. "
                    "The transaction shows up as '{merchant}' but I don't remember authorizing this. "
                    "Can you help me figure out what this is? My account is under {email}. Thanks.",
        },
        {
            "subject": "Unable to update my payment method",
            "body": "I've been trying to update my bank account for direct deposit but keep getting an error "
                    "when I try to save the new account. I've tried three times now and it just says "
                    "'Unable to verify account.' My routing number and account number are definitely correct. "
                    "Please help — I need this updated before my next paycheck.",
        },
        {
            "subject": "Need an invoice for last month",
            "body": "Hello, could you please send me an invoice for {month}? Our accounting team needs it for "
                    "expense reconciliation. Account email is {email}. Please send to {email2} as well. "
                    "We need it in PDF format if possible. Thank you.",
        },
        {
            "subject": "Direct deposit didn't arrive",
            "body": "My direct deposit was supposed to hit today ({date}) but it's not showing in my bank account. "
                    "My employer processed payroll on {prev_date} so it should have cleared by now. "
                    "This is urgent as I have bills due today. Can you look into what happened?",
        },
        {
            "subject": "Question about the ${fee} fee on my statement",
            "body": "I see a ${fee} fee on my recent statement and I'm not sure what it's for. "
                    "I don't recall seeing this fee before. Is this a new charge? Can you explain what "
                    "this covers and whether I can avoid it? I've been a customer for {months} months.",
        },
        {
            "subject": "Payment failed — please help",
            "body": "I tried to make a payment of ${amount} today but it failed. The error message said "
                    "'Insufficient funds' but my bank account shows plenty of money. I've tried twice and "
                    "both times it failed. Is there a hold on my account? Please look into this ASAP.",
        },
        {
            "subject": "My balance looks wrong",
            "body": "Something seems off with my account balance. It's showing ${balance} but based on my "
                    "transactions I should have more than that. The last transaction I see is from {date} "
                    "but I know I had a deposit processed on {prev_date}. Can you audit my account?",
        },
    ],
    "Account Access": [
        {
            "subject": "Can't log in to my account",
            "body": "I'm having trouble logging into my account. I've tried my usual password but it keeps "
                    "saying 'Invalid credentials.' I haven't changed my password recently. "
                    "I tried the 'Forgot password' link but I'm not getting the reset email. "
                    "My account email is {email}. Please help.",
        },
        {
            "subject": "Account locked — need help getting back in",
            "body": "My account appears to be locked. I got a message saying it was locked due to "
                    "too many failed login attempts, but I wasn't the one trying to log in. "
                    "This might be a security issue — someone may be trying to access my account. "
                    "Please unlock my account and let me know if there was suspicious activity.",
        },
        {
            "subject": "Two-factor authentication not working",
            "body": "I enabled two-factor authentication last week and now I can't get in. "
                    "I'm not receiving the SMS codes to my phone number ending in {phone_last4}. "
                    "I've waited several minutes and tried multiple times. "
                    "Is there an alternative way to verify my identity so I can get back in?",
        },
        {
            "subject": "Need to update my email address",
            "body": "Hi, I recently changed jobs and need to update the email address on my account "
                    "from {email} to {email2}. I still have access to the old email so I can verify "
                    "through that. Could you walk me through the process or make the change for me?",
        },
        {
            "subject": "Forgot username / can't find my login",
            "body": "I think I signed up with either {email} or {email2} but neither is working. "
                    "I do have an account because I've used the service before — I can see charges "
                    "on my bank statement. Can you look up what email is on file for me? "
                    "I can verify with my last 4 of SSN or bank account.",
        },
        {
            "subject": "SSO login broken since company update",
            "body": "Since our company updated their SSO provider last week, I can no longer log in "
                    "through the company portal. It redirects me to a blank screen. "
                    "My colleagues are having the same issue. Our company admin is {company}. "
                    "Can you check if something on your end needs to be updated?",
        },
        {
            "subject": "Suspicious login attempt on my account",
            "body": "I received an email saying there was a login attempt from an unrecognized device in "
                    "{location}. I did not attempt to log in at that time. I've already changed my password "
                    "but I'm concerned my account may be compromised. Can you review recent activity "
                    "and confirm my account is secure?",
        },
    ],
    "Technical Issue": [
        {
            "subject": "App keeps crashing when I open it",
            "body": "The mobile app crashes every time I try to open it. This started after the update "
                    "that pushed yesterday. I'm on iPhone {iphone_model} running iOS {ios_ver}. "
                    "I've already tried uninstalling and reinstalling but same issue. "
                    "Is there a known issue with this version?",
        },
        {
            "subject": "Transaction history not loading",
            "body": "When I tap on 'Transaction History' in the app, it just shows a spinning loader "
                    "and never loads. I've waited up to 5 minutes. This has been happening for 2 days. "
                    "Everything else in the app works fine. I'm on Android {android_ver}.",
        },
        {
            "subject": "Payroll integration stopped syncing",
            "body": "Our payroll integration with {payroll_system} stopped syncing employee data yesterday. "
                    "We process payroll on Thursdays and none of our employees are showing updated hours. "
                    "I checked the integration settings and everything looks correct on our end. "
                    "This is urgent — payroll runs in 2 days.",
        },
        {
            "subject": "Getting an error code when trying to transfer funds",
            "body": "Every time I try to transfer money I get error code {error_code}. "
                    "This started happening about {days} days ago. I need to move funds for an urgent "
                    "payment. I've tried different amounts ($50, $100, $500) and get the same error. "
                    "My bank account is verified and in good standing.",
        },
        {
            "subject": "Dashboard showing wrong data",
            "body": "The analytics dashboard is showing {month} data when it should be showing current data. "
                    "It looks like the data is about 3 weeks behind. We rely on this for payroll decisions "
                    "so accurate, up-to-date data is critical. Please investigate.",
        },
        {
            "subject": "Mobile notification not working",
            "body": "I've stopped receiving push notifications on my phone. I checked my phone settings "
                    "and notifications are enabled for the app. This is a problem because I rely on "
                    "notifications for payment confirmations. Please help me re-enable these.",
        },
    ],
    "Product Question": [
        {
            "subject": "How do I request a pay advance?",
            "body": "I just signed up and I'm trying to figure out how to request an advance on my upcoming "
                    "paycheck. I see the option in the app but when I tap it, it says I'm not eligible. "
                    "I've been at my job for {months} months and my employer is enrolled. "
                    "What are the eligibility requirements?",
        },
        {
            "subject": "What's the maximum I can advance?",
            "body": "I wanted to know what the maximum amount I can advance is. I currently have a paycheck "
                    "coming for around ${amount} and I need about ${need_amount} now. "
                    "Is there a limit on what percentage of my paycheck I can access early? "
                    "Also, what's the fee for doing this?",
        },
        {
            "subject": "How long does a transfer take?",
            "body": "If I request a transfer today, when will the money actually show up in my bank account? "
                    "I've seen different timelines mentioned — 1 business day vs instant. "
                    "Is there an option for instant transfer? Is there a fee for faster delivery?",
        },
        {
            "subject": "Does this work with my bank?",
            "body": "I have an account with {bank}. Is your service compatible with all banks or just "
                    "certain ones? I tried adding my account and got an error saying the bank wasn't "
                    "supported. I also have a {bank2} account if that one works better.",
        },
        {
            "subject": "Can I use this if I'm paid biweekly?",
            "body": "My employer pays me every two weeks. Can I still use the early access feature "
                    "between pay periods? Does the amount I can advance reset after each paycheck? "
                    "I'm trying to understand how it works with a biweekly pay schedule.",
        },
        {
            "subject": "Is there a fee to use the service?",
            "body": "I was referred by a coworker but I want to make sure I understand the costs before "
                    "I sign up. Is there a monthly fee? What does it cost to access my pay early? "
                    "Are there any other hidden charges I should know about?",
        },
        {
            "subject": "How does the tipping model work?",
            "body": "I noticed the app asks for an optional tip when I transfer money. Can you explain "
                    "how this works? Is the tip really optional or does it affect my service? "
                    "What percentage do most people tip? I just want to make sure I'm using this correctly.",
        },
    ],
    "Cancellation Request": [
        {
            "subject": "I want to cancel my subscription",
            "body": "Hi, I'd like to cancel my subscription. I'm switching employers and my new company "
                    "doesn't use your service. My last day at my current job is {date}. "
                    "Can you walk me through the cancellation process? "
                    "Also, will I be charged anything for canceling mid-cycle?",
        },
        {
            "subject": "Please close my account",
            "body": "I would like to permanently close my account and have all my personal data deleted. "
                    "I no longer need this service. My account email is {email}. "
                    "Please confirm once the account is closed and my data has been removed.",
        },
        {
            "subject": "Want to remove my employer from the platform",
            "body": "Our company has decided to discontinue using your earned wage access program. "
                    "We have {count} employees enrolled. Can you tell us the process for offboarding "
                    "our company from the platform? We want to make sure employees are notified properly.",
        },
        {
            "subject": "How do I stop automatic deductions?",
            "body": "I took an advance last month and it was automatically deducted from my paycheck, "
                    "which I understood. But now it's happening again this pay period even though I "
                    "didn't take another advance. I want to stop any automatic deductions and ideally "
                    "cancel the service. Please help.",
        },
    ],
    "Refund Request": [
        {
            "subject": "Charged twice for the same transaction",
            "body": "I was charged ${amount} twice on {date}. I only authorized one payment. "
                    "My bank statement clearly shows two identical charges. I need one of these "
                    "refunded immediately. Transaction IDs (if helpful): {tx1} and {tx2}. "
                    "Please process the refund ASAP.",
        },
        {
            "subject": "Incorrect fee charged — requesting refund",
            "body": "I was charged a ${fee} fee that I don't believe I should have been charged. "
                    "When I signed up, I was told the first {months} months were fee-free. "
                    "I'm only on month {current_month}. Can you review and refund this fee?",
        },
        {
            "subject": "Transaction I didn't authorize",
            "body": "There's a ${amount} transaction on my account from {date} that I did not authorize. "
                    "I've never heard of '{merchant}' and I was not in {location} on that date. "
                    "I believe this may be fraud. Please investigate and refund the charge. "
                    "I'd also like to know if my account has been compromised.",
        },
        {
            "subject": "Requesting partial refund",
            "body": "I was charged ${amount} for a service I only partially used. I signed up on {date} "
                    "and canceled on {date2}, which means I used the service for only {days} days of "
                    "the billing period. I'm requesting a pro-rated refund for the unused portion. "
                    "Please let me know how to proceed.",
        },
        {
            "subject": "Wrong amount deducted from my paycheck",
            "body": "My advance deduction was for ${deducted} but I only took an advance of ${advanced}. "
                    "The math doesn't add up — it seems like I was charged a fee I wasn't told about. "
                    "Can you provide a breakdown of the deduction and refund the difference?",
        },
    ],
    "General Inquiry": [
        {
            "subject": "How do I get started?",
            "body": "My company just rolled out your service and I received an email to sign up. "
                    "I clicked the link but I'm not sure what to do next. "
                    "Is there a guide or tutorial? What information do I need to get started? "
                    "Do I need to connect my bank account right away?",
        },
        {
            "subject": "Do you have a referral program?",
            "body": "A friend told me I can earn rewards for referring new users. "
                    "How does the referral program work? Is there a limit to how many people I can refer? "
                    "When do I receive my reward — right when they sign up or after they use the service?",
        },
        {
            "subject": "What are your customer support hours?",
            "body": "I've been trying to reach your phone support but keep getting voicemail. "
                    "What are your support hours? Is there a live chat option? "
                    "I have an issue that I'd prefer to resolve over the phone rather than by email.",
        },
        {
            "subject": "Feedback about the new app update",
            "body": "I just wanted to share some feedback about the recent app update. "
                    "I really miss the old home screen layout — the new one is harder to navigate. "
                    "The transaction history view in particular is much harder to use. "
                    "Is there a way to revert to the old layout, or can you pass this feedback along?",
        },
        {
            "subject": "Is your service available in all states?",
            "body": "I'm considering recommending your service to my employer. "
                    "We have employees in {state1}, {state2}, and {state3}. "
                    "Is your earned wage access product available in all three states? "
                    "Are there any state-specific restrictions I should know about?",
        },
        {
            "subject": "What documents do I need for onboarding?",
            "body": "I'm in the process of setting up my account and it's asking me to verify my identity. "
                    "What documents do you accept? Do I need a government-issued ID? "
                    "Can I use a passport or does it need to be a driver's license? "
                    "Also, is my information secure when I upload documents?",
        },
    ],
    "Compliance & Legal": [
        {
            "subject": "Data privacy request — please delete my data",
            "body": "I am submitting a formal request under the California Consumer Privacy Act (CCPA) "
                    "to delete all personal data you hold about me. My account email is {email}. "
                    "Please confirm receipt of this request and provide a timeline for deletion. "
                    "I expect written confirmation once deletion is complete.",
        },
        {
            "subject": "Request for data export (GDPR)",
            "body": "I am exercising my right under GDPR Article 20 to data portability. "
                    "Please provide a full export of all personal data you hold associated with my account. "
                    "My account ID is {account_id}. Please send the export to {email} within the "
                    "legally required 30-day window.",
        },
        {
            "subject": "Potential fraud on my account — urgent",
            "body": "I believe my account has been used fraudulently. I noticed {count} transactions "
                    "I did not authorize totaling ${amount}. I have already locked my bank account. "
                    "I am filing a police report. I need all transaction records for the past {months} months "
                    "and immediate reversal of the fraudulent charges. This is extremely urgent.",
        },
        {
            "subject": "Legal hold / subpoena response needed",
            "body": "Please be advised that our firm represents {company} in a pending legal matter. "
                    "We have issued a subpoena (attached) for records related to account {account_id}. "
                    "Please direct this to your legal department. The response deadline is {date}. "
                    "Contact our office at {email} with any questions.",
        },
    ],
}

# ─── Random fill-in values ───────────────────────────────────────────────────

def rand_email():
    first = random.choice(["john", "sarah", "mike", "emily", "david", "jessica", "chris", "ashley"])
    last = random.choice(["smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis"])
    domain = random.choice(["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"])
    return f"{first}.{last}{random.randint(1, 99)}@{domain}"

def rand_amount():
    return round(random.choice([12.99, 15.00, 24.99, 29.99, 49.99, 79.99, 99.00, 125.00, 200.00, 350.00, 500.00]), 2)

def rand_date():
    base = datetime(2025, 11, 1)
    delta = timedelta(days=random.randint(0, 180))
    return (base + delta).strftime("%B %d, %Y")

def rand_prev_date():
    base = datetime(2025, 10, 28)
    delta = timedelta(days=random.randint(0, 180))
    return (base + delta).strftime("%B %d, %Y")

FILL_VALUES = {
    "amount":        lambda: str(rand_amount()),
    "fee":           lambda: str(random.choice([1.99, 2.99, 4.99, 9.99, 14.99])),
    "balance":       lambda: str(round(random.uniform(50, 2000), 2)),
    "need_amount":   lambda: str(random.choice([50, 100, 150, 200, 300, 500])),
    "email":         rand_email,
    "email2":        rand_email,
    "date":          rand_date,
    "prev_date":     rand_prev_date,
    "date2":         rand_date,
    "month":         lambda: random.choice(["January", "February", "March", "April", "October", "November"]),
    "months":        lambda: str(random.randint(2, 24)),
    "current_month": lambda: str(random.randint(1, 3)),
    "merchant":      lambda: random.choice(["EarnPay Services", "TP Auto Deduct", "Payroll Advance LLC", "FastPay Inc"]),
    "phone_last4":   lambda: str(random.randint(1000, 9999)),
    "company":       lambda: random.choice(["Acme Corp", "TechStaff Inc", "RetailCo", "HealthFirst", "BuildRight LLC"]),
    "location":      lambda: random.choice(["Texas", "California", "New York", "Chicago", "Miami"]),
    "iphone_model":  lambda: random.choice(["13", "14", "15", "15 Pro"]),
    "ios_ver":       lambda: random.choice(["16.6", "17.0", "17.2", "17.4", "18.0"]),
    "android_ver":   lambda: random.choice(["12", "13", "14"]),
    "payroll_system":lambda: random.choice(["ADP", "Gusto", "Paychex", "Workday", "Paycom"]),
    "error_code":    lambda: f"ERR-{random.randint(1000, 9999)}",
    "days":          lambda: str(random.randint(1, 7)),
    "count":         lambda: str(random.randint(5, 250)),
    "bank":          lambda: random.choice(["Chase", "Bank of America", "Wells Fargo", "Chime", "Capital One"]),
    "bank2":         lambda: random.choice(["TD Bank", "US Bank", "PNC", "Ally", "Citi"]),
    "tx1":           lambda: f"TXN{random.randint(100000, 999999)}",
    "tx2":           lambda: f"TXN{random.randint(100000, 999999)}",
    "deducted":      lambda: str(rand_amount()),
    "advanced":      lambda: str(rand_amount()),
    "state1":        lambda: "California",
    "state2":        lambda: "Texas",
    "state3":        lambda: "New York",
    "account_id":    lambda: f"ACC-{random.randint(10000, 99999)}",
}

def fill_template(text):
    """Replace {placeholder} tokens with random realistic values."""
    import re
    def replace(m):
        key = m.group(1)
        if key in FILL_VALUES:
            return FILL_VALUES[key]()
        return m.group(0)
    return re.sub(r'\{(\w+)\}', replace, text)


def weighted_choice(options_dict):
    keys = list(options_dict.keys())
    weights = list(options_dict.values())
    return random.choices(keys, weights=weights, k=1)[0]


def generate_tickets(n=300):
    rows = []
    categories = list(CATEGORY_WEIGHTS.keys())
    cat_weights = list(CATEGORY_WEIGHTS.values())

    # Build base date range: Nov 2025 – Apr 2026
    start_date = datetime(2025, 11, 1)
    end_date   = datetime(2026, 4, 30)
    date_range = (end_date - start_date).days

    for i in range(1, n + 1):
        ticket_id = f"TKT-{1000 + i}"

        # Category & priority
        category = random.choices(categories, weights=cat_weights, k=1)[0]
        priority = weighted_choice(PRIORITY_BY_CATEGORY[category])

        # Pick a random ticket template for this category
        template = random.choice(TICKETS[category])
        subject = fill_template(template["subject"])
        body    = fill_template(template["body"])

        # Metadata
        created_date = (start_date + timedelta(days=random.randint(0, date_range))).strftime("%Y-%m-%d")
        channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS, k=1)[0]

        lo, hi = HANDLE_TIME_BY_PRIORITY[priority]
        handle_time = random.randint(lo, hi)

        fcr_prob = FCR_BY_PRIORITY[priority]
        resolved_first_contact = random.random() < fcr_prob

        csat_score = random.choice(CSAT_BY_PRIORITY[priority])

        rows.append({
            "ticket_id": ticket_id,
            "created_date": created_date,
            "channel": channel,
            "subject": subject,
            "body": body,
            "priority_actual": priority,
            "category_actual": category,
            "handle_time_minutes": handle_time,
            "resolved_first_contact": resolved_first_contact,
            "csat_score": csat_score,
        })

    return rows


if __name__ == "__main__":
    import os
    out_path = os.path.join(os.path.dirname(__file__), "tickets.csv")
    rows = generate_tickets(300)

    fieldnames = [
        "ticket_id", "created_date", "channel", "subject", "body",
        "priority_actual", "category_actual", "handle_time_minutes",
        "resolved_first_contact", "csat_score",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} tickets -> {out_path}")
    # Quick distribution check
    from collections import Counter
    cats = Counter(r["category_actual"] for r in rows)
    for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {cnt}")
