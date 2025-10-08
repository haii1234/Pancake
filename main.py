"""Command line interface for scraping job postings."""
from __future__ import annotations

import json
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import List
import os
from datetime import datetime

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, WebDriverException

from phlux.config import load_config
from phlux.scraping import ScrapeManager, load_company_data, autoApply
from utils import get_driver, update_icons

GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]

def format_message_html(message: dict) -> str:
    """Return HTML body for the notification email."""
    try:
        with open("icons.json", "r", encoding="utf-8") as f:
            icons = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        icons = {}

    lines = [
        '<h1 style="font-family: sans-serif;">New internships found</h1>',
    ]

    lines.append('<hr style="margin-top: 30px; margin-bottom: 20px;">')

    # Company listings
    for company, jobs in message.get("companies", {}).items():
        icon_url = icons.get(company, {})
        if not isinstance(icon_url, str):
            icon_url = icon_url.get("email", "")
        icon_html = (
            f'<img src="{icon_url}" alt="{company} logo" height="24" style="vertical-align:middle; margin-right:6px;">'
            if icon_url else ""
        )

        lines.append(f'<div style="margin-bottom: 30px;">')
        lines.append(f'<h2 style="margin-bottom: 5px; font-family: monospace;">{icon_html} {company}</h2>')
        lines.append("<ul style='margin-top: 5px;'>")
        for job in jobs["jobs"]:
            cleaned = job["title"].strip().replace("\n", " ")
            lines.append(f"<li style='margin-bottom: 4px; font-family: monospace;'>{cleaned}</li>")
        lines.append("</ul>")
        lines.append(f'<p><strong>🔗 <a style="font-family: monospace;" href="{jobs["link"]}" target="_blank">Apply Here</a></strong></p>')
        lines.append('</div>')
        lines.append('<hr style="margin-top: 20px; margin-bottom: 20px;">')

    # Footer
    lines.append('<p style="font-family: monospace;">View all companies at <a href="https://github.com/haii1234/Pancake" target="_blank">github.com/haii1234/Pancake</a></p>')

    return "\n".join(lines)

def send_email(message: dict, test: bool = False) -> None:
    """Send the notification email."""
    msg = EmailMessage()
    msg["Subject"] = "★ New Opportunity Alert!"
    msg["From"] = "nicolezcui@gmail.com"
    msg["To"] = "nicolezcui@gmail.com"
    if not test:
        msg["Cc"] = "biancazhg9@gmail.com, huan2137@purdue.edu, 27d.gao@gmail.com, bgl2126@columbia.edu, jl7026@columbia.edu, doraliao502@gmail.com, acb2319@columbia.edu, dea2142@columbia.edu, im2663@nyu.edu, floraqiurobot@gmail.com"
    html_content = format_message_html(message)
    msg.set_content("This email contains HTML. Please view it in an HTML-compatible client.")
    msg.add_alternative(html_content, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login("nicolezcui@gmail.com", GMAIL_APP_PASSWORD)
        smtp.send_message(msg)

def main() -> None:
    config = load_config()
    manager = ScrapeManager()
    companies = load_company_data()
    result = manager.scrape_companies(companies=companies)
    data = result["data"]
    new_jobs = result["new_jobs"]

    Path("storage.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    if new_jobs.get("companies"):
        update_icons(companies=companies)
        send_email(new_jobs, test = False)

if __name__ == "__main__":
    main()

