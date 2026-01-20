# 🤝 Guide de Contribution SmartReport

## Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Prérequis](#prérequis)
- [Setup Environnement de Développement](#setup-environnement-de-développement)
- [Structure du Code](#structure-du-code)
- [Conventions de Code](#conventions-de-code)
- [Workflow de Contribution](#workflow-de-contribution)
- [Pull Requests](#pull-requests)
- [Tests](#tests)
- [Documentation](#documentation)
- [Débogage](#débogage)

---

## Vue d'Ensemble

SmartReport est un projet **interne ENOVACOM** développé pour faciliter la génération de rapports professionnels et de diagrammes techniques via IA.

**Stack :**
- **Backend** : Flask 3 (Python)
- **Frontend** : Alpine.js + Tailwind CSS
- **Export** : ReportLab (PDF) + python-docx (DOCX)

---

## Prérequis

### Outils Requis

✅ **Python 3.8+**
```bash
python --version
# Python 3.11.7
```

✅ **Git**
```bash
git --version
# git version 2.40.0
```

✅ **Éditeur de code** (recommandé)
- [Visual Studio Code](https://code.visualstudio.com/) avec extensions :
  - Python (Microsoft)
  - Pylance (Microsoft)
  - Black Formatter (Microsoft)
  - HTML CSS Support
  - Tailwind CSS IntelliSense

✅ **Navigateur moderne**
- Chrome DevTools (recommandé)
- Firefox Developer Tools

### Connaissances Recommandées

- **Python** : Fonctions, classes, décorateurs, compréhensions de listes
- **Flask** : Routes, `request`, `jsonify`, `send_file`
- **HTML/CSS** : Structure DOM, Tailwind CSS utility classes
- **JavaScript** : ES6+, `async/await`, `fetch`, Alpine.js basics
- **Markdown** : Syntaxe de base
- **Mermaid.js** : Syntaxe des diagrammes (optionnel)

---

## Setup Environnement de Développement

### 1. Fork et Clone

```bash
# Fork le projet sur GitHub (bouton "Fork")
# https://github.com/enovacom/SmartReport

# Clone ton fork
git clone https://github.com/<your-username>/SmartReport.git
cd SmartReport

# Ajouter l'upstream (repo principal)
git remote add upstream https://github.com/enovacom/SmartReport.git
```

### 2. Créer une Branche

```bash
# Toujours créer une branche depuis main
git checkout main
git pull upstream main

# Créer une branche feature ou bugfix
git checkout -b feature/nouvelle-fonctionnalite
# ou
git checkout -b fix/correction-bug-export-pdf
```

**Convention de nommage des branches :**
- `feature/description-courte` : Nouvelle fonctionnalité
- `fix/description-courte` : Correction de bug
- `docs/description-courte` : Mise à jour documentation
- `refactor/description-courte` : Refactoring code
- `test/description-courte` : Ajout/modification tests

### 3. Installer les Dépendances

```bash
# Créer environnement virtuel
python -m venv venv

# Activer
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Installer dépendances
pip install --upgrade pip
pip install -r requirements.txt

# Installer dépendances de dev (optionnel)
pip install pytest black flake8 mypy
```

### 4. Configurer l'Environnement

```bash
# Copier .env.example
cp .env.example .env

# Éditer .env avec vos clés API de test
nano .env
```

**Clés API de test (recommandé) :**
- Créer un compte Mistral AI dédié au dev
- Utiliser le tier gratuit (suffisant pour tests)
- Ne **jamais** committer de vraies clés API

### 5. Lancer en Mode Dev

```bash
# Activer mode debug
export FLASK_DEBUG=true  # Linux/macOS
set FLASK_DEBUG=true     # Windows CMD
$env:FLASK_DEBUG="true"  # Windows PowerShell

# Lancer
python app.py
```

**Sortie attendue :**
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server.
 * Running on http://127.0.0.1:5173
 * Restarting with stat
Press CTRL+C to quit
```

**Mode debug activé :**
- ✅ Rechargement automatique du code (hot reload)
- ✅ Traceback détaillé des erreurs
- ✅ Debugger interactif dans le terminal

---

## Structure du Code

### Architecture Backend (`app.py`)

```python
# Imports et configuration
from flask import Flask, render_template, request, jsonify, send_file
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# Configuration en mémoire
config = {
    'mistral_api_key': os.getenv('MISTRAL_API_KEY', ''),
    'active_provider': os.getenv('ACTIVE_PROVIDER', 'mistral'),
    # ...
}

# Prompts système (templates de comptes rendus)
REPORT_PROMPTS = {
    'client_formel': """...""",
    'sprint_agile': """...""",
    # ...
}

# Routes principales
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate():
    # Génération diagramme Mermaid
    pass

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    # Génération compte rendu
    pass

@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf():
    # Export PDF
    pass

# Lancement
if __name__ == '__main__':
    app.run(
        host=os.getenv('HOST', '127.0.0.1'),
        port=int(os.getenv('PORT', 5173)),
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    )
```

### Architecture Frontend (`templates/index.html`)

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SmartReport - Générateur IA</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Alpine.js -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <!-- Mermaid.js -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
</head>
<body>
    <!-- Application Alpine.js -->
    <div x-data="app()" x-init="init()">
        <!-- Interface utilisateur -->
    </div>

    <!-- Script Alpine.js -->
    <script>
        function app() {
            return {
                // État de l'application
                currentProject: {...},
                projects: [],
                
                // Méthodes
                init() {...},
                generateDiagram() {...},
                generateReport() {...},
                generatePDF() {...},
                saveProject() {...}
            };
        }
    </script>
</body>
</html>
```

### Points d'Extension

#### Ajouter un Nouveau Provider IA

**1. Backend (`app.py`)**

```python
# Ajouter config dans .env.example
# NEW_PROVIDER_BASE_URL=https://api.newprovider.com
# NEW_PROVIDER_API_KEY=sk-xxxxx

# Charger config
config = {
    ...
    'new_provider_base_url': os.getenv('NEW_PROVIDER_BASE_URL', ''),
    'new_provider_api_key': os.getenv('NEW_PROVIDER_API_KEY', ''),
}

# Ajouter logique dans generate() et generate_report()
@app.route('/api/generate', methods=['POST'])
def generate():
    provider = config.get('active_provider', 'mistral')
    
    if provider == 'new_provider':
        base_url = config['new_provider_base_url']
        api_key = config['new_provider_api_key']
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': model or 'default-model',
            'messages': [
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': prompt}
            ]
        }
        
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            mermaid_code = data['choices'][0]['message']['content']
            return jsonify({'mermaid': mermaid_code})
    # ...
```

**2. Frontend (`templates/index.html`)**

```html
<!-- Ajouter option dans le select des providers (dans modal Paramètres) -->
<select x-model="selectedProvider">
    <option value="mistral">Mistral AI</option>
    <option value="openai">OpenAI</option>
    <option value="new_provider">New Provider</option>
</select>
```

#### Ajouter un Nouveau Template de Compte Rendu

**1. Backend (`app.py`)**

```python
REPORT_PROMPTS = {
    ...
    'nouveau_template': """Tu es un [rôle] chez ENOVACOM.
Tu rédiges des comptes rendus de [type].

Style : [style]
Format : Markdown pur (sans bloc de code, sans introduction).

RÈGLE CRUCIALE SUR LES DATES :
- TOUJOURS utiliser le format complet : JJ/MM/AAAA

Structure OBLIGATOIRE :
## Section 1
[Description]

## Section 2
[Description]

IMPORTANT : Renvoie UNIQUEMENT le Markdown pur.

Ton rôle : [rôle précis]."""
}
```

**2. Frontend (`templates/index.html`)**

```javascript
reportTemplates: [
    { id: 'client_formel', name: 'Client (formel)' },
    { id: 'sprint_agile', name: 'Sprint Agile' },
    { id: 'nouveau_template', name: 'Nouveau Template' }  // ← Ajouter ici
]
```

---

## Conventions de Code

### Python (Backend)

#### Style : PEP 8

**Formatage automatique :**
```bash
# Installer Black
pip install black

# Formater tout le code
black app.py

# Vérifier style (flake8)
pip install flake8
flake8 app.py --max-line-length=120
```

**Règles principales :**
- **Indentation** : 4 espaces (pas de tabs)
- **Longueur ligne** : Max 120 caractères
- **Naming** :
  - Fonctions : `snake_case` (`def generate_pdf()`)
  - Classes : `PascalCase` (`class ReportGenerator`)
  - Constantes : `UPPER_SNAKE_CASE` (`REPORT_PROMPTS`)
  - Variables : `snake_case` (`api_key`)

**Exemple :**
```python
def generate_pdf(project_data: dict) -> bytes:
    """
    Génère un PDF professionnel depuis les données du projet.
    
    Args:
        project_data (dict): Données du projet (report, images, pdfConfig)
    
    Returns:
        bytes: Contenu du PDF généré
    
    Raises:
        ValueError: Si project_data est invalide
        Exception: Erreur de génération ReportLab
    """
    try:
        # Validation
        if not project_data.get('report', {}).get('generated'):
            raise ValueError("Report content is missing")
        
        # Génération
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
        story = []
        
        # Build PDF
        doc.build(story)
        
        return pdf_buffer.getvalue()
    
    except Exception as e:
        print(f"❌ Erreur génération PDF: {str(e)}")
        raise
```

#### Docstrings : Google Style

```python
def function_name(param1: str, param2: int = 0) -> bool:
    """
    Brève description en une ligne.
    
    Description détaillée sur plusieurs lignes si nécessaire.
    Explication du comportement, cas particuliers, etc.
    
    Args:
        param1 (str): Description du premier paramètre.
        param2 (int, optional): Description du deuxième paramètre. Defaults to 0.
    
    Returns:
        bool: Description de la valeur de retour.
    
    Raises:
        ValueError: Quand param1 est vide.
        TypeError: Quand param2 n'est pas un entier.
    
    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
        True
    """
    pass
```

### JavaScript (Frontend)

#### Style : Airbnb JavaScript Style Guide (adapté)

**Règles principales :**
- **Indentation** : 2 espaces
- **Quotes** : Single quotes `'...'` (sauf HTML)
- **Semicolons** : Optionnel (Alpine.js style)
- **Naming** :
  - Fonctions : `camelCase` (`generateDiagram()`)
  - Variables : `camelCase` (`currentProject`)
  - Constantes : `UPPER_SNAKE_CASE` (`API_BASE_URL`)

**Exemple Alpine.js :**
```javascript
function app() {
  return {
    // État
    currentProject: {
      id: null,
      name: '',
      diagram: {...},
      report: {...}
    },
    
    // Méthodes
    async generateDiagram() {
      try {
        this.loading = true;
        
        const response = await fetch('/api/generate', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            prompt: this.prompt,
            model: this.selectedModel
          })
        });
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        this.mermaidCode = data.mermaid;
        
        this.showToast('Diagramme généré avec succès', 'success');
      } catch (error) {
        console.error('Erreur génération:', error);
        this.showToast(`Erreur: ${error.message}`, 'error');
      } finally {
        this.loading = false;
      }
    },
    
    showToast(message, type = 'info') {
      // Implementation
    }
  };
}
```

### HTML/CSS

**Règles :**
- **Indentation** : 2 espaces
- **Classes Tailwind** : Ordre logique (layout → spacing → colors → typography)
- **Alpine directives** : `x-data`, `x-init`, `x-on`, `x-model`, `x-show`, `x-if`

**Exemple :**
```html
<!-- Bon ordre des classes Tailwind -->
<div class="flex flex-col items-center justify-center gap-4 p-6 bg-white rounded-lg shadow-md">
  <h2 class="text-2xl font-bold text-gray-800">Titre</h2>
  <button 
    @click="handleClick" 
    class="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
  >
    Cliquer
  </button>
</div>
```

---

## Workflow de Contribution

### 1. Identifier une Issue ou Feature

**Vérifier les issues existantes :**
https://github.com/enovacom/SmartReport/issues

**Créer une nouvelle issue si nécessaire :**
- **Bug** : Template "Bug report"
- **Feature** : Template "Feature request"
- **Documentation** : Label `documentation`

### 2. Développer

```bash
# Créer branche
git checkout -b feature/ma-fonctionnalite

# Coder
# ...

# Tester localement
python app.py
# Ouvrir http://127.0.0.1:5173
# Vérifier que tout fonctionne

# Commits atomiques
git add app.py
git commit -m "feat: ajout support provider Gemini"

git add templates/index.html
git commit -m "feat(ui): ajout option Gemini dans paramètres"
```

### 3. Convention de Commits (Conventional Commits)

**Format :**
```
<type>(<scope>): <description>

[body optionnel]

[footer optionnel]
```

**Types :**
- `feat` : Nouvelle fonctionnalité
- `fix` : Correction de bug
- `docs` : Documentation uniquement
- `style` : Formatage (pas de changement de code)
- `refactor` : Refactoring (pas de feat ni fix)
- `test` : Ajout/modification tests
- `chore` : Tâches build, config, etc.

**Scopes (optionnels) :**
- `api` : Routes Flask
- `ui` : Interface utilisateur
- `pdf` : Génération PDF
- `docx` : Génération DOCX
- `ia` : Intégration providers IA
- `config` : Configuration (.env, settings)

**Exemples :**
```bash
git commit -m "feat(ia): ajout support Gemini AI provider"
git commit -m "fix(pdf): correction encoding tableaux UTF-8"
git commit -m "docs: mise à jour README avec exemples Docker"
git commit -m "refactor(api): extraction logique IA dans module séparé"
git commit -m "style: formatage code avec Black"
git commit -m "test(pdf): ajout tests unitaires génération tableaux"
```

### 4. Push et Pull Request

```bash
# Push vers ton fork
git push origin feature/ma-fonctionnalite

# Créer Pull Request sur GitHub
# https://github.com/enovacom/SmartReport/compare
```

---

## Pull Requests

### Template de PR

**Titre :**
```
[TYPE] Brève description (max 50 chars)
```

**Description :**
```markdown
## 📝 Description

Brève description de la PR (1-2 phrases).

## 🎯 Motivation et Contexte

Pourquoi ce changement est nécessaire ? Quelle issue il résout ?

Closes #123

## ✨ Changements Apportés

- Ajout de X
- Modification de Y
- Suppression de Z

## 📸 Captures d'Écran (si applicable)

![Screenshot](url)

## ✅ Checklist

- [ ] Code testé localement
- [ ] Documentation mise à jour (si applicable)
- [ ] Commits suivent Conventional Commits
- [ ] Pas de warnings/erreurs
- [ ] Code formaté (Black pour Python)
```

### Review Process

**Avant de soumettre :**
1. ✅ Code fonctionne localement
2. ✅ Pas de `console.log()` ou `print()` debug laissés
3. ✅ Commits propres et atomiques
4. ✅ Documentation à jour

**Pendant la review :**
- Répondre aux commentaires rapidement
- Effectuer les changements demandés
- Re-push sur la même branche (PR se met à jour auto)

**Après merge :**
```bash
# Mettre à jour ton fork
git checkout main
git pull upstream main
git push origin main

# Supprimer branche locale
git branch -d feature/ma-fonctionnalite

# Supprimer branche remote
git push origin --delete feature/ma-fonctionnalite
```

---

## Tests

### Tests Manuels (Minimum)

**Checklist avant PR :**

✅ **Génération de diagramme**
- [ ] Prompt simple fonctionne
- [ ] Diagramme s'affiche correctement
- [ ] Export SVG/PNG/JPEG fonctionne

✅ **Génération de compte rendu**
- [ ] Tous les templates fonctionnent
- [ ] Édition du compte rendu fonctionne
- [ ] Tableaux sont éditables

✅ **Export PDF/DOCX**
- [ ] PDF généré avec logo, en-tête, pied de page
- [ ] DOCX généré et éditable dans Word
- [ ] Images apparaissent correctement

✅ **Gestion de projets**
- [ ] Sauvegarde automatique fonctionne
- [ ] Ouverture d'un projet restaure l'état
- [ ] Suppression d'un projet fonctionne

### Tests Unitaires (Avancé)

**Framework : pytest**

**Installation :**
```bash
pip install pytest pytest-cov
```

**Structure :**
```
SmartReport/
├── app.py
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_pdf_generation.py
│   └── test_docx_generation.py
```

**Exemple `tests/test_api.py` :**
```python
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    """Test de la route principale"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'SmartReport' in response.data

def test_generate_api(client, monkeypatch):
    """Test de l'API de génération Mermaid"""
    # Mock de l'appel IA
    def mock_post(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return {
                    'choices': [{
                        'message': {
                            'content': 'graph TD\n    A --> B'
                        }
                    }]
                }
        return MockResponse()
    
    monkeypatch.setattr('requests.post', mock_post)
    
    response = client.post('/api/generate', json={
        'prompt': 'Test diagram'
    })
    
    assert response.status_code == 200
    data = response.json
    assert 'mermaid' in data
    assert 'graph TD' in data['mermaid']
```

**Lancer les tests :**
```bash
# Tous les tests
pytest

# Avec coverage
pytest --cov=app --cov-report=html

# Test spécifique
pytest tests/test_api.py::test_index_route -v
```

---

## Documentation

### Mise à Jour de la Documentation

**Fichiers à maintenir :**
- `README.md` : Documentation principale
- `docs/ARCHITECTURE.md` : Architecture technique
- `docs/API.md` : Documentation API REST
- `docs/INSTALLATION.md` : Guide d'installation
- `docs/USAGE.md` : Guide d'utilisation
- `docs/CONTRIBUTING.md` : Ce fichier

**Quand mettre à jour :**
- Ajout de fonctionnalité → `README.md` + `docs/USAGE.md`
- Modification API → `docs/API.md`
- Nouveau provider IA → `docs/INSTALLATION.md` (config)
- Changement architecture → `docs/ARCHITECTURE.md`

### Docstrings dans le Code

**Toujours documenter :**
- Fonctions publiques (routes API)
- Fonctions complexes (génération PDF/DOCX)
- Classes (si ajoutées)

**Ne pas documenter :**
- Fonctions triviales (`get_config()`, `set_value()`)
- Fonctions privées internes (`_helper_function()`)

---

## Débogage

### Backend (Flask)

**Logs :**
```python
# app.py
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/api/generate', methods=['POST'])
def generate():
    logger.debug(f"Prompt reçu: {request.json.get('prompt')}")
    # ...
```

**Debugger interactif :**
```python
# Installer ipdb
pip install ipdb

# Ajouter breakpoint
import ipdb; ipdb.set_trace()
```

### Frontend (Alpine.js)

**DevTools Console :**
```javascript
// Inspecter l'état Alpine
window.Alpine.store('app')

// Logger events
@click="console.log('Clicked:', $event); handleClick()"
```

**Alpine DevTools (Extension Chrome) :**
https://chrome.google.com/webstore/detail/alpinejs-devtools

### Erreurs Communes

#### ❌ `401 Unauthorized` (API IA)

**Cause :** Clé API invalide

**Debug :**
```python
# app.py
print(f"🔑 API Key: {api_key[:10]}...{api_key[-5:]}")  # Masquer clé
print(f"🌐 Base URL: {base_url}")
```

#### ❌ `ModuleNotFoundError`

**Cause :** Dépendance manquante

**Solution :**
```bash
pip install -r requirements.txt
```

#### ❌ PDF generation fails

**Cause :** HTML mal formé

**Debug :**
```python
# app.py - dans generate_pdf()
print(f"📄 HTML content: {report_html[:200]}...")
from bs4 import BeautifulSoup
soup = BeautifulSoup(report_html, 'html.parser')
print(f"🔍 Parsed: {soup.prettify()[:200]}...")
```

---

## Points d'Attention

### Sécurité

⚠️ **Ne jamais committer de clés API**
```bash
# Vérifier avant commit
git diff

# Si clé commitée par erreur
git reset HEAD~1
git add .env
git commit --amend
```

⚠️ **Validation des inputs utilisateur**
```python
# Toujours valider
@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    if not data or 'prompt' not in data:
        return jsonify({'error': 'Prompt manquant'}), 400
    
    prompt = data['prompt']
    if len(prompt) > 5000:  # Limite raisonnable
        return jsonify({'error': 'Prompt trop long'}), 400
```

### Performance

⚠️ **Éviter les boucles sur gros volumes**
```python
# ❌ Mauvais
for row in huge_table:
    process(row)  # Appel lent

# ✅ Bon
processed = [process(row) for row in huge_table]  # Compréhension de liste
```

⚠️ **Cache les résultats coûteux**
```python
# Exemple: cache des modèles IA disponibles
from functools import lru_cache

@lru_cache(maxsize=1)
def get_available_models(provider):
    # Appel API coûteux
    response = requests.get(f"{base_url}/models")
    return response.json()['models']
```

---

## Contact

**Questions ? Problèmes ?**

- 📧 Email : dev@enovacom.com
- 💬 Slack : #smartreport-dev
- 🐛 Issues : https://github.com/enovacom/SmartReport/issues

---

**📖 Documentation complète** : [Retour au README principal](../README.md)
