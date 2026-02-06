import os
import time
import smtplib
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- KONFIGURÁCIA ---
URL = os.environ["TARGET_URL"]
UCO = os.environ["MUNI_UCO"]
HESLO = os.environ["MUNI_HESLO"]
EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_PASS = os.environ["EMAIL_PASS"]
EMAIL_TO = os.environ["EMAIL_TO"]

STATE_FILE = "last_status.txt"

def send_email(text):
    msg = MIMEText(text)
    msg['Subject'] = "🔔 ZMENA V SEMINÁRI (IS MUNI)"
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
        print(f"Chyba emailu: {e}")

def get_page_content_with_login():
    # Nastavenie prehliadača (Headless = bez grafického okna)
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Spustenie prehliadača
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        print("Otváram stránku...")
        driver.get(URL)
        
        # Kontrola, či nás presmerovalo na prihlasovanie (id.muni.cz)
        if "id.muni.cz" in driver.current_url or "Přihlášení" in driver.title:
            print("Zistené prihlasovacie okno. Prihlasujem sa...")
            
            # Čakáme, kým sa načíta políčko pre UČO
            wait = WebDriverWait(driver, 10)
            uco_field = wait.until(EC.presence_of_element_located((By.NAME, "credentialId"))) # Názov poľa pre UCO
            
            # Vyplnenie údajov
            uco_field.clear()
            uco_field.send_keys(UCO)
            
            # Niektoré verzie loginu IS MUNI vyžadujú kliknúť "Ďalej" pred heslom, 
            # ale zvyčajne sú na jednej strane. Skúsime nájsť heslo.
            # Poznámka: IS MUNI má rôzne verzie loginu, toto je pre štandardný Unified Login
            
            password_field = driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(HESLO)
            
            # Odoslanie formulára (klik na tlačidlo Prihlásiť)
            login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_btn.click()
            
            # Čakanie na presmerovanie späť na IS
            print("Čakám na presmerovanie po prihlásení...")
            time.sleep(5) # Dáme mu čas na spracovanie loginu
            
        # Sme na cieľovej stránke?
        if "seminare/student" not in driver.current_url and "auth" not in driver.current_url:
            print(f"Varovanie: Sme na čudnej URL: {driver.current_url}")
        
        # Získame text stránky (len `body`, aby sme ignorovali hlavičky)
        body_text = driver.find_element(By.TAG_NAME, "body").text
        return body_text

    except Exception as e:
        print(f"Chyba prehliadača: {e}")
        # Pre debugovanie v Actions môžeš odkomentovať nasledujúci riadok:
        # print(driver.page_source) 
        return None
    finally:
        driver.quit()

def main():
    current_content = get_page_content_with_login()
    
    if not current_content:
        print("Nepodarilo sa stiahnuť obsah.")
        return

    # Načítanie starého obsahu
    old_content = ""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            old_content = f.read()

    # Porovnanie (jednoduchý hash alebo priamo text)
    # Odstránime časť textu, ktorá sa mení (napr. aktuálny čas na stránke), ak tam je.
    # Pre jednoduchosť porovnávame všetko.
    
    if current_content != old_content:
        # Kontrola, či to nie je len chyba prihlásenia
        if "Chyba přihlášení" in current_content:
            print("Chyba: Zlé heslo alebo UČO.")
            return

        print("ZMENA DETEKOVANÁ!")
        
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.write(current_content)
        
        # Ak súbor existoval (nie je to prvý beh), pošli email
        if old_content != "":
            send_email(f"Zmena na stránke seminára!\nURL: {URL}")
    else:
        print("Žiadna zmena.")

if __name__ == "__main__":
    main()
