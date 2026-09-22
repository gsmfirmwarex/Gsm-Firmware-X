import os
import json
import time
import re
import random
import threading
from datetime import datetime
import feedparser
import requests
from google import genai
from fastapi import FastAPI

app = FastAPI()

# --- কনফিগারেশন সেটআপ ---
RSS_FEED_URL = os.getenv("RSS_FEED_URL", "https://firmwareworld.com/index.php?a=rss")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "gsmfirmwarex/Gsm-Firmware-X")
BRANCH = os.getenv("GITHUB_BRANCH", "master")
POSTS_FOLDER = "_posts"
HISTORY_FILE = "processed_posts.json"

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# --- JSON হিস্ট্রি ট্র্যাকিং (ডুপ্লিকেট প্রতিরোধ) ---
def load_processed_links():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_processed_link(link):
    links = load_processed_links()
    links.add(link)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(links), f, ensure_ascii=False, indent=2)

# --- পাইথনের নিজস্ব অ্যানালাইজার ও হিউম্যান রাইটিং ইঞ্জিন ---
BRANDS = ["Samsung", "Oppo", "Vivo", "Xiaomi", "Realme", "Infinix", "Tecno", "OnePlus", "Motorola", "Huawei"]

def extract_meta_from_title(title):
    detected_brand = "Android"
    for brand in BRANDS:
        if re.search(r'\b' + brand + r'\b', title, re.IGNORECASE):
            detected_brand = brand
            break
    clean_name = re.sub(r'[_.-]', ' ', title).strip()
    return detected_brand, clean_name

def generate_tags_and_hashtags(brand, clean_name):
    base_tags = [
        f"{brand.lower()} firmware",
        f"{brand.lower()} flash file",
        "stock rom",
        "tested firmware",
        "gsm repair",
        "official rom"
    ]
    hashtags = [
        f"#{brand}Firmware",
        f"#{brand}FlashFile",
        "#StockROM",
        "#GSMRepair",
        "#TestedFirmware"
    ]
    return base_tags, " ".join(hashtags)

def build_base_article(raw_title, raw_desc, file_link):
    """পাইথন নিজে থেকেই ৬০০-৮০০ শব্দের পূর্ণাঙ্গ এসইও আর্টিকেল তৈরি করে"""
    brand, clean_name = extract_meta_from_title(raw_title)
    tags, hashtags = generate_tags_and_hashtags(brand, clean_name)
    date_str = datetime.now().strftime("%Y-%m-%d")

    openings = [
        f"Restoring your {clean_name} to its original performance starts with getting the exact tested stock ROM package. Whether you are recovering from a hard bootloop, resolving recurring app crashes, or repairing software integrity, this authentic firmware ensures a clean flash.",
        f"Flashing the correct firmware package is the most secure method to eliminate critical operating system errors and unbrick your {clean_name}. Below is the complete technical package and step-by-step flashing instructions.",
        f"Experiencing software failure, stuck boot screens, or partition damage on your {clean_name}? Using official tested software is essential to unbrick your device without hardware complications."
    ]
    intro = random.choice(openings)

    content = f"""---
title: "{clean_name} Official Tested Firmware Flash File Download"
description: "Download {clean_name} official tested stock ROM firmware. Complete technical overview, USB flashing requirements, and troubleshooting repair guide."
date: {date_str}
categories: [Firmware, {brand}]
tags: {tags}
---

{intro}

### Technical Specification Overview
| Specification | Details |
| :--- | :--- |
| **Package Identifier** | `{raw_title}` |
| **Manufacturer/Brand** | {brand} |
| **Firmware Type** | Official Factory Stock ROM |
| **Testing Status** | 100% Verified & Tested |
| **File Architecture** | Scatter / Raw Program Image Files |

### Key Issues Resolved by This Firmware
* **Bootloop & Logo Freezing:** Solves continuous restarts and devices stuck indefinitely on the brand splash screen.
* **Network & Null Baseband:** Fixes missing modem partitions, null IMEI status, or cellular network loss after bad updates.
* **Malware & System Bloat:** Clears out stubborn root infections, background spyware, and system-level bugs.
* **Factory State Restoration:** Safely rolls back untested custom ROMs and unroots the smartphone back to original factory warranty condition.

### Pre-Requisites & System Setup
Before connecting your device and beginning the flash write operation:
1. Ensure your device retains at least 50% to 70% battery capacity to avoid disconnection midway.
2. Use an authentic high-speed USB data cable plugged into a direct motherboard port.
3. Install the verified {brand} USB drivers on your Windows machine to ensure seamless port handshake.
4. Always backup any accessible files and contacts, as clean flashing will wipe internal data partitions completely.

### Flashing Instructions (Quick Reference Guide)
1. Download and unpack `{raw_title}.zip` using 7-Zip or WinRAR on your PC.
2. Launch the authorized flash utility for {brand} devices with Administrator permissions.
3. Load the primary scatter/raw flash map file directly from the extracted ROM folder.
4. Completely turn off your smartphone.
5. Hold the specified hardware boot keys (typically Volume Up + Down together) and plug in the USB cable.
6. Trigger the **Download** or **Flash** button and let the transfer reach 100% without interruptions.

### Download Tested ROM Package
To download the original, verified firmware archive, proceed to the primary source link:

👉 **[Download {raw_title} Stock ROM Package Here]({file_link})**

---
**Tags & Keywords:** {hashtags}
"""
    return content

