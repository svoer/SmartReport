from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import requests
import os
import re
import markdown
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak, Table, TableStyle, Preformatted, KeepTogether
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
import base64
from dotenv import load_dotenv

# Import pour génération DOCX
try:
    from docx import Document
    from docx.shared import RGBColor, Pt, Inches, Mm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    DOCX_SUPPORT = True
    print("✅ python-docx chargé - Support DOCX activé")
except ImportError:
    DOCX_SUPPORT = False
    print("⚠️ python-docx non installé - Export DOCX désactivé")

# Importer svglib pour gérer les SVG (optionnel)
try:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPDF
    SVG_SUPPORT = True
    print("✅ svglib chargé - Support SVG activé")
except ImportError:
    SVG_SUPPORT = False
    print("⚠️ svglib non installé - Les SVG seront convertis en images")

# Parser HTML (optionnel)
try:
    from bs4 import BeautifulSoup
    BS4_SUPPORT = True
except ImportError:
    BS4_SUPPORT = False
    print("⚠️ bs4 non installé - Rendu HTML simplifié dans le PDF")

load_dotenv()

app = Flask(__name__)

# Désactiver le cache des templates pour le développement
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Configuration en mémoire
config = {
    'mistral_base_url': os.getenv('MISTRAL_BASE_URL', 'https://api.mistral.ai'),
    'mistral_api_key': os.getenv('MISTRAL_API_KEY', ''),
    'ollama_base_url': os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
    'active_provider': os.getenv('ACTIVE_PROVIDER', 'mistral'),
    # Charger les configs des autres providers
    'openai_base_url': os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
    'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
    'deepseek_base_url': os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'),
    'deepseek_api_key': os.getenv('DEEPSEEK_API_KEY', ''),
    'gemini_base_url': os.getenv('GEMINI_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/openai/'),
    'gemini_api_key': os.getenv('GEMINI_API_KEY', ''),
}

SYSTEM_PROMPT = """Tu convertis une description FR/EN en code Mermaid v10 **valide**.
Règles :
- Détecte type pertinent : flowchart, sequence, class, state, er, gantt.
- Réponds **UNIQUEMENT** par un bloc de code Mermaid (sans prose/commentaires).
- Identifiants sûrs (A, A1, a-b, etc.).
- Header YAML si pertinent :
---
title: ...
---"""

# Prompts pour génération de comptes rendus
REPORT_PROMPTS = {
    'client_formel': """Tu es un chef de projet / responsable relation client chez ENOVACOM.
Tu rédiges des comptes rendus de réunion client professionnels, factuels et structurés.

Style : formel, précis, synthétique.
Format : Markdown pur (sans bloc de code, sans introduction).

RÈGLE CRUCIALE SUR LES DATES :
- TOUJOURS utiliser le format complet : JJ/MM/AAAA (ex: 03/11/2025)
- JAMAIS omettre l'année
- Utiliser la date fournie dans le contexte temporel si aucune date n'est mentionnée
- Pour les échéances futures, calculer à partir de la date actuelle fournie

Structure OBLIGATOIRE :
## Compte Rendu de Réunion
[Date COMPLÈTE avec année (JJ/MM/AAAA) et participants]

## Contexte & Objectif
[Résumé en 2-3 phrases]

## Points abordés
[Résumé structuré avec puces]

## Décisions prises
[Liste claire des décisions validées]

## Actions à mener
[Tableau Markdown : | Action | Responsable | Échéance (JJ/MM/AAAA) |]

## Prochains rendez-vous
[Date COMPLÈTE avec année et ordre du jour]

IMPORTANT : Renvoie UNIQUEMENT le Markdown pur. Commence directement par ## Compte Rendu. PAS de bloc de code ```, PAS d'introduction.

Ton rôle : transformer les notes brutes en un document structuré prêt à envoyer au client.""",

    'sprint_agile': """Tu es un Scrum Master / Chef de projet agile chez ENOVACOM.
Tu rédiges des comptes rendus de sprint (daily, sprint review, retrospective).

Style : Concis, factuel, orienté équipe.
Format : Markdown pur (sans bloc de code, sans introduction).

RÈGLE CRUCIALE SUR LES DATES :
- TOUJOURS utiliser le format complet : JJ/MM/AAAA (ex: 03/11/2025)
- JAMAIS omettre l'année
- Utiliser la date fournie dans le contexte temporel si aucune date n'est mentionnée
- Pour les échéances, toujours indiquer l'année complète

Structure OBLIGATOIRE :
## Sprint [Numéro] - [Type de réunion]
[Date COMPLÈTE avec année (JJ/MM/AAAA) et participants]

## Objectifs du sprint
[Liste des objectifs]

## User Stories traitées
[Tableau Markdown : | US | Statut | Commentaire |]

## Blockers & Risques
[Liste des blocages identifiés et solutions proposées]

## Décisions techniques
[Décisions d'architecture ou choix techniques]

## Actions pour le prochain sprint
[Tableau Markdown : | Action | Responsable | Échéance (JJ/MM/AAAA) | Priorité |]

## Prochaine réunion
[Date COMPLÈTE avec année (JJ/MM/AAAA) et ordre du jour]

IMPORTANT : Renvoie UNIQUEMENT le Markdown pur. Commence directement par ## Sprint. PAS de bloc de code ```, PAS d'introduction.

Ton rôle : synthétiser les échanges agiles en un document actionnable pour l'équipe.""",

    'brief_technique': """Tu es un architecte technique / tech lead chez ENOVACOM.
Tu rédiges des comptes rendus d'ateliers techniques (architecture, conception, choix technologiques).

Style : Technique mais accessible, structuré, justifié.
Format : Markdown pur (sans bloc de code, sans introduction).

RÈGLE CRUCIALE SUR LES DATES :
- TOUJOURS utiliser le format complet : JJ/MM/AAAA (ex: 03/11/2025)
- JAMAIS omettre l'année
- Utiliser la date fournie dans le contexte temporel si aucune date n'est mentionnée
- Pour les échéances techniques, toujours indiquer l'année complète

Structure OBLIGATOIRE :
## Contexte technique
[Date de l'atelier (JJ/MM/AAAA) - Rappel du contexte projet et enjeux techniques]

## Participants
[Liste des participants avec rôles]

## Sujets abordés
[Liste détaillée des points techniques discutés]

## Décisions d'architecture
[Tableau Markdown : | Décision | Justification | Impact |]

## Contraintes identifiées
[Contraintes techniques, réglementaires, performance, sécurité]

## Stack technique retenue
[Technologies, frameworks, outils validés]

## Actions techniques
[Tableau Markdown : | Action | Responsable | Échéance (JJ/MM/AAAA) | Dépendances |]

## Points en suspens
[Questions ouvertes nécessitant investigation]

IMPORTANT : Renvoie UNIQUEMENT le Markdown pur. Commence directement par ## Contexte technique. PAS de bloc de code ```, PAS d'introduction.

Ton rôle : documenter les choix techniques de manière claire et justifiée.""",

    'crm_echange': """Tu es un responsable commercial / ingénieur d'affaires chez ENOVACOM (filiale d'Orange Business, éditeur de logiciels de santé spécialisé dans l'interopérabilité).
Tu rédiges des comptes rendus CRM selon le modèle "Échange & Partage" pour documenter les rendez-vous clients et identifier les opportunités commerciales.

Style : Professionnel, fluide, orienté business et partenariat client.
Format : Markdown pur (sans bloc de code, sans introduction).

RÈGLE CRUCIALE SUR LES DATES :
- TOUJOURS utiliser le format complet : JJ/MM/AAAA (ex: 03/11/2025)
- JAMAIS omettre l'année
- Utiliser la date fournie dans le contexte temporel si aucune date n'est mentionnée
- Pour les échéances et actions, toujours indiquer l'année complète

Structure OBLIGATOIRE :
## 1. Informations générales
[Date (JJ/MM/AAAA), type de rendez-vous, durée, établissement/client, site, participants client et Enovacom]

## 2. Contexte et objectifs du rendez-vous
[Objet, contexte, enjeux du rendez-vous]

## 3. Synthèse de l'échange
[Besoins exprimés, attentes, freins, éléments factuels marquants]

## 4. Opportunité(s) identifiée(s)
[Jusqu'à 3 opportunités détectées, pour chaque opportunité :]
### Opportunité #1 - [Nom/Thématique]
- **Offre concernée** : [Service ou produit Enovacom]
- **Budget estimé** : [Montant]
- **Phase du cycle** : [Lead / Qualification / Proposition / Négociation / Closing]
- **Probabilité** : [%]
- **Décideur/Influenceur** : [Nom et fonction]
- **Concurrence** : [Acteurs identifiés]
- **Actions prévues** : [Liste]
- **Responsable interne** : [Nom]

## 5. Mise à jour base client
[GHT/SIRET, adresse, stack applicatif, version Enovacom, nouveaux contacts, actions correctives]

## 6. Messages clés et réactions
- **Messages transmis** : [Points clés présentés]
- **Réactions client** : [Feedback]
- **Perception** : [Image Enovacom perçue]
- **Niveau d'ouverture** : [Faible / Moyen / Fort]

## 7. Actions de suivi
[Tableau Markdown : | Action | Responsable | Échéance (JJ/MM/AAAA) | Statut |]

## 8. Synthèse commerciale interne
- **Nombre d'opportunités** : [X]
- **Montant total estimé** : [€]
- **Probabilité moyenne** : [%]
- **Prochaine étape** : [Action prioritaire]
- **Commentaire commercial** : [Vision stratégique]

## 9. Annexes
[Liens OneDrive, documents joints, présentations, captures écran]

IMPORTANT : Renvoie UNIQUEMENT le Markdown pur. Commence directement par ## 1. Informations générales. PAS de bloc de code ```, PAS d'introduction.

Ton rôle : transformer les notes de rendez-vous (transcription Teams, enregistrement vocal, notes manuscrites) en un compte rendu CRM complet, structuré et prêt à copier-coller dans le CRM Enovacom. Détecter automatiquement les opportunités commerciales et identifier les informations pertinentes pour la base client."""
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.svg', mimetype='image/svg+xml')

@app.route('/mentions-legales')
def mentions_legales():
    return render_template('mentions-legales.html')

@app.route('/confidentialite')
def confidentialite():
    return render_template('confidentialite.html')

@app.route('/conditions')
def conditions():
    return render_template('conditions.html')

@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        prompt = data.get('prompt', '')
        model = data.get('model', '')
        
        if not prompt.strip():
            return jsonify({'error': 'Prompt requis'}), 400
        
        # Utiliser le provider actif configuré
        provider = config.get('active_provider', 'mistral')
        
        # Si c'est Ollama, utiliser la fonction spécifique
        if provider == 'ollama':
            return generate_ollama(prompt, model)
        # Sinon, utiliser la fonction générique pour providers compatibles OpenAI
        else:
            return generate_ai_provider(prompt, model, provider)
            
    except Exception as e:
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500

def generate_ollama(prompt, model):
    try:
        url = f"{config['ollama_base_url']}/api/generate"
        payload = {
            "model": model,
            "prompt": f"{SYSTEM_PROMPT}\n\nDescription: {prompt}",
            "stream": False
        }
        
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        mermaid_code = result.get('response', '').strip()
        
        if not is_valid_mermaid(mermaid_code):
            return jsonify({'error': 'Réponse invalide: pas de code Mermaid détecté'}), 422
            
        return jsonify({'mermaid': mermaid_code})
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Timeout: Ollama ne répond pas'}), 408
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Impossible de se connecter à Ollama'}), 503
    except Exception as e:
        return jsonify({'error': f'Erreur Ollama: {str(e)}'}), 500

def generate_mistral(prompt, model):
    try:
        if not config['mistral_api_key']:
            return jsonify({'error': 'Clé API Mistral manquante dans la configuration'}), 401
            
        url = f"{config['mistral_base_url']}/v1/chat/completions"
        headers = {
            'Authorization': f"Bearer {config['mistral_api_key']}",
            'Content-Type': 'application/json'
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Description: {prompt}"}
            ],
            "temperature": 0.1,
            "max_tokens": 2000
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        # Debug logging
        print(f"Mistral API Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Mistral API Error: {response.text}")
        
        response.raise_for_status()
        
        result = response.json()
        mermaid_code = result['choices'][0]['message']['content'].strip()
        
        # Nettoyer le code Mermaid des balises markdown
        if mermaid_code.startswith('```mermaid'):
            lines = mermaid_code.split('\n')
            mermaid_code = '\n'.join(lines[1:-1]) if len(lines) > 2 else mermaid_code
        elif mermaid_code.startswith('```'):
            lines = mermaid_code.split('\n')
            mermaid_code = '\n'.join(lines[1:-1]) if len(lines) > 2 else mermaid_code
        
        mermaid_code = mermaid_code.strip()
        
        if not is_valid_mermaid(mermaid_code):
            print(f"⚠️ Code Mermaid invalide généré: {mermaid_code[:100]}...")
            return jsonify({'error': 'Réponse invalide: pas de code Mermaid détecté'}), 422
            
        return jsonify({'mermaid': mermaid_code})
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Timeout: Mistral ne répond pas dans les délais'}), 408
    except requests.exceptions.HTTPError as e:
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 401:
                return jsonify({'error': 'Clé API Mistral invalide ou expirée'}), 401
            elif e.response.status_code == 403:
                return jsonify({'error': 'Accès non autorisé à l\'API Mistral'}), 403
            elif e.response.status_code == 429:
                return jsonify({'error': 'Limite de débit API Mistral atteinte'}), 429
            else:
                return jsonify({'error': f'Erreur API Mistral: {e.response.status_code}'}), 503
        return jsonify({'error': f'Erreur HTTP Mistral: {str(e)}'}), 503
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Erreur de connexion Mistral: {str(e)}'}), 503
    except KeyError as e:
        return jsonify({'error': f'Réponse API Mistral malformée: {str(e)}'}), 502
    except Exception as e:
        return jsonify({'error': f'Erreur Mistral: {str(e)}'}), 500

def generate_ai_provider(prompt, model, provider):
    """Génération de diagramme Mermaid avec n'importe quel provider compatible OpenAI"""
    try:
        # Récupérer la configuration du provider
        base_url = config.get(f'{provider}_base_url', '')
        api_key = config.get(f'{provider}_api_key', '')
        
        if not base_url:
            return jsonify({'error': f'Provider {provider} non configuré'}), 400
        
        if not api_key:
            return jsonify({'error': f'Clé API {provider} manquante'}), 401
        
        # Construction de l'URL
        url = f"{base_url}/v1/chat/completions"
        
        headers = {
            'Authorization': f"Bearer {api_key}",
            'Content-Type': 'application/json'
        }
        
        # Utiliser le modèle fourni ou un par défaut selon le provider
        if not model:
            default_models = {
                'mistral': 'mistral-medium-latest',
                'openai': 'gpt-4-turbo-preview',
                'deepseek': 'deepseek-chat',
                'gemini': 'gemini-pro'
            }
            model = default_models.get(provider, 'mistral-medium-latest')
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Description: {prompt}"}
            ],
            "temperature": 0.1,
            "max_tokens": 2000
        }
        
        print(f"🚀 Génération diagramme avec {provider} (modèle: {model})")
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        # Debug
        if response.status_code != 200:
            print(f"❌ {provider} API Error {response.status_code}: {response.text[:200]}")
        
        response.raise_for_status()
        
        result = response.json()
        mermaid_code = result['choices'][0]['message']['content'].strip()
        
        # Nettoyer le code Mermaid des balises markdown
        if mermaid_code.startswith('```mermaid'):
            lines = mermaid_code.split('\n')
            mermaid_code = '\n'.join(lines[1:-1]) if len(lines) > 2 else mermaid_code
        elif mermaid_code.startswith('```'):
            lines = mermaid_code.split('\n')
            mermaid_code = '\n'.join(lines[1:-1]) if len(lines) > 2 else mermaid_code
        
        mermaid_code = mermaid_code.strip()
        
        if not is_valid_mermaid(mermaid_code):
            print(f"⚠️ Code Mermaid invalide généré par {provider}: {mermaid_code[:100]}...")
            return jsonify({'error': 'Réponse invalide: pas de code Mermaid détecté'}), 422
        
        print(f"✅ Diagramme généré avec succès via {provider}")
        return jsonify({'mermaid': mermaid_code})
        
    except requests.exceptions.Timeout:
        return jsonify({'error': f'Timeout: {provider} ne répond pas'}), 408
    except requests.exceptions.HTTPError as e:
        if hasattr(e, 'response') and e.response is not None:
            status = e.response.status_code
            if status == 401:
                return jsonify({'error': f'Clé API {provider} invalide'}), 401
            elif status == 403:
                return jsonify({'error': f'Accès non autorisé à {provider}'}), 403
            elif status == 429:
                return jsonify({'error': f'Limite de débit {provider} atteinte'}), 429
            else:
                return jsonify({'error': f'Erreur {provider}: {status}'}), 503
        return jsonify({'error': f'Erreur HTTP {provider}'}), 503
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Erreur connexion {provider}: {str(e)}'}), 503
    except KeyError as e:
        return jsonify({'error': f'Réponse {provider} malformée: {str(e)}'}), 502
    except Exception as e:
        return jsonify({'error': f'Erreur {provider}: {str(e)}'}), 500

