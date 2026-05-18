import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def get_stealth_chrome_options() -> Options:
    """
    Centralise la configuration de Chrome.
    Actuellement configurée au plus simple pour le MVP Windows.
    """
    options = Options()

    # 💡 ZONE D'ÉVOLUTION FUTURE :
    # Tu n'auras qu'à décommenter ces lignes lors du passage sur Docker/Linux
    # options.add_argument("--no-sandbox")
    # options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--remote-allow-origins=*")
    
    options.add_argument("--headless=new")
    options.add_argument("--remote-allow-origins=*")
    
    return options  

def fetch_page_html(url: str, timeout_seconds: int = 15) -> str:
    """
    Initialise le driver, charge la page cible et retourne le code HTML complet.
    Sécurisé contre les fuites de mémoire (Zombie Processes).
    """
    options = get_stealth_chrome_options()
    driver = webdriver.Chrome(options=options)
    
    # Configuration du timeout de chargement de la page
    driver.set_page_load_timeout(timeout_seconds)
    
    try:
        driver.get(url)
        # On récupère le code source une fois le JavaScript exécuté
        html_source = driver.page_source
        return html_source
        
    except Exception as e:
        print(f"❌ Erreur Selenium lors du chargement de l'URL : {url}\nDétails : {e}", file=sys.stderr)
        raise e
        
    finally:
        # 🚨 CRITIQUE : .quit() tue le processus et libère la RAM, contrairement à .close()
        driver.quit()