import os
import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup

# CONFIGURAZIONE
CITIES = ["rome", "milan", "brescia"]
KEYWORDS = ["startup", "intelligenza artificiale", "legaltech", "networking"]

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "topongo@gmail.com")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "topongo@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

def scrape_eventbrite(city, keyword):
    """
    Scraspa Eventbrite per città e keyword estraendo JSON-LD e link trasparenti.
    """
    url = f"https://www.eventbrite.it/d/italy--{city}/{keyword.replace(' ', '-')}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.8"
    }
    
    events = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return events
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. Estrarre i dati strutturati JSON-LD
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
                items = []
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    if data.get('@type') == 'ItemList':
                        items = [elem.get('item', elem) for elem in data.get('itemListElement', [])]
                    else:
                        items = [data]
                
                for item in items:
                    if isinstance(item, dict):
                        name = item.get('name') or item.get('title')
                        url_event = item.get('url')
                        if name and url_event and '/e/' in str(url_event):
                            events.append({"title": str(name), "link": str(url_event)})
            except Exception:
                continue

        # 2. Fallback: ricerca diretta sui link <a> con pattern '/e/'
        if not events:
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/e/' in href:
                    title = a.get_text(strip=True)
                    if len(title) > 5 and not title.lower().startswith('http') and not title.lower().startswith('iscriviti'):
                        if not href.startswith("http"):
                            href = f"https://www.eventbrite.it{href}"
                        events.append({"title": title, "link": href})

    except Exception as e:
        print(f"Errore scraping {city} - {keyword}: {e}")
    
    # Deduplicazione dei risultati
    unique_events = []
    links_seen = set()
    for ev in events:
        clean_link = ev['link'].split('?')[0]
        if clean_link not in links_seen:
            links_seen.add(clean_link)
            unique_events.append(ev)
            
    return unique_events[:4]

def build_email_body(all_results):
    """
    Costruisce il corpo dell'email in formato HTML.
    """
    html = """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>📌 Digest Settimanale Eventi Tech & Startup</h2>
        <p>Ecco gli eventi selezionati su Roma, Milano e Brescia per questa settimana:</p>
        <hr>
    """
    
    has_events = False
    for city, city_data in all_results.items():
        html += f"<h3 style='color: #1a73e8;'>📍 {city.capitalize()}</h3>"
        city_has_events = False
        
        for kw, events in city_data.items():
            if events:
                city_has_events = True
                has_events = True
                html += f"<h4>Tag: <i>{kw}</i></h4><ul>"
                for ev in events:
                    html += f"<li><a href='{ev['link']}' target='_blank'><b>{ev['title']}</b></a></li>"
                html += "</ul>"
        
        if not city_has_events:
            html += "<p style='color: #777;'><i>Nessun nuovo evento rilevante trovato.</i></p>"
    
    if not has_events:
        html += "<p>Nessun evento trovato per i criteri impostati.</p>"
        
    html += """
        <hr>
        <p style='font-size: 0.8em; color: #888;'>Automazione creata per Alessandro Ghiani - LegalTech & Startup</p>
    </body>
    </html>
    """
    return html

def send_email(subject, html_content):
    """
    Invia l'email tramite server SMTP di Gmail.
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
    for city in CITIES:
        results[city] = {}
        for kw in KEYWORDS:
            results[city][kw] = scrape_eventbrite(city, kw)
            
    html_report = build_email_body(results)
    send_email("🗓️ Eventi Startup & Tech Settimanali (Roma, Milano, Brescia)", html_report)
