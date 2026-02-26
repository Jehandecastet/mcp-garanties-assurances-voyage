# Audit & TODO — Comparateur de Garanties CB (IMA)

> Dernière mise à jour : 26 février 2026

---

## État de la base de données (fichier normalisé)

| Indicateur                  | Valeur           |
|-----------------------------|------------------|
| Nombre de cartes            | 211              |
| Nombre de banques           | 38               |
| Types de garanties          | 26               |
| Garanties incluses (lignes) | 3 847            |
| Taux de remplissage plafonds   | **99,2 %** (29 manquants) |
| Taux de remplissage franchises | **98,5 %** (59 manquants) |

---

## Pipeline de traitement

- [x] **Corrections IMA** — `extraction/apply_corrections.py`
  Les 27 corrections signalées par IMA (onglet `SUIVI_CORRECTIONS_IMA`) ont été appliquées.

- [x] **Normalisation** — `extraction/normalize.py`
  Statuts, zones géographiques et garanties orphelines normalisés. La boucle de normalisation fonctionne parfaitement.

- [x] **Extraction des données manquantes depuis les PDF** — `extraction/extract_from_pdf.py`
  Le script d'extraction a été basculé avec succès sur l'API Gemini (`gemini-2.5-flash`) en remplacement d'Anthropic Claude. Le fichier utilise désormais le SDK `google-genai` et envoie les PDF via `Part.from_bytes`.

- [x] **Serveur MCP** — `server/server.py`
  Le serveur MCP est en place et opérationnel. Il expose 7 outils, 4 ressources et 2 prompts via FastMCP. Compatible Cursor et Claude Desktop (stdio + SSE).

---

## Priorités

### Priorité 1 — Qualité des données

| # | Tâche | Statut |
|---|-------|--------|
| 1A | Extraction des plafonds manquants depuis les PDF | ✅ Terminé — script opérationnel sur API Gemini |
| 1B | Compléter les 29 plafonds encore manquants | 🔲 À faire — lancer `python -m extraction.extract_from_pdf` sur les cartes concernées |
| 1C | Compléter les 59 franchises encore manquantes | 🔲 À faire — même pipeline que 1B |
| 1D | Valider les extractions à confiance MOYENNE/BASSE | 🔲 À faire — vérification humaine recommandée |

### Priorité 2 — Enrichissement

| # | Tâche | Statut |
|---|-------|--------|
| 2A | Extraire les exclusions manquantes depuis les PDF | 🔲 À faire |
| 2B | Compléter les définitions des assurés (doublons à nettoyer : 345 dans `DEFINITIONS_ASSURES`) | 🔲 À faire |
| 2C | Remplir les URLs manquantes des CGV assurance/assistance | 🔲 À faire |

### Priorité 3 — Fiabilisation du serveur MCP

| # | Tâche | Statut |
|---|-------|--------|
| 3A | Mise en place du serveur MCP (outils, ressources, prompts) | ✅ Terminé |
| 3B | Tests automatisés du pipeline complet (`tests/test_pipeline.py`) | 🔲 À faire |
| 3C | Gestion du cache / rechargement à chaud des données | 🔲 À faire |
| 3D | Monitoring des appels et logs d'utilisation | 🔲 À faire |

---

## Outils disponibles

| Script | Commande |
|--------|----------|
| Appliquer les corrections IMA | `python -m extraction.apply_corrections` |
| Normaliser la base | `python -m extraction.normalize` |
| Extraire les données manquantes (Gemini) | `python -m extraction.extract_from_pdf` |
| Audit qualité | `python -m extraction.audit` |
| Comparer original vs corrigé | `python check_diff.py` |
| Lancer le serveur MCP | `python -m server.server` |
