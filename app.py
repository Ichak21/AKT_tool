import sys
from sqlmodel import Session
from database.connection import engine, init_db
from database.crud import (
    get_all_games,
    get_active_games,
    create_tracked_game,
    update_game_active_status,
    delete_tracked_game,
    create_price_snapshot,
    get_game_price_history
)
from scraper.service import scrape_game_prices
from scraper.tool import slugify_name

# =====================================================================
#  FONCTIONS UTILITAIRES DE L'INTERFACE (HELPERS)
# =====================================================================

def _helper_list_and_select_game(session: Session, context_title: str) -> int:
    """
    Affiche la liste des jeux et demande à l'utilisateur d'en sélectionner un.
    Retourne l'ID du jeu ou -1 si le catalogue est vide ou le choix invalide.
    """
    games = get_all_games(session)
    if not games:
        print("📭 Le catalogue est vide pour le moment.")
        return -1

    print(f"\n--- 📋 SELECTIONNER UN JEU ({context_title}) ---")
    for g in games:
        status = "🟢 Actif" if g.is_active else "🔴 Inactif"
        print(f"  [{g.id}] {g.title} ({g.platform.upper()}) - {status}")

    choice = input("\nEntrez l'ID du jeu ciblé : ").strip()
    try:
        game_id = int(choice)
        if any(g.id == game_id for g in games):
            return game_id
        print("⚠️ ID de jeu introuvable dans la liste.")
        return -1
    except ValueError:
        print("⚠️ Veuillez entrer un ID numérique valide.")
        return -1


# =====================================================================
#  SOUS-CONTROLEURS DU MENU (ACTIONS ISOLÉES)
# =====================================================================

def action_add_game():
    """Option 1 : Ajouter un jeu au catalogue"""
    print("\n--- 🆕 AJOUTER UN NOUVEAU JEU ---")
    title = input("Entrez le titre exact du jeu (ex: God of War) : ").strip()
    if not title:
        print("⚠️ Le titre ne peut pas être vide.")
        return

    print("Disponibles : pc, ps5, ps4, xbox series x, xbox one, nintendo switch")
    platform = input("Entrez la plateforme (default: pc) : ").strip().lower() or "pc"
    slug = slugify_name(title)

    with Session(engine) as session:
        try:
            game = create_tracked_game(session, title=title, platform=platform, slug=slug)
            print(f"✅ Succès ! '{game.title}' ({game.platform.upper()}) est maintenant suivi.")
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout en BDD : {e}")


def action_toggle_game_status():
    """Option 2 : Activer/Désactiver le scan d'un jeu"""
    with Session(engine) as session:
        game_id = _helper_list_and_select_game(session, "CHANGER LE STATUT DE SCAN")
        if game_id == -1:
            return

        game = session.get(type(get_all_games(session)[0]), game_id) # Astuce pour type statique, ou get_game_by_id si dispo
        new_status = not game.is_active
        
        update_game_active_status(session, game_id, is_active=new_status)
        status_str = "ACTIVÉ 🟢" if new_status else "DÉSACTIVÉ 🔴"
        print(f"✅ Le scan pour '{game.title}' est désormais {status_str}.")


def action_delete_game():
    """Option 3 : Supprimer définitivement un jeu et son historique"""
    with Session(engine) as session:
        game_id = _helper_list_and_select_game(session, "SUPPRESSION DÉFINITIVE")
        if game_id == -1:
            return

        confirm = input("⚠️ Êtes-vous sûr de vouloir supprimer ce jeu ET TOUT son historique ? (oui/non) : ").strip().lower()
        if confirm == "oui":
            if delete_tracked_game(session, game_id):
                print("🗑️ Jeu et historique supprimés avec succès (Cascade Postgres).")
            else:
                print("❌ Erreur lors de la suppression.")
        else:
            print("❌ Suppression annulée.")


def action_run_scan_loop():
    """Option 4 : Exécuter la boucle de scan nocturne"""
    print("\n--- 🔄 LANCEMENT DU SCAN COMPLET DES PRIX ---")
    
    with Session(engine) as session:
        active_games = get_active_games(session)
        if not active_games:
            print("📭 Aucun jeu n'est actif pour le scan. Modifiez le statut d'un jeu d'abord.")
            return

        print(f"📋 {len(active_games)} jeu(x) actif(s) à scanner.")
        for game in active_games:
            try:
                result = scrape_game_prices(game.title, game.platform)
                offers = result.get("offers", {})

                if offers:
                    valid_prices = [o["price"] for o in offers.values() if o["price"] > 0]
                    min_price = min(valid_prices) if valid_prices else 0.0
                else:
                    min_price = 0.0

                create_price_snapshot(session, game_id=game.id, price=min_price, offers=offers)
                print(f"💾 Snapshot enregistré pour '{game.title}' | Prix Min: {min_price}€")

            except Exception as e:
                print(f"❌ Échec du scan pour '{game.title}' : {e}", file=sys.stderr)
                continue
    print("🏁 Fin du scan complet.")


def action_view_history():
    """Option 5 : Consulter l'historique d'un jeu"""
    with Session(engine) as session:
        game_id = _helper_list_and_select_game(session, "VOIR L'HISTORIQUE")
        if game_id == -1:
            return

        game = session.get(get_all_games(session)[0].__class__, game_id)
        history = get_game_price_history(session, game_id)
        
        print(f"\n📈 Historique pour '{game.title}' ({game.platform.upper()}) :")
        print("-" * 50)
        print(f"{'Date du scan':<25} | {'Prix Minimum':<15}")
        print("-" * 50)
        
        if not history:
            print("  Aucun prix enregistré pour le moment.")
        else:
            for snapshot in history:
                date_str = snapshot.scanned_at.strftime("%Y-%m-%d %H:%M:%S")
                print(f"{date_str:<25} | {snapshot.min_price:<12} €")
        print("-" * 50)


# =====================================================================
#  POINT D'ENTRÉE ET ROUTEUR PRINCIPAL (MAIN)
# =====================================================================

def main():
    # Initialisation de la BDD Postgres Proxmox
    try:
        init_db()
    except Exception as e:
        print(f"❌ Impossible d'initialiser la base Postgres :\n{e}", file=sys.stderr)
        sys.exit(1)

    # Dictionnaire de routage pour lier les choix aux fonctions (Clean Pattern)
    menu_actions = {
        "1": action_add_game,
        "2": action_toggle_game_status,
        "3": action_delete_game,
        "4": action_run_scan_loop,
        "5": action_view_history,
    }

    while True:
        print("\n=====================================")
        print("🎮 CONSOLE DE PILOTAGE - ATK TOOL v1")
        print("=====================================")
        print("1. Ajouter un jeu au catalogue")
        print("2. Activer / Désactiver le scan d'un jeu")
        print("3. Supprimer un jeu du catalogue (et son historique)")
        print("4. Lancer la boucle de mise à jour (Scan Allkeyshop)")
        print("5. Consulter l'historique des prix d'un jeu")
        print("6. Quitter")
        print("=====================================")
        
        choice = input("Votre choix (1-6) : ").strip()
        
        if choice == "6":
            print("👋 Fermeture de l'application.")
            break
        elif choice in menu_actions:
            # Exécution propre de l'action choisie
            menu_actions[choice]()
        else:
            print("⚠️ Choix invalide. Entrez un chiffre entre 1 et 6.")


if __name__ == "__main__":
    main()