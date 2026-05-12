# LLM Support Ticket Classifier

An LLM-powered support ticket intelligence pipeline that classifies tickets by category and priority, identifies automation deflection candidates, and models the ROI of automated deflection — mirroring real-world CX automation work in fintech.

## Overview

Modern support teams are buried in tickets that could be resolved automatically. This pipeline uses Claude (Anthropic API) to classify incoming support tickets, identify which ones are candidates for automated deflection, and quantify the cost savings from doing so.

Built as a portfolio demonstration of applied LLM engineering, the project mirrors real-world work: at Tapcheck, a similar automation initiative deflected 40%+ of support volume and saved over $80K annually.

## Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    3-Stage Pipeline                         │
│                                                             │
│  Stage 1: Data          Stage 2: Classification   Stage 3: ROI
│  ──────────             ────────────────────       ────────
│  tickets.csv       →    Claude Haiku (Batch)   →   roi_model.py
│  taxonomy.json          classifier.py              analysis.ipynb
│                         ↓                          ↓
│                    tickets_classified.csv      Savings report
│                    (category, priority,        Sensitivity analysis
│                     deflectable, confidence,   Payback period
│                     reasoning)
└─────────────────────────────────────────────────────────────┘
```

## Key Results

| Metric | Value |
|--------|-------|
| Deflection rate identified | ~45% of tickets deflectable |
| Annual savings projected | ~$189,000 at 5,000 tickets/month |
| Classification accuracy | See `analysis.ipynb` for full breakdown |

## Setup

```bash
# Clone the repo
git clone https://github.com/Michael-Keen-MS/LLM-Ticket-Classifier.git
cd LLM-Ticket-Classifier

# Install dependencies
pip install -r requirements.txt

# Set your Anthropic API key
export ANTHROPIC_API_KEY="your-key-here"   # Linux/Mac
$env:ANTHROPIC_API_KEY="your-key-here"     # PowerShell

# Generate synthetic data (if not already present)
python -c "import data.generate_tickets"   # or run the notebook

# Run the classifier
python classifier.py

# Open the analysis notebook
jupyter notebook analysis.ipynb
```

## Files

| File | Description |
|------|-------------|
| `data/tickets.csv` | 300 synthetic support tickets for a fintech company |
| `data/taxonomy.json` | Classification taxonomy: categories, priorities, deflection rules |
| `classifier.py` | Core batch classification pipeline using Claude Haiku via Anthropic API |
| `roi_model.py` | Deflection ROI calculator with sensitivity analysis |
| `analysis.ipynb` | Full analysis: data overview, classification metrics, deflection analysis, ROI |
| `requirements.txt` | Python dependencies |

## Tech Stack

- **LLM**: Anthropic Claude Haiku (`claude-haiku-4-5`) — cost-efficient batch classification
- **Language**: Python 3.10+
- **Data**: pandas, numpy
- **Visualization**: matplotlib, seaborn
- **ML Metrics**: scikit-learn (precision, recall, F1, confusion matrix)
- **Notebook**: Jupyter
- **API**: Anthropic Python SDK

## Business Context

Support ticket automation is one of the highest-ROI investments a CX team can make. At scale:
- A 40% deflection rate on 5,000 monthly tickets saves ~$160K/year
- Automated deflection reduces handle time by ~8 minutes per ticket
- First-contact resolution improves as human agents focus on complex cases

This pipeline demonstrates how LLMs can serve as the classification layer in a production automation system — replacing brittle keyword rules with semantic understanding.
