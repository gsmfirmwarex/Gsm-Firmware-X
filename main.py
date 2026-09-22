import os
import json
import time
import re
import threading
from datetime import datetime
import feedparser
import requests
from google import genai
from fastapi import FastAPI

app = FastAPI()

# --- কনফিগারেশন ---
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

# --- AI দিয়ে ১২০০ শব্দের এসইও কনটেন্ট তৈরি ---
def generate_seo_article(raw_title, raw_desc, file_link):
    if not client:
        return None

    prompt = f"""
    You are an expert GSM Firmware, ROM, and flashing specialist and an elite SEO copywriter.
    Generate an in-depth, 1000-1200 word technical flashing guide and review for:
    File/Firmware Name: {raw_title}
    Details: {raw_desc}
    Target Source Link: {file_link}

    Requirements:
    1. Write purely in clean Markdown format for a Jekyll blog.
    2. Start directly with Jekyll front-matter:
    ---
    title: "{raw_title} - Official Tested Flash File Download & Guide"
    description: "Download {raw_title} tested stock ROM firmware. Step-by-step flashing instructions, tool requirements, and troubleshooting."
    date: {datetime.now().strftime("%Y-%m-%d")}
    categories: [Firmware, GSM]
    tags: [flash-file, tested-rom, gsm-repair, firmware-download]
    ---
    3. Include sections: Firmware Details Table, Pre-requisites & Required Tools, Step-by-step Flashing Instructions, Common Errors & Fixes, FAQ.
    4. Integrate high-conversion Call-To-Action (CTA) links targeting the original source: {file_link}
    5. Output ONLY Markdown content. No greetings or meta remarks.
    """

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

# --- গিটহাবে পুশ ---
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
                article_markdown = generate_seo_article(raw_title, raw_desc, link)

                if article_markdown:
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    slug = slugify(raw_title)
                    filename = f"{date_str}-{slug}.md"

                    if push_to_github(filename, article_markdown):
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
