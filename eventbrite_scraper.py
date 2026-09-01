import os
import smtplib
import time
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup

# CONFIGURAZIONE CITTÀ E KEYWORDS UNIFICATE
CITIES = ["Milano", "Roma", "Brescia"]
KEYWORDS_OR = "startup OR business OR networking OR \"intelligenza artificiale\" OR legaltech"

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "topongo@gmail.com")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "topongo@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

def search_eventbrite_per_city(city):
    """
    Esegue un'unica ricerca combinata per città con pausa per evitare rate-limit.
    """
    query = f"site:eventbrite.it/e/ {city} ({KEYWORDS_OR})"
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    events = []
    try:
        # Pausa di rispetto per non far scattare l'anti-bot
        time.sleep(3)
        
        response = requests.post(url, data={"q": query}, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            results = soup.select(".result__a")
            
            for a in results:
                title = a.get_text(strip=True)
                raw_href = a.get("href", "")
                
                clean_link = raw_href
                if "uddg=" in raw_href:
                    parsed = urllib.parse.urlparse(raw_href)
                    qs = urllib.parse.parse_qs(parsed.query)
                    if "uddg" in qs:
                        clean_link = qs["uddg"][0]
                
                if "eventbrite.it/e/" in clean_link and len(title) > 5:
                    clean_link = clean_link.split("?")[0]
                    events.append({"title": title, "link": clean_link})
                    
    except Exception as e:
        print(f"Errore nella ricerca per {city}: {e}")
        
    return events

def build_email_body(all_results):
    """
    Costruisce l'email HTML con i risultati formattati.
    """
    html = """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
        <h2 style="color: #0d47a1;">📌 Digest Settimanale Eventi Tech, AI & Business</h2>
        <p>Ecco gli eventi selezionati su Eventbrite per <b>Milano, Roma e Brescia</b>:</p>
        <hr style="border: 0; border-top: 1px solid #ccc;">
    """
    
    has_events = False
    for city, events in all_results.items():
        html += f"<h3 style='color: #1565c0; margin-top: 20px;'>📍 {city}</h3>"
        
        if events:
            has_events = True
            html += "<ul style='margin-top: 5px;'>"
            for ev in events:
                html += f"<li style='margin-bottom: 8px;'><a href='{ev['link']}' target='_blank' style='color: #1a73e8; text-decoration: none;'><b>{ev['title']}</b></a></li>"
            html += "</ul>"
        else:
            html += "<p style='color: #777;'><i>Nessun evento rilevante intercettato per questa città.</i></p>"
    
    if not has_events:
        html += "<p>Nessun evento trovato per i criteri impostati.</p>"
        
    html += """
        <hr style="border: 0; border-top: 1px solid #ccc; margin-top: 30px;">
        <p style='font-size: 0.85em; color: #777;'>Automazione GitHub Actions - Avv. Alessandro Ghiani</p>
    </body>
    </html>
    """
    return html

def send_email(subject, html_content):
    """
    Invia l'email tramite server SMTP Gmail.
    """
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
    seen_links = set()
    
    for city in CITIES:
        raw_events = search_eventbrite_per_city(city)
        unique_events = []
        for ev in raw_events:
            if ev['link'] not in seen_links:
                seen_links.add(ev['link'])
                unique_events.append(ev)
        
        # Prendiamo fino a 8 eventi principali per città
        results[city] = unique_events[:8]
            
    html_report = build_email_body(results)
    send_email("🗓️ Digest Eventi Tech & Business (Milano, Roma, Brescia)", html_report)