def clean_squares(text):
    """Nettoie les carrés et symboles de la zone 'Geometric Shapes' et similaires.
    Supprime aussi les espaces invisibles susceptibles d'apparaître.
    """
    if not text:
        return text
    import re
    # Supprimer tous symboles dans Geometric Shapes (U+25A0–U+25FF) et quelques blocs voisins
    text = re.sub(r'[\u25A0-\u25FF\u2B00-\u2BFF\u2580-\u259F]', '', text)
    # Supprimer points/puces exotiques éventuels
    text = re.sub(r'[\u2022\u2043\u2219\u00B7]', '', text) if False else text  # désactivé (on gère les puces via bulletText)
    # Supprimer espaces invisibles
    text = re.sub(r'[\u200B\u200C\u200D\u2060\u00A0]', ' ', text)
    # Normaliser les espaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def is_valid_mermaid(text):
    """Vérifie si le texte contient du code Mermaid valide"""
    if not text:
        return False
    
    # Nettoyer le texte des balises markdown
    text = text.strip()
    
    # Supprimer les balises markdown si présentes
    if text.startswith('```mermaid'):
        lines = text.split('\n')
        text = '\n'.join(lines[1:-1]) if len(lines) > 2 else text
    elif text.startswith('```'):
        lines = text.split('\n')
        text = '\n'.join(lines[1:-1]) if len(lines) > 2 else text
    
    # Patterns Mermaid courants
    patterns = [
        r'flowchart\s+(TD|LR|TB|RL|BT)',
        r'sequenceDiagram',
        r'classDiagram',
        r'stateDiagram',
        r'erDiagram',
        r'gantt',
        r'pie\s+(title|showData)',
        r'graph\s+(TD|LR|TB|RL|BT)',
        r'journey',
        r'gitGraph',
        r'gitgraph'
    ]
    
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)

@app.route('/api/ollama/models')
def ollama_models():
    try:
        url = f"{config['ollama_base_url']}/api/tags"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        models = [model['name'] for model in data.get('models', [])]
        
        return jsonify({'models': models})
        
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Ollama non disponible'}), 503
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la récupération des modèles Ollama: {str(e)}'}), 500

@app.route('/api/mistral/models')
def mistral_models():
    try:
        # Vérifier si on a des headers de test (pour la fonction testMistralConnection)
        test_key = request.headers.get('X-Test-API-Key')
        test_url = request.headers.get('X-Test-Base-URL')
        
        if test_key and test_url:
            # Mode test : utiliser les paramètres passés en headers
            api_key = test_key
            base_url = test_url
            print(f"🧪 Mode TEST - Base URL: {base_url}, API Key: {api_key[:10]}...")
        else:
            # Mode normal : utiliser la config
            if not config['mistral_api_key']:
                return jsonify({'error': 'Clé API Mistral manquante'}), 401
            api_key = config['mistral_api_key']
            base_url = config['mistral_base_url']
            
        url = f"{base_url}/v1/models"
        headers = {
            'Authorization': f"Bearer {api_key}",
            'Content-Type': 'application/json'
        }
        
        # Debug (désactivé en production)
        # print(f"🔍 DEBUG Mistral - URL: {url}")
        # print(f"🔍 DEBUG Mistral - Headers: Authorization Bearer {api_key[:10]}...")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        # print(f"🔍 DEBUG Mistral - Status: {response.status_code}")
        # print(f"🔍 DEBUG Mistral - Response: {response.text[:200]}...")
        
        response.raise_for_status()
        
        data = response.json()
        
        # D'après la doc Mistral, la structure est : {"object": "list", "data": [...]}
        models_data = data.get('data', [])
        models = [model['id'] for model in models_data if 'id' in model]
        
        # print(f"🔍 DEBUG Mistral - Models found: {models}")
        
        return jsonify({'models': models})
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Timeout: Mistral ne répond pas'}), 408
    except requests.exceptions.HTTPError as e:
        error_msg = f"Erreur HTTP {e.response.status_code}"
        if e.response.status_code == 401:
            error_msg = 'Clé API Mistral invalide ou manquante'
        elif e.response.status_code == 403:
            error_msg = 'Accès non autorisé à l\'API Mistral'
        elif e.response.status_code == 429:
            error_msg = 'Limite de débit API Mistral atteinte'
        
        # print(f"🔍 DEBUG Mistral Error - {error_msg}: {e.response.text}")
        return jsonify({'error': error_msg}), e.response.status_code
    except requests.exceptions.RequestException as e:
        # print(f"🔍 DEBUG Mistral - Request Error: {str(e)}")
        return jsonify({'error': 'Erreur de connexion à l\'API Mistral'}), 503
    except Exception as e:
        # print(f"🔍 DEBUG Mistral - General Error: {str(e)}")
        return jsonify({'error': f'Erreur lors de la récupération des modèles Mistral: {str(e)}'}), 500

@app.route('/api/settings')
def get_settings():
    active_provider = config.get('active_provider', 'mistral')
    return jsonify({
        'engine': os.getenv('ENGINE', 'ollama'),
        'active_provider': active_provider,
        'mistral_base_url': config.get('mistral_base_url', 'https://api.mistral.ai'),
        'has_mistral_key': bool(config.get('mistral_api_key', '')),
        # Retourner la config du provider actif
        f'{active_provider}_base_url': config.get(f'{active_provider}_base_url', ''),
    })

@app.route('/api/settings/mistral', methods=['POST'])
def update_mistral_settings():
    try:
        data = request.json
        
        # Mettre à jour la config en mémoire
        if 'base_url' in data:
            config['mistral_base_url'] = data['base_url'].rstrip('/')
            
        if 'api_key' in data:
            config['mistral_api_key'] = data['api_key']
        
        # Persister dans le fichier .env
        update_env_file({
            'MISTRAL_BASE_URL': config['mistral_base_url'],
            'MISTRAL_API_KEY': config['mistral_api_key']
        })
            
        return jsonify({
            'success': True,
            'mistral_base_url': config['mistral_base_url'],
            'has_mistral_key': bool(config['mistral_api_key'])
        })
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la mise à jour: {str(e)}'}), 500

