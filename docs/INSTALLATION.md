# 📦 Guide d'Installation SmartReport

## Table des Matières

- [Prérequis](#prérequis)
- [Installation Windows](#installation-windows)
- [Installation Linux](#installation-linux)
- [Installation macOS](#installation-macos)
- [Configuration](#configuration)
- [Vérification](#vérification)
- [Dépannage](#dépannage)
- [Mise à Jour](#mise-à-jour)
- [Désinstallation](#désinstallation)

---

## Prérequis

### Requis

✅ **Python 3.8+**
- Télécharger : https://www.python.org/downloads/
- Vérifier : `python --version` ou `python3 --version`

✅ **Navigateur moderne**
- Chrome 90+ (recommandé pour dictée vocale)
- Edge 90+
- Firefox 88+
- Safari 14+

✅ **Connexion Internet**
- Pour télécharger les dépendances (installation)
- Pour les appels aux providers IA cloud (Mistral, OpenAI, etc.)
- **Ollama** fonctionne 100% offline après installation

### Optionnel

⚙️ **Git** (pour cloner le dépôt)
- Windows : https://git-scm.com/download/win
- Linux : `sudo apt install git` (Debian/Ubuntu) ou `sudo yum install git` (RHEL/CentOS)
- macOS : Préinstallé ou `brew install git`

🔑 **Clé API** d'un provider IA
- **Mistral AI** (gratuit) : https://console.mistral.ai/ ⭐ Recommandé
- **OpenAI** (payant) : https://platform.openai.com/
- **Ollama** (local, gratuit) : https://ollama.ai/

---

## Installation Windows

### Méthode Automatique (Recommandée)

#### 1. Télécharger SmartReport

**Option A : Via Git**
```powershell
git clone https://github.com/enovacom/SmartReport.git
cd SmartReport
```

**Option B : Sans Git (téléchargement ZIP)**
1. Télécharger : https://github.com/enovacom/SmartReport/archive/main.zip
2. Extraire dans `C:\Users\<votre_user>\Desktop\SmartReport`
3. Ouvrir PowerShell dans ce dossier

#### 2. Lancer l'Installation

```powershell
.\start.bat
```

Le script effectue automatiquement :
- ✅ Vérification de Python
- ✅ Création de l'environnement virtuel (`venv/`)
- ✅ Installation des dépendances (`requirements.txt`)
- ✅ Création du fichier `.env` depuis `.env.example`
- ✅ Lancement du serveur Flask
- ✅ Ouverture du navigateur sur `http://127.0.0.1:5173`

**Sortie attendue :**
```
========================================
   ENOVACOM SmartReport - Demarrage
========================================

Creation de l'environnement virtuel...
Activation de l'environnement virtuel...
Mise a jour de pip...
Installation/Verification des dependances...
Toutes les dependances sont installees !

ATTENTION: Editez le fichier .env pour configurer vos cles API

========================================
    Demarrage du serveur...
========================================

Interface disponible sur: http://127.0.0.1:5173
Appuyez sur Ctrl+C pour arreter le serveur
```

#### 3. Configurer l'API IA (Première Utilisation)

Éditer le fichier `.env` avec un éditeur de texte (Notepad, VS Code, etc.) :

```env
# Mistral AI (Recommandé - RGPD France)
ACTIVE_PROVIDER=mistral
MISTRAL_BASE_URL=https://api.mistral.ai
MISTRAL_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Remplacer par votre clé
```

**Obtenir une clé Mistral (gratuit) :**
1. Créer un compte : https://console.mistral.ai/
2. API Keys → Create new key
3. Copier la clé `sk-...`
4. Coller dans `.env`

#### 4. Redémarrer l'Application

```powershell
.\start.bat
```

---

### Méthode Manuelle (Windows)

#### 1. Installer Python

1. Télécharger Python 3.11 : https://www.python.org/downloads/
2. Lancer l'installateur
3. ⚠️ **COCHER** "Add Python to PATH"
4. Cliquer "Install Now"

#### 2. Vérifier l'Installation

```powershell
python --version
# Python 3.11.7

pip --version
# pip 23.3.1
```

#### 3. Télécharger SmartReport

```powershell
git clone https://github.com/enovacom/SmartReport.git
cd SmartReport
```

#### 4. Créer l'Environnement Virtuel

```powershell
python -m venv venv
```

#### 5. Activer l'Environnement Virtuel

```powershell
venv\Scripts\activate
# (venv) PS C:\...\SmartReport>
```

#### 6. Installer les Dépendances

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

**Liste des dépendances installées :**
```
Flask==3.0.3
python-dotenv==1.0.1
requests==2.32.3
waitress==3.0.0
reportlab==4.4.3
markdown==3.5.2
svglib==1.6.0
beautifulsoup4==4.12.3
lxml==5.3.0
python-docx==1.1.2
```

#### 7. Configurer l'Environnement

```powershell
copy .env.example .env
notepad .env
```

Éditer les variables :
```env
ACTIVE_PROVIDER=mistral
MISTRAL_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### 8. Lancer l'Application

```powershell
python app.py
```

**Sortie attendue :**
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5173
Press CTRL+C to quit
```

#### 9. Ouvrir le Navigateur

Aller sur http://127.0.0.1:5173

---

## Installation Linux

### Ubuntu / Debian

#### 1. Installer Python et Git

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git -y
```

#### 2. Cloner le Dépôt

```bash
git clone https://github.com/enovacom/SmartReport.git
cd SmartReport
```

#### 3. Créer l'Environnement Virtuel

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 4. Installer les Dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. Configurer

```bash
cp .env.example .env
nano .env  # ou vim .env
```

Éditer :
```env
ACTIVE_PROVIDER=mistral
MISTRAL_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### 6. Lancer

```bash
python app.py
```

#### 7. Accéder

Ouvrir http://127.0.0.1:5173 dans le navigateur

---

### RHEL / CentOS / Fedora

#### 1. Installer Python et Git

```bash
# RHEL/CentOS 7/8
sudo yum install python3 python3-pip git -y

# Fedora
sudo dnf install python3 python3-pip git -y
```

#### 2-7. Identiques à Ubuntu

---

### Script de Démarrage Automatique (Linux)

Créer un service systemd :

```bash
sudo nano /etc/systemd/system/smartreport.service
```

Contenu :
```ini
[Unit]
Description=SmartReport Service
After=network.target

[Service]
Type=simple
User=<votre_user>
WorkingDirectory=/home/<votre_user>/SmartReport
Environment="PATH=/home/<votre_user>/SmartReport/venv/bin"
ExecStart=/home/<votre_user>/SmartReport/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Activer :
```bash
sudo systemctl daemon-reload
sudo systemctl enable smartreport
sudo systemctl start smartreport
sudo systemctl status smartreport
```

---

## Installation macOS

### 1. Installer Homebrew (si pas déjà fait)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Installer Python

```bash
brew install python@3.11
```

### 3. Cloner le Dépôt

```bash
git clone https://github.com/enovacom/SmartReport.git
cd SmartReport
```

### 4. Créer l'Environnement Virtuel

```bash
python3 -m venv venv
source venv/bin/activate
```

### 5. Installer les Dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Configurer

```bash
cp .env.example .env
nano .env
```

Éditer :
```env
ACTIVE_PROVIDER=mistral
MISTRAL_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 7. Lancer

```bash
python app.py
```

### 8. Accéder

Ouvrir http://127.0.0.1:5173

---

## Configuration

### Fichier `.env`

**Template complet :**

```env
# Configuration Réseau
HOST=127.0.0.1              # Adresse d'écoute (127.0.0.1 = localhost uniquement)
PORT=5173                   # Port du serveur
FLASK_DEBUG=true            # Mode debug (true pour dev, false pour prod)

# Provider IA Actif
ACTIVE_PROVIDER=mistral     # mistral | openai | deepseek | gemini | ollama

# 🌟 Mistral AI (Recommandé - RGPD France)
MISTRAL_BASE_URL=https://api.mistral.ai
MISTRAL_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI (Optionnel)
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# DeepSeek (Optionnel)
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Gemini (Optionnel)
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
GEMINI_API_KEY=AIza-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Ollama Local (Optionnel - Données sensibles)
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

### Obtenir des Clés API

#### Mistral AI (Gratuit - Recommandé)

1. Créer un compte : https://console.mistral.ai/
2. Aller dans **API Keys**
3. Cliquer **Create new key**
4. Copier la clé `sk-...` dans `.env`

**Quota gratuit :**
- ~5€ de crédits gratuits
- ~200 requêtes/minute
- Modèles : mistral-medium, mistral-large

#### OpenAI (Payant)

1. Créer un compte : https://platform.openai.com/
2. Ajouter un moyen de paiement
3. API Keys → Create new secret key
4. Copier dans `.env`

**Tarification :**
- GPT-4 Turbo : ~$0.01 / 1k tokens input, ~$0.03 / 1k tokens output
- GPT-3.5 Turbo : ~$0.0005 / 1k tokens

#### Ollama (Local - Gratuit)

1. Installer Ollama : https://ollama.ai/
2. Télécharger un modèle :
   ```bash
   ollama pull mistral
   # ou
   ollama pull llama2
   ```
3. Lancer :
   ```bash
   ollama serve
   ```
4. Utiliser l'URL `http://127.0.0.1:11434` dans SmartReport

**Avantages :**
- ✅ 100% offline
- ✅ Aucun coût
- ✅ Données confidentielles (pas de fuite)
- ✅ Pas de limite de requêtes

**Inconvénients :**
- ❌ Nécessite GPU (recommandé)
- ❌ Plus lent que les APIs cloud
- ❌ Qualité variable selon modèle

---

## Vérification

### 1. Tester l'Installation Python

```bash
python --version
# Python 3.11.7 ✅

pip list | grep -i flask
# Flask                     3.0.3 ✅
```

### 2. Tester le Serveur Flask

```bash
curl http://127.0.0.1:5173
# Devrait retourner le HTML de la page d'accueil
```

### 3. Tester l'API

```bash
curl -X POST http://127.0.0.1:5173/api/ai/test \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "mistral",
    "base_url": "https://api.mistral.ai",
    "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  }'
```

**Réponse attendue :**
```json
{
  "success": true,
  "message": "✅ Connexion Mistral réussie ! Modèles disponibles : mistral-medium-latest, mistral-large-latest"
}
```

---

## Dépannage

### ❌ Erreur : `python n'est pas reconnu`

**Cause** : Python n'est pas dans le PATH

**Solution Windows :**
1. Paramètres Système → Variables d'environnement → Path
2. Ajouter :
   - `C:\Users\<votre_user>\AppData\Local\Programs\Python\Python311\`
   - `C:\Users\<votre_user>\AppData\Local\Programs\Python\Python311\Scripts\`
3. Redémarrer le terminal

**Solution Linux/macOS :**
```bash
# Vérifier où est Python
which python3
# /usr/bin/python3

# Ajouter au PATH (~/.bashrc ou ~/.zshrc)
export PATH="/usr/bin/python3:$PATH"
source ~/.bashrc
```

---

### ❌ Erreur : `pip install` échoue

**Cause** : Pip obsolète ou problème de réseau

**Solution :**
```bash
# Mettre à jour pip
python -m pip install --upgrade pip

# Installer avec verbose pour voir l'erreur
pip install -r requirements.txt --verbose

# Si problème réseau, utiliser un miroir
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

### ❌ Erreur : `ModuleNotFoundError: No module named 'flask'`

**Cause** : Environnement virtuel non activé

**Solution :**
```bash
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

# Vérifier
which python
# Doit pointer vers venv/bin/python ou venv\Scripts\python.exe
```

---

### ❌ Erreur : `Address already in use` (port 5173 occupé)

**Cause** : Une autre instance de SmartReport (ou autre app) utilise le port 5173

**Solution 1 : Tuer le processus**
```bash
# Windows
netstat -ano | findstr :5173
# TCP    127.0.0.1:5173    0.0.0.0:0    LISTENING    12345
taskkill /PID 12345 /F

# Linux/macOS
lsof -ti:5173 | xargs kill -9
```

**Solution 2 : Changer le port**
```env
# .env
PORT=8080
```

---

### ❌ Erreur : `401 Unauthorized` lors des appels IA

**Cause** : Clé API invalide ou expirée

**Solution :**
1. Vérifier la clé dans `.env` (pas d'espaces, pas de guillemets)
2. Tester la clé directement :
   ```bash
   curl https://api.mistral.ai/v1/models \
     -H "Authorization: Bearer sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   ```
3. Régénérer une nouvelle clé si nécessaire

---

### ❌ Erreur : PDF generation failed - `lxml not found`

**Cause** : Dépendance système manquante

**Solution Linux :**
```bash
# Ubuntu/Debian
sudo apt install libxml2-dev libxslt-dev python3-dev

# RHEL/CentOS
sudo yum install libxml2-devel libxslt-devel python-devel

# Réinstaller lxml
pip install --force-reinstall lxml
```

**Solution macOS :**
```bash
brew install libxml2 libxslt
pip install --force-reinstall lxml
```

---

### ❌ Erreur : `cannot import name 'soft_unicode' from 'markupsafe'`

**Cause** : Incompatibilité MarkupSafe/Jinja2

**Solution :**
```bash
pip install --upgrade markupsafe jinja2
```

---

### ❌ Dictée vocale ne fonctionne pas

**Cause** : Navigateur non compatible ou HTTPS requis

**Solution :**
1. Utiliser **Chrome** ou **Edge** (Firefox/Safari ont un support limité)
2. Autoriser le microphone dans les paramètres du navigateur
3. Si localhost, c'est OK. Si IP distante, utiliser HTTPS

---

### ❌ Erreur : `Ollama connection refused`

**Cause** : Ollama n'est pas démarré

**Solution :**
```bash
# Démarrer Ollama
ollama serve

# Vérifier
curl http://127.0.0.1:11434/api/tags
```

---

## Mise à Jour

### Méthode Git

```bash
cd SmartReport
git pull origin main

# Activer venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Mettre à jour dépendances
pip install --upgrade -r requirements.txt

# Relancer
python app.py
```

### Méthode Manuelle

1. Télécharger la nouvelle version (ZIP)
2. Sauvegarder votre fichier `.env`
3. Extraire et remplacer les fichiers
4. Remettre votre `.env`
5. Réinstaller les dépendances :
   ```bash
   pip install --upgrade -r requirements.txt
   ```

---

## Désinstallation

### Windows

```powershell
cd SmartReport
venv\Scripts\deactivate  # Si activé
cd ..
rmdir /s /q SmartReport
```

### Linux/macOS

```bash
cd SmartReport
deactivate  # Si activé
cd ..
rm -rf SmartReport
```

### Nettoyage Complet

```bash
# Supprimer aussi les données utilisateur (localStorage du navigateur)
# Chrome: Paramètres → Confidentialité → Effacer les données de navigation → Données de site
# Ou dans DevTools (F12) → Application → Local Storage → http://127.0.0.1:5173 → Clear All
```

---

## Installation Docker (Avancé)

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Installer dépendances système
RUN apt-get update && apt-get install -y \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier code
COPY . .

# Exposer port
EXPOSE 5173

# Lancer avec Waitress (production)
CMD ["waitress-serve", "--listen=0.0.0.0:5173", "app:app"]
```

### Construire et Lancer

```bash
# Construire
docker build -t smartreport:latest .

# Lancer
docker run -d \
  -p 5173:5173 \
  -e ACTIVE_PROVIDER=mistral \
  -e MISTRAL_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx \
  --name smartreport \
  smartreport:latest

# Accéder
# http://localhost:5173
```

### Docker Compose

```yaml
version: '3.8'

services:
  smartreport:
    build: .
    ports:
      - "5173:5173"
    environment:
      - ACTIVE_PROVIDER=mistral
      - MISTRAL_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    restart: unless-stopped
```

Lancer :
```bash
docker-compose up -d
```

---

**📖 Documentation complète** : [Retour au README principal](../README.md)
