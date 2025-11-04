# Enovacom SmartReport

> **Notez. Validez. Envoyez.**

## 🚀 Pourquoi SmartReport ?

**Divisez par 10 le temps passé sur vos comptes rendus et diagrammes.**

Avant SmartReport | Après SmartReport
--- | ---
Notes + 1h de mise en forme | **5 min de notes → 1 clic → PDF/DOCX prêt**
Diagrammes manuels (Visio, draw.io) | **Décrivez en français → IA génère le diagramme**
Copier-coller vers Word, retravailler la mise en page | **Export direct PDF + DOCX avec logo et charte Enovacom**
Documents clients hétérogènes | **Templates pro unifiés (formel, agile, technique, commercial)**

**Résultat:** jusqu'à **1h gagnée par réunion** client, sprint review ou atelier technique.

---

## ⚡ Features clés

### 1. Génération de diagrammes par IA (Mermaid)
- **Prompt en français** → l'IA (Mistral/OpenAI/DeepSeek/Gemini) produit le code Mermaid
- **10+ types**: Flowchart, Sequence, Class, State, ER, Gantt, Pie, Journey, Timeline, Mindmap, Git Graph
- **30+ thèmes pro** avec personnalisation couleurs/polices
- **Exports vectoriels**: SVG, PNG transparent, JPEG
- **Dictée vocale** intégrée (français)

### 2. Comptes rendus auto-structurés
- **4 templates IA**:
  - **Client formel**: Synthèse exécutive, décisions, actions, prochaines étapes
  - **Sprint Agile**: Objectifs, user stories, blockers, décisions techniques
  - **Brief technique**: Architecture, stack, contraintes, actions
  - **CRM Échange & Partage**: Opportunités commerciales, mise à jour base client, actions de suivi
- **Éditeur riche**: titres, listes, tableaux, gras/italique, liens, code
- **De notes brutes à CR structuré en 10 secondes**

### 3. Exports PDF & DOCX qualité pro
- **Logo** (Enovacom ou personnalisé), **titre**, **client**, **sous-titre**
- **Pied de page** avec mentions légales + numérotation auto
- **Tableaux stylés** (en-tête vert Enovacom, colonnes alignées)
- **Images** intégrées avec titres (automatiquement placées)
- **Mise en page identique** PDF ↔ DOCX (couleurs, marges, polices)
- **Watermark** "CONFIDENTIEL" optionnel

### 4. Gestion de projet intégrée
- **Sauvegarde auto** dans le navigateur (localStorage)
- **Historique complet**: créer, ouvrir, renommer, supprimer
- **Pas de serveur** requis pour vos données (stockage local)

## 🤝 Compatibilité API & conformité

- Providers compatibles: **Mistral**, **OpenAI (ChatGPT)**, **DeepSeek**, **Gemini**, ainsi que **Ollama** (local).
- Recommandation: utilisez en priorité **Mistral** (hébergé en France, conformité **RGPD**). Même si l’application n’envoie pas de données sensibles, adoptez de bons réflexes lorsque vous transmettez des informations professionnelles à des services d’IA.
- Vous pouvez démarrer avec une **clé gratuite Mistral**.

---

## 📦 Installation

1. Installez **Python 3.x**: https://www.python.org/downloads/
   - Cochez « Add Python to PATH » lors de l’installation (Windows)
2. Téléchargez ou clonez ce dépôt
3. Double-cliquez sur `start.bat`

Le script effectue automatiquement:
- Création de l’environnement virtuel
- Installation des dépendances (Flask, ReportLab, python-docx, BeautifulSoup, …)
- Lancement de l’application
- Ouverture du navigateur sur http://127.0.0.1:5173

En cas d’erreur « python n’est pas reconnu »:
- Paramètres Système > Variables d'environnement > Path > Ajouter:
  - `C:\Users\<votre_user>\AppData\Local\Programs\Python\Python3x\`
  - `C:\Users\<votre_user>\AppData\Local\Programs\Python\Python3x\Scripts\`

---

## 🎯 Utilisation rapide

1. **Lancer** l'app (double-clic sur `start.bat`)
2. **Configurer l'IA** (1ère fois):
   - Cliquer sur « Paramètres »
   - Choisir un provider (Mistral recommandé)
   - Coller votre clé API
   - Tester → Sauvegarder
3. **Créer un diagramme**:
   - Décrire en français (ex: "Flux d'authentification utilisateur avec JWT")
   - Cliquer « Générer » → le diagramme apparaît
   - Personnaliser (thème, couleurs, éditer le code)
   - Exporter (SVG/PNG/JPEG)
4. **Rédiger un compte rendu**:
   - Prendre des notes rapides (bullet points OK)
   - Choisir un template (client, sprint, technique, commercial)
   - Cliquer « Générer le CR » → texte structuré en Markdown
   - Éditer si besoin (éditeur riche)
5. **Ajouter des images** (optionnel):
   - Glisser-déposer ou upload
   - Ajouter des titres descriptifs
6. **Exporter**:
   - Cliquer « Générer PDF » ou « Générer DOCX »
   - Document prêt avec logo, mise en page pro, tableaux stylés

**Temps total:** 3-5 minutes pour un document complet.

---

## 🛠️ Pour les développeurs

### Stack technique
- **Backend**: Flask 3 (Python)
- **PDF**: ReportLab 4 (génération pro)
- **DOCX**: python-docx (tables, logo, styles)
- **HTML**: BeautifulSoup4 + lxml (parsing robuste)
- **IA**: requests (providers OpenAI-compatible + Ollama)
- **Frontend**: Alpine.js, Mermaid.js, Tailwind CSS

### API REST (extraits)
- `POST /api/generate` → génère Mermaid depuis prompt
- `POST /api/generate-report` → génère CR structuré (4 templates)
- `POST /api/generate-pdf` → export PDF
- `POST /api/generate-docx` → export DOCX
- `GET /api/ai/models` → liste modèles du provider actif
- `POST /api/ai/settings` → configure provider + clé API

### Config (optionnel, .env)
```env
HOST=127.0.0.1
PORT=5173
FLASK_DEBUG=true
ACTIVE_PROVIDER=mistral
MISTRAL_BASE_URL=https://api.mistral.ai
MISTRAL_API_KEY=sk-xxxxx
```

Providers supportés: **Mistral**, OpenAI, DeepSeek, Gemini, Ollama (local).

### Lancement dev manuel
```bash
python app.py
# ou en production
waitress-serve --listen=0.0.0.0:5173 app:app
```

---

## 💡 Cas d'usage

- **Réunion client**: notes vocales → CR formel + diagramme d'archi → PDF client-ready en 5 min
- **Sprint review**: backlog → CR Agile structuré → partage équipe en 1 clic
- **Atelier technique**: décisions → brief technique + diagrammes → export DOCX modifiable
- **Visite commerciale**: besoins exprimés → CR commercial + opportunités → CRM update rapide

---

## 🔒 Licence

**Propriétaire — Enovacom.**  
Usage interne uniquement. Tous droits réservés.  
Toute diffusion, copie ou utilisation externe est interdite sans autorisation écrite d'Enovacom.
