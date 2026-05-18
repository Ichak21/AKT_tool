# 🏗️ Architecture Technique — AKT_TOOL

Ce document détaille l'organisation structurelle du projet afin de guider le développement de fonctionnalités futures tout en respectant l'isolation des responsabilités.

## 🛰️ Schéma Conceptuel des Couches

Le projet est conçu selon les principes de la *Clean Architecture* simplifiée : le point d'entrée interagit avec les modules d'orchestration, qui consomment à leur tour des composants purement techniques et isolés.

```text
    +---------------------------------------+
    |               app.py                  | <-- Point d'entrée (CLI Routeur)
    +---------------------------------------+
         |                             |
         v                             v
+------------------+         +--------------------+
| database/crud.py |         | scraper/service.py | <-- Orchestrateurs de domaine
+------------------+         +--------------------+
         |                             |
         v                             v
+-------------------+       +-----------------------+
| database/model.py |       | scraper/engine.py     | <-- Infrastructure / IO
+-------------------+       | scraper/tool.py       | <-- Règles techniques pures
                            +-----------------------+
```

## 1. Couche de Données (`database/`)
* **`model.py` :** Définit les structures de tables avec SQLModel. Le modèle `TrackedGame` porte une contrainte SQL forte de type `UniqueConstraint("title", "platform")`. Le modèle `PriceSnapshot` est lié par une clé étrangère avec une clause `ondelete="CASCADE"`.
* **`crud.py` :** Centralise l'accès aux données. Toute création de jeu passe impérativement par une vérification d'existence en amont pour lever une exception métier explicite (`ValueError`) plutôt qu'un crash de base de données.

## 2. Couche d'Extraction (`scraper/`)
* **`engine.py` (Infrastructure) :** Contient la responsabilité unique d'ouvrir et fermer le navigateur Google Chrome. Il utilise l'argument de rendu moderne `--headless=new` pour assurer l'invisibilité et encapsule son cycle de vie dans un bloc `try/finally` pour garantir la fermeture du processus système (`driver.quit()`), prévenant toute fuite de mémoire (processus zombies).
* **`tool.py` (Logique pure) :** Composant déterministe (sans effets de bord, sans réseau). Il prend en entrée des chaînes de caractères brutes ou des arbres de parsing BeautifulSoup et retourne des structures nettoyées (dictionnaires). C'est le cœur intellectuel du scraping d'Allkeyshop.
* **`service.py` (Service Applicatif) :** Réalise la médiation. Il appelle `tool.py` pour préparer l'URL, transmet la requête à `engine.py` pour exécuter le JavaScript, puis repasse le HTML à `tool.py` pour en extraire le dictionnaire final.

## 3. Interface Utilisateur (`app.py`)
* Le script utilise un dictionnaire de routage pour exécuter les actions du menu. La logique métier calculant le prix minimum (`min_price`) et le décompte des offres valides s'effectue ici au moment de la réception des données avant la persistance.