import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def get_stealth_chrome_options() -> Options:
    """
    Configure les options de Chrome pour maximiser la furtivité 
    et éviter la détection par les systèmes anti-bots (Cloudflare Turnstile).
    """
    options = Options()
    
    # État de l'art : Utilisation du nouveau moteur headless (moins détectable)
    options.add_argument("--headless=new")
    
    # Configuration d'un User-Agent réaliste et moderne (Évite l'UA 'HeadlessChrome')
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    
    # Contournement des flags d'automatisation standard
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Optimisations pour l'environnement Linux / Docker LXC Proxmox cible
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")  # Évite le repli d'éléments responsives
    
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