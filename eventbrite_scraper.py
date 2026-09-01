import os
import smtplib
import json
import cloudscraper
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# CONFIGURAZIONE CITTÀ E KEYWORDS
CITIES = ["milan", "rome", "brescia"]
KEYWORDS = ["startup", "business", "networking", "intelligenza-artificiale", "legaltech"]

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "topongo@gmail.com")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "topongo@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

def scrape_eventbrite_direct(city, keyword):
    """
    Usa cloudscraper per superare i blocchi Cloudflare ed estrarre gli eventi direttamente da Eventbrite.
    """
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    url = f"https://www.eventbrite.it/d/italy--{city}/{keyword}/"
    events = []
    
    try:
        res = scraper.get(url, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 1. Estrarre i dati JSON-LD
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
                                events.append({"title": str(name), "link": str(url_event).split('?')[0]})
                except Exception:
                    continue

            # 2. Fallback su tag <a> con URL /e/
            if not events:
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if '/e/' in href:
                        title = a.get_text(strip=True)
                        if len(title) > 5 and not title.lower().startswith('http') and not title.lower().startswith('iscriviti'):
                            if not href.startswith("http"):
                                href = f"https://www.eventbrite.it{href}"
                            events.append({"title": title, "link": href.split('?')[0]})
    except Exception as e:
        print(f"Errore scraping per {city} - {keyword}: {e}")
        
    return events

def build_email_body(all_results):
    """
    Costruisce l'email HTML.
    """
    html = """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
        <h2 style="color: #0d47a1;">📌 Digest Settimanale Eventi Tech, AI & Business</h2>
        <p>Ecco gli eventi selezionati direttamente su Eventbrite per <b>Milano, Roma e Brescia</b>:</p>
        <hr style="border: 0; border-top: 1px solid #ccc;">
    """
    
    has_events = False
    for city, city_data in all_results.items():
        html += f"<h3 style='color: #1565c0; margin-top: 20px;'>📍 {city.capitalize()}</h3>"
        city_has_events = False
        
        for kw, events in city_data.items():
            if events:
                city_has_events = True
                has_events = True
                html += f"<p style='margin-bottom: 5px;'><b>Categoria:</b> <i>{kw}</i></p><ul style='margin-top: 0;'>"
                for ev in events:
                    html += f"<li style='margin-bottom: 6px;'><a href='{ev['link']}' target='_blank' style='color: #1a73e8; text-decoration: none;'><b>{ev['title']}</b></a></li>"
                html += "</ul>"
        
        if not city_has_events:
            html += "<p style='color: #777;'><i>Nessun nuovo evento trovato per questa città.</i></p>"
    
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
        results[city] = {}
        for kw in KEYWORDS:
            raw_events = scrape_eventbrite_direct(city, kw)
            unique_events = []
            for ev in raw_events:
                if ev['link'] not in seen_links:
                    seen_links.add(ev['link'])
                    unique_events.append(ev)
            
            results[city][kw] = unique_events[:5]
            
    html_report = build_email_body(results)
    send_email("🗓️ Digest Eventi Tech & Business (Direct Scraping)", html_report)
