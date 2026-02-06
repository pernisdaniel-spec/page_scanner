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
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Dôležité: Nastavíme veľkosť okna, aby sa prvky vykreslili
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        print("Otváram stránku...")
        driver.get(URL)
        
        # Logika prihlásenia
        if "id.muni.cz" in driver.current_url or "Přihlášení" in driver.title:
            print("Prihlasujem sa...")
            wait = WebDriverWait(driver, 10)
            uco_field = wait.until(EC.presence_of_element_located((By.NAME, "credentialId")))
            uco_field.clear()
            uco_field.send_keys(UCO)
            
            password_field = driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(HESLO)
            
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            
            # Dlhšie čakanie po prihlásení
            time.sleep(8) 
            
        print(f"Aktuálna URL: {driver.current_url}")
        print(f"Titulok stránky: {driver.title}")

        # --- DIAGNOSTIKA: Urobíme screenshot ---
        driver.save_screenshot("debug_screenshot.png")
        print("Screenshot uložený ako 'debug_screenshot.png'")
        
        # Skúsime nájsť hlavný obsah. Ak je body prázdne, skúsime page_source
        body_element = driver.find_element(By.TAG_NAME, "body")
        body_text = body_element.text
        
        if not body_text.strip():
            print("VAROVANIE: Body je prázdne! Ukladám surové HTML.")
            return driver.page_source # Vráti HTML kód namiesto čistého textu
            
        return body_text

    except Exception as e:
        print(f"Chyba: {e}")
        driver.save_screenshot("error_screenshot.png")
        return None
    finally:
        driver.quit()

def main():
    current_content = get_page_content_with_login()
    
    if not current_content:
        print("Nepodarilo sa stiahnuť obsah (funkcia vrátila None).")
        return

    print(f"Stiahnutý obsah má dĺžku: {len(current_content)} znakov.")

    # Uloženie do súboru (bez ohľadu na zmenu, aby sme videli, čo sťahuje)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(current_content)
            
    # Tu by nasledovalo porovnanie a email (zatial vynechane pre debugging)
    # ... (kód pre porovnanie ostáva rovnaký ako predtým)

if __name__ == "__main__":
    main()
