"""
Applique les corrections IMA en statut "À CORRIGER" sur la base de données.

Lit l'onglet SUIVI_CORRECTIONS_IMA, identifie les corrections en attente,
et les applique sur les onglets correspondants (MATRICE_GARANTIES, EXCLUSIONS, etc.)

Usage :
    python -m extraction.apply_corrections
    python -m extraction.apply_corrections --dry-run   # Affiche sans modifier
"""

import re
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()
console = Console()

EXCEL_PATH = Path("data/Migration_INEKTO_V2_2.xlsx")
OUTPUT_PATH = Path("data/Migration_INEKTO_V2_2_CORRIGE.xlsx")


def parse_champ_garantie(champ: str) -> tuple[str, str | None]:
    """
    Parse le champ de correction pour extraire le nom de colonne et la garantie.
    Ex: 'franchise_montant (frais_medicaux_etranger)' → ('franchise_montant', 'frais_medicaux_etranger')
    Ex: 'franchise_montant' → ('franchise_montant', None)
    """
    match = re.match(r"^(\w+)\s*\((\w+)\)$", champ.strip())
    if match:
        return match.group(1), match.group(2)
    return champ.strip(), None


def apply_matrice_correction(
    matrice: pd.DataFrame,
    carte: str,
    champ: str,
    valeur_erronee,
    valeur_corrigee,
) -> tuple[pd.DataFrame, bool]:
    """Applique une correction sur MATRICE_GARANTIES."""
    col_name, garantie = parse_champ_garantie(champ)

    if col_name not in matrice.columns:
        console.print(f"  [red]⚠ Colonne '{col_name}' introuvable dans MATRICE_GARANTIES[/red]")
        return matrice, False

    mask = matrice["id_carte"] == carte
    if garantie:
        mask = mask & (matrice["id_garantie"] == garantie)

    rows = matrice[mask]
    if rows.empty:
        console.print(f"  [red]⚠ Aucune ligne trouvée pour carte={carte}, garantie={garantie}[/red]")
        return matrice, False

    # Convertir la valeur corrigée au bon type
    try:
        val = float(valeur_corrigee) if pd.notna(valeur_corrigee) else None
    except (ValueError, TypeError):
        val = valeur_corrigee

    count = mask.sum()
    matrice.loc[mask, col_name] = val
    console.print(f"  [green]✓ {count} ligne(s) modifiée(s) : {col_name}={val}[/green]")
    return matrice, True


def apply_exclusion_correction(
    exclusions: pd.DataFrame,
    carte: str,
    champ: str,
    valeur_erronee,
    valeur_corrigee,
) -> tuple[pd.DataFrame, bool]:
    """Applique une correction sur EXCLUSIONS."""
    mask = exclusions["id_carte"] == carte
    if champ in exclusions.columns:
        rows = exclusions[mask]
        if not rows.empty:
            try:
                val = float(valeur_corrigee) if pd.notna(valeur_corrigee) else None
            except (ValueError, TypeError):
                val = valeur_corrigee
            exclusions.loc[mask, champ] = val
            console.print(f"  [green]✓ {mask.sum()} ligne(s) modifiée(s) : {champ}={val}[/green]")
            return exclusions, True
    console.print(f"  [yellow]⚠ Correction EXCLUSIONS non appliquée : {carte}/{champ}[/yellow]")
    return exclusions, False


def main():
    dry_run = "--dry-run" in sys.argv

    if not EXCEL_PATH.exists():
        console.print(f"[red]Fichier introuvable : {EXCEL_PATH}[/red]")
        console.print("Copiez votre fichier Excel dans data/")
        return

    console.print(f"\n[bold]📋 Application des corrections IMA[/bold]")
    if dry_run:
        console.print("[yellow]Mode dry-run : aucune modification ne sera sauvegardée[/yellow]\n")

    # Charger les données
    xls = pd.ExcelFile(EXCEL_PATH)
    corrections = pd.read_excel(xls, "SUIVI_CORRECTIONS_IMA", header=0)
    matrice = pd.read_excel(xls, "MATRICE_GARANTIES", header=0)
    exclusions = pd.read_excel(xls, "EXCLUSIONS", header=0)

    a_corriger = corrections[corrections["statut"] == "À CORRIGER"]
    console.print(f"Corrections en attente : [bold]{len(a_corriger)}[/bold]\n")

    # Tableau récapitulatif
    table = Table(title="Corrections à appliquer")
    table.add_column("ID", style="cyan")
    table.add_column("Onglet")
    table.add_column("Carte")
    table.add_column("Champ")
    table.add_column("Ancien", style="red")
    table.add_column("Nouveau", style="green")

    applied = 0
    failed = 0

    for _, row in a_corriger.iterrows():
        corr_id = row["id_correction"]
        onglet = row["onglet"]
        carte = row["carte"]
        champ = str(row["champ"])
        val_old = row["valeur_erronee"]
        val_new = row["valeur_corrigee"]

        table.add_row(corr_id, onglet, carte, champ, str(val_old), str(val_new))

        if not dry_run:
            console.print(f"\n[bold]{corr_id}[/bold] — {carte} / {champ}")
            success = False

            if onglet == "MATRICE_GARANTIES":
                matrice, success = apply_matrice_correction(
                    matrice, carte, champ, val_old, val_new
                )
            elif onglet == "EXCLUSIONS":
                exclusions, success = apply_exclusion_correction(
                    exclusions, carte, champ, val_old, val_new
                )
            else:
                console.print(f"  [yellow]⚠ Onglet '{onglet}' non géré automatiquement[/yellow]")

            if success:
                # Mettre à jour le statut de la correction
                idx = corrections[corrections["id_correction"] == corr_id].index
                corrections.loc[idx, "statut"] = "CORRIGE"
                applied += 1
            else:
                failed += 1

    console.print()
    console.print(table)

    if dry_run:
        console.print(f"\n[yellow]Dry-run terminé. Relancez sans --dry-run pour appliquer.[/yellow]")
        return

    console.print(f"\n[bold]Résultat : {applied} appliquées, {failed} échouées[/bold]")

    if applied > 0:
        console.print(f"\n💾 Sauvegarde dans {OUTPUT_PATH}...")

        # Recharger tous les onglets et sauvegarder
        all_sheets = {}
        for sheet_name in xls.sheet_names:
            if sheet_name == "MATRICE_GARANTIES":
                all_sheets[sheet_name] = matrice
            elif sheet_name == "EXCLUSIONS":
                all_sheets[sheet_name] = exclusions
            elif sheet_name == "SUIVI_CORRECTIONS_IMA":
                all_sheets[sheet_name] = corrections
            else:
                all_sheets[sheet_name] = pd.read_excel(xls, sheet_name, header=0)

        with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
            for sheet_name, df in all_sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        console.print(f"[green]✅ Fichier sauvegardé : {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    main()