# --- জেমিনির মাধ্যমে মডিফিকেশন (উন্নত ফলব্যাকসহ) ---
MODELS_TO_TRY = ['gemini-3.6-flash', 'gemini-3.0-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']

def polish_with_gemini(base_draft):
    """জেমিনি দিয়ে হালকা রিফাইন করাবে; কোনো এরর হলে পাইথনের ড্রাফটই সরাসরি রিটার্ন করবে"""
    if not client:
        return base_draft

    prompt = f"""
    You are an expert technical smartphone repair editor.
    Review the following Jekyll Markdown post draft.
    Requirements:
    1. Keep the front-matter (YAML) and download links EXACTLY as they are.
    2. Maintain the structure, headings, table, and bullet points cleanly.
    3. Ensure the text flows naturally with strong technical accuracy (between 600-800 words).
    4. Output ONLY the polished Markdown content with no meta remarks or greetings.

    Draft:
    {base_draft}
    """

    for model_name in MODELS_TO_TRY:
        try:
            print(f"Attempting polish with model: {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response.text and len(response.text) > 300:
                print(f"Successfully polished using {model_name}")
                return response.text
        except Exception as e:
            print(f"Model {model_name} failed: {e}. Trying next...")

    print("All Gemini models bypassed. Using Python base article directly.")
    return base_draft

# --- গিটহাবে পুশ করার ফাংশন ---
def push_to_github(file_name, content):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{POSTS_FOLDER}/{file_name}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    import base64
    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    data = {
        "message": f"Auto-publish firmware guide: {file_name}",
        "content": encoded_content,
        "branch": BRANCH
    }

    res = requests.put(url, headers=headers, json=data)
    return res.status_code in [200, 201]

def slugify(text):
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text).strip().lower()
    return re.sub(r'[\s+]+', '-', text)[:45]

# --- আরএসএস সিনক্রোনাইজার লুপ ---
def rss_worker():
    while True:
        try:
            print(f"[{datetime.now()}] Checking RSS feed: {RSS_FEED_URL}")
            feed = feedparser.parse(RSS_FEED_URL)
            processed_links = load_processed_links()

            for entry in feed.entries:
                link = entry.link
                if link in processed_links:
                    continue

                raw_title = entry.title
                raw_desc = getattr(entry, "description", raw_title)

                print(f"New entry found: {raw_title}")
                
                # পাইথন দিয়ে বেস ড্রাফট তৈরি
                base_article = build_base_article(raw_title, raw_desc, link)
                
                # জেমিনি দিয়ে মডিফাই করার চেষ্টা (ফেইল করলে পাইথন ড্রাফট স্বয়ংক্রিয়ভাবে ব্যবহৃত হবে)
                final_article = polish_with_gemini(base_article)

                date_str = datetime.now().strftime("%Y-%m-%d")
                slug = slugify(raw_title)
                filename = f"{date_str}-{slug}.md"

                if push_to_github(filename, final_article):
                    save_processed_link(link)
                    print(f"Successfully published & saved: {filename}")
                else:
                    print(f"GitHub push failed for: {filename}")

                time.sleep(15)  # API রেট লিমিট বজায় রাখতে সাময়িক বিরতি

        except Exception as e:
            print(f"Error in sync cycle: {e}")

        # ৩০ মিনিট পর পর ফিড চেক করবে
        time.sleep(1800)

# ব্যাকগ্রাউন্ডে আরএসএস ওয়ার্কার চালু রাখা
@app.on_event("startup")
def start_background_task():
    thread = threading.Thread(target=rss_worker, daemon=True)
    thread.start()

# UptimeRobot-এর জন্য হেলথ চেক এন্ডপয়েন্ট
@app.get("/")
def health_check():
    return {"status": "running", "service": "RSS to GitHub Pages Bot"}
