# 🔌 Documentation API SmartReport

## Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Authentification](#authentification)
- [Endpoints](#endpoints)
  - [Interface](#interface)
  - [Génération IA](#génération-ia)
  - [Export Documents](#export-documents)
  - [Configuration](#configuration)
- [Codes d'Erreur](#codes-derreur)
- [Exemples d'Utilisation](#exemples-dutilisation)

---

## Vue d'Ensemble

SmartReport expose une **API REST** simple permettant de :
- Générer des diagrammes Mermaid via IA
- Générer des comptes rendus structurés
- Exporter des documents PDF/DOCX professionnels
- Configurer et tester les providers IA

**Base URL** : `http://127.0.0.1:5173` (par défaut)

**Format** : JSON  
**Content-Type** : `application/json`

---

## Authentification

❌ **Aucune authentification requise** pour l'instant (application interne).

Pour un déploiement en production, considérez :
- API Keys (via headers `X-API-Key`)
- JWT tokens
- OAuth 2.0

---

## Endpoints

### Interface

#### `GET /`
Affiche l'interface principale de l'application.

**Réponse** : HTML (Single Page Application)

---

#### `GET /favicon.ico`
Retourne l'icône de l'application.

**Réponse** : SVG

---

#### `GET /mentions-legales`
Page des mentions légales.

**Réponse** : HTML

---

#### `GET /confidentialite`
Page de politique de confidentialité.

**Réponse** : HTML

---

#### `GET /conditions`
Page des conditions générales d'utilisation.

**Réponse** : HTML

---

### Génération IA

#### `POST /api/generate`
Génère du code Mermaid depuis un prompt en langage naturel.

**Request Body:**
```json
{
  "prompt": "Diagramme de séquence pour authentification JWT avec refresh token",
  "model": "mistral-medium-latest"  // optionnel
}
```

**Paramètres:**
| Nom | Type | Requis | Description |
|-----|------|--------|-------------|
| `prompt` | string | ✅ Oui | Description en français/anglais du diagramme souhaité |
| `model` | string | ❌ Non | Modèle IA à utiliser (défaut : modèle par défaut du provider actif) |

**Réponse Success (200):**
```json
{
  "mermaid": "sequenceDiagram\n    autonumber\n    participant Client\n    participant API\n    participant AuthService\n    participant DB\n    \n    Client->>API: POST /login (username, password)\n    API->>AuthService: Validate credentials\n    AuthService->>DB: Query user\n    DB-->>AuthService: User data\n    AuthService->>AuthService: Generate JWT access token (15min)\n    AuthService->>AuthService: Generate refresh token (7d)\n    AuthService-->>API: Tokens\n    API-->>Client: {accessToken, refreshToken}\n    \n    Note over Client: Store tokens securely\n    \n    Client->>API: GET /api/protected (Authorization: Bearer accessToken)\n    API->>AuthService: Validate access token\n    AuthService-->>API: Token valid\n    API-->>Client: Protected resource\n    \n    Note over Client: Access token expired\n    \n    Client->>API: POST /refresh (refreshToken)\n    API->>AuthService: Validate refresh token\n    AuthService->>DB: Check token validity\n    DB-->>AuthService: Token valid\n    AuthService->>AuthService: Generate new access token\n    AuthService-->>API: New access token\n    API-->>Client: {accessToken}"
}
```

**Codes d'Erreur:**
- `400 Bad Request` : Prompt manquant ou vide
- `401 Unauthorized` : Clé API invalide ou manquante
- `500 Internal Server Error` : Erreur du provider IA

**Exemple cURL:**
```bash
curl -X POST http://127.0.0.1:5173/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Flowchart du processus de validation de commande e-commerce",
    "model": "mistral-medium-latest"
  }'
```

---

#### `POST /api/generate-report`
Génère un compte rendu structuré depuis des notes brutes.

**Request Body:**
```json
{
  "notes": "Réunion kick-off projet Interop V3\nDate: 15/01/2026\nParticipants: Marie (CP), Jean (Archi), Client (DSI)\n\nPoints abordés:\n- Migration HL7 v2 vers FHIR\n- Budget: 150k€\n- Deadline: juin 2026\n- Risques: ressources limitées\n\nDécisions:\n- Go pour FHIR R4\n- Sprint 0 début février\n\nActions:\n- Marie: rédiger CDC - 22/01\n- Jean: POC FHIR - 31/01",
  "template": "client_formel",
  "context": {
    "date": "15/01/2026",
    "participants": "Marie (Chef Projet), Jean (Architecte), Dr. Dupont (DSI)"
  }
}
```

**Paramètres:**
| Nom | Type | Requis | Description |
|-----|------|--------|-------------|
| `notes` | string | ✅ Oui | Notes brutes de la réunion/sprint/atelier |
| `template` | string | ✅ Oui | Template à utiliser : `client_formel`, `sprint_agile`, `brief_technique`, `crm_echange`, `correction_orthographe` |
| `context` | object | ❌ Non | Contexte additionnel (date, participants, etc.) |
| `context.date` | string | ❌ Non | Date de la réunion (JJ/MM/AAAA) |
| `context.participants` | string | ❌ Non | Liste des participants |

**Templates Disponibles:**

| Template | Description | Use Case |
|----------|-------------|----------|
| `client_formel` | Compte rendu de réunion client professionnel | Kick-offs, comités de pilotage, réunions exécutives |
| `sprint_agile` | Synthèse de sprint agile | Daily standups, sprint reviews, retrospectives |
| `brief_technique` | Atelier technique | Choix d'architecture, décisions technologiques |
| `crm_echange` | Compte rendu commercial avec opportunités | Visites clients, prospection, détection opportunités |
| `correction_orthographe` | Correction grammaticale sans modification de contenu | Relecture de documents existants |

**Réponse Success (200):**
```json
{
  "report": "## Compte Rendu de Réunion\n\n**Date** : 15/01/2026  \n**Participants** : Marie (Chef Projet), Jean (Architecte), Dr. Dupont (DSI)\n\n## Contexte & Objectif\n\nRéunion de lancement du projet Interop V3 visant à moderniser l'infrastructure d'interopérabilité de l'établissement en migrant de HL7 v2 vers FHIR R4.\n\n## Points abordés\n\n- **Migration HL7 v2 vers FHIR** : Nécessité de mettre à niveau l'infrastructure d'échange de données pour bénéficier des standards modernes FHIR R4.\n- **Budget** : Enveloppe de 150 000€ allouée au projet.\n- **Deadline** : Livraison attendue pour juin 2026.\n- **Risques identifiés** : Disponibilité des ressources techniques internes limitée, nécessité d'arbitrage sur les priorités.\n\n## Décisions prises\n\n- ✅ **Go pour FHIR R4** : Validation du choix technologique FHIR R4 comme standard d'interopérabilité cible.\n- ✅ **Sprint 0 début février** : Lancement de la phase de cadrage et de préparation technique dès le 1er février 2026.\n\n## Actions à mener\n\n| Action | Responsable | Échéance |\n|--------|-------------|----------|\n| Rédiger le cahier des charges détaillé | Marie | 22/01/2026 |\n| Réaliser un POC FHIR sur cas d'usage pilote | Jean | 31/01/2026 |\n\n## Prochains rendez-vous\n\n**Date** : 05/02/2026  \n**Ordre du jour** : Présentation POC FHIR, validation du cahier des charges, planification détaillée du Sprint 0."
}
```

**Codes d'Erreur:**
- `400 Bad Request` : Notes ou template manquants, template invalide
- `401 Unauthorized` : Clé API invalide
- `500 Internal Server Error` : Erreur du provider IA

**Exemple cURL:**
```bash
curl -X POST http://127.0.0.1:5173/api/generate-report \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Sprint 3 review\nUS terminées: US-12 (8pts), US-15 (5pts)\nBlocker: perfs requêtes complexes",
    "template": "sprint_agile",
    "context": {
      "date": "24/01/2026"
    }
  }'
```

---

### Export Documents

#### `POST /api/generate-pdf`
Génère un PDF professionnel depuis un projet complet.

**Request Body:**
```json
{
  "project": {
    "report": {
      "generated": "<h2>Compte Rendu de Réunion</h2><p><strong>Date</strong> : 15/01/2026<br><strong>Participants</strong> : Marie, Jean, DSI Client</p><h2>Contexte &amp; Objectif</h2><p>Réunion de lancement du projet...</p>"
    },
    "images": [
      {
        "title": "Architecture cible FHIR",
        "dataUrl": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA..."
      }
    ],
    "diagram": {
      "mermaid": "graph TD\n    A[Client] --> B[API Gateway]\n    B --> C[FHIR Server]",
      "svg": "<svg>...</svg>",
      "include": true,
      "position": "after_report",
      "title": "Diagramme d'architecture"
    },
    "pdfConfig": {
      "logo": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA...",
      "title": "Compte Rendu - Kick-off Projet Interop V3",
      "client": "CHU de Toulouse",
      "subtitle": "Phase de cadrage",
      "footer": "{page}/{pages} • {projet} • {date}",
      "legal": "ENOVACOM - Tous droits réservés",
      "watermark": false,
      "page_numbers": true,
      "theme": {
        "font": "Inter",
        "primary": "#0C4A45",
        "margins": {
          "top": 24,
          "right": 18,
          "bottom": 28,
          "left": 18
        }
      },
      "order": ["report", "images", "diagram"]
    }
  }
}
```

**Paramètres:**

| Nom | Type | Requis | Description |
|-----|------|--------|-------------|
| `project.report.generated` | string | ✅ Oui | HTML du compte rendu (contentEditable) |
| `project.images` | array | ❌ Non | Liste des images à insérer |
| `project.images[].title` | string | ✅ Oui | Titre de l'image |
| `project.images[].dataUrl` | string | ✅ Oui | Image en base64 data URL |
| `project.diagram.include` | boolean | ❌ Non | Inclure le diagramme dans le PDF? |
| `project.diagram.svg` | string | ❌ Non | SVG du diagramme |
| `project.diagram.title` | string | ❌ Non | Titre du diagramme |
| `project.pdfConfig.logo` | string | ❌ Non | Logo en base64 data URL |
| `project.pdfConfig.title` | string | ✅ Oui | Titre du document |
| `project.pdfConfig.client` | string | ❌ Non | Nom du client |
| `project.pdfConfig.subtitle` | string | ❌ Non | Sous-titre |
| `project.pdfConfig.footer` | string | ❌ Non | Template pied de page |
| `project.pdfConfig.legal` | string | ❌ Non | Mentions légales |
| `project.pdfConfig.watermark` | boolean | ❌ Non | Afficher watermark "CONFIDENTIEL"? |
| `project.pdfConfig.theme.primary` | string | ❌ Non | Couleur primaire (hex) |
| `project.pdfConfig.theme.margins` | object | ❌ Non | Marges en mm |
| `project.pdfConfig.order` | array | ❌ Non | Ordre des blocs : `["report", "images", "diagram"]` |

**Réponse Success (200):**
- **Content-Type** : `application/pdf`
- **Content-Disposition** : `attachment; filename="Document_2026-01-15.pdf"`
- **Body** : Fichier PDF binaire

**Codes d'Erreur:**
- `400 Bad Request` : Projet mal formé, report manquant
- `500 Internal Server Error` : Erreur de génération PDF (ReportLab)

**Exemple cURL:**
```bash
curl -X POST http://127.0.0.1:5173/api/generate-pdf \
  -H "Content-Type: application/json" \
  -d @project.json \
  --output document.pdf
```

---

#### `POST /api/generate-docx`
Génère un document Word (.docx) éditable.

**Request Body:** (identique à `/api/generate-pdf`)

**Réponse Success (200):**
- **Content-Type** : `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Content-Disposition** : `attachment; filename="Document_2026-01-15.docx"`
- **Body** : Fichier DOCX binaire

**Codes d'Erreur:** (identiques à `/api/generate-pdf`)

---

### Configuration

#### `GET /api/settings`
Récupère la configuration actuelle des providers IA.

**Réponse Success (200):**
```json
{
  "active_provider": "mistral",
  "mistral_base_url": "https://api.mistral.ai",
  "mistral_api_key": "sk-***************************xyz"
}
```

**Note** : Les clés API sont masquées (premiers et derniers caractères visibles).

---

#### `POST /api/ai/settings`
Sauvegarde les paramètres d'un provider IA.

**Request Body:**
```json
{
  "provider": "mistral",
  "base_url": "https://api.mistral.ai",
  "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

**Paramètres:**
| Nom | Type | Requis | Description |
|-----|------|--------|-------------|
| `provider` | string | ✅ Oui | Provider : `mistral`, `openai`, `deepseek`, `gemini`, `ollama` |
| `base_url` | string | ✅ Oui | URL de base de l'API |
| `api_key` | string | ✅ Oui | Clé API (sauf Ollama) |

**Réponse Success (200):**
```json
{
  "success": true,
  "message": "Paramètres Mistral AI sauvegardés avec succès"
}
```

**Codes d'Erreur:**
- `400 Bad Request` : Paramètres manquants ou invalides
- `500 Internal Server Error` : Erreur lors de la sauvegarde (fichier .env)

---

#### `POST /api/ai/test`
Teste la connexion à un provider IA.

**Request Body:**
```json
{
  "provider": "mistral",
  "base_url": "https://api.mistral.ai",
  "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

**Réponse Success (200):**
```json
{
  "success": true,
  "message": "✅ Connexion Mistral réussie ! Modèles disponibles : mistral-medium-latest, mistral-large-latest, mistral-small-latest",
  "models": [
    {
      "id": "mistral-medium-latest",
      "name": "Mistral Medium"
    },
    {
      "id": "mistral-large-latest",
      "name": "Mistral Large"
    }
  ]
}
```

**Réponse Erreur (400/401/500):**
```json
{
  "success": false,
  "error": "Erreur d'authentification : clé API invalide (401 Unauthorized)"
}
```

**Codes d'Erreur:**
- `400 Bad Request` : Paramètres manquants
- `401 Unauthorized` : Clé API invalide
- `500 Internal Server Error` : Erreur réseau ou timeout

---

#### `GET /api/ai/models`
Retourne les modèles disponibles pour le provider actif.

**Réponse Success (200):**
```json
{
  "models": [
    {
      "id": "mistral-medium-latest",
      "name": "Mistral Medium"
    },
    {
      "id": "mistral-large-latest",
      "name": "Mistral Large"
    },
    {
      "id": "mistral-small-latest",
      "name": "Mistral Small"
    }
  ]
}
```

**Codes d'Erreur:**
- `401 Unauthorized` : Clé API manquante ou invalide
- `500 Internal Server Error` : Erreur provider

---

#### `GET /api/ollama/models`
Retourne les modèles Ollama disponibles localement.

**Réponse Success (200):**
```json
{
  "models": [
    {
      "name": "mistral:latest",
      "size": 4109867424,
      "digest": "61e88e884507ba5e06c49b40e6226884b2a16e872382c2b4a5a1b0",
      "modified_at": "2026-01-15T10:30:00Z"
    },
    {
      "name": "llama2:13b",
      "size": 7365960704,
      "digest": "d5611f7c428b85b8e5a7b1e9f5a7c1d8e9f5a7c1d8e9f5a7c1",
      "modified_at": "2026-01-10T15:20:00Z"
    }
  ]
}
```

**Codes d'Erreur:**
- `500 Internal Server Error` : Ollama non démarré ou inaccessible

---

#### `GET /api/mistral/models`
Retourne les modèles Mistral AI disponibles.

**Headers:**
```
Authorization: Bearer sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Réponse Success (200):**
```json
{
  "models": [
    {
      "id": "mistral-medium-latest",
      "object": "model",
      "created": 1704067200,
      "owned_by": "mistralai"
    },
    {
      "id": "mistral-large-latest",
      "object": "model",
      "created": 1704067200,
      "owned_by": "mistralai"
    }
  ]
}
```

---

## Codes d'Erreur

| Code | Message | Description |
|------|---------|-------------|
| `400` | Bad Request | Paramètres manquants, invalides ou mal formés |
| `401` | Unauthorized | Clé API manquante, invalide ou expirée |
| `404` | Not Found | Endpoint inexistant |
| `500` | Internal Server Error | Erreur serveur (génération PDF, appel IA, etc.) |
| `503` | Service Unavailable | Provider IA inaccessible (timeout, maintenance) |

### Format des Erreurs

```json
{
  "error": "Message d'erreur détaillé"
}
```

**Exemple:**
```json
{
  "error": "Erreur lors de la génération du PDF: Invalid HTML structure"
}
```

---

## Exemples d'Utilisation

### Python

#### Générer un Diagramme

```python
import requests

url = "http://127.0.0.1:5173/api/generate"
payload = {
    "prompt": "Diagramme de classe pour un système de gestion de bibliothèque avec livres, auteurs, emprunts et utilisateurs",
    "model": "mistral-medium-latest"
}

response = requests.post(url, json=payload)

if response.status_code == 200:
    mermaid_code = response.json()["mermaid"]
    print(mermaid_code)
else:
    print(f"Erreur {response.status_code}: {response.json()['error']}")
```

#### Générer un Compte Rendu

```python
import requests

url = "http://127.0.0.1:5173/api/generate-report"
payload = {
    "notes": """
Sprint 5 Review - 24/01/2026
Équipe: 5 devs + PO + SM

US terminées:
- US-23: API REST CRUD patients (13 pts) ✅
- US-24: Interface admin (8 pts) ✅
- US-26: Tests e2e Playwright (5 pts) ✅

Blockers:
- Performances dégradées sur requêtes complexes avec +10k patients
- Investigation en cours (Jean)

Décisions:
- Mise en place Redis pour cache
- Refactoring API en sprint 6

Actions:
- Jean: POC Redis - 31/01
- Marie: Planif sprint 6 - 26/01
""",
    "template": "sprint_agile",
    "context": {
        "date": "24/01/2026"
    }
}

response = requests.post(url, json=payload)

if response.status_code == 200:
    report_markdown = response.json()["report"]
    print(report_markdown)
```

#### Télécharger un PDF

```python
import requests
import json

url = "http://127.0.0.1:5173/api/generate-pdf"

with open('project.json', 'r') as f:
    project_data = json.load(f)

response = requests.post(url, json={"project": project_data})

if response.status_code == 200:
    with open('document.pdf', 'wb') as f:
        f.write(response.content)
    print("PDF généré avec succès !")
else:
    print(f"Erreur {response.status_code}: {response.json()['error']}")
```

### JavaScript (Fetch API)

#### Générer un Diagramme

```javascript
async function generateDiagram() {
  const response = await fetch('http://127.0.0.1:5173/api/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      prompt: 'Flowchart du processus de validation de commande e-commerce',
      model: 'mistral-medium-latest'
    })
  });

  if (response.ok) {
    const data = await response.json();
    console.log(data.mermaid);
  } else {
    const error = await response.json();
    console.error('Erreur:', error.error);
  }
}
```

#### Tester un Provider

```javascript
async function testMistralConnection() {
  const response = await fetch('http://127.0.0.1:5173/api/ai/test', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      provider: 'mistral',
      base_url: 'https://api.mistral.ai',
      api_key: 'sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    })
  });

  const data = await response.json();
  
  if (data.success) {
    console.log('✅', data.message);
    console.log('Modèles disponibles:', data.models);
  } else {
    console.error('❌', data.error);
  }
}
```

---

## Rate Limiting

❌ **Pas de rate limiting côté SmartReport** actuellement.

⚠️ **Attention** : Les providers IA ont leurs propres limites :
- **Mistral AI** : ~200 requêtes/min (tier gratuit)
- **OpenAI** : ~3 requêtes/min (tier gratuit), ~3500 req/min (tier payant)
- **Ollama** : Pas de limite (local)

---

## Webhook / Callbacks

❌ **Pas de support webhook** actuellement.

Les requêtes sont synchrones (bloquantes jusqu'à réponse).

Pour des générations asynchrones :
1. Implémenter un système de jobs (Celery, RQ)
2. Retourner un `job_id`
3. Exposer un endpoint `GET /api/jobs/{job_id}` pour polling

---

## Versioning

**Version actuelle** : `1.0` (implicite, pas de versioning dans l'URL)

Pour une future v2, utiliser :
- `/api/v2/generate`
- Header `Accept: application/vnd.smartreport.v2+json`

---

**📖 Documentation complète** : [Retour au README principal](../README.md)
