from typing import List, Optional
from sqlmodel import Session, select
from database.model import TrackedGame, PriceSnapshot

# =====================================================================
#  SECTION : GESTION DU CATALOGUE (TrackedGame)
# =====================================================================
# --- CREATE (Ajout) ---
def create_tracked_game(session: Session, title: str, platform: str, slug: str) -> TrackedGame:
    """
    Ajoute un nouveau jeu au catalogue après vérification des doublons.
    Lève une ValueError si le couple jeu/plateforme existe déjà.
    """
    # 🚨 La validation est déplacée ici, à la source
    existing = session.exec(
        select(TrackedGame).where(
            TrackedGame.title == title, 
            TrackedGame.platform == platform
        )
    ).first()
    
    if existing:
        raise ValueError(f"Le jeu '{title}' est déjà suivi sur la plateforme '{platform.upper()}'.")

    game = TrackedGame(title=title, platform=platform, slug=slug)
    session.add(game)
    session.commit()
    session.refresh(game)
    return game

# --- READ (Lecture) ---
def get_active_games(session: Session) -> List[TrackedGame]:
    """
    Récupère la liste de tous les jeux dont le scan est actif.
    """
    return session.exec(select(TrackedGame).where(TrackedGame.is_active == True)).all()

def get_all_games(session: Session) -> List[TrackedGame]:
    """
    Récupère la liste de tous les jeux.
    """
    return session.exec(select(TrackedGame)).all()

def get_game_by_id(session: Session, game_id: int) -> Optional[TrackedGame]:
    """
    Récupère un jeu spécifique par son identifiant unique.
    """
    return session.get(TrackedGame, game_id)

# --- UPDATE (Modification) ---
def update_game_active_status(session: Session, game_id: int, is_active: bool) -> Optional[TrackedGame]:
    """
    Active ou désactive le scan quotidien pour un jeu (sans supprimer son historique).
    """
    game = session.get(TrackedGame, game_id)
    if game:
        game.is_active = is_active
        session.add(game)
        session.commit()
        session.refresh(game)
    return game

# --- DELETE (Suppression) ---
def delete_tracked_game(session: Session, game_id: int) -> bool:
    """
    Supprime un jeu du catalogue.
    INFO : Grâce à la contrainte ondelete="CASCADE" qu'on a configuré dans le modèle,
    cela va automatiquement supprimer tout l'historique des prix de ce jeu dans Postgres.
    """
    game = session.get(TrackedGame, game_id)
    if game:
        session.delete(game)
        session.commit()
        return True
    return False


# =====================================================================
#  SECTION : GESTION DE L'HISTORIQUE (PriceSnapshot)
# =====================================================================
# --- CREATE (Ajout) ---
def create_price_snapshot(session: Session, game_id: int, price: float, offers: dict) -> PriceSnapshot:
    """
    Insère un nouveau snapshot de prix dans l'historique d'un jeu.
    """
    snapshot = PriceSnapshot(game_id=game_id, min_price=price, offers_json=offers)
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return snapshot

# --- READ (Lecture de l'historique) ---
def get_game_price_history(session: Session, game_id: int) -> List[PriceSnapshot]:
    """
    Récupère tout l'historique des prix d'un jeu, du plus récent au plus ancien.
    """
    statement = (
        select(PriceSnapshot)
        .where(PriceSnapshot.game_id == game_id)
        .order_by(PriceSnapshot.scanned_at.desc())
    )
    return session.exec(statement).all()
