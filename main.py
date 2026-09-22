import os
import json
import time
import re
import random
import threading
from datetime import datetime
import base64
import feedparser
import requests
from fastapi import FastAPI

app = FastAPI()

# ==============================================================================
# ১. কনফিগারেশন সেটআপ
# ==============================================================================
RSS_FEED_URL = os.getenv("RSS_FEED_URL", "https://firmwareworld.com/index.php?a=rss")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "gsmfirmwarex/Gsm-Firmware-X")
BRANCH = os.getenv("GITHUB_BRANCH", "master")
POSTS_FOLDER = "_posts"
HISTORY_FILE = "processed_posts.json"

# ==============================================================================
# ২. JSON হিস্ট্রি ট্র্যাকিং (ডুপ্লিকেট প্রতিরোধ)
# ==============================================================================
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

# ==============================================================================
# ৩. খাঁটি পাইথন কনটেন্ট জেনারেটর (SEO & Human Diversity Engine)
# ==============================================================================
BRANDS = [
    "Samsung", "Oppo", "Vivo", "Xiaomi", "Realme", "Infinix", 
    "Tecno", "OnePlus", "Motorola", "Huawei", "Honor", "Nokia", "Itel"
]

def analyze_firmware_data(title):
    """টাইটেল থেকে ব্র্যান্ড, মডেল ও চিপসেট/টুলস অনুমান করার ইঞ্জিন"""
    detected_brand = "Android"
    for brand in BRANDS:
        if re.search(r'\b' + brand + r'\b', title, re.IGNORECASE):
            detected_brand = brand
            break

    # ফ্ল্যাশ টুল ও চিপসেট নির্ধারণ
    title_lower = title.lower()
    if "scatter" in title_lower or "mt" in title_lower or "mediatek" in title_lower:
        chipset = "MediaTek (MTK)"
        tool = "SP Flash Tool / UnlockTool"
    elif "qualcomm" in title_lower or "qcom" in title_lower or "edl" in title_lower or "prog" in title_lower:
        chipset = "Qualcomm Snapdragon"
        tool = "QFIL / QPST / Qualcomm Flash Image Loader"
    elif "pac" in title_lower or "spd" in title_lower or "unisoc" in title_lower:
        chipset = "Spreadtrum (SPD / Unisoc)"
        tool = "SPD Upgrade Tool / Research Download"
    elif detected_brand == "Samsung":
        chipset = "Exynos / Snapdragon"
        tool = "Odin Downloader"
    else:
        chipset = "Official Manufacturer Hardware"
        tool = f"Authorized {detected_brand} Flash Suite"

    clean_name = re.sub(r'[_.-]', ' ', title).strip()
    return detected_brand, clean_name, chipset, tool

