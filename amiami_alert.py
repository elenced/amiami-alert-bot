import time
import json
import os
import requests
from playwright.sync_api import sync_playwright

PRODUCTS = [
    "https://www.amiami.com/eng/detail/?scode=FIGURE-003419",
    "https://www.amiami.com/eng/detail/?gcode=FIGURE-197378",
    "https://www.amiami.com/eng/detail/?gcode=FIGURE-197768",
]

DISCORD_WEBHOOK_URL = os.getenv("https://discordapp.com/api/webhooks/1515078069226836088/6NOV-lFe_iIpTmaqLcelta75dHIvZWb1vcsSyaL1jqLMGkow2-1v8liruECHCtCGmNZX")
DISCORD_USER_ID = "588054517078294617"

CHECK_EVERY_SECONDS = 60
STATUS_FILE = "status.json"


def send_discord_alert(message):
    requests.post(DISCORD_WEBHOOK_URL, json={"content": message})


def load_statuses():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as file:
            return json.load(file)
    return {}


def save_statuses(statuses):
    with open(STATUS_FILE, "w") as file:
        json.dump(statuses, file)


def check_page(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)

    text = page.inner_text("body")

    CLOSED = [
        "Pre-orders Closed",
        "Order Closed",
        "Sold Out",
        "Unavailable"
    ]

    AVAILABLE = [
        "Pre-order",
        "Add to Cart"
    ]

    for word in CLOSED:
        if word in text:
            return "closed"

    for word in AVAILABLE:
        if word in text:
            return "available"

    return "unknown"


last_status = load_statuses()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for url in PRODUCTS:
        try:
            status = check_page(page, url)
            old_status = last_status.get(url)

            print(url)
            print("Old:", old_status)
            print("New:", status)

           if old_status == "closed" and status == "available":
                send_discord_alert(
                    f"<@{DISCORD_USER_ID}> 🚨 **AMIAMI PREORDER OPEN!**\n\n{url}"
                )

            last_status[url] = status
            save_statuses(last_status)

        except Exception as e:
            print("Error:", e)

    browser.close()
