"""
Normalise la base de données :
  1. Statuts du SUIVI_CORRECTIONS_IMA (accents → sans accents)
  2. Zone orpheline MONDE_HORS_PAYS_RESIDENCE → HORS_RESIDENCE
  3. Garantie rachat_franchise_location → est_binaire=TRUE
  4. Garanties orphelines → mapping vers REF_GARANTIES
  5. est_incluse NaN → True (présence = inclusion)

Usage :
    python -m extraction.normalize
    python -m extraction.normalize --dry-run
"""

import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
console = Console()

OUTPUT_PATH = Path("data/Migration_INEKTO_V2_2_NORMALISE.xlsx")

# Chaîne de priorité : enrichi > corrigé > source
EXCEL_PATH = Path("data/Migration_INEKTO_V2_2_CORRIGE.xlsx")
for candidate in [
    Path("data/Migration_INEKTO_V2_2_ENRICHI.xlsx"),
    Path("data/Migration_INEKTO_V2_2_CORRIGE.xlsx"),
    Path("data/Migration_INEKTO_V2_2.xlsx"),
]:
    if candidate.exists():
        EXCEL_PATH = candidate
        break

# ─────────────────────────────────────────────────────────────
# Mapping de normalisation des garanties orphelines
# ─────────────────────────────────────────────────────────────

GARANTIES_MAPPING = {
    # Garanties à rattacher à une garantie REF existante
    "annulation_voyage": "annulation",
    "modification_annulation_voyage": "annulation",
    "protection_des_achats": "garantie_achats",
    "garantie_achats": None,  # Déjà dans la liste? À ajouter à REF si absent
    "perte_vol_bagages": "bagages",
    "perte_vol_deterioration_bagages": "bagages",
    "retard_transport_annulation_transporteur": "retard_transport",
    "vehicule_location": "dommages_vehicule_location",
    "responsabilite_civile_sport": "responsabilite_civile",
    "responsabilite_civile_etranger_assistance_juridique_etranger": "responsabilite_civile",
    "location_equipement_ski": "sport",
    "frais_recherche_secours": "sport_recherche_secours",
    "avance_caution_penale": None,  # Garantie distincte → ajouter à REF
    "caution_penale": None,  # Alias → ajouter à REF
    "aide_juridique": None,
    "assistance_juridique_amiable": None,
    "prise_en_charge_honoraires_homme_de_loi": None,
    # Garanties décès/invalidité granulaires → rattacher à deces_invalidite
    "deces": "deces_invalidite",
    "deces_accident_transport_public": "deces_invalidite",
    "deces_invalidite_trajet": "deces_invalidite",
    "accident_voyage_deces": "deces_invalidite",
    "accident_voyage_transport_public": "deces_invalidite",
    "accident_voyage_vehicule_de_location": "deces_invalidite",
    "accident_voyage_vehicule_location_deces": "deces_invalidite",
    "perte_deux_mains_deux_pieds": "deces_invalidite",
    "perte_main_pied": "deces_invalidite",
    "perte_main_pied_perte_vue_oeil": "deces_invalidite",
    "perte_totale_vue_deux_yeux": "deces_invalidite",
    "perte_totale_vue_oeil_perte_main_pied": "deces_invalidite",
    "perte_totale_vue_un_oeil_perte_main_pied": "deces_invalidite",
    "perte_une_main_un_pied": "deces_invalidite",
    # Garanties achats/services
    "achat_a_distance": None,
    "achat_location_articles_premiere_necessite": None,
    "annulation_evenement": None,
    "avance_fonds_perte_vol_moyens_paiement": None,
    "avance_frais_carte_perdue_volee": None,
    "avance_frais_hospitalisation_etranger": "frais_medicaux_etranger",
    "execution_de_commande": None,
    "fraude": None,
    "utilisation_frauduleuse_carte": None,
    "utilisation_frauduleuse_telephone": None,
    "frais_supplementaires_transport": "retard_transport",
    "garantie_legale": None,
    "garantie_legale_annuelle": None,
    "location_materiel_professionnel": None,
}

# Normalisation des statuts
STATUTS_MAPPING = {
    "CORRIGÉ": "CORRIGE",
    "SUPPRIMÉ": "SUPPRIME",
    "AJOUTÉ": "AJOUTE",
    "À CORRIGER": "A_CORRIGER",
    "CLARIFICATION REQUISE": "CLARIFICATION_REQUISE",
}


def normalize_statuts(corrections: pd.DataFrame) -> pd.DataFrame:
    """Normalise les statuts : supprime accents, uniformise."""
    console.print("\n[bold]1. Normalisation des statuts SUIVI_CORRECTIONS_IMA[/bold]")
    changes = 0
    for old, new in STATUTS_MAPPING.items():
        mask = corrections["statut"] == old
        count = mask.sum()
        if count > 0:
            corrections.loc[mask, "statut"] = new
            console.print(f"  '{old}' → '{new}' : {count} lignes")
            changes += count
    console.print(f"  [green]Total : {changes} statuts normalisés[/green]")
    return corrections


