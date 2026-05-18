# 🤖 Guide de Contexte pour Agent IA (LLM Instructions)

Ce fichier définit les contraintes strictes, les styles de code et les règles de conception que tout agent IA doit appliquer lorsqu'il modifie ou étend le projet **AKT_TOOL**.

## 🎯 Règles de Conception Strictes

1.  **Pas d'effets de bord dans `tool.py` :** Ce fichier doit contenir exclusivement des fonctions pures faciles à tester de manière déterministe. Ne jamais y importer `engine.py`, SQLModel ou effectuer des appels réseau / BDD.
2.  **Sécurité des Processus Chrome :** Toute modification de la gestion du cycle de vie de Selenium dans `engine.py` doit impérativement s'exécuter dans une structure garantissant l'appel à `driver.quit()`. L'utilisation de `driver.close()` seule est interdite.
3.  **Gestion des Erreurs et Résilience :** Le worker s'exécute en boucle sur plusieurs entités. Tout crash d'extraction sur un jeu spécifique doit être capturé par un `try/except` dans la boucle d'orchestration afin de consigner l'erreur dans `sys.stderr` et de permettre au script de passer immédiatement au jeu suivant sans interrompre le processus complet.
4.  **Contraintes de Persistance :** Ne jamais contourner le fichier `crud.py` pour insérer des données depuis l'interface ou les services. Les contraintes d'unicité et les messages d'exceptions métier doivent être maintenus au sein de la couche `database/crud.py`.

## 🧪 Charte des Tests Unitaires
* Chaque fonction de traitement de données ajoutée dans `tool.py` doit posséder son pendant de test unitaire paramétré dans `tests/test_tool.py`.
* Les tests de base de données dans `tests/test_database.py` s'exécutent dans une session isolée fournie par une fixture Pytest. Ne jamais écrire de tests unitaires écrivant en dur dans la base de données de production définie dans le fichier `.env`.

## 🎨 Style de Code
* Utilisation stricte du typage Python (`typing`, `Optional`, `List`).
* Formatage des chaînes de caractères via les *f-strings*.
* Documentation systématique des fonctions via des Docstrings clairs (Args, Returns).