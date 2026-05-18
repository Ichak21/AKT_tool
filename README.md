# 🎮 AKT_TOOL — Tracker de Prix de Clés de Jeux Vidéo

Worker automatisé et interface CLI de suivi des prix du marché gris et officiel de clés de jeux vidéo. Conçu spécifiquement pour une intégration légère et résiliente au sein d'un environnement Home Lab.

---

## 📊 Présentation Générale

**AKT_TOOL** cible l'extraction de données de prix depuis Allkeyshop en contournant les protections anti-bots de manière furtive, filtre les offres non désirées (comptes partagés), calcule le prix plancher et historise chaque point de donnée dans une base PostgreSQL centralisée.

### ✨ Fonctionnalités Clés
* **Extraction Furtive :** Injection et parsing direct du JSON applicatif interne d'Allkeyshop via Selenium (moteur invisible `headless=new`).
* **Filtrage Anti-Scam :** Nettoyage automatique des offres de type "ACCOUNT" ou associées à des régions invalides.
* **Architecture Robuste :** Gestion des contraintes d'unicité (couple jeu/plateforme unique) et suppression en cascade de l'historique lors du retrait d'un jeu.
* **Interface CLI Intuitive :** Console interactive structurée sous forme de tableaux textuels alignés avec routage dynamique.

---

## 📁 Structure du Projet

```text
AKT_TOOL/
├── database/            # Couche de persistance et modèles de données
│   ├── connection.py    # Initialisation sécurisée de l'engine SQLModel via .env
│   ├── crud.py          # Opérations atomiques et validation métier des doublons
│   └── model.py         # Schémas de tables (TrackedGame & PriceSnapshot)
├── scraper/             # Module d'extraction de données (Scraping)
│   ├── engine.py        # Gestion de l'instance Chrome Headless
│   ├── service.py       # Chef d'orchestre du flux d'extraction
│   └── tool.py          # Fonctions pures (slugify, build_url, extract_data)
├── tests/               # Suite de tests automatisés (Couverture 100% Green)
│   ├── fixtures/        # Mock HTML réels d'Allkeyshop pour les tests déterministes
│   ├── test_database.py # Validation des comportements CRUD, cascades et unicité
│   └── test_tool.py     # Validation unitaire des parseurs et cas d'erreurs
├── docs/                # Spécifications d'architecture pour humains & agents IA
├── app.py               # Point d'entrée de l'application (Console CLI)
├── .env.example         # Template des variables de configuration requises
└── pyproject.toml       # Dépendances du projet gérées par Poetry
```

---

## 🛠️ Installation et Configuration

### Prérequis
* Python 3.11 ou supérieur
* Poetry (Gestionnaire de dépendances)
* Google Chrome (installé sur la machine hôte)

### 1. Cloner le projet et installer les dépendances
```bash
poetry install
```

### 2. Configurer les variables d'environnement
Créez un fichier `.env` à la racine du projet sur le modèle du fichier `.env.example` :
```ini
DATABASE_URL=postgresql://<user>:<password>@<ip_proxmox>:5432/<db_name>
```

### 3. Exécuter la suite de tests
Vérifiez la parfaite intégrité de l'application avant de lancer un scan :
```bash
poetry run pytest
```

---

## 🚀 Utilisation

Lancez la console de pilotage interactive :
```bash
poetry run python app.py
```

L'interface vous permet d'interagir directement avec le catalogue :
1.  **Ajouter un jeu :** Enregistre une nouvelle cible de tracking (ex: *God of War*, *PC*).
2.  **Activer / Désactiver :** Suspend ou reprend le scan quotidien d'un jeu sans altérer son historique.
3.  **Supprimer un jeu :** Purge définitivement le jeu et toutes ses lignes de prix associées.
4.  **Lancer la mise à jour :** Exécute manuellement la boucle de scraping sur l'ensemble du catalogue actif.
5.  **Consulter l'historique :** Affiche un tableau détaillé des fluctuations de prix et du volume d'offres saines détectées.