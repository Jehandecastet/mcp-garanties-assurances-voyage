# 🏦 Comparateur IMA - Serveur MCP (Cartes Bancaires)

Ce projet contient un serveur MCP (Model Context Protocol) couplé à une base de données d'assurances de cartes bancaires. Il permet à un assistant IA (comme l'Agent Cursor ou Claude Desktop) d'interroger en langage naturel les plafonds, franchises et exclusions juridiques (Responsabilité Civile, Location de voiture, Neige et Montagne, etc.) de plus de 210 cartes bancaires.

## 🛠️ Installation pour l'équipe

Pour tester ce serveur sur votre machine, suivez ces étapes :

**1. Récupérer le projet**

Dans votre terminal, clonez ce dépôt :

```bash
git clone git@github.com:Jehandecastet/mcp-garanties-assurances-voyage.git
cd mcp-garanties-assurances-voyage
```

**2. Préparer l'environnement Python**

```bash
python -m venv .venv
source .venv/bin/activate  # Sur Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

**3. Ajouter votre clé API**

Créez un fichier nommé `.env` à la racine du projet et ajoutez-y la clé API de Gemini (demandez-la à l'administrateur du projet) :

```
GEMINI_API_KEY=votre_cle_api_ici
```

*Note : Ce fichier est ignoré par Git pour des raisons de sécurité, ne le commitez jamais.*

## 🚀 Connecter Cursor au Serveur MCP

1. Ouvrez ce dossier avec Cursor.
2. Allez dans **Settings** > **Features** > **MCP**.
3. Cliquez sur **+ Add New MCP Server**.
   - **Name** : `ima-comparateur`
   - **Type** : `command`
   - **Command** : `.venv/bin/python -m server.server`

   > Si cela ne fonctionne pas, utilisez le chemin complet vers l'exécutable Python de votre `.venv` (ex : `/Users/votre-nom/chemin/du/projet/.venv/bin/python -m server.server`).

4. Enregistrez et vérifiez que le voyant passe au vert !

## 💡 Exemples de questions à poser à l'Agent (Cmd + L)

Maintenant que le serveur est branché, vous pouvez poser des questions pointues à l'IA :

- *"D'après les données normalisées, quelles sont les exclusions majeures de la Responsabilité Civile pour la carte AXA Visa Infinite ?"*
- *"Quelle carte entre la BNP Visa Premier et la CIC Mastercard Gold a la meilleure franchise pour la location de voiture ?"*
- *"Donne-moi les conditions d'activation pour la RC de la carte Caisse d'Épargne Visa Platinum."*
