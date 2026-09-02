import os
import smtplib
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import feedparser
from bs4 import BeautifulSoup

# CONFIGURAZIONE FONTI
REDDIT_SUBS = ["LocalLLaMA", "AITools", "ArtificialInteligence"]
TELEGRAM_CHANNELS = ["n8n_io", "aitools"]
YOUTUBE_CHANNELS = {
    "Matt Wolfe": "UCJQJaiTKy3fzacOpqL5WTEg",
    "AI Advantage": "UCHL9snU3056o9qR3hR4c_CA"
}

# KEYWORD PER FILTRARE I CONTENUTI DI QUALITÀ
QUALITY_KEYWORDS = ["free", "tool", "gratis", "github", "ai", "app", "tutorial", "software", "model"]

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "topongo@gmail.com")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "topongo@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def fetch_reddit_rss():
    """Estrae i post tramite i Feed RSS ufficiali di Reddit (bypassa il blocco JSON)."""
    items = []
    print("\n--- AVVIO SCRAPING REDDIT (RSS) ---")
    for sub in REDDIT_SUBS:
        url = f"https://www.reddit.com/r/{sub}/hot.rss"
        try:
            feed = feedparser.parse(url, agent=USER_AGENT)
            print(f"Reddit r/{sub}: trovati {len(feed.entries)} elementi.")
            for entry in feed.entries[:4]:
                title = entry.title
                link = entry.link
                items.append({"title": title, "link": link, "source": f"r/{sub}"})
        except Exception as e:
            print(f"Errore Reddit r/{sub}: {e}")
    return items

def fetch_youtube_tutorials():
    """Estrae i video tutorial dai Feed RSS ufficiali dei canali YouTube."""
    items = []
    print("\n--- AVVIO SCRAPING YOUTUBE ---")
    for name, channel_id in YOUTUBE_CHANNELS.items():
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            feed = feedparser.parse(rss_url, agent=USER_AGENT)
            print(f"YouTube {name}: trovati {len(feed.entries)} video.")
            for entry in feed.entries[:2]:
                items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "source": f"YouTube ({name})"
                })
        except Exception as e:
            print(f"Errore YouTube {name}: {e}")
    return items

def fetch_instagram_ai_news():
    """Aggira il blocco Instagram usando l'indice Google RSS per Reel e post su AI Tool."""
    items = []
    print("\n--- AVVIO SCRAPING INSTAGRAM (VIA GOOGLE RSS) ---")
    query = 'site:instagram.com ("AI tool" OR "tool gratuito" OR "intelligenza artificiale")'
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=it&gl=IT&ceid=IT:it"
    
    try:
        feed = feedparser.parse(rss_url, agent=USER_AGENT)
        print(f"Instagram (via Google): trovati {len(feed.entries)} risultati.")
        for entry in feed.entries[:4]:
            title = entry.title.split(" - ")[0].strip()
            items.append({
                "title": title,
                "link": entry.link,
                "source": "Instagram News"
            })
    except Exception as e:
        print(f"Errore Instagram: {e}")
    return items

def fetch_telegram_filtered():
    """Estrae i messaggi Telegram filtrando solo quelli che contengono tool o novità reali."""
    items = []
    print("\n--- AVVIO SCRAPING TELEGRAM (FILTRATO) ---")
    headers = {"User-Agent": USER_AGENT}
    
    for ch in TELEGRAM_CHANNELS:
        url = f"https://t.me/s/{ch}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                messages = soup.find_all("div", class_="tgme_widget_message_text")
                
                count = 0
                for msg in reversed(messages):
                    text = msg.get_text(strip=True)
                    # Filtra solo se il messaggio contiene parole chiave di interesse
                    if any(kw in text.lower() for kw in QUALITY_KEYWORDS) and len(text) > 40:
                        short_text = text[:140] + "..."
                        items.append({"title": short_text, "link": url, "source": f"Telegram @{ch}"})
                        count += 1
                        if count >= 3:
                            break
                print(f"Telegram @{ch}: trovati {count} messaggi rilevanti.")
        except Exception as e:
            print(f"Errore Telegram {ch}: {e}")
    return items

def build_email_body(reddit_items, youtube_items, instagram_items, telegram_items):
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #222; line-height: 1.6;">
        <h2 style="color: #6200ee;">⚡ AI Radar: Nuovi Tool Gratuiti, Trend & Tutorial</h2>
        <p>Digest multi-fonte per rimanere aggiornato su novità, script e strumenti AI.</p>
        <hr style="border: 0; border-top: 1px solid #ddd;">
        
        <h3 style="color: #03a9f4;">🛠️ Reddit: Nuovi Tool & Discussioni Tech</h3>
    """
    if reddit_items:
        html += "<ul>"
        for item in reddit_items:
            html += f"<li style='margin-bottom: 8px;'><a href='{item['link']}' target='_blank'><b>{item['title']}</b></a> <span style='font-size:0.8em; color:#666;'>[{item['source']}]</span></li>"
        html += "</ul>"
    else:
        html += "<p style='color:#777;'>Nessun dato da Reddit.</p>"

    html += "<h3 style='color: #ff9800;'>🎬 YouTube: Video Tutorial & Demo</h3>"
    if youtube_items:
        html += "<ul>"
        for item in youtube_items:
            html += f"<li style='margin-bottom: 8px;'><a href='{item['link']}' target='_blank'><b>{item['title']}</b></a> <span style='font-size:0.8em; color:#666;'>[{item['source']}]</span></li>"
        html += "</ul>"
    else:
        html += "<p style='color:#777;'>Nessun video trovato.</p>"

    html += "<h3 style='color: #e1306c;'>📸 Instagram: Post & Trend AI</h3>"
    if instagram_items:
        html += "<ul>"
        for item in instagram_items:
            html += f"<li style='margin-bottom: 8px;'><a href='{item['link']}' target='_blank'><b>{item['title']}</b></a> <span style='font-size:0.8em; color:#666;'>[{item['source']}]</span></li>"
        html += "</ul>"
    else:
        html += "<p style='color:#777;'>Nessun contenuto Instagram intercettato.</p>"

    html += "<h3 style='color: #0088cc;'>📢 Telegram: Selezione Tool Gratuiti</h3>"
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
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print("Email inviata con successo!")
    except Exception as e:
        print(f"Errore invio e-mail: {e}")

if __name__ == "__main__":
    reddit = fetch_reddit_rss()
    youtube = fetch_youtube_tutorials()
    instagram = fetch_instagram_ai_news()
    telegram = fetch_telegram_filtered()
    
    html = build_email_body(reddit, youtube, instagram, telegram)
    send_email("🚀 AI Radar: Nuovi Tool Gratuiti, YouTube & Instagram", html)
