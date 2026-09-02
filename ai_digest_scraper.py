import os
import smtplib
import requests
import feedparser
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# CONFIGURAZIONE FONTI AI
REDDIT_SUBREDDITS = ["LocalLLaMA", "AITools", "ArtificialInteligence"]
TELEGRAM_CHANNELS = ["n8n_io", "aitools"]  # Esempi di canali pubblici AI
YOUTUBE_CHANNELS = {
    "Matt Wolfe": "UCJQJaiTKy3fzacOpqL5WTEg",
    "AI Advantage": "UCHL9snU3056o9qR3hR4c_CA"
}

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "topongo@gmail.com")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "topongo@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Radar-Bot/1.0"
}

def fetch_reddit_ai_tools():
    """Raccoglie i post più votati e le novità da Reddit via JSON pubblico."""
    items = []
    for sub in REDDIT_SUBREDDITS:
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=5"
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                data = res.json()
                posts = data.get("data", {}).get("children", [])
                for p in posts:
                    pdata = p.get("data", {})
                    # Prendi solo post con link o discussioni su nuovi tool
                    title = pdata.get("title")
                    permalink = f"https://reddit.com{pdata.get('permalink')}"
                    score = pdata.get("score", 0)
                    if score > 15:  # Filtro qualità minima
                        items.append({"title": title, "link": permalink, "source": f"r/{sub}", "score": score})
        except Exception as e:
            print(f"Errore Reddit {sub}: {e}")
    return items

def fetch_telegram_public_preview():
    """Estrae le ultime novità dai canali Telegram pubblici tramite web preview."""
    items = []
    for ch in TELEGRAM_CHANNELS:
        url = f"https://t.me/s/{ch}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                messages = soup.find_all("div", class_="tgme_widget_message_text")
                for msg in messages[-3:]:  # Prendi gli ultimi 3 messaggi
                    text = msg.get_text(strip=True)
                    if len(text) > 30:
                        short_text = text[:120] + "..."
                        items.append({"title": short_text, "link": url, "source": f"Telegram @{ch}"})
        except Exception as e:
            print(f"Errore Telegram {ch}: {e}")
    return items

def fetch_youtube_tutorials():
    """Estrae gli ultimi video tutorial AI tramite feed RSS nativi di YouTube."""
    items = []
    for name, channel_id in YOUTUBE_CHANNELS.items():
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:2]:  # Ultimi 2 video per canale
                items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "source": f"YouTube ({name})"
                })
        except Exception as e:
            print(f"Errore YouTube {name}: {e}")
    return items

def build_email_body(reddit_items, telegram_items, youtube_items):
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #222; line-height: 1.6;">
        <h2 style="color: #6200ee;">⚡ AI Radar: Novità, Free Tools & Tutorial</h2>
        <p>Report di aggiornamento per rimanere un passo avanti. Generato tre volte a settimana.</p>
        <hr style="border: 0; border-top: 1px solid #ddd;">
        
        <h3 style="color: #03a9f4;">🛠️ Nuovi Tool Gratis & Trend da Reddit</h3>
    """
    if reddit_items:
        html += "<ul>"
        for item in reddit_items:
            html += f"<li style='margin-bottom: 8px;'><a href='{item['link']}' target='_blank'><b>{item['title']}</b></a> <span style='font-size:0.8em; color:#666;'>[{item['source']} - 👍 {item['score']}]</span></li>"
        html += "</ul>"
    else:
        html += "<p>Nessun aggiornamento rilevante da Reddit.</p>"

    html += "<h3 style='color: #ff9800;'>🎬 Video Tutorial & Demo (YouTube)</h3>"
    if youtube_items:
        html += "<ul>"
        for item in youtube_items:
            html += f"<li style='margin-bottom: 8px;'><a href='{item['link']}' target='_blank'><b>{item['title']}</b></a> <span style='font-size:0.8em; color:#666;'>[{item['source']}]</span></li>"
        html += "</ul>"
    else:
        html += "<p>Nessun nuovo tutorial trovato.</p>"

    html += "<h3 style='color: #0088cc;'>📢 Flash News da Telegram</h3>"
    if telegram_items:
        html += "<ul>"
        for item in telegram_items:
            html += f"<li style='margin-bottom: 8px;'><a href='{item['link']}' target='_blank'>{item['title']}</a> <span style='font-size:0.8em; color:#666;'>[{item['source']}]</span></li>"
        html += "</ul>"
    else:
        html += "<p>Nessun aggiornamento dai canali Telegram.</p>"

    html += """
        <hr style="border: 0; border-top: 1px solid #ddd; margin-top: 30px;">
        <p style='font-size: 0.8em; color: #888;'>Automazione GitHub Actions - Avv. Alessandro Ghiani</p>
    </body>
    </html>
    """
    return html

def send_email(subject, html_content):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print("Email inviata con successo!")
    except Exception as e:
        print(f"Errore invio e-mail: {e}")

if __name__ == "__main__":
    reddit = fetch_reddit_ai_tools()
    telegram = fetch_telegram_public_preview()
    youtube = fetch_youtube_tutorials()
    
    html = build_email_body(reddit, telegram, youtube)
    send_email("🚀 AI Radar: Novità, Tool Gratuiti & Tutorial Settimanali", html)
