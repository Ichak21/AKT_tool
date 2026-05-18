from pathlib import Path
import pytest
from bs4 import BeautifulSoup
from scraper.tool import slugify_name, parse_price, extract_data, build_url

# On récupère le chemin absolu du dossier des fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"

@pytest.fixture
def god_of_war_soup() -> BeautifulSoup:
    """Fixture qui charge le fichier HTML et renvoie un objet BeautifulSoup"""
    html_path = FIXTURES_DIR / "allkeyshop_god_of_war.html"
    
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    return BeautifulSoup(html_content, "html.parser")

def test_slugify_name():
    """Vérifie la transformation correcte des titres en slugs d'URL"""
    assert slugify_name("Elden Ring") == "elden-ring"
    assert slugify_name("Grand Theft Auto V ") == "grand-theft-auto-v"
    # Test avec des caractères spéciaux et des espaces multiples
    assert slugify_name("Cyberpunk 2077 & Phantom Liberty") == "cyberpunk-2077-phantom-liberty"
    assert slugify_name("  Portal 2  ") == "portal-2"


def test_parse_price():
    """Vérifie le nettoyage et la conversion des chaînes de prix en float"""
    assert parse_price("14.50€") == 14.50
    assert parse_price(" 14,50 € ") == 14.50
    assert parse_price("1 250,99 €") == 1250.99  # Gestion des milliers/espaces
    assert parse_price("") == 0.0
    assert parse_price("Gratuit") == 0.0


def test_extract_data_with_external_file(god_of_war_soup):
    """Le test utilise directement la fixture injectée en paramètre"""
    result = extract_data(god_of_war_soup)
    
# Le nom du jeu doit être propre
    assert result["game"] == "God of War"
    assert len(result["offers"]) > 0
    
    # L'offre index 0 DOIT être Instant Gaming (les comptes Kinguin/G2A ayant été jetés)
    offer_1 = result["offers"][0]
    assert offer_1["merchant"] == "Instant Gaming"
    assert offer_1["region"] == "GLOBAL"
    assert offer_1["edition"] == "Standard"
    assert offer_1["platform"] == "steam"
    assert offer_1["price"] == 14.79
    
    # L'offre index 1 devient Loaded (l'offre suivante sur ta capture)
    offer_2 = result["offers"][1]
    assert offer_2["merchant"] == "Loaded"
    assert offer_2["price"] == 15.09

def test_extract_data_missing_game_name():
    """Vérifie le comportement de secours si le HTML est corrompu ou invalide"""
    html_content = "<html><body><p>Pas de balises Allkeyshop ici</p></body></html>"
    soup = BeautifulSoup(html_content, "html.parser")
    result = extract_data(soup)
    
    assert result["game"] == "Unknown"
    assert result["offers"] == {}
    
@pytest.mark.parametrize(
    "html_payload, expected_game",
    [
        # Cas 1 : Pas de balise script du tout
        ("<html><body><span data-itemprop='name'>Elden Ring</span></body></html>", "Elden Ring"),
        
        # Cas 2 : Balise présente mais JSON complètement corrompu
        ("<html><body><span data-itemprop='name'>Elden Ring</span><script id='aks-offers-js-extra'>var gamePageTrans = { casse };</script></body></html>", "Elden Ring"),
        
        # Cas 3 : Jeu existant mais liste de prix vide []
        ("<html><body><span data-itemprop='name'>Elden Ring</span><script id='aks-offers-js-extra'>var gamePageTrans = {'prices': []};</script></body></html>", "Elden Ring"),
        
        # Cas 4 : Uniquement des offres de type 'ACCOUNT' (doivent toutes être filtrées)
        ("""<html><body><span data-itemprop='name'>Elden Ring</span><script id='aks-offers-js-extra'>
            var gamePageTrans = {
                'prices': [{ 'merchantName': 'G2A', 'account': true, 'region': '1' }],
                'regions': { '1': { 'region_name': 'ACCOUNT' } }
            };
         </script></body></html>""", "Elden Ring")
    ]
)

def test_extract_data_error_and_edge_cases(html_payload, expected_game):
    """Teste en série tous les scénarios de crashs et d'offres vides"""
    soup = BeautifulSoup(html_payload, "html.parser")
    result = extract_data(soup)
    
    # Peu importe l'erreur ou le piège, le scraper doit survivre, 
    # trouver le nom du jeu si dispo, et renvoyer un dictionnaire d'offres VIDE.
    assert result["game"] == expected_game
    assert result["offers"] == {}
    
def test_build_url(game_name="Cyberpunk 2077", platform="pc"):
    """Vérifie que l'URL est construite correctement à partir du nom et de la plateforme"""
    from scraper.tool import build_url
    url = build_url("Cyberpunk 2077", "pc")
    assert url == "https://www.allkeyshop.com/blog/buy-cyberpunk-2077-cd-key-compare-prices/"
    url = build_url("God of War", "ps5")
    assert url == "https://www.allkeyshop.com/blog/buy-god-of-war-ps5-compare-prices/"
    
def test_build_url_invalid():
    """Vérifie que la fonction lève bien une erreur pour une mauvaise plateforme"""
    with pytest.raises(ValueError):
        build_url("Elden Ring", "gameboy-color")