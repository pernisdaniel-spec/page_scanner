# --- NAČÍTANIE PREMENNÝCH Z GITHUB SECRETS ---
URL = os.environ["TARGET_URL"]
EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_PASS = os.environ["EMAIL_PASS"]
EMAIL_TO = os.environ["EMAIL_TO"]
STATE_FILE = "last_status.txt"

def clean_html(html_content):
    """Vyčistí HTML od dynamických prvkov (skripty, štýly), aby sme nemali falošné poplachy."""
    soup = BeautifulSoup(html_content, "html.parser")
    for script in soup(["script", "style", "noscript"]):
        script.extract()
    # Vráti čistý text bez nadbytočných medzier
    return soup.get_text(separator=' ', strip=True)

def send_email(news):
    msg = MIMEText(f"Na stránke {URL} nastala zmena.\n\nNový začiatok obsahu:\n{news[:500]}...")
    msg['Subject'] = "🔔 ZMENA NA STRÁNKE"
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_TO

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())
        server.quit()
        print("Email odoslaný.")
    except Exception as e:
        print(f"Chyba pri odosielaní emailu: {e}")

def main():
    # 1. Stiahnutie aktuálneho obsahu
    try:
        response = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'})
        current_content = clean_html(response.text)
    except Exception as e:
        print(f"Chyba pri sťahovaní stránky: {e}")
        return

    # 2. Načítanie starého obsahu zo súboru
    old_content = ""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            old_content = f.read()

    # 3. Porovnanie
    if current_content != old_content:
        print("Zmena detekovaná!")
        
        # Uložíme nový stav do súboru
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.write(current_content)
            
        # Ak to nie je prvý beh (kedy sa súbor len vytvára), pošli email
        if old_content != "":
            send_email(current_content)
    else:
        print("Žiadna zmena.")

if __name__ == "__main__":
    main()