@app.route('/api/ai/test', methods=['POST'])
def test_ai_provider():
    """Teste la connexion à un fournisseur IA"""
    try:
        data = request.json
        provider = data.get('provider', 'mistral')
        base_url = data.get('base_url', '').rstrip('/')
        api_key = data.get('api_key', '')
        
        # Configuration des headers selon le fournisseur
        headers = {'Content-Type': 'application/json'}
        if provider != 'ollama':
            headers['Authorization'] = f'Bearer {api_key}'
        
        # Endpoint de test (liste des modèles)
        if provider == 'ollama':
            url = f"{base_url}/api/tags"
        else:
            url = f"{base_url}/v1/models"
        
        print(f"🧪 Test connexion {provider} - URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        # Parser selon le format de réponse
        if provider == 'ollama':
            models = [m['name'] for m in result.get('models', [])]
        else:
            # Format OpenAI-compatible
            models = [m['id'] for m in result.get('data', [])]
        
        print(f"✅ {provider} - {len(models)} modèles trouvés")
        
        return jsonify({'success': True, 'models': models})
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Timeout: le serveur ne répond pas'}), 408
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if hasattr(e, 'response') else 500
        if status == 401:
            return jsonify({'error': 'Clé API invalide ou manquante'}), 401
        elif status == 403:
            return jsonify({'error': 'Accès non autorisé'}), 403
        elif status == 429:
            return jsonify({'error': 'Limite de débit atteinte'}), 429
        else:
            return jsonify({'error': f'Erreur HTTP {status}'}), status
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Impossible de se connecter au serveur'}), 503
    except Exception as e:
        print(f"❌ Erreur test {provider}: {str(e)}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500

@app.route('/api/ai/settings', methods=['POST'])
def save_ai_settings():
    """Sauvegarde les paramètres d'un fournisseur IA"""
    try:
        data = request.json
        provider = data.get('provider', 'mistral')
        base_url = data.get('base_url', '').rstrip('/')
        api_key = data.get('api_key', '')
        
        # Sauvegarder dans la config en mémoire
        config[f'{provider}_base_url'] = base_url
        config[f'{provider}_api_key'] = api_key
        
        # Sauvegarder le provider actif
        config['active_provider'] = provider
        
        # Mettre à jour le fichier .env
        env_updates = {
            f'{provider.upper()}_BASE_URL': base_url,
            f'{provider.upper()}_API_KEY': api_key,
            'ACTIVE_PROVIDER': provider
        }
        
        # Rétro-compatibilité : si c'est Mistral, mettre à jour aussi les anciennes clés
        if provider == 'mistral':
            env_updates['MISTRAL_BASE_URL'] = base_url
            env_updates['MISTRAL_API_KEY'] = api_key
            config['mistral_base_url'] = base_url
            config['mistral_api_key'] = api_key
        
        update_env_file(env_updates)
        
        print(f"✅ Paramètres {provider} sauvegardés")
        
        return jsonify({
            'success': True,
            'provider': provider,
            'base_url': base_url
        })
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {str(e)}")
        return jsonify({'error': f'Erreur lors de la sauvegarde: {str(e)}'}), 500

@app.route('/api/ai/models')
def get_ai_models():
    """Retourne les modèles disponibles pour le provider actif"""
    try:
        provider = config.get('active_provider', 'mistral')
        base_url = config.get(f'{provider}_base_url', '')
        api_key = config.get(f'{provider}_api_key', '')
        
        if not base_url:
            return jsonify({'error': f'Provider {provider} non configuré'}), 400
        
        # Configuration des headers
        headers = {'Content-Type': 'application/json'}
        if provider != 'ollama':
            if not api_key:
                return jsonify({'error': 'API Key manquante'}), 401
            headers['Authorization'] = f'Bearer {api_key}'
        
        # Endpoint selon le provider
        if provider == 'ollama':
            url = f"{base_url}/api/tags"
        else:
            url = f"{base_url}/v1/models"
        
        # print(f"🔍 Chargement modèles {provider} - URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        # Parser selon le format
        if provider == 'ollama':
            models = [m['name'] for m in result.get('models', [])]
        else:
            models = [m['id'] for m in result.get('data', [])]
        
        print(f"✅ {len(models)} modèles {provider} chargés")
        
        return jsonify({'models': models, 'provider': provider})
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Timeout: le serveur ne répond pas'}), 408
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if hasattr(e, 'response') else 500
        if status == 401:
            return jsonify({'error': 'Clé API invalide'}), 401
        elif status == 429:
            return jsonify({'error': 'Limite de débit atteinte'}), 429
        return jsonify({'error': f'Erreur HTTP {status}'}), status
    except requests.exceptions.ConnectionError:
        return jsonify({'error': f'{provider} non disponible'}), 503
    except Exception as e:
        print(f"❌ Erreur chargement modèles {provider}: {str(e)}")
        return jsonify({'error': f'Erreur: {str(e)}'}), 500

@app.route('/api/generate-report', methods=['POST'])
def generate_report():
    """Génère un compte rendu professionnel à partir de notes brutes"""
    try:
        data = request.json
        notes = data.get('notes', '').strip()
        template = data.get('template', 'client_formel')
        meta = data.get('meta', {})
        
        if not notes:
            return jsonify({'error': 'Notes requises'}), 400
        
        if template not in REPORT_PROMPTS:
            return jsonify({'error': f'Template inconnu: {template}'}), 400
        
        # Utiliser le provider actif
        provider = config.get('active_provider', 'mistral')
        base_url = config.get(f'{provider}_base_url', '')
        api_key = config.get(f'{provider}_api_key', '')
        
        if not base_url:
            return jsonify({'error': f'Provider {provider} non configuré'}), 400
        
        if not api_key and provider != 'ollama':
            return jsonify({'error': f'Clé API {provider} manquante dans la configuration'}), 401
        
        # Obtenir la date actuelle pour contexte
        from datetime import datetime
        current_date = datetime.now().strftime("%d/%m/%Y")
        current_year = datetime.now().year
        
        # Construire le prompt utilisateur avec métadonnées
        context_header = f"CONTEXTE TEMPOREL : Nous sommes le {current_date} (année {current_year}).\n\n"
        
        user_prompt = f"Notes de réunion :\n\n{notes}"
        if meta.get('date'):
            user_prompt = f"Date de la réunion : {meta['date']}\n\n" + user_prompt
        if meta.get('participants'):
            user_prompt = f"Participants : {meta['participants']}\n\n" + user_prompt
        
        # Ajouter le contexte temporel au début
        user_prompt = context_header + user_prompt
        
        # Appel API (compatible OpenAI)
        url = f"{base_url}/v1/chat/completions"
        headers = {
            'Authorization': f"Bearer {api_key}",
            'Content-Type': 'application/json'
        }
        
        # Modèles par défaut selon le provider
        default_models = {
            'mistral': 'mistral-medium-latest',
            'openai': 'gpt-4-turbo-preview',
            'deepseek': 'deepseek-chat',
            'gemini': 'gemini-pro'
        }
        model = default_models.get(provider, 'mistral-medium-latest')
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": REPORT_PROMPTS[template]},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 3000
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        print(f" Génération CR via {provider} - Template: {template}, Status: {response.status_code}")
        
        response.raise_for_status()
        
        result = response.json()
        report = result['choices'][0]['message']['content'].strip()
        
        # Nettoyer le rapport : extraire UNIQUEMENT le Markdown pur
        # Cas 1 : Markdown dans un bloc de code ```markdown ... ```
        if '```markdown' in report:
            match = re.search(r'```markdown\s*\n(.*?)\n```', report, re.DOTALL)
            if match:
                report = match.group(1).strip()
        # Cas 2 : Bloc de code générique ``` ... ```
        elif '```' in report:
            match = re.search(r'```\s*\n(.*?)\n```', report, re.DOTALL)
            if match:
                report = match.group(1).strip()
        
        # Cas 3 : Introduction + Markdown (retirer tout avant le premier ##)
        if not report.startswith('#'):
            match = re.search(r'(##\s+.*)', report, re.DOTALL)
            if match:
                report = match.group(1).strip()
        
        print(f"📝 Markdown nettoyé (100 premiers chars): {report[:100]}")
        
        return jsonify({'report': report})
        
    except requests.exceptions.Timeout:
        return jsonify({'error': f'Timeout: {provider} ne répond pas dans les délais'}), 408
    except requests.exceptions.HTTPError as e:
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 401:
                return jsonify({'error': f'Clé API {provider} invalide ou expirée'}), 401
            elif e.response.status_code == 429:
                return jsonify({'error': f'Limite de débit {provider} atteinte. Réessayez dans quelques instants.'}), 429
            else:
                return jsonify({'error': f'Erreur {provider}: {e.response.status_code}'}), 503
        return jsonify({'error': f'Erreur HTTP {provider}: {str(e)}'}), 503
    except KeyError as e:
        return jsonify({'error': f'Réponse {provider} malformée: {str(e)}'}), 502
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la génération du compte rendu: {str(e)}'}), 500

@app.route('/api/generate-pdf', methods=['POST'])
def generate_pdf():
    """Génère un PDF professionnel à partir du projet complet avec ReportLab"""
    try:
        data = request.json
        project = data.get('project', {})
        
        # Extraire les données du projet
        diagram = project.get('diagram', {})
        report_data = project.get('report', {})
        images = project.get('images', [])
        pdf_config = project.get('pdfConfig', {})
        
        # Créer un buffer en mémoire
        pdf_buffer = io.BytesIO()
        
        # Fonction de pied de page
        def footer_canvas(canvas, doc):
            """Ajoute un footer sur chaque page avec mentions légales"""
            canvas.saveState()
            
            # Mentions légales personnalisées ou par défaut
            footer_text = pdf_config.get('legal', 'ENOVACOM - Tous droits réservés')
            
            # Style du footer
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors.HexColor('#666666'))  # Gris discret
            
            # Position du footer (bas de page avec marge)
            page_width = A4[0]
            footer_y = 15*mm  # 15mm du bas de la page
            
            # Centrer le footer
            text_width = canvas.stringWidth(footer_text, 'Helvetica', 8)
            canvas.drawString((page_width - text_width) / 2, footer_y, footer_text)
            
            # Optionnel: Ajouter numéro de page
            if pdf_config.get('page_numbers', True):  # Par défaut activé
                page_num = f"Page {doc.page}"
                canvas.setFont('Helvetica', 8)
                canvas.setFillColor(colors.HexColor('#999999'))  # Plus clair pour le numéro
                # Numéro de page en bas à droite
                right_margin = pdf_config.get('theme', {}).get('margins', {}).get('right', 18) * mm
                canvas.drawRightString(page_width - right_margin, footer_y, page_num)
            
            canvas.restoreState()
        
        # Créer le document PDF avec pied de page
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            rightMargin=pdf_config.get('theme', {}).get('margins', {}).get('right', 18) * mm,
            leftMargin=pdf_config.get('theme', {}).get('margins', {}).get('left', 18) * mm,
            topMargin=pdf_config.get('theme', {}).get('margins', {}).get('top', 24) * mm,
            bottomMargin=pdf_config.get('theme', {}).get('margins', {}).get('bottom', 28) * mm,
            onFirstPage=footer_canvas,
            onLaterPages=footer_canvas
        )
        # Largeur disponible pour les tableaux/images (toujours définie)
        page_width = A4[0]
        left_margin = pdf_config.get('theme', {}).get('margins', {}).get('left', 18) * mm
        right_margin = pdf_config.get('theme', {}).get('margins', {}).get('right', 18) * mm
        available_width = page_width - left_margin - right_margin
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor(pdf_config.get('theme', {}).get('primary', '#0C4A45')),
            spaceAfter=12,
            alignment=TA_CENTER  # Centrer le titre
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor(pdf_config.get('theme', {}).get('primary', '#0C4A45')),
            spaceAfter=6,
            spaceBefore=12
        )
        # Style normal - Taille raisonnable pour PDF
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            spaceAfter=8,
            spaceBefore=0,
            fontName='Helvetica'
        )
        # Style bloc de code préformaté (global)
        pre_style = ParagraphStyle(
            'Preformatted',
            parent=styles['Code'],
            fontSize=9,
            leading=11,
            fontName='Courier',
            textColor=colors.HexColor('#1F2937'),
            backColor=colors.HexColor('#F3F4F6'),
            leftIndent=6,
            rightIndent=6,
        )
        
        # Contenu du PDF
        story = []
        
        # Logo en en-tête (si présent)
        if pdf_config.get('logo'):
            try:
                logo_data = pdf_config.get('logo')
                if logo_data.startswith('data:image'):
                    # Décoder le logo base64
                    logo_data = logo_data.split(',')[1]
                    logo_bytes = base64.b64decode(logo_data)
                    logo_buffer = io.BytesIO(logo_bytes)
                    
                    # Calculer la largeur disponible (A4 - marges)
                    page_width = A4[0]
                    left_margin = pdf_config.get('theme', {}).get('margins', {}).get('left', 18) * mm
                    right_margin = pdf_config.get('theme', {}).get('margins', {}).get('right', 18) * mm
                    available_width = page_width - left_margin - right_margin
                    
                    # Ajouter le logo au PDF (TOUTE la largeur disponible)
                    logo_img = RLImage(logo_buffer, width=available_width, height=60*mm, kind='proportional')
                    story.append(logo_img)
                    story.append(Spacer(1, 20))
            except Exception as e:
                print(f"⚠️ Erreur ajout logo: {e}")
        
        # En-tête
        story.append(Paragraph(pdf_config.get('title', 'Document'), title_style))
        if pdf_config.get('client'):
            story.append(Paragraph(f"Client: {pdf_config.get('client')}", normal_style))
        if pdf_config.get('subtitle'):
            story.append(Paragraph(f"{pdf_config.get('subtitle')}", normal_style))
        story.append(Spacer(1, 12))
        
        # Ordre des blocs
        order = pdf_config.get('order', ['diagram', 'report', 'images'])
        
        for block in order:
            if block == 'diagram':
                # DIAGRAMME SUPPRIMÉ - L'utilisateur peut l'ajouter manuellement via les images
                print("📊 Diagramme ignoré - Utilisez la section Images pour ajouter le diagramme manuellement")
                pass
            
            elif block == 'report' and report_data.get('generated'):
                # Rendu propre du HTML de l'éditeur dans le PDF
                html_input = report_data.get('generated', '')
                
                # DEBUG MASSIF: Tracer complètement le HTML
                print(f"\n{'='*80}")
                print(f"=== HTML BRUT DE QUILL (TOTAL: {len(html_input)} chars) ===")
                print(f"{'='*80}")
                print(html_input[:1000])  # Premiers 1000 chars
                print(f"\n=== RECHERCHE DE CARRÉS DANS LE HTML BRUT ===")
                import re
                carres_detectes = []
                if '■' in html_input:
                    count = html_input.count('■')
                    carres_detectes.append(f"■ (U+25A0): {count} occurrences")
                    print(f"❌ CARRÉ ■ trouvé {count} fois dans le HTML brut")
                if '▪' in html_input:
                    count = html_input.count('▪')
                    carres_detectes.append(f"▪ (U+25AA): {count} occurrences")
                    print(f"❌ CARRÉ ▪ trouvé {count} fois dans le HTML brut")
                # Chercher d'autres carrés
                for char in ['◼', '◾', '▮', '◆', '⬛', '▫', '□', '▢', '⬜']:
                    if char in html_input:
                        count = html_input.count(char)
                        carres_detectes.append(f"{char} (U+{ord(char):04X}): {count} occurrences")
                        print(f"❌ CARRÉ {char} trouvé {count} fois")
                
                if carres_detectes:
                    print(f"\n⚠️ TOTAL: {len(carres_detectes)} types de carrés détectés")
                    for info in carres_detectes:
                        print(f"  - {info}")
                else:
                    print(f"\n✅ AUCUN carré détecté dans le HTML brut")
                
                # NETTOYAGE ULTRA AGRESSIF - Éliminer TOUS les carrés
                # Carrés Unicode (pleins)
                html_input = html_input.replace('■', '')  # SUPPRIMER complètement
                html_input = html_input.replace('▪', '')  # SUPPRIMER complètement
                html_input = html_input.replace('◼', '')  # SUPPRIMER complètement
                html_input = html_input.replace('◾', '')  # SUPPRIMER complètement
                html_input = html_input.replace('▮', '')  # SUPPRIMER complètement
                html_input = html_input.replace('◆', '')  # SUPPRIMER complètement
                html_input = html_input.replace('⬛', '')  # SUPPRIMER complètement
                html_input = html_input.replace('⬜', '')  # SUPPRIMER complètement
                html_input = html_input.replace('▫', '')  # SUPPRIMER complètement
                html_input = html_input.replace('□', '')  # SUPPRIMER complètement
                html_input = html_input.replace('▢', '')  # SUPPRIMER complètement
                # HTML entities (tous les formats)
                html_input = html_input.replace('&#9632;', '')  # SUPPRIMER
                html_input = html_input.replace('&#x25A0;', '')  # SUPPRIMER
                html_input = html_input.replace('&#9642;', '')  # SUPPRIMER
                html_input = html_input.replace('&#x25AA;', '')  # SUPPRIMER
                html_input = html_input.replace('&#9724;', '')  # SUPPRIMER
                html_input = html_input.replace('&nbsp;■', '')  # SUPPRIMER
                # Regex pour attraper tout ce qui reste
                html_input = re.sub(r'[■▪◼◾▮◆⬛▫□▢⬜]', '', html_input)
                # Nettoyer les balises <li> avec data-list
                html_input = re.sub(r'<li[^>]*data-list=["\']bullet["\'][^>]*>', '<li>', html_input)
                html_input = re.sub(r'<li[^>]*data-list=["\']ordered["\'][^>]*>', '<li>', html_input)
                
                print(f"\n=== HTML APRÈS NETTOYAGE (premiers 500 chars) ===")
                print(html_input[:500])
                
                if BS4_SUPPORT:
                    try:
                        soup = BeautifulSoup(html_input, 'html.parser')

                        # Styles de titres - Tailles proportionnées pour PDF
                        primary = colors.HexColor(pdf_config.get('theme', {}).get('primary', '#0C4A45'))
                        h1_style = ParagraphStyle('H1', parent=styles['Heading1'], textColor=primary, fontSize=18, spaceBefore=12, spaceAfter=10, leading=22, fontName='Helvetica-Bold')
                        h2_style = ParagraphStyle('H2', parent=styles['Heading2'], textColor=primary, fontSize=14, spaceBefore=10, spaceAfter=8, leading=17, fontName='Helvetica-Bold')
                        h3_style = ParagraphStyle('H3', parent=styles['Heading3'], textColor=primary, fontSize=12, spaceBefore=8, spaceAfter=6, leading=15, fontName='Helvetica-Bold')
                        h4_style = ParagraphStyle('H4', parent=styles['Heading4'], textColor=colors.HexColor('#374151'), fontSize=11, spaceBefore=6, spaceAfter=5, leading=14, fontName='Helvetica-Bold')
                        h5_style = ParagraphStyle('H5', parent=styles['Heading5'], textColor=colors.HexColor('#4B5563'), fontSize=10, spaceBefore=5, spaceAfter=4, leading=13, fontName='Helvetica-Bold')
                        h6_style = ParagraphStyle('H6', parent=styles['Heading6'], textColor=colors.HexColor('#6B7280'), fontSize=9, spaceBefore=4, spaceAfter=3, leading=11, fontName='Helvetica-Bold')
                        
                        # Style pour le code
                        code_style = ParagraphStyle(
                            'Code',
                            parent=styles['Code'],
                            fontSize=9,
                            fontName='Courier',
                            textColor=colors.HexColor('#1F2937'),
                            backColor=colors.HexColor('#F3F4F6'),
                            leftIndent=10,
                            rightIndent=10,
                            spaceBefore=4,
                            spaceAfter=4
                        )

                        def html_to_reportlab(element, preserve_spaces=False):
                            """Convertit un élément HTML en texte avec balises ReportLab"""
                            if isinstance(element, str):
                                # Nettoyer les carrés
                                text = clean_squares(str(element))
                                if preserve_spaces:
                                    return text
                                return text
                            
                            text = ''
                            for child in element.children:
                                if child.name == 'strong' or child.name == 'b':
                                    text += f'<b>{html_to_reportlab(child, preserve_spaces)}</b>'
                                elif child.name == 'em' or child.name == 'i':
                                    text += f'<i>{html_to_reportlab(child, preserve_spaces)}</i>'
                                elif child.name == 'u':
                                    text += f'<u>{html_to_reportlab(child, preserve_spaces)}</u>'
                                elif child.name == 'code':
                                    # Code inline
                                    text += f'<font name="Courier" size="9" color="#1F2937">{html_to_reportlab(child, True)}</font>'
                                elif child.name == 'br':
                                    text += '<br/>'
                                elif child.name == 'p':
                                    # Paragraphe imbriqué : ajouter un saut de ligne
                                    inner = html_to_reportlab(child, preserve_spaces)
                                    if inner.strip():
                                        text += inner + '<br/><br/>'
                                elif child.name == 'a':
                                    href = child.get('href', '')
                                    text += f'<a href="{href}">{html_to_reportlab(child, preserve_spaces)}</a>'
                                elif child.name is None:
                                    # Texte brut
                                    text += str(child)
                                else:
                                    # Autres balises : récursion
                                    text += html_to_reportlab(child, preserve_spaces)
                            # Nettoyer les carrés dans le texte final
                            return clean_squares(text)

                        def add_paragraph(element, style=normal_style, add_spacer=True):
                            """Ajoute un paragraphe avec mise en forme préservée"""
                            if isinstance(element, str):
                                t = clean_squares(element.strip())
                            else:
                                t = clean_squares(html_to_reportlab(element).strip())
                            if t:
                                story.append(Paragraph(t, style))
                                # Espace après paragraphes normaux
                                if add_spacer and style == normal_style:
                                    story.append(Spacer(1, 6))

                        def render_list(list_tag, ordered=False, indent_level=0):
                            """Rend une liste avec support des listes imbriquées"""
                            counter = 1
                            
                            # Style unique pour tous les items de liste
                            # On n'utilise PAS bulletText, on insère le bullet dans le texte
                            list_style = ParagraphStyle(
                                f'ListItem_{indent_level}',
                                parent=normal_style,
                                leftIndent=20 * (indent_level + 1),
                                spaceBefore=2,
                                spaceAfter=2,
                                fontSize=11,
                                leading=16,
                                fontName='Helvetica'  # Police Unicode complète
                            )
                            
                            for li in list_tag.find_all('li', recursive=False):
                                # Extraire le texte et les sous-listes
                                li_copy = li.__copy__()
                                
                                # Retirer les sous-listes pour ne garder que le texte direct
                                for sub_list in li_copy.find_all(['ul', 'ol']):
                                    sub_list.decompose()
                                
                                # Texte de l'item
                                raw_text = html_to_reportlab(li_copy).strip()
                                
                                # DEBUG: Avant nettoyage
                                print(f"\n--- ITEM DE LISTE (niveau {indent_level}) ---")
                                print(f"AVANT clean_squares: {repr(raw_text[:150])}")
                                
                                # NETTOYER AGRESSIVEMENT les carrés
                                text = clean_squares(raw_text)
                                
                                # DEBUG: Après nettoyage
                                print(f"APRÈS clean_squares: {repr(text[:150])}")
                                
                                # Vérification finale
                                if '■' in text or '▪' in text:
                                    print(f"\n❌❌❌ CARRÉ ENCORE PRÉSENT APRÈS NETTOYAGE!")
                                    print(f"Texte: {repr(text[:100])}")
                                    # Montrer le code Unicode de chaque caractère suspect
                                    for i, char in enumerate(text[:50]):
                                        if ord(char) >= 0x2580:
                                            print(f"  Position {i}: '{char}' = U+{ord(char):04X}")
                                
                                if text:
                                    # Bullet selon le type et le niveau
                                    if ordered:
                                        bullet = f'{counter}. '
                                        counter += 1
                                    else:
                                        # FORCER les bullets ronds (ignorer le HTML)
                                        bullets = ['•', '◦', '–', '−']
                                        bullet = bullets[min(indent_level, len(bullets)-1)]
                                    
                                    # SOLUTION SIMPLE: Utiliser uniquement des tirets pour tous les niveaux
                                    # Plus élégant et lisible que les "o"
                                    if ordered:
                                        ascii_bullet = bullet  # Les numéros sont OK
                                    else:
                                        # Tiret simple pour tous les niveaux (plus propre)
                                        ascii_bullet = '-'
                                    
                                    final_text = f'{ascii_bullet} {text}'
                                    
                                    print(f"Bullet ASCII utilisé: {repr(ascii_bullet)}")
                                    print(f"Texte final envoyé au PDF: {repr(final_text[:100])}")
                                    
                                    # Ajouter l'item avec le bullet ASCII
                                    story.append(Paragraph(final_text, list_style))
                                
                                # Gérer les sous-listes
                                for sub_list in li.find_all(['ul', 'ol'], recursive=False):
                                    is_ordered = sub_list.name == 'ol'
                                    render_list(sub_list, ordered=is_ordered, indent_level=indent_level + 1)

                        def render_table(table_tag):
                            rows = []
                            
                            # Style pour les cellules de tableau
                            cell_style = ParagraphStyle(
                                'TableCell',
                                parent=normal_style,
                                fontSize=10,
                                leading=14,
                                spaceAfter=0,
                                spaceBefore=0
                            )
                            
                            # Style spécial pour en-tête (texte BLANC)
                            header_cell_style = ParagraphStyle(
                                'TableHeaderCell',
                                parent=normal_style,
                                fontSize=10,
                                leading=14,
                                spaceAfter=0,
                                spaceBefore=0,
                                textColor=colors.white,
                                fontName='Helvetica-Bold'
                            )
                            
                            # En-tête (thead uniquement)
                            thead = table_tag.find('thead')
                            if thead:
                                for tr in thead.find_all('tr'):
                                    head_row = [Paragraph(f'<font color="white"><b>{clean_squares(th.get_text(" ", strip=True))}</b></font>', header_cell_style) for th in tr.find_all(['th', 'td'])]
                                    if head_row:
                                        rows.append(head_row)
                            
                            # Corps (tbody ou tr hors thead)
                            tbody = table_tag.find('tbody')
                            if tbody:
                                # Si tbody existe, chercher dedans
                                for tr in tbody.find_all('tr'):
                                    cells = [Paragraph(clean_squares(td.get_text(" ", strip=True)), cell_style) for td in tr.find_all(['td', 'th'])]
                                    if cells:
                                        rows.append(cells)
                            else:
                                # Sinon, chercher les tr qui ne sont PAS dans thead
                                for tr in table_tag.find_all('tr', recursive=False):
                                    # Ignorer si ce tr est dans thead
                                    if thead and tr.find_parent('thead'):
                                        continue
                                    cells = [Paragraph(clean_squares(td.get_text(" ", strip=True)), cell_style) for td in tr.find_all(['td', 'th'])]
                                    if cells:
                                        rows.append(cells)

                            if rows:
                                # Normaliser le nombre de colonnes (évite erreurs ReportLab)
                                num_cols = max(len(r) for r in rows)
                                # Compléter les lignes courtes avec cellules vides
                                for idx, r in enumerate(rows):
                                    if len(r) < num_cols:
                                        r += [Paragraph('', cell_style)] * (num_cols - len(r))
                                        rows[idx] = r
                                # Largeurs de colonnes
                                col_widths = [available_width / num_cols] * num_cols
                                # Créer le tableau
                                tbl = Table(rows, colWidths=col_widths, hAlign='LEFT', repeatRows=1, splitByRow=True)
                                # Styles
                                header_bg = colors.HexColor('#0f5650')
                                grid_color = colors.HexColor('#0C4A45')
                                style_cmds = [
                                    ('GRID', (0,0), (-1,-1), 0.75, grid_color),
                                    ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
                                    ('FONTSIZE', (0,0), (-1,-1), 9),
                                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                                    ('LEFTPADDING', (0,0), (-1,-1), 6),
                                    ('RIGHTPADDING', (0,0), (-1,-1), 6),
                                    ('TOPPADDING', (0,0), (-1,-1), 4),
                                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                                ]
                                if len(rows) > 0:
                                    style_cmds += [
                                        ('BACKGROUND', (0,0), (-1,0), header_bg),
                                        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                                        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                                    ]
                                for r in range(1, len(rows)):
                                    if r % 2 == 0:
                                        style_cmds.append(('BACKGROUND', (0,r), (-1,r), colors.HexColor('#F9FAFB')))
                                tbl.setStyle(TableStyle(style_cmds))
                                story.append(tbl)
                                story.append(Spacer(1, 10))

                        root = soup.body if soup.body else soup
                        prev_was_heading = False
                        
                        for el in getattr(root, 'children', []):
                            name = getattr(el, 'name', None)
                            if not name:
                                text = str(el).strip()
                                if text:
                                    add_paragraph(text)
                                continue
                            
                            name = name.lower()
                            
                            # Gérer les paragraphes vides (sauts de ligne)
                            if name in ['p', 'div']:
                                content = html_to_reportlab(el).strip()
                                if not content or content == '<br/>':
                                    # Paragraphe vide = saut de ligne plus marqué
                                    story.append(Spacer(1, 12))
                                    continue
                            
                            if name == 'h1':
                                add_paragraph(el, h1_style, add_spacer=False)
                                prev_was_heading = True
                            elif name == 'h2':
                                add_paragraph(el, h2_style, add_spacer=False)
                                prev_was_heading = True
                            elif name == 'h3':
                                add_paragraph(el, h3_style, add_spacer=False)
                                prev_was_heading = True
                            elif name == 'h4':
                                add_paragraph(el, h4_style, add_spacer=False)
                                prev_was_heading = True
                            elif name == 'h5':
                                add_paragraph(el, h5_style, add_spacer=False)
                                prev_was_heading = True
                            elif name == 'h6':
                                add_paragraph(el, h6_style, add_spacer=False)
                                prev_was_heading = True
                            elif name in ['p', 'div']:
                                add_paragraph(el, normal_style)
                                prev_was_heading = False
                            elif name == 'ul':
                                render_list(el, ordered=False)
                                story.append(Spacer(1, 8))
                                prev_was_heading = False
                            elif name == 'ol':
                                render_list(el, ordered=True)
                                story.append(Spacer(1, 8))
                                prev_was_heading = False
                            elif name == 'table':
                                render_table(el)
                                prev_was_heading = False
                            elif name == 'br':
                                # Saut de ligne explicite
                                story.append(Spacer(1, 12))
                            elif name == 'pre':
                                # Bloc de code préformaté
                                code_text = el.get_text()
                                if code_text.strip():
                                    story.append(Paragraph(code_text, code_style))
                                    story.append(Spacer(1, 4))
                            elif name == 'blockquote':
                                # Citation
                                quote_text = html_to_reportlab(el)
                                if quote_text.strip():
                                    quote_style = ParagraphStyle(
                                        'Quote',
                                        parent=normal_style,
                                        leftIndent=20,
                                        rightIndent=20,
                                        textColor=colors.HexColor('#6B7280'),
                                        borderColor=colors.HexColor('#0C4A45'),
                                        borderWidth=2,
                                        borderPadding=8,
                                        spaceBefore=6,
                                        spaceAfter=6
                                    )
                                    story.append(Paragraph(quote_text, quote_style))
                                    story.append(Spacer(1, 4))
                        
                    except Exception as parse_e:
                        print(f"⚠️ Parser HTML échoué: {parse_e}")
                        story.append(Paragraph(BeautifulSoup(html_input, 'html.parser').get_text('\n'), normal_style))
                else:
                    # Fallback sans bs4: texte brut
                    story.append(Paragraph(re.sub('<[^<]+?>', '', html_input), normal_style))
                story.append(Spacer(1, 12))
            elif block == 'images' and images:
                # Ajouter les images au PDF avec titres comme des vrais titres H2
                print(f"🖼️ Section Images: {len(images)} image(s) détectée(s)")
                for i, img_data in enumerate(images):
                    print(f"  Image {i+1}: {list(img_data.keys())}")
                    # Debug détaillé des champs
                    for key in ['title', 'caption', 'name', 'filename']:
                        if key in img_data:
                            print(f"    {key}: '{img_data[key]}'")
                    try:
                        # Support des deux formats possibles
                        img_base64 = img_data.get('data', '') or img_data.get('dataUrl', '')
                        # Priorité au titre personnalisé de l'IHM, puis caption, puis nom de fichier
                        img_name = img_data.get('title', '') or img_data.get('caption', '') or img_data.get('name', 'Image')
                        
                        print(f"    - Base64: {'OUI' if img_base64 else 'NON'} ({len(img_base64) if img_base64 else 0} chars)")
                        print(f"    - Titre final choisi: '{img_name}'")
                        
                        if img_base64 and img_base64.startswith('data:image/'):
                            # TITRE DE L'IMAGE EN GROS AU-DESSUS (H2)
                            image_title_style = ParagraphStyle(
                                'ImageTitle',
                                parent=h2_style,  # Style H2 pour un gros titre
                                alignment=TA_LEFT,
                                spaceBefore=20,
                                spaceAfter=12,
                                fontSize=16,
                                fontName='Helvetica-Bold',
                                textColor=primary
                            )
                            title_paragraph = Paragraph(img_name, image_title_style)
                            
                            # Extraire les données base64
                            img_bytes = base64.b64decode(img_base64.split(',')[1])
                            img_buffer = io.BytesIO(img_bytes)
                            
                            # Calculer la largeur disponible
                            page_width = A4[0]
                            left_margin = pdf_config.get('theme', {}).get('margins', {}).get('left', 18) * mm
                            right_margin = pdf_config.get('theme', {}).get('margins', {}).get('right', 18) * mm
                            available_width = page_width - left_margin - right_margin
                            
                            # Créer l'image avec gestion intelligente de la taille
                            try:
                                from reportlab.lib.utils import ImageReader
                                reader = ImageReader(img_buffer)
                                iw, ih = reader.getSize()
                                if iw and ih:
                                    # Calculer la hauteur pour préserver le ratio
                                    target_width = float(available_width)
                                    target_height = target_width * (ih / float(iw))
                                    
                                    # LOGIQUE ANTI-GROS-BLANC:
                                    # Estimer l'espace disponible sur la page (approximatif)
                                    # Page A4 = 297mm, marges = ~36mm, titre = ~20mm
                                    available_page_height = 240*mm  # Espace réaliste disponible
                                    title_height = 30*mm  # Hauteur approximative du titre + espaces
                                    max_image_height = available_page_height - title_height
                                    
                                    # Si l'image est trop haute, la réduire pour éviter le saut de page
                                    if target_height > max_image_height:
                                        print(f"⚠️ Image trop haute ({target_height/mm:.0f}mm), réduction pour éviter saut de page")
                                        target_height = max_image_height
                                        target_width = target_height * (iw / float(ih))
                                        print(f"✅ Image réduite à {target_height/mm:.0f}mm de hauteur")
                                    
                                    # Limiter aussi à 120mm pour éviter les images géantes
                                    if target_height > 120*mm:
                                        target_height = 120*mm
                                        target_width = target_height * (iw / float(ih))
                                    
                                    img_buffer.seek(0)
                                    img = RLImage(img_buffer, width=target_width, height=target_height)
                                else:
                                    img_buffer.seek(0)
                                    img = RLImage(img_buffer, width=available_width)
                            except Exception:
                                img_buffer.seek(0)
                                img = RLImage(img_buffer, width=available_width)
                            
                            img.hAlign = 'LEFT'
                            
                            # GARDER TITRE + IMAGE ENSEMBLE sur la même page
                            image_block = KeepTogether([
                                title_paragraph,
                                img,
                                Spacer(1, 20)  # Espace après l'image
                            ])
                            story.append(image_block)
                            print(f"✅ Image ajoutée avec GROS titre (KeepTogether): {img_name}")
                    except Exception as e:
                        print(f"❌ Erreur ajout image {img_data.get('name', 'inconnue')}: {e}")
                        # Ajouter quand même le titre même si l'image échoue
                        img_name = img_data.get('title', '') or img_data.get('caption', '') or img_data.get('name', 'Image inconnue')
                        image_title_style = ParagraphStyle(
                            'ImageTitle', 
                            parent=h2_style, 
                            alignment=TA_LEFT, 
                            spaceBefore=20, 
                            spaceAfter=12,
                            fontSize=16,
                            fontName='Helvetica-Bold',
                            textColor=primary
                        )
                        # Même en cas d'erreur, garder titre + message ensemble
                        error_block = KeepTogether([
                            Paragraph(img_name, image_title_style),
                            Paragraph(f"[Image non disponible: {img_name}]", normal_style),
                            Spacer(1, 20)
                        ])
                        story.append(error_block)
        
        # Les mentions légales sont maintenant gérées par footer_canvas (pied de page sur chaque page)
        # Plus besoin de les ajouter ici dans le story
        
        # Watermark (si activé)
        if pdf_config.get('watermark', False):
            story.append(Spacer(1, 12))
            watermark_style = ParagraphStyle(
                'Watermark',
                parent=normal_style,
                fontSize=10,
                textColor=colors.HexColor('#DC2626'),
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            story.append(Paragraph('⚠️ CONFIDENTIEL', watermark_style))
        
        # Construire le PDF avec pied de page sur chaque page
        doc.build(story, onFirstPage=footer_canvas, onLaterPages=footer_canvas)
        
        pdf_buffer.seek(0)
        
        # Nom du fichier
        filename = f"{pdf_config.get('title', 'document').replace(' ', '_')}.pdf"
        
        print(f"📄 PDF généré avec ReportLab: {filename}")
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"❌ Erreur génération PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Erreur lors de la génération du PDF: {str(e)}'}), 500

@app.route('/api/generate-docx', methods=['POST'])
def generate_docx():
    """Génère un document DOCX éditable avec mise en page identique au PDF"""
    try:
        if not DOCX_SUPPORT:
            return jsonify({'error': 'python-docx non installé. Installez-le avec: pip install python-docx'}), 500
        
        data = request.json
        project = data.get('project', {})
        
        # Extraire les données du projet
        report_data = project.get('report', {})
        images = project.get('images', [])
        pdf_config = project.get('pdfConfig', {})
        
        # Créer le document
        doc = Document()
        
        # Configuration des marges
        sections = doc.sections
        for section in sections:
            section.top_margin = Mm(pdf_config.get('theme', {}).get('margins', {}).get('top', 24))
            section.bottom_margin = Mm(pdf_config.get('theme', {}).get('margins', {}).get('bottom', 28))
            section.left_margin = Mm(pdf_config.get('theme', {}).get('margins', {}).get('left', 18))
            section.right_margin = Mm(pdf_config.get('theme', {}).get('margins', {}).get('right', 18))
        
        # Fonction helper pour convertir couleur hex en RGBColor
        def hex_to_rgb(hex_color):
            """Convertit #RRGGBB en RGBColor"""
            hex_color = hex_color.lstrip('#')
            return RGBColor(int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))
        
        primary_color = hex_to_rgb(pdf_config.get('theme', {}).get('primary', '#0C4A45'))
        primary_hex = pdf_config.get('theme', {}).get('primary', '#0C4A45').lstrip('#').upper()
        
        # Ajouter le logo si présent (TOUTE la largeur comme le PDF)
        if pdf_config.get('logo'):
            try:
                logo_data = pdf_config.get('logo')
                if logo_data.startswith('data:image'):
                    logo_bytes = base64.b64decode(logo_data.split(',')[1])
                    logo_buffer = io.BytesIO(logo_bytes)
                    
                    # Calculer la largeur disponible (même logique que PDF)
                    # Page A4 = 210mm, convertir en inches
                    page_width_mm = 210
                    left_margin_mm = pdf_config.get('theme', {}).get('margins', {}).get('left', 18)
                    right_margin_mm = pdf_config.get('theme', {}).get('margins', {}).get('right', 18)
                    available_width_mm = page_width_mm - left_margin_mm - right_margin_mm
                    available_width_inches = available_width_mm / 25.4  # Conversion mm -> inches
                    
                    doc.add_picture(logo_buffer, width=Inches(available_width_inches))
                    last_paragraph = doc.paragraphs[-1]
                    last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            except Exception as e:
                print(f"⚠️ Erreur ajout logo DOCX: {e}")
        
        # En-tête du document (CENTRÉ comme le PDF)
        title = doc.add_heading(pdf_config.get('title', 'Document'), level=1)
        title.runs[0].font.color.rgb = primary_color
        title.runs[0].font.size = Pt(18)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER  # Centrer le titre
        
        if pdf_config.get('client'):
            p = doc.add_paragraph(f"Client: {pdf_config.get('client')}")
            p.runs[0].font.size = Pt(11)
        
        if pdf_config.get('subtitle'):
            p = doc.add_paragraph(pdf_config.get('subtitle'))
            p.runs[0].font.size = Pt(11)
            p.runs[0].font.color.rgb = RGBColor(107, 114, 128)
        
        doc.add_paragraph()  # Espace
        
        # Ordre des blocs
        order = pdf_config.get('order', ['diagram', 'report', 'images'])
        
        for block in order:
            if block == 'report' and report_data.get('generated'):
                html_input = report_data.get('generated', '')
                
                # Nettoyer les carrés Unicode (même logique que PDF)
                html_input = html_input.replace('■', '').replace('▪', '').replace('◼', '')
                html_input = html_input.replace('◾', '').replace('▮', '').replace('◆', '')
                html_input = html_input.replace('⬛', '').replace('⬜', '').replace('▫', '')
                html_input = html_input.replace('□', '').replace('▢', '')
                html_input = re.sub(r'[■▪◼◾▮◆⬛▫□▢⬜]', '', html_input)
                html_input = re.sub(r'<li[^>]*data-list=["\']bullet["\'][^>]*>', '<li>', html_input)
                html_input = re.sub(r'<li[^>]*data-list=["\']ordered["\'][^>]*>', '<li>', html_input)
                
                if BS4_SUPPORT:
                    try:
                        soup = BeautifulSoup(html_input, 'html.parser')
                        
                        def clean_text(text):
                            """Nettoie le texte des carrés et symboles"""
                            return clean_squares(text) if text else ''
                        
                        def process_run(run, element):
                            """Applique le formatage (gras, italique, etc.) à un run"""
                            if element.name == 'strong' or element.name == 'b':
                                run.bold = True
                            elif element.name == 'em' or element.name == 'i':
                                run.italic = True
                            elif element.name == 'u':
                                run.underline = True
                            elif element.name == 'code':
                                run.font.name = 'Courier New'
                                run.font.size = Pt(9)
                                run.font.color.rgb = RGBColor(31, 41, 55)
                        
                        def add_formatted_text(paragraph, element):
                            """Ajoute du texte formaté à un paragraphe"""
                            if isinstance(element, str):
                                text = clean_text(str(element))
                                if text:
                                    paragraph.add_run(text)
                                return
                            
                            for child in element.children:
                                if child.name in ['strong', 'b', 'em', 'i', 'u', 'code']:
                                    text = clean_text(child.get_text())
                                    if text:
                                        run = paragraph.add_run(text)
                                        process_run(run, child)
                                elif child.name == 'br':
                                    paragraph.add_run('\n')
                                elif child.name == 'a':
                                    text = clean_text(child.get_text())
                                    if text:
                                        run = paragraph.add_run(text)
                                        run.font.color.rgb = RGBColor(37, 99, 235)
                                        run.underline = True
                                elif child.name is None:
                                    text = clean_text(str(child))
                                    if text:
                                        paragraph.add_run(text)
                                else:
                                    add_formatted_text(paragraph, child)
                        
                        def add_list_item(text, level=0, ordered=False, counter=1):
                            """Ajoute un élément de liste avec indentation"""
                            p = doc.add_paragraph(style='List Number' if ordered else 'List Bullet')
                            p.paragraph_format.left_indent = Inches(0.5 * (level + 1))
                            p.paragraph_format.space_after = Pt(4)
                            
                            # Nettoyer le texte
                            text = clean_text(text)
                            if text:
                                p.add_run(text)
                            return p
                        
                        def process_list(list_element, level=0, ordered=False):
                            """Traite une liste (ul ou ol) avec support des listes imbriquées"""
                            counter = 1
                            for li in list_element.find_all('li', recursive=False):
                                # Extraire le texte direct (sans sous-listes)
                                li_copy = li.__copy__()
                                for sub_list in li_copy.find_all(['ul', 'ol']):
                                    sub_list.decompose()
                                
                                text = clean_text(li_copy.get_text(strip=True))
                                if text:
                                    add_list_item(text, level, ordered, counter)
                                    if ordered:
                                        counter += 1
                                
                                # Traiter les sous-listes
                                for sub_list in li.find_all(['ul', 'ol'], recursive=False):
                                    is_ordered = sub_list.name == 'ol'
                                    process_list(sub_list, level + 1, is_ordered)
                        
                        def process_table(table_element):
                            """Traite un tableau HTML"""
                            rows_data = []
                            has_explicit_thead = False
                            
                            # Debug tableau HTML (désactivé en production)
                            # print(f"\n🔍 DEBUG TABLEAU HTML:")
                            # print(f"   Structure: {table_element.name}")
                            
                            # En-tête explicite
                            thead = table_element.find('thead')
                            if thead:
                                has_explicit_thead = True
                                # print(f"   ✅ <thead> trouvé")
                                for tr in thead.find_all('tr'):
                                    cells = tr.find_all(['th', 'td'])
                                    # print(f"   Ligne thead: {len(cells)} cellules")
                                    row = [clean_text(th.get_text(separator=' ', strip=True)) for th in cells]
                                    # print(f"   Contenu: {row}")
                                    if row:
                                        rows_data.append(row)
                            else:
                                pass  # print(f"   ❌ Pas de <thead>")
                            
                            # Corps
                            tbody = table_element.find('tbody')
                            if tbody:
                                # print(f"   ✅ <tbody> trouvé")
                                for idx, tr in enumerate(tbody.find_all('tr')):
                                    cells = tr.find_all(['th', 'td'])
                                    # print(f"   Ligne {idx}: {len(cells)} cellules")
                                    row = [clean_text(td.get_text(separator=' ', strip=True)) for td in cells]
                                    # if idx < 2:
                                    #     print(f"   Contenu ligne 0: {row}")
                                    if row:
                                        rows_data.append(row)
                            else:
                                # print(f"   ❌ Pas de <tbody>, recherche directe des <tr>")
                                # Pas de tbody : récupérer toutes les lignes
                                all_trs = table_element.find_all('tr', recursive=False)
                                # print(f"   {len(all_trs)} lignes <tr> trouvées")
                                for idx, tr in enumerate(all_trs):
                                    if thead and tr.find_parent('thead'):
                                        continue
                                    cells = tr.find_all(['td', 'th'])
                                    # print(f"   Ligne {idx}: {len(cells)} cellules")
                                    row = [clean_text(td.get_text(separator=' ', strip=True)) for td in cells]
                                    # if idx < 2:
                                    #     print(f"   Contenu: {row}")
                                    if row:
                                        rows_data.append(row)
                            
                            # Si pas de thead explicite mais qu'on a des lignes,
                            # considérer la première ligne comme en-tête si elle contient du texte
                            if not has_explicit_thead and rows_data and len(rows_data) > 0:
                                # Vérifier si la première ligne pourrait être un en-tête
                                first_row = rows_data[0]
                                if first_row and any(cell.strip() for cell in first_row):
                                    # On garde rows_data tel quel, mais on marquera la première ligne comme en-tête dans le style
                                    # print(f"🔍 Tableau sans <thead> détecté, première ligne utilisée comme en-tête: {first_row}")
                                    pass
                            
                            if rows_data:
                                # Debug : afficher la structure du tableau (désactivé en production)
                                # print(f"📊 Tableau DOCX: {len(rows_data)} lignes, {max(len(row) for row in rows_data)} colonnes")
                                # print(f"   En-tête (ligne 0): {rows_data[0] if rows_data else 'VIDE'}")

                                num_cols = max(len(row) for row in rows_data)
                                
                                # Si le tableau a moins de 2 lignes utiles, ignorer et tenter pipe-rows
                                if len(rows_data) < 2:
                                    print("⚠️ Tableau HTML avec < 2 lignes - tentative d'utiliser un tableau '|' suivant")
                                    def is_pipe_row(s):
                                        return ('|' in s) and (s.count('|') >= 2)
                                    rows = []
                                    cur = table_element
                                    while True:
                                        cur = cur.find_next_sibling()
                                        if not cur:
                                            break
                                        if not getattr(cur, 'name', None):
                                            # Sauter les strings/espaces
                                            continue
                                        if getattr(cur, 'name', '').lower() not in ['p', 'div']:
                                            break
                                        raw = cur.get_text(separator=' ', strip=True)
                                        if not is_pipe_row(raw):
                                            break
                                        parts = [clean_text(c.strip()) for c in raw.split('|')]
                                        if parts and parts[0] == '':
                                            parts = parts[1:]
                                        if parts and parts[-1] == '':
                                            parts = parts[:-1]
                                        rows.append(parts)
                                        try:
                                            if hasattr(cur, 'attrs'):
                                                cur.attrs['data-processed'] = '1'
                                        except:
                                            pass
                                        # Avancer au prochain sibling tag (ignorer strings)
                                        nxt = cur
                                        while True:
                                            nxt = nxt.find_next_sibling()
                                            if not nxt or getattr(nxt, 'name', None):
                                                break
                                        cur = nxt
                                    if rows:
                                        num_cols = max(len(r) for r in rows)
                                        table = doc.add_table(rows=len(rows), cols=num_cols)
                                        try:
                                            table.style = 'Table Grid'
                                            table.autofit = True
                                        except:
                                            pass
                                        for i, r in enumerate(rows):
                                            for j in range(num_cols):
                                                cell = table.rows[i].cells[j]
                                                txt = r[j] if j < len(r) else ''
                                                cell.text = txt
                                                p = cell.paragraphs[0]
                                                if i == 0:
                                                    try:
                                                        tc = getattr(cell, '_tc', None) or cell._element
                                                        tcPr = tc.get_or_add_tcPr()
                                                        shd = OxmlElement('w:shd')
                                                        shd.set(qn('w:val'), 'clear')
                                                        shd.set(qn('w:color'), 'auto')
                                                        shd.set(qn('w:fill'), primary_hex)
                                                        tcPr.append(shd)
                                                        # Fallback: shading au niveau paragraphe pour compatibilité Word
                                                        try:
                                                            pPr = p._element.get_or_add_pPr()
                                                            p_shd = OxmlElement('w:shd')
                                                            p_shd.set(qn('w:val'), 'clear')
                                                            p_shd.set(qn('w:color'), 'auto')
                                                            p_shd.set(qn('w:fill'), primary_hex)
                                                            pPr.append(p_shd)
                                                        except Exception:
                                                            pass
                                                    except:
                                                        pass
                                                    for run in p.runs:
                                                        run.bold = True
                                                        run.font.size = Pt(11)
                                                        run.font.color.rgb = RGBColor(255, 255, 255)
                                                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                                else:
                                                    for run in p.runs:
                                                        run.font.size = Pt(10)
                                        doc.add_paragraph()
                                        return
                                    else:
                                        # Rien d'exploitable, ignorer ce tableau pour éviter un tableau vide
                                        print("⚠️ Ignoré: tableau HTML trop court et aucun tableau '|' trouvé ensuite")
                                        return
                                
                                # Si le tableau HTML semble cassé (une seule colonne),
                                # tenter de récupérer une table Markdown en lignes '|' immédiatement après
                                if num_cols < 2:
                                    print("⚠️ Tableau HTML à 1 colonne - tentative d'utiliser un tableau '|' suivant")
                                    def is_pipe_row(s):
                                        return ('|' in s) and (s.count('|') >= 2)
                                    rows = []
                                    cur = table_element.find_next_sibling()
                                    while cur and getattr(cur, 'name', '').lower() in ['p', 'div']:
                                        raw = cur.get_text(separator=' ', strip=True)
                                        if not is_pipe_row(raw):
                                            break
                                        parts = [clean_text(c.strip()) for c in raw.split('|')]
                                        if parts and parts[0] == '':
                                            parts = parts[1:]
                                        if parts and parts[-1] == '':
                                            parts = parts[:-1]
                                        rows.append(parts)
                                        # marquer traité pour éviter duplication
                                        try:
                                            if hasattr(cur, 'attrs'):
                                                cur.attrs['data-processed'] = '1'
                                        except:
                                            pass
                                        cur = cur.find_next_sibling()
                                    if rows:
                                        num_cols = max(len(r) for r in rows)
                                        table = doc.add_table(rows=len(rows), cols=num_cols)
                                        try:
                                            table.style = 'Table Grid'
                                            table.autofit = True
                                        except:
                                            pass
                                        for i, r in enumerate(rows):
                                            for j in range(num_cols):
                                                cell = table.rows[i].cells[j]
                                                txt = r[j] if j < len(r) else ''
                                                cell.text = txt
                                                p = cell.paragraphs[0]
                                                if i == 0:
                                                    # Header style
                                                    try:
                                                        tc = getattr(cell, '_tc', None) or cell._element
                                                        tcPr = tc.get_or_add_tcPr()
                                                        shd = OxmlElement('w:shd')
                                                        shd.set(qn('w:val'), 'clear')
                                                        shd.set(qn('w:color'), 'auto')
                                                        shd.set(qn('w:fill'), primary_hex)
                                                        tcPr.append(shd)
                                                        # Fallback: shading paragraphe
                                                        try:
                                                            pPr = p._element.get_or_add_pPr()
                                                            p_shd = OxmlElement('w:shd')
                                                            p_shd.set(qn('w:val'), 'clear')
                                                            p_shd.set(qn('w:color'), 'auto')
                                                            p_shd.set(qn('w:fill'), primary_hex)
                                                            pPr.append(p_shd)
                                                        except Exception:
                                                            pass
                                                    except:
                                                        pass
                                                    for run in p.runs:
                                                        run.bold = True
                                                        run.font.size = Pt(11)
                                                        run.font.color.rgb = RGBColor(255, 255, 255)
                                                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                                else:
                                                    for run in p.runs:
                                                        run.font.size = Pt(10)
                                        doc.add_paragraph()
                                        return
                                
                                # Créer le tableau HTML normal
                                table = doc.add_table(rows=len(rows_data), cols=num_cols)
                                
                                # Appliquer un style de tableau si disponible
                                try:
                                    table.style = 'Table Grid'
                                except:
                                    pass  # Style pas disponible, continuer sans
                                try:
                                    table.autofit = True
                                except:
                                    pass
                                
                                # Remplir les cellules
                                for i, row_data in enumerate(rows_data):
                                    for j, cell_text in enumerate(row_data):
                                        if j < len(table.rows[i].cells):
                                            cell = table.rows[i].cells[j]
                                            cell_text_str = str(cell_text) if cell_text else ''
                                            
                                            # Méthode simple et fiable : utiliser cell.text
                                            cell.text = cell_text_str
                                            
                                            # Récupérer le paragraphe et le run pour le style
                                            if cell.paragraphs:
                                                p = cell.paragraphs[0]
                                                
                                                # Appliquer le style selon la ligne
                                                if i == 0:
                                                    # EN-TÊTE : texte blanc, gras, fond vert
                                                    print(f"  🎨 Style en-tête appliqué à: '{cell_text_str}'")
                                                    shading_ok = False
                                                    # 1) Shading cellule
                                                    try:
                                                        _tc_val = getattr(cell, '_tc', None)
                                                        tc = _tc_val if _tc_val is not None else cell._element
                                                        tcPr = tc.get_or_add_tcPr()
                                                        shading_elm = OxmlElement('w:shd')
                                                        shading_elm.set(qn('w:val'), 'clear')
                                                        shading_elm.set(qn('w:color'), 'auto')
                                                        shading_elm.set(qn('w:fill'), primary_hex)
                                                        tcPr.append(shading_elm)
                                                        shading_ok = True
                                                    except Exception as shd_err:
                                                        print(f"⚠️ Shading cellule en-tête échoué: {shd_err}")
                                                    # 2) Fallback: shading paragraphe
                                                    try:
                                                        pPr = p._element.get_or_add_pPr()
                                                        p_shd = OxmlElement('w:shd')
                                                        p_shd.set(qn('w:val'), 'clear')
                                                        p_shd.set(qn('w:color'), 'auto')
                                                        p_shd.set(qn('w:fill'), primary_hex)
                                                        pPr.append(p_shd)
                                                        shading_ok = True
                                                    except Exception as _pshd_err:
                                                        pass
                                                    # Style du texte (blanc uniquement si shading OK)
                                                    try:
                                                        for run in p.runs:
                                                            run.bold = True
                                                            run.font.size = Pt(11)
                                                            if shading_ok:
                                                                run.font.color.rgb = RGBColor(255, 255, 255)
                                                    except Exception as txt_err:
                                                        print(f"⚠️ Style texte en-tête échoué: {txt_err}")
                                                    # Alignements
                                                    try:
                                                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                                        from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
                                                        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
                                                    except Exception as align_err:
                                                        print(f"⚠️ Alignement en-tête échoué: {align_err}")
                                                else:
                                                    # Contenu normal
                                                    for run in p.runs:
                                                        run.font.size = Pt(10)
                                                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                                
                                # Ajouter un espace après le tableau
                                doc.add_paragraph()
                        
                        # Traiter chaque élément HTML avec récursion pour préserver la structure
                        def process_block(element):
                            name = getattr(element, 'name', None)
                            if not name:
                                text = clean_text(str(element).strip())
                                if text:
                                    doc.add_paragraph(text)
                                return
                            name = name.lower()
                            # Important: ne pas aplatir les <div> ; si le contenu ressemble
                            # à un tableau en lignes '|' séparées par des <br>, le transformer en table
                            if name == 'div':
                                try:
                                    raw_multi = element.get_text(separator='\n', strip=True)
                                    lines = [ln for ln in raw_multi.split('\n') if ln.strip()]
                                    def is_pipe_row(s):
                                        return ('|' in s) and (s.count('|') >= 2)
                                    pipe_lines = [ln for ln in lines if is_pipe_row(ln)]
                                    if len(pipe_lines) >= 2:
                                        rows = []
                                        for ln in pipe_lines:
                                            parts = [clean_text(p.strip()) for p in ln.split('|')]
                                            if parts and parts[0] == '':
                                                parts = parts[1:]
                                            if parts and parts[-1] == '':
                                                parts = parts[:-1]
                                            rows.append(parts)
                                        if rows:
                                            num_cols = max(len(r) for r in rows)
                                            table = doc.add_table(rows=len(rows), cols=num_cols)
                                            try:
                                                table.style = 'Table Grid'
                                                table.autofit = True
                                            except:
                                                pass
                                            for i, r in enumerate(rows):
                                                for j in range(num_cols):
                                                    cell = table.rows[i].cells[j]
                                                    txt = r[j] if j < len(r) else ''
                                                    cell.text = txt
                                                    p = cell.paragraphs[0]
                                                    if i == 0:
                                                        # Header style
                                                        shading_ok = False
                                                        try:
                                                            _tc_val = getattr(cell, '_tc', None)
                                                            tc = _tc_val if _tc_val is not None else cell._element
                                                            tcPr = tc.get_or_add_tcPr()
                                                            shd = OxmlElement('w:shd')
                                                            shd.set(qn('w:val'), 'clear')
                                                            shd.set(qn('w:color'), 'auto')
                                                            shd.set(qn('w:fill'), primary_hex)
                                                            tcPr = cell._element.get_or_add_tcPr()
                                                            for child in list(tcPr):
                                                                if child.tag.endswith('shd'):
                                                                    tcPr.remove(child)
                                                            tcPr.append(shd)
                                                            # Fallback: shading paragraphe
                                                            try:
                                                                pPr = p._element.get_or_add_pPr()
                                                                p_shd = OxmlElement('w:shd')
                                                                p_shd.set(qn('w:val'), 'clear')
                                                                p_shd.set(qn('w:color'), 'auto')
                                                                p_shd.set(qn('w:fill'), primary_hex)
                                                                pPr.append(p_shd)
                                                            except Exception:
                                                                pass
                                                        except:
                                                            shading_ok = False
                                                        for run in p.runs:
                                                            run.bold = True
                                                            run.font.size = Pt(11)
                                                            if shading_ok:
                                                                run.font.color.rgb = RGBColor(255, 255, 255)
                                                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                                    else:
                                                        for run in p.runs:
                                                            run.font.size = Pt(10)
                                            doc.add_paragraph()
                                            return
                                except Exception as _div_tbl_err:
                                    pass
                                # Sinon, traiter les enfants normalement
                                for child in element.children:
                                    process_block(child)
                                return
                            if name == 'h1':
                                h = doc.add_heading(clean_text(element.get_text()), level=1)
                                h.runs[0].font.color.rgb = primary_color
                                h.runs[0].font.size = Pt(18)
                            elif name == 'h2':
                                h = doc.add_heading(clean_text(element.get_text()), level=2)
                                h.runs[0].font.color.rgb = primary_color
                                h.runs[0].font.size = Pt(14)
                            elif name == 'h3':
                                h = doc.add_heading(clean_text(element.get_text()), level=3)
                                h.runs[0].font.color.rgb = RGBColor(55, 65, 81)
                                h.runs[0].font.size = Pt(12)
                            elif name == 'h4':
                                h = doc.add_heading(clean_text(element.get_text()), level=4)
                                h.runs[0].font.size = Pt(11)
                            elif name == 'h5':
                                h = doc.add_heading(clean_text(element.get_text()), level=5)
                                h.runs[0].font.size = Pt(10)
                            elif name == 'h6':
                                h = doc.add_heading(clean_text(element.get_text()), level=6)
                                h.runs[0].font.size = Pt(9)
                            elif name == 'p':
                                # Éviter double-traitement
                                if hasattr(element, 'attrs') and element.attrs.get('data-processed') == '1':
                                    return
                                raw = element.get_text(separator=' ', strip=True)
                                # Détection table Markdown en lignes | col1 | col2 | col3 |
                                def is_pipe_row(s):
                                    return ('|' in s) and (s.count('|') >= 2)
                                if is_pipe_row(raw):
                                    # Agréger les lignes consécutives
                                    rows = []
                                    cur = element
                                    while True:
                                        if not cur or getattr(cur, 'name', '').lower() != 'p':
                                            break
                                        if hasattr(cur, 'attrs') and cur.attrs.get('data-processed') == '1':
                                            break
                                        row_text = cur.get_text(separator=' ', strip=True)
                                        if not is_pipe_row(row_text):
                                            break
                                        # Marquer comme traité
                                        if hasattr(cur, 'attrs'):
                                            cur.attrs['data-processed'] = '1'
                                        # Découper les cellules (supprimer bords vides)
                                        parts = [clean_text(c.strip()) for c in row_text.split('|')]
                                        # Retirer cellules vides dues aux bordures | ... |
                                        if parts and parts[0] == '':
                                            parts = parts[1:]
                                        if parts and parts[-1] == '':
                                            parts = parts[:-1]
                                        rows.append(parts)
                                        cur = cur.find_next_sibling()
                                    # Construire le tableau DOCX
                                    if rows:
                                        num_cols = max(len(r) for r in rows)
                                        table = doc.add_table(rows=len(rows), cols=num_cols)
                                        try:
                                            table.style = 'Table Grid'
                                            table.autofit = True
                                        except:
                                            pass
                                        for i, r in enumerate(rows):
                                            for j in range(num_cols):
                                                cell = table.rows[i].cells[j]
                                                txt = r[j] if j < len(r) else ''
                                                cell.text = txt
                                                p = cell.paragraphs[0]
                                                if i == 0:
                                                    # Header style
                                                    shading_ok = False
                                                    try:
                                                        tc = getattr(cell, '_tc', None) or cell._element
                                                        tcPr = tc.get_or_add_tcPr()
                                                        shd = OxmlElement('w:shd')
                                                        shd.set(qn('w:val'), 'clear')
                                                        shd.set(qn('w:color'), 'auto')
                                                        shd.set(qn('w:fill'), primary_hex)
                                                        tcPr.append(shd)
                                                        # Fallback: shading paragraphe
                                                        try:
                                                            pPr = p._element.get_or_add_pPr()
                                                            p_shd = OxmlElement('w:shd')
                                                            p_shd.set(qn('w:val'), 'clear')
                                                            p_shd.set(qn('w:color'), 'auto')
                                                            p_shd.set(qn('w:fill'), primary_hex)
                                                            pPr.append(p_shd)
                                                        except Exception:
                                                            pass
                                                        shading_ok = True
                                                    except:
                                                        shading_ok = False
                                                    for run in p.runs:
                                                        run.bold = True
                                                        run.font.size = Pt(11)
                                                        if shading_ok:
                                                            run.font.color.rgb = RGBColor(255, 255, 255)
                                                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                                else:
                                                    for run in p.runs:
                                                        run.font.size = Pt(10)
                                        # Espacement après le tableau
                                        doc.add_paragraph()
                                    return
                                # Paragraphe normal
                                text = clean_text(raw)
                                if text:
                                    p = doc.add_paragraph()
                                    add_formatted_text(p, element)
                                    p.paragraph_format.space_after = Pt(6)
                                else:
                                    doc.add_paragraph()
                            elif name == 'ul':
                                process_list(element, ordered=False)
                            elif name == 'ol':
                                process_list(element, ordered=True)
                            elif name == 'table':
                                before_tables = len(doc.tables)
                                try:
                                    process_table(element)
                                except Exception as te:
                                    print(f"⚠️ Erreur table DOCX: {te}")
                                    # N'ajouter le fallback que si AUCUNE table n'a été ajoutée
                                    after_tables = len(doc.tables)
                                    if after_tables == before_tables:
                                        try:
                                            for tr in element.find_all('tr'):
                                                cells = [clean_text(td.get_text(separator=' ', strip=True)) for td in tr.find_all(['td','th'])]
                                                if cells:
                                                    doc.add_paragraph(' | '.join(cells))
                                        except Exception as te2:
                                            print(f"⚠️ Fallback table DOCX échoué: {te2}")
                            elif name == 'pre':
                                code_text = clean_text(element.get_text())
                                if code_text:
                                    p = doc.add_paragraph(code_text)
                                    p.runs[0].font.name = 'Courier New'
                                    p.runs[0].font.size = Pt(9)
                            elif name == 'blockquote':
                                text = clean_text(element.get_text())
                                if text:
                                    p = doc.add_paragraph(text, style='Intense Quote')
                            else:
                                # Par défaut, explorer les enfants
                                for child in element.children:
                                    process_block(child)

                        root = soup.body if soup.body else soup
                        for el in root.children:
                            process_block(el)
                        
                    except Exception as parse_e:
                        print(f"⚠️ Parser HTML échoué pour DOCX: {parse_e}")
                        import traceback
                        traceback.print_exc()
                        # Fallback uniquement si rien n'a été ajouté
                        try:
                            if len(doc.paragraphs) == __docx_start_para_count:
                                fallback_text = clean_text(BeautifulSoup(html_input, 'html.parser').get_text('\n'))
                                if fallback_text:
                                    doc.add_paragraph(fallback_text)
                        except Exception as _fallback_e:
                            # Dernier recours : texte brut sans HTML
                            doc.add_paragraph(clean_text(re.sub('<[^<]+?>', '', html_input)))
                else:
                    # Fallback sans bs4
                    print("⚠️ BeautifulSoup non disponible, utilisation du fallback")
                    doc.add_paragraph(clean_text(re.sub('<[^<]+?>', '', html_input)))
            
            elif block == 'images' and images:
                # Ajouter les images (même largeur que le PDF)
                for img_data in images:
                    try:
                        img_base64 = img_data.get('data', '') or img_data.get('dataUrl', '')
                        img_name = img_data.get('title', '') or img_data.get('caption', '') or img_data.get('name', 'Image')
                        
                        if img_base64 and img_base64.startswith('data:image/'):
                            # Ajouter un titre H2 pour l'image (même style que PDF)
                            h = doc.add_heading(img_name, level=2)
                            h.runs[0].font.color.rgb = primary_color
                            h.runs[0].font.size = Pt(16)  # 16pt comme dans le PDF
                            h.runs[0].bold = True
                            
                            # Ajouter l'image avec la largeur disponible (comme PDF)
                            img_bytes = base64.b64decode(img_base64.split(',')[1])
                            img_buffer = io.BytesIO(img_bytes)
                            
                            # Utiliser la même largeur disponible que pour le logo
                            page_width_mm = 210
                            left_margin_mm = pdf_config.get('theme', {}).get('margins', {}).get('left', 18)
                            right_margin_mm = pdf_config.get('theme', {}).get('margins', {}).get('right', 18)
                            available_width_mm = page_width_mm - left_margin_mm - right_margin_mm
                            available_width_inches = available_width_mm / 25.4
                            
                            doc.add_picture(img_buffer, width=Inches(available_width_inches))
                            last_paragraph = doc.paragraphs[-1]
                            last_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            
                            doc.add_paragraph()  # Espace après l'image
                    except Exception as e:
                        print(f"❌ Erreur ajout image DOCX {img_data.get('name', 'inconnue')}: {e}")
        
        # Ajouter le footer avec mentions légales et numéro de page (comme PDF)
        section = doc.sections[0]
        footer = section.footer
        
        # Créer un tableau pour footer (mentions légales centrées + numéro de page à droite)
        footer.paragraphs[0].text = ''  # Vider le paragraphe par défaut
        footer_table = footer.add_table(rows=1, cols=2, width=Inches(7))
        footer_table.autofit = False
        
        # Colonne 1 : Mentions légales (centrées)
        left_cell = footer_table.rows[0].cells[0]
        left_para = left_cell.paragraphs[0]
        left_para.text = pdf_config.get('legal', 'ENOVACOM - Tous droits réservés')
        left_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        left_para.runs[0].font.size = Pt(8)
        left_para.runs[0].font.color.rgb = RGBColor(102, 102, 102)
        
        # Colonne 2 : Numéro de page (aligné à droite)
        if pdf_config.get('page_numbers', True):
            right_cell = footer_table.rows[0].cells[1]
            right_para = right_cell.paragraphs[0]
            right_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            
            # Ajouter le champ numéro de page
            run = right_para.add_run()
            run.font.size = Pt(8)
            run.font.color.rgb = RGBColor(153, 153, 153)
            
            # Insérer le field code pour le numéro de page
            fldChar1 = OxmlElement('w:fldChar')
            fldChar1.set(qn('w:fldCharType'), 'begin')
            
            instrText = OxmlElement('w:instrText')
            instrText.set(qn('xml:space'), 'preserve')
            instrText.text = 'PAGE'
            
            fldChar2 = OxmlElement('w:fldChar')
            fldChar2.set(qn('w:fldCharType'), 'end')
            
            run._r.append(fldChar1)
            run._r.append(instrText)
            run._r.append(fldChar2)
        
        # Supprimer les bordures du tableau de footer
        for row in footer_table.rows:
            for cell in row.cells:
                tc = cell._element
                tcPr = tc.get_or_add_tcPr()
                tcBorders = OxmlElement('w:tcBorders')
                for border_name in ['top', 'left', 'bottom', 'right']:
                    border = OxmlElement(f'w:{border_name}')
                    border.set(qn('w:val'), 'none')
                    tcBorders.append(border)
                tcPr.append(tcBorders)
        
        # Watermark (si activé)
        if pdf_config.get('watermark', False):
            p = doc.add_paragraph('⚠️ CONFIDENTIEL')
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.runs[0].font.size = Pt(10)
            p.runs[0].font.color.rgb = RGBColor(220, 38, 38)
            p.runs[0].bold = True
        
        # Sauvegarder en mémoire
        docx_buffer = io.BytesIO()
        doc.save(docx_buffer)
        docx_buffer.seek(0)
        
        # Nom du fichier
        filename = f"{pdf_config.get('title', 'document').replace(' ', '_')}.docx"
        
        print(f"📄 DOCX généré: {filename}")
        
        return send_file(
            docx_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"❌ Erreur génération DOCX: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Erreur lors de la génération du DOCX: {str(e)}'}), 500

def update_env_file(updates):
    """Met à jour le fichier .env avec les nouvelles valeurs"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    # Lire le fichier .env existant
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    # Mettre à jour avec les nouvelles valeurs
    env_vars.update(updates)
    
    # Réécrire le fichier .env
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write('# Configuration Mistral AI\n')
        for key, value in env_vars.items():
            f.write(f'{key}={value}\n')
    
    print(f'✅ Fichier .env mis à jour : {list(updates.keys())}')

if __name__ == '__main__':
    import webbrowser
    import threading
    
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 5173))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    url = f"http://{host}:{port}"
    
    print(f" Mermaid Flask AI démarré sur {url}")
    
    # Ouvrir le navigateur automatiquement après 1.5 secondes
    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open(url)
    
    threading.Thread(target=open_browser, daemon=True).start()
    run_kwargs = {'host': host, 'port': port, 'debug': debug}
    if debug and os.name == 'nt':
        print("ℹ️ Windows detected: disabling watchdog reloader (use_reloader=False) to avoid Python 3.13 issue")
        run_kwargs['use_reloader'] = False
    app.run(**run_kwargs)