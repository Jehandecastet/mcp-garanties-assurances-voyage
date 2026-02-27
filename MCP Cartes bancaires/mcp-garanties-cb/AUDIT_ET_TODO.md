# Audit & TODO — Comparateur de Garanties CB (IMA)

> Dernière mise à jour : 25 février 2026

> **Le pipeline de normalisation est désormais 100 % automatisé et incrémental** (`apply_corrections` → `normalize` → `extract_from_pdf`). La base de données est purifiée et enrichie pour le serveur MCP : 0 orpheline, 0 NaN dans `est_incluse`, 44 garanties référencées, **analyse juridique RC complète** (exclusions, conditions, personnes couvertes) sur l'ensemble du catalogue.

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
  Basculé sur l'API Gemini (`gemini-3.1-pro-preview`). Pipeline incrémental (lecture prioritaire du fichier `_CORRIGE.xlsx`). 60+ valeurs standard extraites + enrichissement RC complet (voir section dédiée ci-dessous).

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

### ✅ Chantier Responsabilité Civile (RC) — Terminé

> **Le serveur MCP est désormais capable de restituer une analyse juridique de pointe sur les exclusions, conditions d'activation et personnes couvertes de la Responsabilité Civile de chaque carte du catalogue.**

| # | Accomplissement | Détail |
|---|-----------------|--------|
| RC-1 | Mode `--enrichir-rc` propulsé par **Gemini 3.1 Pro** | Prompt spécialisé d'analyse du jargon juridique des CGV : extraction des exclusions, conditions d'activation, personnes couvertes, sous-plafonds et zone géographique. |
| RC-2 | Restructuration de la BDD avec **colonnes dédiées illimitées** | Création automatique de `rc_conditions`, `rc_exclusions`, `rc_personnes_couvertes`, `rc_sous_plafonds`, `rc_zone_geographique` — supprime la troncature à 500 car. qui perdait les données. |
| RC-3 | Pipeline d'extraction **rendu incrémental** | Chaîne de priorité `ENRICHI > CORRIGE > NORMALISE > source brut` : le script reprend là où il s'était arrêté, économisant temps et jetons API. Écriture en place dans le fichier source. |
| RC-4 | Extraction réussie sur l'ensemble du catalogue | **+220 valeurs juridiques complexes** intégrées (exclusions véhicules à moteur, pays sous embargo, RC pro, sports dangereux…), y compris les plafonds aux frais réels et les franchises spécifiques (ex : 30 € Neige). |

**Exemples de données RC extraites :**
- AXA Visa Infinite : 4 600 000 € RC (8 exclusions, 5 conditions, 3 catégories de personnes couvertes)
- BNP Visa Premier : 1 525 000 € RC (6 exclusions, 4 conditions, 5 catégories de personnes couvertes)

**Commandes :**
```bash
python -m extraction.extract_from_pdf --enrichir-rc                         # Toutes les cartes
python -m extraction.extract_from_pdf --enrichir-rc --carte AXA-VISA-INFINITE  # Une carte
python -m extraction.extract_from_pdf --enrichir-rc --dry-run               # Prévisualiser
```

---

### Priorité 2 — Enrichissement

| # | Tâche | Statut |
|---|-------|--------|
| 2A | Extraire les exclusions manquantes depuis les PDF | ✅ Terminé — intégré au chantier RC (colonnes `rc_exclusions`) |
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
| Enrichir la RC (toutes les cartes) | `python -m extraction.extract_from_pdf --enrichir-rc` |
| Enrichir la RC (une carte) | `python -m extraction.extract_from_pdf --enrichir-rc --carte <ID>` |
| Audit qualité | `python -m extraction.audit` |
| Comparer original vs corrigé | `python check_diff.py` |
| Lister les modèles Gemini disponibles | `python list_models.py` |
| Lancer le serveur MCP | `python -m server.server` |
