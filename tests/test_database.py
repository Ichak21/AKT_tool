import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy import event
from database.model import TrackedGame, PriceSnapshot
import database.crud as crud

@pytest.fixture(name="session")
def session_fixture():
    """
    Fixture pytest qui crée une base SQLite éphémère en mémoire
    et force l'activation des contraintes de clés étrangères (Cascade).
    """
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    
    # 2. LA MAGIE : On écoute la connexion et on force SQLite à activer les Foreign Keys
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # On génère les tables dedans
    SQLModel.metadata.create_all(engine)
    
    # On ouvre la session pour le test
    with Session(engine) as session:
        yield session


# =====================================================================
#  SÉRIE DE TESTS POUR LE CRUD
# =====================================================================

def test_create_and_get_tracked_game(session: Session):
    """Vérifie qu'on peut ajouter un jeu et le retrouver via son slug."""
    # 1. Action : Ajout via notre CRUD
    new_game = crud.create_tracked_game(
        session=session, 
        title="Elden Ring", 
        platform="pc", 
        slug="elden-ring"
    )
    
    # 2. Vérifications (Assertions)
    assert new_game.id is not None
    assert new_game.title == "Elden Ring"
    assert new_game.is_active is True
    
    # 3. Action : Recherche par slug
    retrieved_game = crud.get_game_by_id(session, game_id=new_game.id)
    assert retrieved_game is not None
    assert retrieved_game.id == new_game.id
    
def test_create_and_get_active_games(session: Session):
    """Vérifie qu'on peut ajouter plusieurs jeux et les récupérer tous."""
    # 1. On ajoute plusieurs jeux
    game_a = crud.create_tracked_game(session=session, title="Game A", platform="pc", slug="game-a")
    game_b = crud.create_tracked_game(session=session, title="Game B", platform="ps5", slug="game-b")
    game_c = crud.create_tracked_game(session=session, title="Game C", platform="xbox", slug="game-c")
    
    # on modifier 2 tag is_ative a false pour tester la fonction get_active_games
    crud.update_game_active_status(session=session, game_id=game_a.id, is_active=False)
    crud.update_game_active_status(session=session, game_id=game_b.id, is_active=False)    
    
    # 2. Action : Récupération de tous les jeux actifs
    games = crud.get_active_games(session=session)
    
    # 3. Vérifications
    assert len(games) == 1  # On doit en avoir 1 au total
    assert games[0].title == "Game C"

def test_create_and_get_all_games(session: Session):
    """Vérifie qu'on peut ajouter plusieurs jeux et les récupérer tous."""
    # 1. On ajoute plusieurs jeux
    game_a = crud.create_tracked_game(session=session, title="Game A", platform="pc", slug="game-a")
    game_b = crud.create_tracked_game(session=session, title="Game B", platform="ps5", slug="game-b")
    game_c = crud.create_tracked_game(session=session, title="Game C", platform="xbox", slug="game-c")
    
    # on modifier 2 tag is_ative a false pour tester la fonction get_active_games
    crud.update_game_active_status(session=session, game_id=game_a.id, is_active=False)
    crud.update_game_active_status(session=session, game_id=game_b.id, is_active=False)    
    
    # 2. Action : Récupération de tous les jeux actifs
    games = crud.get_all_games(session=session)
    
    # 3. Vérifications
    assert len(games) == 3  # On doit en avoir 3 au total
    
    status_map = {game.title: game.is_active for game in games} 
    assert status_map["Game A"] is False
    assert status_map["Game B"] is False
    assert status_map["Game C"] is True

def test_update_game_active_status(session: Session):
    """Vérifie qu'on peut passer un jeu en 'inactif' (pause du scan)."""
    # 1. On insère un jeu de test
    game = crud.create_tracked_game(session, "Fifa 25", "ps5", "fifa-25")
    
    # 2. Action : On le désactive
    updated_game = crud.update_game_active_status(session, game.id, is_active=False)
    
    # 3. Vérification
    assert updated_game is not None
    assert updated_game.is_active is False

def test_delete_tracked_game(session: Session):
    """Vérifie qu'un jeu est correctement supprimé."""
    # 1. On insère un jeu de test
    game = crud.create_tracked_game(session, "Test Game", "pc", "test-game")
    
    # 2. Action : Suppression
    success = crud.delete_tracked_game(session, game.id)
    
    # 3. Vérifications
    assert success is True
    assert crud.get_game_by_id(session, game.id) is None
    
