import os
import random
import re
from datetime import datetime
from google import genai

# --- ১. এপিআই ও কনফিগারেশন ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# --- ২. পাইথনের নিজস্ব অ্যানালাইজার ও হিউম্যান ভ্যারিয়েশন ইঞ্জিন ---

BRANDS = ["Samsung", "Oppo", "Vivo", "Xiaomi", "Realme", "Infinix", "Tecno", "OnePlus", "Motorola"]

def extract_meta_from_title(title):
    """ফাইলের টাইটেল থেকে ব্র্যান্ড ও মডেল আলাদা করার লজিক"""
    detected_brand = "Android"
    for brand in BRANDS:
        if re.search(r'\b' + brand + r'\b', title, re.IGNORECASE):
            detected_brand = brand
            break
            
    # ক্লিন মডেল নাম
    clean_name = re.sub(r'[_.-]', ' ', title).strip()
    return detected_brand, clean_name

def generate_tags_and_hashtags(brand, clean_name):
    """অটোমেটিক এসইও ট্যাগ ও হ্যাশট্যাগ তৈরি"""
    base_tags = [
        f"{brand.lower()} firmware",
        f"{brand.lower()} flash file",
        "stock rom",
        "tested firmware",
        "official rom",
        "usb driver",
        "unbrick guide"
    ]
    hashtags = [
        f"#{brand}Firmware",
        f"#{brand}FlashFile",
        "#StockROM",
        "#FirmwareWorld",
        "#GSMRepair",
        "#PhoneFlashing"
    ]
    return base_tags, " ".join(hashtags)

def build_base_article(raw_title, file_link):
    """পাইথন নিজে থেকেই ৬০০-৮০০ শব্দের একটি কাঠামো তৈরি করবে"""
    brand, clean_name = extract_meta_from_title(raw_title)
    tags, hashtags = generate_tags_and_hashtags(brand, clean_name)
    
    # হিউম্যান স্টাইলের ভিন্ন ভিন্ন ওপেনিং বাক্য
    openings = [
        f"If you are dealing with software bugs, bootloop issues, or simply need to restore your {clean_name} to factory condition, having the official tested flash file is critical.",
        f"Encountering system errors or looking to unbrick your device? The official firmware for {clean_name} provides the safest route to restore original performance.",
        f"Proper flashing requires clean and authentic software. This guide covers everything you need to know about installing the official stock ROM on your {clean_name}."
    ]
    intro = random.choice(openings)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # পাইথনের নিজস্ব বেস ড্রাফট (Jekyll Front-Matter সহ)
    base_draft = f"""---
title: "{clean_name} Official Tested Stock ROM Flash File"
description: "Download tested {clean_name} firmware flash file. Step-by-step unbrick and repair guide with official flash tool instructions."
date: {date_str}
categories: [Firmware, {brand}]
tags: {tags}
---

{intro}

### Technical File Overview
| Specification | Details |
| :--- | :--- |
| **Package Name** | {raw_title} |
| **Device Brand** | {brand} |
| **Status** | 100% Tested & Verified |
| **Target Architecture** | Official Stock Firmware |

### Core Advantages of This Firmware
1. **Unbrick Stuck Devices:** Fixes devices stuck on boot logo or bootloop cycles.
2. **Remove Software Glitches:** Cleans system bugs, malware, and unexpected crashes.
3. **Revert Modifications:** Easily rollback custom ROMs or unroot device back to genuine factory state.
4. **Network & Baseband Fix:** Restores missing IMEI or baseband null errors caused by corrupted partitions.

### Pre-Requisites & Safety Checklist
Before initiating the flashing process, make sure you prepare the following requirements:
* Maintain at least 60% battery level to prevent accidental shutdown during firmware write.
* Reliable high-speed USB data cable and a stable Windows PC.
* Install dedicated {brand} USB drivers on your computer.
* Back up all your vital photos, contacts, and personal data, as flashing wipes the entire internal storage.

### Flashing Instructions (Quick Steps)
1. Extract the firmware package `{raw_title}.zip` using 7-Zip or WinRAR.
2. Open the recommended official flashing tool for {brand} as Administrator.
3. Load the scatter or firmware image files into the designated tool interface.
4. Power down your smartphone completely.
5. Connect your device while holding the required Boot Key combination (Volume Down or Both Volume keys).
6. Click Download/Flash and wait for the successful confirmation checkmark.

### Download Tested ROM Package
For direct access to the clean, virus-free, and tested ROM package, navigate to the source link below:

👉 **[Download {raw_title} Official Package Here]({file_link})**

---
**Tags & Keywords:** {hashtags}
"""
    return base_draft

# --- ৩. জেমিনির মাধ্যমে সামান্য মডিফিকেশন (Human Touch Polish) ---

def polish_with_gemini(base_draft):
    """জেমিনি কেবল পাইথনের লেখাকে ন্যাচারাল ও হিউম্যানাইজ করবে (পুরোটা নতুন করে লেখার দরকার নেই)"""
    if not client:
        return base_draft

    prompt = f"""
    You are an expert technical editor.
    Review the following Jekyll Markdown post draft. 
    Task:
    - Keep the front-matter (YAML) and download links EXACTLY as they are.
    - Polish the text to sound completely natural, human-written, and technically engaging.
    - Keep the overall length between 600 to 800 words.
    - Maintain all headings, tables, and bullet points cleanly.
    - Return ONLY the final polished Markdown with no meta commentary or polite talk.

    Draft:
    {base_draft}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini polishing skipped due to: {e}. Using Python base draft directly.")
        return base_draft

# --- ৪. মূল রানার ফাংশন ---

def process_single_file(raw_title, file_link):
    print(f"Generating base draft with Python for: {raw_title}")
    # পাইথন দিয়ে কাঠামো ও কনটেন্ট তৈরি
    draft = build_base_article(raw_title, file_link)
    
    print("Sending to Gemini for quick human-touch polishing...")
    # জেমিনি দিয়ে হালকা রিফাইন করিয়ে নেওয়া
    final_article = polish_with_gemini(draft)
    return final_article

# --- টেস্ট রান ---
if __name__ == "__main__":
    test_title = "Oppo F29 Pro 5G CPH2785export_11_16.0.6.705EX01"
    test_link = "https://firmwareworld.com/index.php?a=downloads&b=file&id=1234"
    
    output = process_single_file(test_title, test_link)
    print("\n--- Output Preview (First 500 chars) ---\n")
    print(output[:500] + "...")
