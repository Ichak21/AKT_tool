import os
from dotenv import load_dotenv
from sqlmodel import create_engine, SQLModel

# 🚨 Charge les variables d'environnement du fichier .env
load_dotenv()

# Récupération sécurisée de l'URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "❌ Erreur : La variable DATABASE_URL n'est pas définie dans le fichier .env !\n"
        "Veuillez créer un fichier .env à la racine avec votre chaîne de connexion."
    )

engine = create_engine(DATABASE_URL, echo=False)

def init_db() -> None:
    """Crée les tables et les index si nécessaire au démarrage"""
    # Import local pour enregistrer les modèles dans les métadonnées de SQLModel
    from database.model import TrackedGame, PriceSnapshot
    
    SQLModel.metadata.create_all(engine)