def generate_seo_article(raw_title, raw_desc, file_link):
    """পাইথন নিজে থেকেই ৬০০-৮০০ শব্দের পূর্ণাঙ্গ এসইও আর্টিকেল তৈরি করে"""
    brand, clean_name, chipset, flash_tool = analyze_firmware_data(raw_title)
    date_str = datetime.now().strftime("%Y-%m-%d")

    # এসইও মেটা ট্যাগ ও হ্যাশট্যাগ
    tags = [
        f"{brand.lower()} firmware",
        f"{brand.lower()} flash file",
        "stock rom",
        "tested rom",
        "gsm repair",
        "official software",
        "unbrick smartphone"
    ]
    hashtags = f"#{brand}Firmware #{brand}FlashFile #StockROM #GSMRepair #FlashingGuide #UnbrickPhone"

    # ভিন্ন ভিন্ন হিউম্যান ওপেনিং স্টাইল
    openings = [
        f"Restoring your {clean_name} back to factory fresh operating condition requires genuine and verified stock software. Whether you are dealing with a severe bootloop, resolving continuous app crashes, or recovering from a corrupted OS update, this official tested firmware package provides the ultimate repair solution.",
        f"Encountering system stability problems, frozen startup screens, or firmware partition errors on your {clean_name}? Flashing the original factory ROM remains the most reliable technical method to revive your device safely without damaging system health.",
        f"Having a clean and verified stock flash file is paramount when troubleshooting advanced Android software malfunctions. Below is the full technical breakdown, USB setup parameters, and step-by-step unbrick procedure for the {clean_name}."
    ]
    intro = random.choice(openings)

    # ৬০০ - ৮০০ শব্দের পূর্ণাঙ্গ প্রফেশনাল টেকনিক্যাল পোস্ট (Google Anti-Spam Link সহ)
    content = f"""---
title: "{clean_name} Official Tested Stock ROM Firmware Flash File"
description: "Download verified {clean_name} official stock firmware. Complete technical specifications, USB flashing setup, and step-by-step repair guide."
date: {date_str}
categories: [Firmware, {brand}]
tags: {tags}
---

{intro}

### Technical Specification Overview
The table below highlights the critical technical information regarding this firmware build:

| Parameter | Specification Details |
| :--- | :--- |
| **Package / ROM Name** | `{raw_title}` |
| **Device Manufacturer** | {brand} |
| **Chipset Architecture** | {chipset} |
| **Recommended Utility** | {flash_tool} |
| **Software Status** | 100% Tested & Verified Clean |
| **File Format Structure** | Factory Stock Binary Archive |

### Critical Software Issues Resolved by This Firmware
Installing this official tested flash file addresses numerous critical operational errors:
* **Bootloop and Logo Freezes:** Eliminates constant reboot cycles where the device cannot pass the brand boot logo.
* **Network & Baseband Corruption:** Restores missing IMEI numbers, unknown baseband versions, and unstable radio signals caused by damaged NVRAM/EFS partitions.
* **System Bloat & Malware Infiltration:** Eradicates stubborn adware, root-level trojans, and unwanted preloaded background bloatware.
* **Rollback & Warranty Restoration:** Reverts risky experimental custom ROMs and unroots the device cleanly back to genuine factory state.
* **Hard Brick & Fastboot Recovery:** Safely recovers devices that fail to power on normally or remain stuck inside emergency download modes.

### Flashing Pre-requisites & Preparation
Before initiating the write operation on your computer, ensure the following measures are in place:
1. **Sufficient Battery Power:** Charge the handset to at least 60% capacity to eliminate shutdown risks midway through the write cycle.
2. **Motherboard Data Cable:** Utilize an authentic, high-grade USB data cable connected directly to your computer's rear USB ports for uninterrupted data transfer.
3. **Dedicated Driver Handshake:** Install the official {brand} USB drivers and proper {chipset} CDC/VCOM drivers on your Windows workstation.
4. **Complete Data Backup:** Flashing will format internal user storage partitions entirely. Ensure you back up all personal files, media, and contacts if the phone is still accessible.

### Step-by-Step Installation Instructions
1. Download the archive package `{raw_title}.zip` to your computer and extract it using 7-Zip or WinRAR.
2. Launch the authorized **{flash_tool}** using Administrator privileges.
3. Locate and load the firmware partition map (Scatter, PAC, or RawProgram XML file) from the extracted ROM folder.
4. Power off your {clean_name} completely.
5. Hold the hardware Boot Key sequence (commonly Volume Up + Volume Down or Volume Down only) and plug the USB cable into your device.
6. The flashing utility will initiate the handshake. Click **Download / Flash** and allow the data transfer to reach 100% completion.
7. Disconnect the USB cable once you see the green checkmark or Success notification, then restart the smartphone.

### Frequently Asked Questions (FAQ)
* **Q: Will this firmware void my manufacturer warranty?**  
  *No, this is genuine official factory stock ROM, meaning it restores original factory warranty compliance.*
* **Q: What should I do if the flashing process gets interrupted?**  
  *Do not panic. Keep calm, reinstall proper USB drivers, recharge the device via wall adapter, and re-run the flashing procedure from Step 1.*

### Download Tested ROM Package
To download the verified, virus-free stock ROM package, proceed directly to the primary download page:

<p align="center">
  <a href="{file_link}" rel="nofollow noopener" target="_blank" style="background-color: #2ea44f; color: #ffffff; padding: 12px 24px; font-size: 16px; font-weight: bold; text-decoration: none; border-radius: 6px; display: inline-block;">
    📥 Download {raw_title} Official Package
  </a>
</p>

---
**Tags & Keywords:** {hashtags}
"""
    return content

# ==============================================================================
# ৪. গিটহাবে পুশ ও স্লাগ তৈরি
# ==============================================================================
def push_to_github(file_name, content):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{POSTS_FOLDER}/{file_name}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

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

# ==============================================================================
# ৫. ব্যাকগ্রাউন্ড আরএসএস সিঙ্ক লুপ
# ==============================================================================
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

                print(f"New firmware found: {raw_title}")
                
                # পাইথনের নিজস্ব এসইও কনটেন্ট ইঞ্জিন
                article_markdown = generate_seo_article(raw_title, raw_desc, link)

                date_str = datetime.now().strftime("%Y-%m-%d")
                slug = slugify(raw_title)
                filename = f"{date_str}-{slug}.md"

                if push_to_github(filename, article_markdown):
                    save_processed_link(link)
                    print(f"Successfully published & saved to history: {filename}")
                else:
                    print(f"GitHub push failed for: {filename}")

                # গিটহাব পুশ রেট লিমিট বজায় রাখতে ছোট বিরতি
                time.sleep(5)

        except Exception as e:
            print(f"Error in sync cycle: {e}")

        # প্রতি ২০ মিনিট পর পর ফিড চেক করবে
        time.sleep(1200)

@app.on_event("startup")
def start_background_task():
    thread = threading.Thread(target=rss_worker, daemon=True)
    thread.start()

@app.get("/")
def health_check():
    return {"status": "running", "service": "Pure Python RSS-to-GitHub Automation Bot"}
