#!/usr/bin/env python3
"""SEBI AIF circular/notification watcher with optional ChatGPT summaries."""

from __future__ import annotations

import argparse
import json
import os
import re
import smtplib
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

DEFAULT_FEEDS = [
    # You can replace these with the latest SEBI RSS feeds you prefer.
    "https://www.sebi.gov.in/sebirss.xml",
]

AIF_KEYWORDS = [
    "alternative investment fund",
    "alternative investment funds",
    "aif",
    "cat i aif",
    "cat ii aif",
    "cat iii aif",
]


@dataclass
class FeedItem:
    title: str
    link: str
    published: str
    description: str


class SebiAifMonitor:
    def __init__(self, state_file: Path, feeds: list[str], keywords: list[str]) -> None:
        self.state_file = state_file
        self.feeds = feeds
        self.keywords = [k.lower() for k in keywords]
        self.seen_links = self._load_state()

    def _load_state(self) -> set[str]:
        if not self.state_file.exists():
            return set()
        try:
            payload = json.loads(self.state_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return set()
        return set(payload.get("seen_links", []))

    def _save_state(self) -> None:
        payload = {"seen_links": sorted(self.seen_links)}
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def fetch_feed(self, url: str) -> list[FeedItem]:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            xml_data = resp.read()

        root = ET.fromstring(xml_data)
        items: list[FeedItem] = []
        for node in root.findall(".//item"):
            title = (node.findtext("title") or "").strip()
            link = (node.findtext("link") or "").strip()
            published = (node.findtext("pubDate") or "").strip()
            description = (node.findtext("description") or "").strip()
            if link:
                items.append(
                    FeedItem(
                        title=title,
                        link=link,
                        published=published,
                        description=description,
                    )
                )
        return items

    def _is_aif_related(self, item: FeedItem) -> bool:
        text = f"{item.title}\n{item.description}".lower()
        return any(keyword in text for keyword in self.keywords)

    def get_new_aif_items(self) -> list[FeedItem]:
        fresh: list[FeedItem] = []
        for feed in self.feeds:
            try:
                entries = self.fetch_feed(feed)
            except (urllib.error.URLError, ET.ParseError) as exc:
                print(f"[WARN] Could not fetch {feed}: {exc}")
                continue

            for item in entries:
                if item.link in self.seen_links:
                    continue
                if self._is_aif_related(item):
                    fresh.append(item)
                self.seen_links.add(item.link)

        self._save_state()
        return fresh


def strip_html(text: str) -> str:
    text = re.sub(r"<script.*?>.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style.*?>.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch_article_text(url: str, max_chars: int = 6000) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    text = strip_html(html)
    return text[:max_chars]


def summarize_with_chatgpt(text: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "OPENAI_API_KEY not configured, so summary is skipped."

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    prompt = (
        "Summarize the following SEBI circular/notification in very simple Indian-English. "
        "Use 5 bullet points and add a final line: 'What this means for AIF investors/managers'.\n\n"
        f"Document:\n{text}"
    )

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a regulatory assistant. Explain legal text in very simple language.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            response_data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        return f"Could not generate summary from ChatGPT: {exc}"

    try:
        return response_data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError):
        return "ChatGPT response format was unexpected; summary unavailable."


def send_email_alert(subject: str, body: str) -> None:
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    username = os.environ.get("SMTP_USERNAME")
    password = os.environ.get("SMTP_PASSWORD")
    sender = os.environ.get("ALERT_FROM_EMAIL")
    recipient = os.environ.get("ALERT_TO_EMAIL")

    required = [host, username, password, sender, recipient]
    if not all(required):
        print("[INFO] Email config missing; printing alert only.")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(body)

    ctx = ssl.create_default_context()
    with smtplib.SMTP(host, port) as server:
        server.starttls(context=ctx)
        server.login(username, password)
        server.send_message(msg)


def format_alert(item: FeedItem, summary: str) -> str:
    return (
        f"New SEBI update (AIF-related)\n"
        f"Title: {item.title}\n"
        f"Published: {item.published}\n"
        f"Link: {item.link}\n\n"
        f"Simple Summary:\n{summary}\n"
    )


def run_monitor(monitor: SebiAifMonitor) -> int:
    fresh_items = monitor.get_new_aif_items()
    if not fresh_items:
        print("No new AIF-related SEBI circulars/notifications found.")
        return 0

    print(f"Found {len(fresh_items)} new AIF-related update(s).")
    for item in fresh_items:
        try:
            article_text = fetch_article_text(item.link)
        except urllib.error.URLError:
            article_text = f"{item.title}\n{item.description}"

        summary = summarize_with_chatgpt(article_text)
        alert_text = format_alert(item, summary)
        print("\n" + "=" * 80)
        print(alert_text)
        send_email_alert(f"SEBI AIF Alert: {item.title}", alert_text)

    return len(fresh_items)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Alert on new AIF-related SEBI circulars/notifications with simple summaries."
    )
    parser.add_argument(
        "--interval-minutes",
        type=int,
        default=30,
        help="Polling interval in minutes when running continuously (default: 30)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run only one check and exit.",
    )
    parser.add_argument(
        "--state-file",
        default=".state/sebi_seen.json",
        help="Where to store already-seen links.",
    )
    parser.add_argument(
        "--feed-url",
        action="append",
        dest="feed_urls",
        help="RSS feed URL(s). Can be passed multiple times.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    feeds = args.feed_urls if args.feed_urls else DEFAULT_FEEDS
    monitor = SebiAifMonitor(
        state_file=Path(args.state_file),
        feeds=feeds,
        keywords=AIF_KEYWORDS,
    )

    if args.once:
        run_monitor(monitor)
        return

    while True:
        run_monitor(monitor)
        time.sleep(max(args.interval_minutes, 1) * 60)


if __name__ == "__main__":
    main()
