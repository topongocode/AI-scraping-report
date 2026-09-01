import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

CITIES = ["milan", "rome", "brescia"]
KEYWORDS = ["startup", "business", "networking", "intelligenza-artificiale", "legaltech"]

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "topongo@gmail.com")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "topongo@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

def scrape_with_browser(city, keyword):
    """
    Apre un browser reale Headless tramite Playwright per eseguire il JavaScript di Eventbrite.
    """
    events = []
    url = f"https://www.eventbrite.it/d/italy--{city}/{keyword}/"
    
    with sync_playwright() as p:
        # Avvia browser Chromium con User-Agent reale
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto(url, timeout=30000, wait_until="networkidle")
            # Attesa per consentire a React di caricare la lista eventi
            page.wait_for_timeout(4000)
            
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Cerca tutti i link che portano a singoli eventi (/e/)
            links = soup.find_all('a', href=True)
            for a in links:
                href = a['href']
                title = a.get_text(strip=True)
                
                if '/e/' in href and len(title) > 8:
                    clean_href = href.split('?')[0]
                    if not clean_href.startswith("http"):
                        clean_href = f"https://www.eventbrite.it{clean_href}"
                    
                    # Evita duplicati di navigazione
                    if not any(x in clean_href for x in ["/login", "/signin", "/checkout"]):
                        events.append({"title": title, "link": clean_href})
                        
        except Exception as e:
            print(f"Errore caricamento pagina per {city} - {keyword}: {e}")
        finally:
            browser.close()
            
    return events

def build_email_body(all_results):
    html = """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
        <h2 style="color: #0d47a1;">📌 Digest Settimanale Eventi Tech, AI & Business</h2>
        <p>Ecco gli eventi estratti in tempo reale da Eventbrite per <b>Milano, Roma e Brescia</b>:</p>
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
            html += "<p style='color: #777;'><i>Nessun evento trovato per questa città.</i></p>"
    
    if not has_events:
        html += "<p>Nessun evento trovato per i criteri impostati.</p>"
        
    html += """
        <hr style="border: 0; border-top: 1px solid #ccc; margin-top: 30px;">
        <p style='font-size: 0.85em; color: #777;'>Automazione Headless Playwright - Avv. Alessandro Ghiani</p>
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
    seen_links = set()
    
    for city in CITIES:
        results[city] = {}
        for kw in KEYWORDS:
            raw_events = scrape_with_browser(city, kw)
            unique_events = []
            for ev in raw_events:
                if ev['link'] not in seen_links:
                    seen_links.add(ev['link'])
                    unique_events.append(ev)
            
            results[city][kw] = unique_events[:4]
            
    html_report = build_email_body(results)
    send_email("🗓️ Digest Eventi Tech & Business (Playwright Engine)", html_report)
