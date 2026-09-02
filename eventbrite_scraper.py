import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# URL GENERALI "QUESTA SETTIMANA" SENZA FILTRI PER KEYWORD
TARGET_URLS = {
    "Milano": "https://www.eventbrite.it/d/italy--milan/events--this-week/",
    "Roma": "https://www.eventbrite.it/d/italy--rome/events--this-week/",
    "Brescia": "https://www.eventbrite.it/d/italy--brescia/events--this-week/"
}

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "topongo@gmail.com")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "topongo@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

def test_broad_scrape(city_name, url):
    """
    Carica la pagina generale degli eventi della settimana ed estrae tutti gli URL di tipo /e/
    """
    events = []
    print(f"\n--- AVVIO TEST PER {city_name.upper()} ---")
    print(f"URL: {url}")
    
    with sync_playwright() as p:
        # Configurazione browser per simulare un utente reale
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="it-IT"
        )
        page = context.new_page()
        
        try:
            response = page.goto(url, timeout=40000, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)  # Attesa per il rendering dei componenti JS
            
            page_title = page.title()
            print(f"LOG DEBUG - Titolo pagina caricata: '{page_title}'")
            print(f"LOG DEBUG - Codice di risposta HTTP: {response.status if response else 'N/A'}")
            
            # Verifica blocco Cloudflare
            if "pardon our interruption" in page_title.lower() or "just a moment" in page_title.lower():
                print("⚠️ RILEVATO BLOCCO ANTI-BOT (Cloudflare) sull'IP di GitHub Actions!")
                return events

            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Estrazione di tutti i link che portano ad eventi (/e/)
            links = soup.find_all('a', href=True)
            for a in links:
                href = a['href']
                title = a.get_text(strip=True)
                
                if '/e/' in href and len(title) > 3:
                    clean_href = href.split('?')[0]
                    if not clean_href.startswith("http"):
                        clean_href = f"https://www.eventbrite.it{clean_href}"
                    
                    if not any(x in clean_href for x in ["/login", "/signin", "/checkout"]):
                        events.append({"title": title, "link": clean_href})
                        
            print(f"LOG DEBUG - Trovati {len(events)} elementi grezzi per {city_name}.")

        except Exception as e:
            print(f"Errore durante la navigazione su {city_name}: {e}")
        finally:
            browser.close()
            
    return events

def build_email_body(all_results):
    html = """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.5;">
        <h2 style="color: #0d47a1;">🧪 TEST: Tutti gli Eventi della Settimana</h2>
        <p>Risultati grezzi per <b>Milano, Roma e Brescia</b> (senza filtri di categoria):</p>
        <hr style="border: 0; border-top: 1px solid #ccc;">
    """
    
    has_events = False
    for city, events in all_results.items():
        html += f"<h3 style='color: #1565c0; margin-top: 20px;'>📍 {city} ({len(events)} trovati)</h3>"
        
        if events:
            has_events = True
            html += "<ul style='margin-top: 5px;'>"
            for ev in events:
                html += f"<li style='margin-bottom: 6px;'><a href='{ev['link']}' target='_blank' style='color: #1a73e8; text-decoration: none;'><b>{ev['title']}</b></a></li>"
            html += "</ul>"
        else:
            html += "<p style='color: #d32f2f;'><i>Nessun evento estratto (pagina vuota o blocco anti-bot).</i></p>"
    
    if not has_events:
        html += "<p><b>Nessun evento trovato in totale. Verificare i log di GitHub Actions per dettagli sul blocco IP.</b></p>"
        
    html += """
        <hr style="border: 0; border-top: 1px solid #ccc; margin-top: 30px;">
        <p style='font-size: 0.85em; color: #777;'>Test di connessione diretta Eventbrite - Avv. Alessandro Ghiani</p>
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
        print("Email di test inviata con successo!")
    except Exception as e:
        print(f"Errore nell'invio dell'email: {e}")

if __name__ == "__main__":
    results = {}
    
    for city, url in TARGET_URLS.items():
        raw_events = test_broad_scrape(city, url)
        
        # Deduplicazione dei link
        unique_events = []
        seen_links = set()
        for ev in raw_events:
            if ev['link'] not in seen_links:
                seen_links.add(ev['link'])
                unique_events.append(ev)
                
        # Prendiamo fino a 15 eventi per città per il test
        results[city] = unique_events[:15]
            
    html_report = build_email_body(results)
    send_email("🧪 TEST Eventbrite: Eventi Indistinti della Settimana", html_report)
