# ==========================================
# Étape 1 : Image de base légère
# ==========================================
FROM python:3.11-slim-bookworm

# Éviter les fichiers .pyc et forcer l'affichage direct des logs dans Docker
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Ajouter Poetry au PATH system
ENV PATH="$POETRY_HOME/bin:$PATH"

# Définir le dossier de travail dans le conteneur
WORKDIR /app

# ==========================================
# Étape 2 : Installation des dépendances système & Google Chrome
# ==========================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    ca-certificates \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://dl-colors.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y --no-install-recommends \
    google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ==========================================
# Étape 3 : Installation de Poetry & des dépendances Python
# ==========================================
# Installation de Poetry via le script officiel
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copie uniquement les fichiers de dépendances pour mettre en cache cette couche Docker
COPY pyproject.toml poetry.lock* ./

# Installation des dépendances de production uniquement (sans l'environnement virtuel)
RUN poetry install --only main --no-root

# ==========================================
# Étape 4 : Copie du code source
# ==========================================
COPY . .

# Par défaut, si aucune commande n'est passée, on lance l'application normalement
CMD ["python", "app.py"]