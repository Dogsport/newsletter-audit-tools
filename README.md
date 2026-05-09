# Newsletter Audit Tools

Flask-based auditing tools for analyzing newsletter subscribers across:

- Shopify
- Shopware
- PushOwl
- Brevo

The toolkit helps validate newsletter migrations, compare customer databases, detect unsubscribed users, clean campaign audiences, and investigate sync inconsistencies between ecommerce and marketing systems.

---

# Project Goal

This project was created to audit and validate newsletter subscriber data after migration from Shopware to Shopify and synchronization with PushOwl and Brevo.

The tools help answer questions like:

- Which historical subscribers still exist?
- Which customers unsubscribed?
- Which contacts are missing in Shopify?
- Which subscribers exist only in Shopware?
- Which customers exist only in Shopify?
- Which contacts are duplicated?
- Which contacts are campaign-ready?
- Why are Shopify, PushOwl, and Brevo counts different?

---

# Systems Included

| System | Purpose |
|---|---|
| Shopware | Historical newsletter/customer database |
| Shopify | Current ecommerce customer platform |
| PushOwl | Shopify sync layer |
| Brevo | Email marketing platform |

---

# Important Discovery During Audit

The audit identified two separate Brevo environments:

| Account | Purpose |
|---|---|
| IQ Dogsport | Connected to Shopify + PushOwl |
| IQ Dogsport GmbH | Historical marketing account with older newsletter audience |

Because of this:

- Shopify synced customers were entering one account
- historical marketing contacts existed in another account
- audience counts became inconsistent
- campaigns were being sent from different environments

---

# Main Audit Results

| Result | Approximate Count |
|---|---:|
| Historical Shopware newsletter contacts | 8,952 |
| Clean campaign-ready audience | ~8,425 |
| Shopify subscribed customers | ~1,838 |
| Customers existing in both systems | 1,651 |
| Shopify-only new subscribers | 187 |
| Combined valid audience | ~8,612 |
| Expanded K9 audience | ~15,379 |
| Brevo historical contacts | ~17,000 |
| PushOwl synced Shopify contacts | ~34,000 |

---

# Included Tools

---

# 1. Shopware Marketing Campaign Audit

File:

```bash
shopware_marketing_campaign_audit.py
```

Analyzes Shopware newsletter exports.

## Features

- Unique customer detection
- Duplicate email analysis
- Newsletter group analysis
- DOI analysis
- Campaign candidate filtering
- Group membership matrix
- Repeated customer detection
- Email-only export generation

## Generated Reports

- subscribed_unique_full_data.csv
- unsubscribed_unique_full_data.csv
- duplicate_email_summary.csv
- duplicate_rows_full_data.csv
- group_breakdown.csv
- group_membership_matrix.csv
- emails_repeated_across_groups.csv

---

# 2. Shopware vs Shopify Subscription Audit

File:

```bash
shopware_shopify_compare.py
```

Compares historical Shopware newsletter subscribers against current Shopify customers.

## Features

- Historical migration audit
- Subscription validation
- Missing customer detection
- Unsubscribed customer detection
- Shopify-only customer detection
- Full migration comparison

## Generated Reports

- shopware_still_subscribed_in_shopify.csv
- changed_subscribed_to_unsubscribed.csv
- shopware_missing_in_shopify.csv
- shopify_only_subscribed.csv
- all_comparison.csv

---

# 3. Shopify Unsubscribe Audit

File:

```bash
shopify_unsubscribed_audit.py
```

Compares old Shopify subscriber exports against current Shopify exports.

## Features

- Historical unsubscribe detection
- Subscription status comparison
- Missing customer detection
- Current subscription validation

## Generated Reports

- now_unsubscribed.csv
- still_subscribed.csv
- missing_in_current.csv
- full_comparison.csv

---

# 4. Main Dashboard

File:

```bash
main_dashboard.py
```

Central launcher for all tools.

## Features

- One-click tool launcher
- Automatic Flask startup
- Port management
- Browser redirects
- Multi-tool dashboard

## Ports

| Tool | Port |
|---|---:|
| Dashboard | 5000 |
| Shopware Audit | 5001 |
| Shopware vs Shopify | 5002 |
| Shopify Unsubscribe Audit | 5003 |

---

# Project Structure

```bash
newsletter-audit-tools/
│
├── main_dashboard.py
├── shopware_marketing_campaign_audit.py
├── shopware_shopify_compare.py
├── shopify_unsubscribed_audit.py
│
├── uploads/
├── audit_reports/
├── audit_downloads/
│
├── requirements.txt
├── README.md
└── venv/
```

---

# Installation

## Clone Repository

```bash
git clone <repository-url>
cd newsletter-audit-tools
```

---

## Create Virtual Environment

```bash
python3 -m venv venv
```

---

## Activate Environment

### macOS / Linux

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# requirements.txt

```txt
Flask
pandas
openpyxl
Werkzeug
```

---

# Start Dashboard

```bash
python main_dashboard.py
```

Open:

```text
http://127.0.0.1:5000
```

---

# Run Individual Tools

## Shopware Audit

```bash
python shopware_marketing_campaign_audit.py
```

---

## Shopware vs Shopify

```bash
python shopware_shopify_compare.py
```

---

## Shopify Unsubscribe Audit

```bash
python shopify_unsubscribed_audit.py
```

---

# CSV Requirements

## Shopify CSV

Must contain:

- Email
- Accepts Email Marketing
OR
- Email Subscription Status

---

## Shopware CSV

Recommended columns:

- email
- newsletter
- customer_group
- group
- doi
- double_opt_in

---

# Port Conflict Fix

If ports are already running:

```bash
lsof -ti:5000,5001,5002,5003 | xargs kill -9
```

---

# GDPR / Compliance Notice

These tools provide technical audience analysis only.

They DO NOT prove lawful marketing eligibility.

Before sending campaigns always verify:

- Shopify marketing state = subscribed
- Brevo DOI confirmed = true
- no unsubscribe exists
- no bounce exists
- no complaint exists
- consent timestamp exists
- consent source exists

If consent data is missing or unclear:

DO NOT SEND MARKETING EMAILS.

---

# Future Improvements

Possible future additions:

- Brevo API integration
- Shopify Admin API integration
- Automated PDF reporting
- Contact suppression validation
- Scheduled audit jobs
- Multi-store support
- Campaign eligibility scoring

