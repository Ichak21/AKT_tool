from bs4 import BeautifulSoup
from scraper.engine import fetch_page_html
from scraper.tool import build_url, extract_data

def scrape_game_prices(game_name: str, platform: str = "pc") -> dict:
    """Orchestre le scraping d'un jeu pour une plateforme donnée."""
    
    # 1. Obtenir l'URL isolée de manière safe
    url = build_url(game_name, platform)
    
    print(f"🕵️‍♂️ Lancement du scan furtif : URL générée avec succès.")
    
    # 2. Récupération du HTML
    html_source = fetch_page_html(url)
    soup = BeautifulSoup(html_source, "html.parser")
    
    # 3. Extraction
    result = extract_data(soup)
    
    print(f"✅ {len(result['offers'])} offres valides pour '{result['game']}'.")
    
    return result