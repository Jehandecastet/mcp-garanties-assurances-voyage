# Audit & TODO — Comparateur de Garanties CB (IMA)

> Dernière mise à jour : 26 février 2026

> **Le pipeline de normalisation est désormais 100 % automatisé** (`apply_corrections` → `normalize` → `extract_from_pdf`). La base de données est purifiée et prête pour le serveur MCP : 0 orpheline, 0 NaN dans `est_incluse`, 44 garanties référencées.

---

## État de la base de données (fichier normalisé)

| Indicateur                       | Valeur                            |
|----------------------------------|-----------------------------------|
| Nombre de cartes                 | 211                               |
| Nombre de banques                | 38                                |
| Types de garanties (REF)         | **44** (26 d'origine + 18 ajoutées) |
| Lignes matrice garanties         | 4 781                             |
| Garanties incluses               | **4 077** (0 NaN restant)         |
| Taux de remplissage plafonds     | **99,2 %** (32 manquants)         |
| Taux de remplissage franchises   | **93,5 %** (263 manquants)        |
| Garanties orphelines             | **0**                             |

---

## Pipeline de traitement

- [x] **Corrections IMA** — `extraction/apply_corrections.py`
  Les 27 corrections signalées par IMA ont été appliquées (152 cellules modifiées).

- [x] **Normalisation** — `extraction/normalize.py`
  5 étapes automatisées : statuts, zones, garanties binaires, garanties orphelines (27 renommées + 18 ajoutées), `est_incluse` NaN → True.

- [x] **Extraction PDF** — `extraction/extract_from_pdf.py`
  Basculé sur l'API Gemini (`gemini-2.5-flash`). 60 valeurs extraites lors de la dernière exécution (franchises, plafonds, retards vol).

- [x] **Serveur MCP** — `server/server.py`
  Opérationnel via FastMCP. 7 outils, 4 ressources, 2 prompts. Compatible Cursor et Claude Desktop (stdio + SSE).

---

## Priorités

### Priorité 1 — Qualité des données

| # | Tâche | Statut |
|---|-------|--------|
| 1A | Extraction des plafonds/franchises manquants depuis les PDF | ✅ Terminé — 60 valeurs extraites via Gemini |
| 1B | Correction des `est_incluse = NaN` (231 lignes) | ✅ Terminé — passées à True (présence = inclusion) |
| 1C | Nettoyage des garanties orphelines (45 garanties) | ✅ Terminé — 27 renommées, 18 ajoutées à REF, 0 orpheline restante |
| 1D | Valider les extractions à confiance MOYENNE/BASSE | 🔲 À faire — vérification humaine recommandée |

### Priorité 2 — Enrichissement

| # | Tâche | Statut |
|---|-------|--------|
| 2A | Extraire les exclusions manquantes depuis les PDF | 🔲 À faire |
| 2B | Compléter les définitions des assurés (345 doublons dans `DEFINITIONS_ASSURES`) | 🔲 À faire |
| 2C | Remplir les URLs manquantes des CGV assurance/assistance | 🔲 À faire |
| 2D | Traiter la carte orpheline `HLB-VISA-HELLOONE` (0 garantie) | 🔲 À faire |

### Priorité 3 — Fiabilisation du serveur MCP

| # | Tâche | Statut |
|---|-------|--------|
| 3A | Mise en place du serveur MCP (outils, ressources, prompts) | ✅ Terminé |
| 3B | Tests automatisés du pipeline complet (`tests/test_pipeline.py`) | 🔲 À faire |
| 3C | Gestion du cache / rechargement à chaud des données | 🔲 À faire |
| 3D | Supprimer/documenter les colonnes 100 % vides de MATRICE | 🔲 À faire |

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
