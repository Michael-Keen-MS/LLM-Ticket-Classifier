# PLANNING.md — LLM Ticket Classifier

## Project Summary

A support ticket intelligence pipeline that uses the Anthropic API to classify customer support tickets by category and priority, identify which tickets are candidates for automated deflection, and model the ROI of that deflection at scale. Built as a portfolio demonstration of LLM-powered operations automation — directly mirroring Michael Keen's real-world $80K+ Zendesk automation work at Tapcheck.

---

## Problem Statement

Customer support teams at scale face two compounding problems: routing tickets incorrectly wastes agent time, and failing to identify deflectable tickets means paying human handle cost on issues that could be resolved automatically. Manual tagging is inconsistent and slow. Rule-based classifiers break on edge cases and require constant maintenance. LLMs classify with near-human accuracy at a fraction of human cost — but most teams haven't modeled the ROI or built a pipeline to prove it. This project does both.

---

## Goals

| Goal | Success Metric |
|------|---------------|
| Accurate ticket classification | F1 > 0.80 across major categories |
| Deflection candidate identification | Deflectable tickets correctly flagged with reasoning |
| Quantified ROI model | Annual savings calculated across volume scenarios |
| Reproducible pipeline | Full run from raw tickets → classified output → ROI report in under 5 minutes |
| Portfolio-ready code | Clean separation of classifier, ROI model, and analysis notebook |

---

## Target Audience

- **Hiring managers for AI success / deployment roles** (OpenAI, AI-forward CX platforms) evaluating ability to apply LLMs to real business problems
- **CX operations leaders** evaluating automation ROI methodology
- **Technical interviewers** assessing LLM API usage, prompt engineering, and output structuring

---

## Functional Requirements

### Data (`data/`)
- [ ] `tickets.csv` — 300 synthetic fintech support tickets across 8 categories
- [ ] Realistic subject + body text per category (not Lorem Ipsum placeholders)
- [ ] Ground truth labels: `priority_actual`, `category_actual`, `handle_time_minutes`, `csat_score`
- [ ] `taxonomy.json` — category list, priority levels, deflectable vs. human-required rules
- [ ] `generate_tickets.py` — reproducible generator using template pools per category

### Classifier (`classifier.py`)
- [ ] Batch classification using `claude-haiku-4-5-20251001` (cost-efficient for batch workloads)
- [ ] Structured JSON output per ticket: `predicted_category`, `predicted_priority`, `deflectable`, `confidence`, `reasoning`
- [ ] `classify_single(subject, body)` function for real-time single ticket use
- [ ] Accuracy report: precision, recall, F1 by category vs. ground truth labels
- [ ] Save classified output to `data/tickets_classified.csv`
- [ ] API key from `ANTHROPIC_API_KEY` environment variable

### ROI Model (`roi_model.py`)
- [ ] Inputs: classified ticket dataframe, cost_per_human_ticket, cost_per_automated_ticket, monthly_volume
- [ ] Outputs: deflection_rate, monthly_savings, annual_savings, payback_period_months
- [ ] `sensitivity_analysis()` — savings across ticket volume range (1k–20k/month)
- [ ] Standalone runnable with printed summary report

### Analysis Notebook (`analysis.ipynb`)
- [ ] Section 1: Data overview — volume by category, channel, priority; handle time + CSAT distributions
- [ ] Section 2: Classification results — F1 by category, confusion matrix heatmap, confidence distribution
- [ ] Section 3: Deflection analysis — deflectable vs. non-deflectable breakdown by category
- [ ] Section 4: ROI model — summary table, sensitivity analysis chart
- [ ] Section 5: Sample classifications — 10 example tickets with predicted labels and reasoning

---

## Technical Requirements

- Python 3.9+
- `anthropic>=0.25.0` — API client; model `claude-haiku-4-5-20251001` for batch cost efficiency
- `pandas>=2.0.0`, `numpy>=1.24.0` — data handling
- `scikit-learn>=1.3.0` — classification metrics (precision, recall, F1, confusion matrix)
- `matplotlib>=3.7.0`, `seaborn>=0.12.0` — visualizations
- API key via `ANTHROPIC_API_KEY` environment variable
- No database — CSV in / CSV out pipeline

---

## Out of Scope (v1)

- Real Zendesk or Salesforce API integration
- Fine-tuned model (zero-shot only)
- Real-time webhook-based classification
- Multi-language ticket support
- Agent escalation routing logic

---

## Development Phases

### Phase 1 — Core (complete)
- [x] Synthetic ticket generation (300 tickets, 8 categories, realistic text)
- [x] Classification taxonomy JSON
- [x] Batch classifier with structured JSON output
- [x] `classify_single()` for real-time use
- [x] ROI calculator with sensitivity analysis
- [x] Analysis notebook (20 cells, all 5 sections)
- [x] README with pipeline diagram

### Phase 2 — Validation (next)
- [ ] Run classifier against actual Anthropic API (requires `ANTHROPIC_API_KEY`)
- [ ] Record real F1 scores per category and update README Key Results section
- [ ] Tune prompt for any underperforming categories (target: all > 0.80 F1)
- [ ] Add token usage tracking and actual cost-per-classification metric

### Phase 3 — Production Patterns (future)
- [ ] Async batch processing for high-volume throughput
- [ ] Confidence threshold routing: low-confidence tickets flagged for human review
- [ ] Streamlit app: paste a ticket, get instant classification + deflection recommendation
- [ ] Zendesk API integration: classify tickets from a live queue

---

## Dependencies

| Dependency | Version | Purpose |
|---|---|---|
| `anthropic` | >=0.25.0 | API client; Haiku model for batch classification |
| `pandas` | >=2.0.0 | Ticket data handling and CSV I/O |
| `numpy` | >=1.24.0 | Synthetic data generation |
| `scikit-learn` | >=1.3.0 | Classification metrics |
| `matplotlib` | >=3.7.0 | Visualizations |
| `seaborn` | >=0.12.0 | Heatmaps and distribution plots |
| `jupyter` | >=1.0.0 | Analysis notebook runtime |

---

## Notes

- Haiku (`claude-haiku-4-5-20251001`) is used for classification — it is significantly cheaper than Sonnet for high-volume batch workloads while maintaining strong classification accuracy on structured tasks
- The ROI baseline uses $15/ticket (human handle cost) and $1.50/ticket (automated), based on industry benchmarks for SaaS/fintech support operations
- At 45% deflection rate and 5,000 tickets/month, the model projects ~$364K annual savings — this will be updated with real classifier output once the API run completes
- The `reasoning` field in classifier output is intentional: it makes the deflection decision auditable, which is critical for real-world deployment and stakeholder trust