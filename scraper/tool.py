import re
import json
from bs4 import BeautifulSoup

# À ajouter dans scraper/tool.py

PLATFORM_URL_MAPPING = {
    "pc": "cd-key",
    "ps5": "ps5",
    "ps4": "ps4",
    "xbox series x": "xbox-series",
    "xbox one": "xbox-one",
    "nintendo switch": "nintendo-switch",
}

def build_url(game_name: str, platform: str) -> str:
    """
    Génère l'URL Allkeyshop exacte pour un jeu et une plateforme donnés.
    Lève une ValueError si la plateforme n'est pas supportée.
    """
    target_platform = platform.lower().strip()
    
    if target_platform not in PLATFORM_URL_MAPPING:
        supported = ", ".join(PLATFORM_URL_MAPPING.keys())
        raise ValueError(
            f"❌ Plateforme '{platform}' non supportée. Options valides : [{supported}]"
        )
        
    game_slug = slugify_name(game_name)
    platform_slug = PLATFORM_URL_MAPPING[target_platform]
    
    return f"https://www.allkeyshop.com/blog/buy-{game_slug}-{platform_slug}-compare-prices/"

def slugify_name(name: str) -> str:
    """Transforme le nom d'un jeu en slug propre pour l'URL d'Allkeyshop."""
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    return slug


def parse_price(price_val) -> float:
    """Garantit que le prix est un float propre."""
    if not price_val:
        return 0.0
    if isinstance(price_val, (int, float)):
        return float(price_val)
    try:
        clean_str = str(price_val).replace(",", ".").strip()
        clean_str = "".join(c for c in clean_str if c.isdigit() or c == '.')
        return float(clean_str) if clean_str else 0.0
    except ValueError:
        return 0.0


def extract_data(soup: BeautifulSoup) -> dict:
    """
    Extrait les données en ciblant le payload JSON.
    Filtre et élimine TOUTES les offres de type 'ACCOUNT' pour ne garder que les clés.
    """
    game_bs = soup.find("span", {"data-itemprop": "name"})
    game_name = game_bs.text.strip() if game_bs else "Unknown"

    offers = {}

    script_tags = soup.find_all("script", {"type": "text/javascript", "id": "aks-offers-js-extra"})
    
    if script_tags:
        script_content = script_tags[0].string
        try:
            json_str = script_content.split('var gamePageTrans = ')[1].split(';')[0].strip()
            data = json.loads(json_str)
            
            if "prices" in data:
                regions_map = data.get("regions", {})
                editions_map = data.get("editions", {})
                
                valid_index = 0
                for item in data["prices"]:
                    # 1. Extraction de la région pour vérification
                    region_id = str(item.get("region", ""))
                    region_name = regions_map.get(region_id, {}).get("region_name", "Unknown") if isinstance(regions_map.get(region_id), dict) else "Unknown"

                    # 🚨 LA BARRIÈRE ANTI-COMPTE : On vire les offres "ACCOUNT"
                    if item.get("account") is True or region_name.upper() == "ACCOUNT":
                        continue

                    # 2. Extraction des autres métadonnées pour les offres valides
                    edition_id = str(item.get("edition", ""))
                    edition_name = editions_map.get(edition_id, {}).get("name", "Unknown") if isinstance(editions_map.get(edition_id), dict) else "Unknown"

                    offers[valid_index] = {
                        "merchant": item.get("merchantName", "Unknown"),
                        "region": region_name,
                        "edition": edition_name,
                        "platform": item.get("activationPlatform", "Unknown"),
                        "price": parse_price(item.get("price", 0.0))
                    }
                    valid_index += 1
                    
        except (IndexError, json.JSONDecodeError, KeyError) as e:
            print(f"Erreur d'extraction JSON : {e}")

    return {
        "game": game_name,
        "offers": offers
    }