# -*- coding: utf-8 -*-
import os
import smtplib
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import feedparser
from bs4 import BeautifulSoup

# 1. CANALI YOUTUBE INFLUENCER AI (ID Canale Ufficiali)
YOUTUBE_INFLUENCERS = {
    "Matt Wolfe": "UCJQJaiTKy3fzacOpqL5WTEg",
    "AI Advantage": "UCHL9snU3056o9qR3hR4c_CA",
    "Matthew Berman": "UCm63P_OAt1L2O0jXWACmO0Q",
    "Nate MacIntyre": "UCyLBy9S9v6O-d7v40Apt9fA"
}

# 2. SUBREDDIT DEDICATI A TOOL E APP AI
REDDIT_SUBS = ["AITools", "CoolGithubProjects", "ArtificialInteligence"]

# 3. CANALI TELEGRAM AI TOOL & APP
TELEGRAM_CHANNELS = ["aitools", "n8n_io", "aitoolsdaily"]

# PAROLE CHIAVE PER FILTRARE I CONSIGLI SULLE APP
APP_KEYWORDS = ["app", "tool", "free", "gratis", "github", "software", "consiglio", "tutorial", "prompt", "workflow"]

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "topongo@gmail.com")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "topongo@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def fetch_youtube_influencers():
    items = []
    print("\n--- SCRAPING YOUTUBE INFLUENCERS ---")
    for name, channel_id in YOUTUBE_INFLUENCERS.items():
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            res = requests.get(rss_url, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                feed = feedparser.parse(res.text)
                print(f"YouTube @{name}: trovati {len(feed.entries)} video.")
                for entry in feed.entries[:2]:
                    items.append({
                        "title": entry.title,
                        "link": entry.link,
                        "source": f"YouTube (@{name})"
                    })
            else:
                print(f"Errore HTTP {res.status_code} su YouTube per {name}")
        except Exception as e:
            print(f"Eccezione YouTube {name}: {e}")
    return items

def fetch_instagram_influencer_reels():
    items = []
    print("\n--- SCRAPING INSTAGRAM REELS & CREATOR ---")
    query = '(site:instagram.com/reel/ OR site:instagram.com/p/) ("ai tool" OR "app intelligenza artificiale" OR "consigli ai" OR "tool gratuito")'
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=it&gl=IT&ceid=IT:it"
    
    try:
        res = requests.get(rss_url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            feed = feedparser.parse(res.text)
            print(f"Instagram Reels/Post intercettati: {len(feed.entries)}")
            for entry in feed.entries[:5]:
                title = entry.title.split(" - ")[0].strip()
                items.append({
                    "title": title,
                    "link": entry.link,
                    "source": "Instagram Creator/Reels"
                })
    except Exception as e:
        print(f"Errore Instagram: {e}")
    return items

def fetch_reddit_app_showcases():
    items = []
    print("\n--- SCRAPING REDDIT TOOL SHOWCASE ---")
    for sub in REDDIT_SUBS:
        url = f"https://www.reddit.com/r/{sub}/hot.rss"
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                feed = feedparser.parse(res.text)
                count = 0
                for entry in feed.entries:
                    title = entry.title
                    if any(kw in title.lower() for kw in APP_KEYWORDS):
                        items.append({"title": title, "link": entry.link, "source": f"r/{sub}"})
                        count += 1
                        if count >= 3:
                            break
                print(f"Reddit r/{sub}: estratti {count} tool/app rilevanti.")
        except Exception as e:
            print(f"Errore Reddit r/{sub}: {e}")
    return items

def fetch_telegram_app_tips():
    items = []
    print("\n--- SCRAPING TELEGRAM APP TIPS ---")
    for ch in TELEGRAM_CHANNELS:
        url = f"https://t.me/s/{ch}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                messages = soup.find_all("div", class_="tgme_widget_message_text")
                
                count = 0
                for msg in reversed(messages):
                    text = msg.get_text(strip=True)
                    if any(kw in text.lower() for kw in APP_KEYWORDS) and len(text) > 30:
                        short_text = text[:130] + "..."
                        items.append({"title": short_text, "link": url, "source": f"Telegram @{ch}"})
                        count += 1
                        if count >= 2:
                            break
                print(f"Telegram @{ch}: trovati {count} consigli app.")
        except Exception as e:
            print(f"Errore Telegram {ch}: {e}")
    return items

def build_email_body(youtube_items, instagram_items, reddit_items, telegram_items):
    html = """
    <html>
    <body style="font-family: Arial, sans-serif; color: #222; line-height: 1.6;">
        <h2 style="color: #6200ee;">&#9889; AI Radar: Consigli, App &amp; Tutorial dagli Influencer</h2>
        <p>Selezione aggiornata dei migliori tool gratuiti, video e consigli pratici sul mondo AI.</p>
        <hr style="border: 0; border-top: 1px solid #ddd;">
        
        <h3 style="color: #ff9800;">&#127916; Video Tutorial &amp; Demo dagli Influencer (YouTube)</h3>
    """
    if youtube_items:
        html += "<ul>"
        for item in youtube_items:
            html += f"<li style='margin-bottom: 8px;'><a href='{item['link']}' target='_blank'><b>{item['title']}</b></a> <span style='font-size:0.8em; color:#666;'>[{item['source']}]</span></li>"
        html += "</ul>"
    else:
        html += "<p style='color:#777;'>Nessun nuovo video dagli influencer YouTube selezionati.</p>"

    html += "<h3 style='color: #e1306c;'>&#128248; Consigli App &amp; Reel AI (Instagram)</h3>"
    if instagram_items:
        html += "<ul>"
        for item in instagram_items:
            html += f"<li style='margin-bottom: 8px;'><a href='{item['link']}' target='_blank'><b>{item['title']}</b></a> <span style='font-size:0.8em; color:#666;'>[{item['source']}]</span></li>"
        html += "</ul>"
    else:
        html += "<p style='color:#777;'>Nessun Reel o post di consigli intercettato.</p>"

    html += "<h3 style='color: #03a9f4;'>&#128736; Nuove App &amp; Tool Gratuiti (Reddit)</h3>"
    if reddit_items:
        html += "<ul>"
        for item in reddit_items:
            html += f"<li style='margin-bottom: 8px;'><a href='{item['link']}' target='_blank'><b>{item['title']}</b></a> <span style='font-size:0.8em; color:#666;'>[{item['source']}]</span></li>"
        html += "</ul>"
    else:
        html += "<p style='color:#777;'>Nessuna nuova app rilevata su Reddit.</p>"

    html += "<h3 style='color: #0088cc;'>&#128227; Mini-Guide &amp; Flash Tips (Telegram)</h3>"
    if telegram_items:
        html += "<ul>"
        for item in telegram_items:
            html += f"<li style='margin-bottom: 8px;'><a href='{item['link']}' target='_blank'>{item['title']}</a> <span style='font-size:0.8em; color:#666;'>[{item['source']}]</span></li>"
        html += "</ul>"
    else:
        html += "<p style='color:#777;'>Nessun messaggio rilevante da Telegram.</p>"

    html += """
        <hr style="border: 0; border-top: 1px solid #ddd; margin-top: 30px;">
        <p style='font-size: 0.8em; color: #888;'>Automazione AI Radar Engine - Avv. Alessandro Ghiani</p>
    </body>
    </html>
    """
    return html

def send_email(subject, html_content):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print("Email inviata con successo!")
    except Exception as e:
        print(f"Errore invio e-mail: {e}")

if __name__ == "__main__":
    youtube = fetch_youtube_influencers()
    instagram = fetch_instagram_influencer_reels()
    reddit = fetch_reddit_app_showcases()
    telegram = fetch_telegram_app_tips()
    
    html = build_email_body(youtube, instagram, reddit, telegram)
    send_email("🚀 AI Radar: Consigli App, Video & Tool dagli Influencer", html)
