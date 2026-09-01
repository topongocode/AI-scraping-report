import os
import smtplib
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup

# CONFIGURAZIONE AMPLIATA
CITIES = ["Milano", "Roma", "Brescia"]
KEYWORDS = ["startup", "business", "networking", "intelligenza artificiale", "legaltech", "innovazione"]

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "topongo@gmail.com")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "topongo@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

def search_eventbrite_via_ddg(city, keyword):
    """
    Cerca eventi Eventbrite attivi per le prossime settimane tramite DuckDuckGo.
    """
    # Query avanzata per prendere sia i singoli eventi (/e/) che le raccolte di settembre
    query = f"site:eventbrite.it {keyword} {city} settembre 2026"
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.8"
    }
    
    events = []
    try:
        response = requests.post(url, data={"q": query}, headers=headers, timeout=12)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            results = soup.select(".result__a")
            
            for a in results:
                title = a.get_text(strip=True)
                raw_href = a.get("href", "")
                
                # Decodifica URL dal redirect di DuckDuckGo
                clean_link = raw_href
                if "uddg=" in raw_href:
                    parsed = urllib.parse.urlparse(raw_href)
                    qs = urllib.parse.parse_qs(parsed.query)
                    if "uddg" in qs:
                        clean_link = qs["uddg"][0]
                
                # Filtra link pertineneti a Eventbrite
                if "eventbrite.it" in clean_link and len(title) > 5:
                    clean_link = clean_link.split("?")[0]
                    # Escludi pagine generiche di login o assistenza
                    if not any(x in clean_link for x in ["/login", "/signin", "/help", "/about"]):
                        events.append({"title": title, "link": clean_link})
                    
    except Exception as e:
        print(f"Errore nella ricerca per {city} - {keyword}: {e}")
        
    return events

def build_email_body(all_results):
    """
    Costruisce l'email HTML con i risultati filtrati.
    """
    html = """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
        <h2 style="color: #0d47a1;">📌 Digest Settimanale Eventi Tech, Business & Networking</h2>
        <p>Ecco gli eventi trovati per <b>Milano, Roma e Brescia</b> (Settembre 2026):</p>
        <hr style="border: 0; border-top: 1px solid #ccc;">
    """
    
    has_events = False
    for city, city_data in all_results.items():
        html += f"<h3 style='color: #1565c0; margin-top: 20px;'>📍 {city}</h3>"
        city_has_events = False
        
        for kw, events in city_data.items():
            if events:
                city_has_events = True
                has_events = True
                html += f"<p style='margin-bottom: 5px;'><b>Macro-area:</b> <i>{kw}</i></p><ul style='margin-top: 0;'>"
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
        print("Email inviata con successo con il report degli eventi!")
    except Exception as e:
        print(f"Errore nell'invio dell'email: {e}")

if __name__ == "__main__":
    results = {}
    seen_links = set()
    
    for city in CITIES:
        results[city] = {}
        for kw in KEYWORDS:
            raw_events = search_eventbrite_via_ddg(city, kw)
            unique_events = []
            for ev in raw_events:
                if ev['link'] not in seen_links:
                    seen_links.add(ev['link'])
                    unique_events.append(ev)
            
            # Manteniamo fino a 7 risultati per keyword/città
            results[city][kw] = unique_events[:7]
            
    html_report = build_email_body(results)
    send_email("🗓️ Digest Eventi Tech & Business (Roma, Milano, Brescia)", html_report)
