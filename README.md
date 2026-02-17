# SEBI AIF Alert Bot

This repository now includes a Python script that watches SEBI RSS feed(s), detects **AIF-related circulars/notifications**, and sends you an alert with a **simple-language ChatGPT summary**.

## File

- `aif_sebi_alert.py`

## What it does

1. Polls SEBI RSS feed(s).
2. Filters entries related to Alternative Investment Funds (AIF).
3. Skips items it has already processed (state saved locally).
4. Pulls article text from the SEBI link.
5. Sends text to OpenAI for a simple summary.
6. Prints alert in terminal and (optionally) sends email.

## Setup

### 1) Python

Use Python 3.10+.

### 2) Environment variables

```bash
export OPENAI_API_KEY="your_openai_api_key"
# Optional; defaults to gpt-4o-mini
export OPENAI_MODEL="gpt-4o-mini"

# Optional email alerts
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="you@example.com"
export SMTP_PASSWORD="app_password"
export ALERT_FROM_EMAIL="you@example.com"
export ALERT_TO_EMAIL="your_destination@example.com"
```

## Usage

### One-time check

```bash
python aif_sebi_alert.py --once
```

### Continuous monitoring (every 30 min default)

```bash
python aif_sebi_alert.py
```

### Custom interval

```bash
python aif_sebi_alert.py --interval-minutes 15
```

### Use custom feed URL(s)

```bash
python aif_sebi_alert.py --once \
  --feed-url "https://www.sebi.gov.in/sebirss.xml"
```

## Notes

- If `OPENAI_API_KEY` is missing, alerts still work, but summary is skipped.
- If SMTP settings are missing, alert is printed to terminal only.
- Seen links are stored in `.state/sebi_seen.json` by default.
- If SEBI changes feed URL/format, update `--feed-url` or `DEFAULT_FEEDS` in script.
