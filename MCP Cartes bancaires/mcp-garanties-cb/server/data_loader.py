"""
Charge la base de données INEKTO depuis le fichier Excel
et expose des fonctions de requête performantes.

Les données sont chargées en mémoire au démarrage et indexées pour
des recherches rapides.
"""

import os
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Chercher le fichier le plus récent
_CANDIDATES = [
    os.getenv("EXCEL_PATH", ""),
    "data/Migration_INEKTO_V2_2_ENRICHI.xlsx",
    "data/Migration_INEKTO_V2_2_NORMALISE.xlsx",
    "data/Migration_INEKTO_V2_2_CORRIGE.xlsx",
    "data/Migration_INEKTO_V2_2.xlsx",
]


def _find_excel() -> Path:
    for p in _CANDIDATES:
        if p and Path(p).exists():
            return Path(p)
    raise FileNotFoundError("Aucun fichier Excel trouvé. Copiez-le dans data/")


class GarantiesDB:
    """Base de données en mémoire des garanties cartes bancaires."""

    def __init__(self, excel_path: Optional[Path] = None):
        self.path = excel_path or _find_excel()
        self._load()

    def _load(self):
        xls = pd.ExcelFile(self.path)
        self.cartes = pd.read_excel(xls, "CARTES", header=0)
        self.matrice = pd.read_excel(xls, "MATRICE_GARANTIES", header=0)
        self.ref_banques = pd.read_excel(xls, "REF_BANQUES", header=0)
        self.ref_garanties = pd.read_excel(xls, "REF_GARANTIES", header=0)
        self.ref_zones = pd.read_excel(xls, "REF_ZONES", header=0)
        self.ref_unites = pd.read_excel(xls, "REF_UNITES", header=0)
        self.definitions_assures = pd.read_excel(xls, "DEFINITIONS_ASSURES", header=0)
        self.conditions = pd.read_excel(xls, "CONDITIONS_APPLICATION", header=0)
        self.exclusions = pd.read_excel(xls, "EXCLUSIONS", header=0)
        self.details_rc_location = pd.read_excel(xls, "DETAILS_RC_LOCATION", header=0)
        self.partenaires = pd.read_excel(xls, "REF_PARTENAIRES", header=0)

        # Index pour recherche rapide
        self._cartes_idx = {row["id_carte"]: row.to_dict() for _, row in self.cartes.iterrows()}
        self._banques_idx = {row["id_banque"]: row.to_dict() for _, row in self.ref_banques.iterrows()}

    def lister_cartes(
        self,
        reseau: Optional[str] = None,
        gamme: Optional[str] = None,
        banque: Optional[str] = None,
    ) -> list[dict]:
        """Liste les cartes avec filtres optionnels."""
        df = self.cartes.copy()
        if reseau:
            df = df[df["reseau"].str.upper() == reseau.upper()]
        if gamme:
            df = df[df["gamme_normalisee"].str.upper() == gamme.upper()]
        if banque:
            df = df[df["banque"].str.contains(banque, case=False, na=False)]

        return [
            {
                "id_carte": row["id_carte"],
                "banque": row["banque"],
                "reseau": row["reseau"],
                "nom_commercial": row["nom_commercial"],
                "gamme": row["gamme_normalisee"],
                "gamme_commerciale": row["gamme_commerciale"],
            }
            for _, row in df.iterrows()
        ]

    def details_carte(self, carte_id: str) -> Optional[dict]:
        """Retourne les détails complets d'une carte."""
        if carte_id not in self._cartes_idx:
            return None

        carte = self._cartes_idx[carte_id]

        # Garanties
        gar = self.matrice[self.matrice["id_carte"] == carte_id]
        garanties = []
        for _, g in gar.iterrows():
            entry = {
                "id_garantie": g["id_garantie"],
                "est_incluse": bool(g["est_incluse"]) if pd.notna(g["est_incluse"]) else None,
                "zone": g["zone"] if pd.notna(g["zone"]) else None,
            }
            if pd.notna(g.get("plafond_montant")):
                entry["plafond_montant"] = float(g["plafond_montant"])
                entry["plafond_unite"] = g.get("plafond_unite")
            if g.get("plafond_frais_reels") == True:
                entry["plafond_frais_reels"] = True
            if pd.notna(g.get("franchise_montant")):
                entry["franchise_montant"] = float(g["franchise_montant"])
            if pd.notna(g.get("paiement_cb_requis")):
                entry["paiement_cb_requis"] = bool(g["paiement_cb_requis"])
            garanties.append(entry)

        # Bénéficiaires
        defs = self.definitions_assures[self.definitions_assures["id_carte"] == carte_id]
        beneficiaires = []
        for _, d in defs.iterrows():
            beneficiaires.append({
                "type": d["type_assure"],
                "couvert": bool(d["est_couvert"]) if pd.notna(d["est_couvert"]) else None,
                "age_max": int(d["age_max"]) if pd.notna(d["age_max"]) else None,
                "condition_cohabitation": bool(d["condition_cohabitation"]) if pd.notna(d["condition_cohabitation"]) else None,
            })

        # Conditions
        cond = self.conditions[self.conditions["id_carte"] == carte_id]
        conditions = {}
        if not cond.empty:
            row = cond.iloc[0]
            if pd.notna(row.get("duree_voyage_max_jour")):
                conditions["duree_voyage_max_jours"] = int(row["duree_voyage_max_jour"])
            if pd.notna(row.get("distance_min_domicile")):
                conditions["distance_min_domicile_km"] = int(row["distance_min_domicile"])
            if pd.notna(row.get("delai_declaration_jours")):
                conditions["delai_declaration_jours"] = int(row["delai_declaration_jours"])

        return {
            "id_carte": carte_id,
            "banque": carte.get("banque"),
            "reseau": carte.get("reseau"),
            "nom_commercial": carte.get("nom_commercial"),
            "gamme": carte.get("gamme_normalisee"),
            "url_cgv_assurance": carte.get("url_cgv_assurance"),
            "url_cgv_assistance": carte.get("url_cgv_assistance"),
            "garanties": garanties,
            "beneficiaires": beneficiaires,
            "conditions": conditions,
        }

    def comparer(self, carte_id_1: str, carte_id_2: str) -> Optional[dict]:
        """Compare deux cartes sur toutes les garanties."""
        c1 = self.details_carte(carte_id_1)
        c2 = self.details_carte(carte_id_2)
        if not c1 or not c2:
            return None

        # Indexer les garanties par id
        g1_idx = {g["id_garantie"]: g for g in c1["garanties"]}
        g2_idx = {g["id_garantie"]: g for g in c2["garanties"]}
        all_gar = set(list(g1_idx.keys()) + list(g2_idx.keys()))

        comparaisons = []
        avantages_1 = []
        avantages_2 = []

        for gar_id in sorted(all_gar):
            g1 = g1_idx.get(gar_id, {})
            g2 = g2_idx.get(gar_id, {})
            inc1 = g1.get("est_incluse", False)
            inc2 = g2.get("est_incluse", False)
            p1 = g1.get("plafond_montant")
            p2 = g2.get("plafond_montant")

            comp = {"garantie": gar_id}
            comp[carte_id_1] = {"incluse": inc1, "plafond": p1, "franchise": g1.get("franchise_montant")}
            comp[carte_id_2] = {"incluse": inc2, "plafond": p2, "franchise": g2.get("franchise_montant")}
            comparaisons.append(comp)

            # Identifier avantages
            ref = self.ref_garanties[self.ref_garanties["id_garantie"] == gar_id]
            gar_nom = ref.iloc[0]["nom"] if not ref.empty else gar_id

            if inc1 and not inc2:
                avantages_1.append(f"{gar_nom} incluse (absente de {c2['nom_commercial']})")
            elif inc2 and not inc1:
                avantages_2.append(f"{gar_nom} incluse (absente de {c1['nom_commercial']})")
            elif inc1 and inc2 and p1 and p2:
                if p1 > p2:
                    avantages_1.append(f"{gar_nom}: plafond {p1}€ vs {p2}€")
                elif p2 > p1:
                    avantages_2.append(f"{gar_nom}: plafond {p2}€ vs {p1}€")

        return {
            "carte_1": {"id": carte_id_1, "nom": c1["nom_commercial"], "banque": c1["banque"], "gamme": c1["gamme"]},
            "carte_2": {"id": carte_id_2, "nom": c2["nom_commercial"], "banque": c2["banque"], "gamme": c2["gamme"]},
            "comparaisons": comparaisons,
            "avantages_carte_1": avantages_1,
            "avantages_carte_2": avantages_2,
            "beneficiaires_1": c1["beneficiaires"],
            "beneficiaires_2": c2["beneficiaires"],
            "conditions_1": c1["conditions"],
            "conditions_2": c2["conditions"],
        }

    def rechercher_par_situation(self, situation: str) -> list[dict]:
        """Recherche les cartes couvrant une situation donnée."""
        MAPPING = {
            "médecin": "frais_medicaux_etranger", "medical": "frais_medicaux_etranger",
            "hopital": "frais_medicaux_etranger", "maladie": "frais_medicaux_etranger",
            "dentaire": "urgence_dentaire", "dent": "urgence_dentaire",
            "rapatriement": "rapatriement", "rapatrier": "rapatriement",
            "annulation": "annulation", "annuler": "annulation",
            "bagage": "bagages", "valise": "bagages",
            "retard": "retard_de_vol", "avion": "retard_de_vol",
            "vol retardé": "retard_de_vol",
            "location": "dommages_vehicule_location", "voiture": "dommages_vehicule_location",
            "véhicule": "dommages_vehicule_location",
            "franchise location": "rachat_franchise_location",
            "ski": "sport", "montagne": "sport", "neige": "frais_medicaux_neige",
            "responsabilité": "responsabilite_civile",
            "décès": "deces_invalidite", "invalidité": "deces_invalidite",
        }

        sit_lower = situation.lower()
        garanties_cibles = set()
        for mot, gar in MAPPING.items():
            if mot in sit_lower:
                garanties_cibles.add(gar)

        if not garanties_cibles:
            return []

        resultats = []
        incluses = self.matrice[
            (self.matrice["est_incluse"] == True)
            & (self.matrice["id_garantie"].isin(garanties_cibles))
        ]

        for carte_id, group in incluses.groupby("id_carte"):
            carte = self._cartes_idx.get(carte_id, {})
            couvertures = []
            for _, g in group.iterrows():
                couvertures.append({
                    "garantie": g["id_garantie"],
                    "plafond": float(g["plafond_montant"]) if pd.notna(g["plafond_montant"]) else None,
                    "frais_reels": bool(g["plafond_frais_reels"]) if pd.notna(g["plafond_frais_reels"]) else False,
                    "franchise": float(g["franchise_montant"]) if pd.notna(g["franchise_montant"]) else None,
                })

            resultats.append({
                "carte": carte_id,
                "banque": carte.get("banque"),
                "nom": carte.get("nom_commercial"),
                "gamme": carte.get("gamme_normalisee"),
                "couvertures": couvertures,
            })

        # Trier par plafond max décroissant
        resultats.sort(
            key=lambda r: max((c.get("plafond") or 0 for c in r["couvertures"]), default=0),
            reverse=True,
        )
        return resultats

    def simuler_sinistre(
        self,
        carte_id: str,
        garantie_id: str,
        montant: float,
    ) -> Optional[dict]:
        """Simule un sinistre et calcule l'indemnisation."""
        mask = (self.matrice["id_carte"] == carte_id) & (self.matrice["id_garantie"] == garantie_id)
        rows = self.matrice[mask]
        if rows.empty:
            return {"erreur": f"Garantie {garantie_id} non trouvée pour {carte_id}"}

        g = rows.iloc[0]
        if g["est_incluse"] != True:
            return {
                "carte": carte_id, "garantie": garantie_id, "couvert": False,
                "message": "Cette garantie n'est pas incluse dans cette carte.",
            }

        plafond = float(g["plafond_montant"]) if pd.notna(g["plafond_montant"]) else None
        frais_reels = g.get("plafond_frais_reels") == True
        franchise = float(g["franchise_montant"]) if pd.notna(g["franchise_montant"]) else 0

        if frais_reels:
            indemnisation = max(0, montant - franchise)
        elif plafond:
            indemnisation = min(max(0, montant - franchise), plafond)
        else:
            indemnisation = max(0, montant - franchise)

        return {
            "carte": carte_id,
            "garantie": garantie_id,
            "couvert": True,
            "montant_sinistre": montant,
            "plafond": plafond,
            "frais_reels": frais_reels,
            "franchise": franchise,
            "indemnisation_estimee": indemnisation,
            "reste_a_charge": montant - indemnisation,
            "taux_couverture_pct": round(indemnisation / montant * 100, 1) if montant > 0 else 0,
            "avertissement": "Simulation indicative. Contactez IMA pour une évaluation officielle.",
        }


# Singleton
_db: Optional[GarantiesDB] = None


def get_db() -> GarantiesDB:
    global _db
    if _db is None:
        _db = GarantiesDB()
    return _db
