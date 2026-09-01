import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup

# CONFIGURAZIONE
CITIES = ["rome", "milan", "brescia"]
KEYWORDS = ["startup", "intelligenza artificiale", "legaltech", "networking"]

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "topongo@gmail.com")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "topongo@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")  # App Password di Google

def scrape_eventbrite(city, keyword):
    """
    Effettua lo scraping di Eventbrite per la città e keyword specificata.
    """
    url = f"https://www.eventbrite.it/d/italy--{city}/{keyword.replace(' ', '-')}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "it-IT,it;q=0.9"
    }
    
    events = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return events
        
        soup = BeautifulSoup(res.text, 'html.parser')
        # Cerca le schede degli eventi nel markup
        articles = soup.find_all('article')
        
        for art in articles[:4]: # Prendi i primi 4 eventi più rilevanti
            link_tag = art.find('a', href=True)
            title_tag = art.find('h3') or art.find('h2')
            
            if link_tag and title_tag:
                title = title_tag.get_text(strip=True)
                link = link_tag['href']
                if not link.startswith("http"):
                    link = f"https://www.eventbrite.it{link}"
                events.append({"title": title, "link": link})
    except Exception as e:
        print(f"Errore scraping {city} - {keyword}: {e}")
    
    return events

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