def normalize_zones(matrice: pd.DataFrame) -> pd.DataFrame:
    """Corrige les zones orphelines."""
    console.print("\n[bold]2. Normalisation des zones[/bold]")
    mask = matrice["zone"] == "MONDE_HORS_PAYS_RESIDENCE"
    count = mask.sum()
    if count > 0:
        matrice.loc[mask, "zone"] = "HORS_RESIDENCE"
        console.print(f"  'MONDE_HORS_PAYS_RESIDENCE' → 'HORS_RESIDENCE' : {count} lignes")
    else:
        console.print("  Aucune zone orpheline trouvée")
    return matrice


def normalize_binary_guarantees(ref_garanties: pd.DataFrame) -> pd.DataFrame:
    """Marque les garanties binaires correctement."""
    console.print("\n[bold]3. Garanties binaires[/bold]")

    updates = {
        "rachat_franchise_location": True,  # Déjà TRUE dans le fichier, vérifier
        "teleconsultation": True,           # Déjà TRUE, vérifier
        "deces_invalidite": False,          # NaN → FALSE (barème, pas binaire)
    }

    for garantie, valeur in updates.items():
        mask = ref_garanties["id_garantie"] == garantie
        if mask.any():
            old = ref_garanties.loc[mask, "est_binaire"].values[0]
            ref_garanties.loc[mask, "est_binaire"] = valeur
            console.print(f"  {garantie}: est_binaire = {old} → {valeur}")

    return ref_garanties


GARANTIES_NEW_REF = {
    "garantie_achats": ("Garantie des achats", "ACHATS"),
    "avance_caution_penale": ("Avance de caution pénale", "ASSISTANCE_JURIDIQUE"),
    "caution_penale": ("Caution pénale", "ASSISTANCE_JURIDIQUE"),
    "aide_juridique": ("Aide juridique", "ASSISTANCE_JURIDIQUE"),
    "assistance_juridique_amiable": ("Assistance juridique amiable", "ASSISTANCE_JURIDIQUE"),
    "prise_en_charge_honoraires_homme_de_loi": ("Prise en charge honoraires d'avocat", "ASSISTANCE_JURIDIQUE"),
    "achat_a_distance": ("Achat à distance", "ACHATS"),
    "achat_location_articles_premiere_necessite": ("Achat/location articles de première nécessité", "ASSISTANCE"),
    "annulation_evenement": ("Annulation d'événement", "ANNULATION"),
    "avance_fonds_perte_vol_moyens_paiement": ("Avance de fonds perte/vol moyens de paiement", "ASSISTANCE"),
    "avance_frais_carte_perdue_volee": ("Avance frais carte perdue ou volée", "ASSISTANCE"),
    "execution_de_commande": ("Exécution de commande", "ACHATS"),
    "fraude": ("Fraude", "PROTECTION_MOYENS_PAIEMENT"),
    "utilisation_frauduleuse_carte": ("Utilisation frauduleuse de la carte", "PROTECTION_MOYENS_PAIEMENT"),
    "utilisation_frauduleuse_telephone": ("Utilisation frauduleuse du téléphone", "PROTECTION_MOYENS_PAIEMENT"),
    "garantie_legale": ("Garantie légale", "ACHATS"),
    "garantie_legale_annuelle": ("Garantie légale annuelle", "ACHATS"),
    "location_materiel_professionnel": ("Location de matériel professionnel", "PROFESSIONNEL"),
}