def test_create_price_snapshot(session: Session):
    """Vérifie qu'on peut créer une capture de prix pour un jeu."""
    # 1. On insère un jeu de test
    game = crud.create_tracked_game(session, "Cyberpunk 2077", "pc", "cyberpunk-2077")
    
    # On simule un extrait de ton VRAI dictionnaire, converti en types primitifs
    real_mock_offers = {
        '0': {'price': 20.99, 'merchant': 'Humble Store', 'region': 'GLOBAL', 'edition': 'Standard'},
        '1': {'price': 22.74, 'merchant': 'GAMIVO', 'region': 'GLOBAL', 'edition': 'Standard'},
        '2': {'price': 22.86, 'merchant': 'Eneba', 'region': 'EUROPE', 'edition': 'Standard'}
    }
    
    # 2. Action : Création d'une capture de prix
    snapshot = crud.create_price_snapshot(session=session,
                                          game_id=game.id, # type: ignore
                                          price=20.99,
                                          offers=real_mock_offers
                                          )
    

    # 3. ASSERT (Vérifications de l'état de l'art)
    assert snapshot.id is not None
    assert snapshot.game_id == game.id
    assert snapshot.min_price == 20.99
    
    # On va vérifier à l'intérieur du JSON stocké en base :
    assert isinstance(snapshot.offers_json, dict)  # Est-ce bien un dictionnaire ?
    assert "0" in snapshot.offers_json              # Est-ce que la clé '0' existe ?
    
    # Est-ce que les données à l'intérieur de l'offre '0' sont intactes ?
    assert snapshot.offers_json["0"]["merchant"] == "Humble Store"
    assert snapshot.offers_json["0"]["price"] == 20.99
    
    # On vérifie une autre offre au hasard pour être sûr
    assert snapshot.offers_json["2"]["region"] == "EUROPE"

def test_get_game_price_history_ordering(session: Session):
    """Vérifie qu'on récupère l'historique d'un jeu trié du plus récent au plus ancien."""
    # 1. ARRANGE : On crée un jeu et deux captures de prix
    game = crud.create_tracked_game(session, "The Witcher 3", "pc", "the-witcher-3")
    
    # Premier snapshot (le plus ancien)
    crud.create_price_snapshot(session, game.id, price=15.00, offers={"0": {"price": 15.00}})
    # Deuxième snapshot (le plus récent)
    crud.create_price_snapshot(session, game.id, price=12.50, offers={"0": {"price": 12.50}})
    
    # 2. ACT : Récupération de l'historique
    history = crud.get_game_price_history(session, game.id)
    
    # 3. ASSERT
    assert len(history) == 2
    
    # Comme le tri est descendant (desc), le snapshot créé en DEUXIÈME (le moins cher)
    # doit obligatoirement apparaître en PREMIER dans notre liste.
    assert history[0].min_price == 12.50
    assert history[1].min_price == 15.00
    
def test_delete_game_cascade_snapshots(session: Session):
    """Vérifie que la suppression d'un jeu détruit automatiquement son historique de prix."""
    # 1. ARRANGE : On crée un jeu et on lui associe un snapshot
    game = crud.create_tracked_game(session, "Cyberpunk", "pc", "cyberpunk")
    crud.create_price_snapshot(session, game.id, price=29.99, offers={})
    
    # On vérifie rapidement que le snapshot est bien là avant de tester
    assert len(session.exec(select(PriceSnapshot)).all()) == 1
    
    # 2. ACT : On supprime le jeu via le CRUD
    success = crud.delete_tracked_game(session, game.id)
    assert success is True
    
    # 3. ASSERT : La magie du Cascade
    # Le jeu n'existe plus
    assert crud.get_game_by_id(session, game.id) is None
    
    # La table des snapshots doit être redevenue totalement vide !
    remaining_snapshots = session.exec(select(PriceSnapshot)).all()
    assert len(remaining_snapshots) == 0
    
def test_create_tracked_game_duplicate_raises_value_error(session: Session):
    """
    Vérifie que le CRUD lève bien une ValueError si on tente
    d'insérer deux fois le même couple (title, platform).
    """
    # 1. Premier enregistrement : Tout doit bien se passer
    game_1 = crud.create_tracked_game(
        session=session, 
        title="Cyberpunk 2077", 
        platform="pc", 
        slug="cyberpunk-2077"
    )
    assert game_1.id is not None

    # 2. Tentative d'insertion du doublon exact : Pytest doit intercepter la ValueError
    with pytest.raises(ValueError) as exc_info:
        crud.create_tracked_game(
            session=session, 
            title="Cyberpunk 2077", 
            platform="pc", 
            slug="cyberpunk-2077"
        )

    # 3. Vérification que le message d'erreur est bien celui configuré dans le CRUD
    assert "déjà suivi sur la plateforme 'PC'" in str(exc_info.value)