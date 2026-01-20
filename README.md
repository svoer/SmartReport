# 📊 SmartReport

**Générez des comptes rendus professionnels avec l'IA en quelques clics.**

---

## 🎯 Qu'est-ce que c'est ?

SmartReport transforme vos notes en rapports PDF/DOCX prêts à envoyer :
- **40 templates** (réunions, projets, support, technique santé)
- **Export PDF/DOCX** avec votre logo
- **Diagrammes techniques** (Mermaid.js)
- **Dictée vocale** intégrée

**Gain de temps : ~1h par document.**

---

## 🚀 Installation

### Windows (automatique)
```bash
git clone https://github.com/enovacom/SmartReport.git
cd SmartReport
start.bat
```

### Linux/macOS
```bash
git clone https://github.com/enovacom/SmartReport.git
cd SmartReport
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec votre clé API Mistral
python app.py
```

**Clé API Mistral (gratuit)** : https://console.mistral.ai/

---

## 📖 Utilisation

1. **Lancez l'app** : `start.bat` ou `python app.py`
2. **Ouvrez** : http://127.0.0.1:5173
3. **Tapez vos notes** (ou dictez)
4. **Choisissez un template** et cliquez "Générer"
5. **Exportez en PDF/DOCX**

---

## 🛠️ Stack

**Backend** : Flask, ReportLab (PDF), python-docx  
**Frontend** : Alpine.js, Tailwind CSS, Mermaid.js  
**IA** : Mistral AI (recommandé), OpenAI, Ollama

---

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API](docs/API.md)
- [Installation détaillée](docs/INSTALLATION.md)
- [Guide utilisateur](docs/USAGE.md)

---

## 📄 Licence

**Propriétaire ENOVACOM** — Usage interne uniquement.

---

**Questions ?** [support@enovacom.com](mailto:support@enovacom.com)