def fix_orphan_guarantees(
    matrice: pd.DataFrame, ref_garanties: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Renomme les garanties mappables et ajoute les nouvelles à REF_GARANTIES."""
    console.print("\n[bold]4. Garanties orphelines[/bold]")

    gar_ref = set(ref_garanties["id_garantie"].unique())
    gar_matrice = set(matrice["id_garantie"].unique())
    orphans = gar_matrice - gar_ref

    if not orphans:
        console.print("  Aucune garantie orpheline")
        return matrice, ref_garanties

    console.print(f"  {len(orphans)} garanties orphelines détectées\n")

    # --- Étape A : renommer les garanties mappables dans MATRICE ---
    renamed = 0
    for g in sorted(orphans):
        target = GARANTIES_MAPPING.get(g, "???")
        if target and target != "???":
            count = (matrice["id_garantie"] == g).sum()
            matrice.loc[matrice["id_garantie"] == g, "id_garantie"] = target
            console.print(f"    [green]→[/green] {g} ({count} lignes) → [green]{target}[/green]")
            renamed += count

    dupes_before = len(matrice)

    # Trier pour garder en priorité les lignes avec données enrichies
    enrichment_cols = [
        "rc_conditions", "rc_exclusions", "rc_personnes_couvertes",
        "conditions", "texte_source", "plafond_montant",
    ]
    for col in enrichment_cols:
        if col in matrice.columns:
            matrice[f"_has_{col}"] = matrice[col].notna().astype(int)
    sort_cols = [f"_has_{c}" for c in enrichment_cols if f"_has_{c}" in matrice.columns]
    if sort_cols:
        matrice = matrice.sort_values(sort_cols, ascending=False)

    matrice = matrice.drop_duplicates(subset=["id_carte", "id_garantie", "zone"], keep="first")
    matrice = matrice.drop(columns=[c for c in matrice.columns if c.startswith("_has_")], errors="ignore")

    dupes_removed = dupes_before - len(matrice)
    console.print(f"  [green]{renamed} lignes renommées[/green]", end="")
    if dupes_removed:
        console.print(f" ({dupes_removed} doublons fusionnés, lignes enrichies préservées)")
    else:
        console.print()

    # --- Étape B : ajouter les nouvelles garanties à REF_GARANTIES ---
    added = 0
    new_rows = []
    for g in sorted(orphans):
        if GARANTIES_MAPPING.get(g, "???") is not None:
            continue
        if g in gar_ref:
            continue
        if g not in GARANTIES_NEW_REF:
            console.print(f"    [red]?[/red] {g} → pas de définition, ignoré")
            continue

        nom, categorie = GARANTIES_NEW_REF[g]
        new_rows.append({
            "id_garantie": g,
            "nom": nom,
            "categorie": categorie,
            "id_garantie_parente": None,
            "est_binaire": False,
            "description": None,
            "libelle": nom,
        })
        console.print(f"    [yellow]＋[/yellow] {g} → [yellow]{nom}[/yellow] ({categorie})")
        added += 1

    if new_rows:
        ref_garanties = pd.concat(
            [ref_garanties, pd.DataFrame(new_rows)], ignore_index=True
        )

    console.print(f"  [green]{added} garanties ajoutées à REF_GARANTIES[/green]")

    # --- Vérification finale ---
    remaining = set(matrice["id_garantie"].unique()) - set(ref_garanties["id_garantie"].unique())
    if remaining:
        console.print(f"  [yellow]⚠ {len(remaining)} orphelines restantes : {sorted(remaining)}[/yellow]")
    else:
        console.print(f"  [green]✓ 0 garantie orpheline restante[/green]")

    return matrice, ref_garanties


def fix_null_incluse(matrice: pd.DataFrame) -> pd.DataFrame:
    """Remplace les est_incluse=NaN par True (la présence de la ligne vaut inclusion)."""
    console.print("\n[bold]5. Nettoyage est_incluse = NaN[/bold]")

    null_mask = matrice["est_incluse"].isna()
    count = null_mask.sum()

    if count == 0:
        console.print("  Aucune valeur NaN")
        return matrice

    console.print(f"  {count} lignes avec est_incluse = NaN")
    matrice.loc[null_mask, "est_incluse"] = True
    console.print(f"  [green]{count} lignes passées à True[/green]")

    remaining = matrice["est_incluse"].isna().sum()
    console.print(f"  [green]✓ {remaining} NaN restant[/green]")

    return matrice


def main():
    dry_run = "--dry-run" in sys.argv

    if not EXCEL_PATH.exists():
        console.print(f"[red]Fichier introuvable : {EXCEL_PATH}[/red]")
        return

    console.print(f"\n[bold]🔧 Normalisation de la base de données[/bold]")
    console.print(f"Source : {EXCEL_PATH}")
    if dry_run:
        console.print("[yellow]Mode dry-run\n[/yellow]")

    xls = pd.ExcelFile(EXCEL_PATH)
    corrections = pd.read_excel(xls, "SUIVI_CORRECTIONS_IMA", header=0)
    matrice = pd.read_excel(xls, "MATRICE_GARANTIES", header=0)
    ref_garanties = pd.read_excel(xls, "REF_GARANTIES", header=0)

    # 1. Statuts
    corrections = normalize_statuts(corrections)

    # 2. Zones
    matrice = normalize_zones(matrice)

    # 3. Garanties binaires
    ref_garanties = normalize_binary_guarantees(ref_garanties)

    # 4. Garanties orphelines (renommage + ajout à REF)
    matrice, ref_garanties = fix_orphan_guarantees(matrice, ref_garanties)

    # 5. Nettoyage est_incluse NaN → True
    matrice = fix_null_incluse(matrice)

    if dry_run:
        console.print(f"\n[yellow]Dry-run terminé.[/yellow]")
        return

    # Sauvegarder
    console.print(f"\n💾 Sauvegarde dans {OUTPUT_PATH}...")
    all_sheets = {}
    for sheet_name in xls.sheet_names:
        if sheet_name == "MATRICE_GARANTIES":
            all_sheets[sheet_name] = matrice
        elif sheet_name == "SUIVI_CORRECTIONS_IMA":
            all_sheets[sheet_name] = corrections
        elif sheet_name == "REF_GARANTIES":
            all_sheets[sheet_name] = ref_garanties
        else:
            all_sheets[sheet_name] = pd.read_excel(xls, sheet_name, header=0)

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        for sheet_name, df in all_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    console.print(f"[green]✅ Fichier normalisé sauvegardé : {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    main()
