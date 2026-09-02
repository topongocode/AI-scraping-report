import os
import smtplib
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import feedparser
import requests
from bs4 import BeautifulSoup

# CITTÀ DA MONITORARE
CITIES = ["Milano", "Roma", "Brescia"]
KEYWORDS = "startup OR business OR networking OR \"intelligenza artificiale\" OR legaltech"

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "topongo@gmail.com")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "topongo@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

def resolve_google_link(rss_link):
    """
    Risolve il redirect interno di Google News per ottenere l'URL reale di Eventbrite.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        res = requests.get(rss_link, headers=headers, timeout=8, allow_redirects=True)
        if res.status_code == 200:
            return res.url.split('?')[0]
    except Exception:
        pass
    return rss_link

def fetch_events_via_rss(city):
    """
    Interroga il Feed RSS di Google Search per trovare eventi Eventbrite per la città specificata.
    Bypassa al 100% i blocchi IP di Cloudflare/GitHub.
    """
    query = f"site:eventbrite.it {city} ({KEYWORDS})"
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=it&gl=IT&ceid=IT:it"
    
    print(f"\n--- DOWNLOAD RSS PER {city.upper()} ---")
    feed = feedparser.parse(rss_url)
    
    events = []
    seen_titles = set()

    for entry in feed.entries:
        title = entry.title
        # Pulizia del titolo rimosso il suffisso del publisher se presente
        clean_title = title.split(" - ")[0].strip()
        
        if clean_title.lower() in seen_titles:
            continue
        seen_titles.add(clean_title.lower())
        
        # Estrazione e risoluzione link reale
        raw_link = entry.link
        final_link = resolve_google_link(raw_link)
        
        events.append({
            "title": clean_title,
            "link": final_link
        })
        
        if len(events) >= 8:
            break
            
    print(f"Estratti {len(events)} eventi per {city}.")
    return events

def build_email_body(all_results):
    html = """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
        <h2 style="color: #0d47a1;">📌 Digest Settimanale Eventi Tech, AI & Business</h2>
        <p>Ecco gli eventi identificati per <b>Milano, Roma e Brescia</b>:</p>
        <hr style="border: 0; border-top: 1px solid #ccc;">
    """
    
    has_events = False
    for city, events in all_results.items():
        html += f"<h3 style='color: #1565c0; margin-top: 20px;'>📍 {city} ({len(events)} trovati)</h3>"
        
        if events:
            has_events = True
            html += "<ul style='margin-top: 5px;'>"
            for ev in events:
                html += f"<li style='margin-bottom: 8px;'><a href='{ev['link']}' target='_blank' style='color: #1a73e8; text-decoration: none;'><b>{ev['title']}</b></a></li>"
            html += "</ul>"
        else:
            html += "<p style='color: #777;'><i>Nessun evento recente intercettato per questa città.</i></p>"
    
    if not has_events:
        html += "<p>Nessun evento trovato per i criteri impostati.</p>"
        
    html += """
        <hr style="border: 0; border-top: 1px solid #ccc; margin-top: 30px;">
        <p style='font-size: 0.85em; color: #777;'>Automazione RSS Engine - Avv. Alessandro Ghiani</p>
    </body>
    </html>
    """
    return html

def send_email(subject, html_content):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    part_html = MIMEText(html_content, "html")
    msg.attach(part_html)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print("Email inviata con successo!")
    except Exception as e:
        print(f"Errore nell'invio dell'email: {e}")

if __name__ == "__main__":
    results = {}
    
    for city in CITIES:
        results[city] = fetch_events_via_rss(city)
            
    html_report = build_email_body(results)
    send_email("🗓️ Digest Eventi Tech & Business (RSS Engine)", html_report)
