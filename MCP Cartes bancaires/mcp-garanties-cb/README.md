# 🏦 Comparateur de Garanties Cartes Bancaires — Projet IMA

Pipeline complet : **PDF → Extraction IA → Base normalisée → Serveur MCP → Agent IA**

## Prérequis

- Python 3.11+
- [Cursor](https://cursor.sh) (recommandé) ou VS Code
- Clé API Anthropic (`ANTHROPIC_API_KEY`) ou Google Gemini (`GEMINI_API_KEY`)
- Google Drive Desktop (pour synchroniser les PDF)

## Installation

```bash
# Cloner le projet
git init mcp-garanties-cb && cd mcp-garanties-cb

# Environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Dépendances
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Remplir les clés API dans .env
```

## Structure du projet

```
mcp-garanties-cb/
├── .cursor/
│   └── mcp.json                  ← Config MCP pour Cursor
├── .env.example                  ← Template variables d'environnement
├── data/
│   ├── Migration_INEKTO_V2_2.xlsx  ← Base de données source (à copier)
│   └── pdfs/                       ← Sync Google Drive → dossiers Banque_XXX/
│       ├── Banque_ALL/
│       ├── Banque_AMX/
│       └── ...
├── extraction/
│   ├── apply_corrections.py      ← Applique les 27 corrections IMA
│   ├── normalize.py              ← Normalise statuts, zones, garanties orphelines
│   ├── extract_from_pdf.py       ← Extraction IA des données manquantes depuis PDF
│   └── audit.py                  ← Vérifie la qualité de la base
├── server/
│   ├── data_loader.py            ← Charge le Excel en structures Python
│   └── server.py                 ← Serveur MCP exposant les outils
├── tests/
│   └── test_pipeline.py          ← Tests du pipeline complet
├── requirements.txt
└── README.md
```

## Usage

### Étape 1 — Préparer les données

```bash
# Copier le fichier Excel dans data/
cp ~/Drive/PROJET_GARANTIES_CB/Migration_INEKTO_V2_2.xlsx data/

# Synchroniser les PDF (via Google Drive Desktop ou manuellement)
# Les PDF doivent suivre la structure Banque_XXX/*.pdf
```

### Étape 2 — Appliquer les corrections et normaliser

```bash
# Appliquer les 27 corrections IMA "À CORRIGER"
python -m extraction.apply_corrections

# Normaliser (statuts, zones, garanties orphelines)
python -m extraction.normalize

# Vérifier la qualité
python -m extraction.audit
```

### Étape 3 — Extraire les données manquantes des PDF

```bash
# Extraire les plafonds/franchises manquants (utilise l'API Claude ou Gemini)
python -m extraction.extract_from_pdf

# Re-vérifier après extraction
python -m extraction.audit
```

### Étape 4 — Lancer le serveur MCP

```bash
# Mode stdio (pour Claude Desktop / Cursor)
python -m server.server

# Mode SSE (pour intégration HTTP)
python -m server.server --transport sse --port 8000
```

### Intégration Cursor

Le fichier `.cursor/mcp.json` est déjà configuré. Cursor détectera automatiquement
le serveur MCP. Vous pourrez interagir avec vos données de garanties directement
depuis l'éditeur.

### Intégration Claude Desktop

Ajoutez dans `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac)
ou `%APPDATA%\Claude\claude_desktop_config.json` (Windows) :

```json
{
  "mcpServers": {
    "garanties-cb": {
      "command": "python",
      "args": ["-m", "server.server"],
      "cwd": "/chemin/vers/mcp-garanties-cb",
      "env": {
        "PYTHONPATH": "/chemin/vers/mcp-garanties-cb"
      }
    }
  }
}
```
