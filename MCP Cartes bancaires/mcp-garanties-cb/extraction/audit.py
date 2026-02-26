"""
Vérifie la qualité de la base de données et produit un rapport.

Usage :
    python -m extraction.audit
    python -m extraction.audit --json    # Sortie JSON pour intégration CI
"""

import json
import sys
from pathlib import Path

import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from rich.console import Console
    from rich.table import Table
    console = Console()
except ImportError:
    # Fallback sans rich
    class _Console:
        def print(self, *args, **kwargs):
            text = str(args[0]) if args else ""
            # Strip rich markup
            import re
            text = re.sub(r"\[/?[^\]]*\]", "", text)
            print(text)
    console = _Console()
    Table = None

# Chercher le fichier le plus récent
CANDIDATES = [
    "data/Migration_INEKTO_V2_2_ENRICHI.xlsx",
    "data/Migration_INEKTO_V2_2_NORMALISE.xlsx",
    "data/Migration_INEKTO_V2_2_CORRIGE.xlsx",
    "data/Migration_INEKTO_V2_2.xlsx",
]

EXCEL_PATH = None
for p in CANDIDATES:
    if Path(p).exists():
        EXCEL_PATH = Path(p)
        break


def check_completeness(matrice: pd.DataFrame) -> dict:
    """Vérifie la complétude des données critiques."""
    incluses = matrice[matrice["est_incluse"] == True]
    binary = {"rachat_franchise_location", "teleconsultation", "retard_vol_parametrique", "dossier_retards_avion"}
    non_binary = incluses[~incluses["id_garantie"].isin(binary)]

    total = len(non_binary)
    plafond_ok = non_binary["plafond_montant"].notna().sum() + (non_binary["plafond_frais_reels"] == True).sum()
    franchise_ok = non_binary["franchise_montant"].notna().sum()

    return {
        "total_garanties_incluses": int(total),
        "plafond_rempli": int(plafond_ok),
        "plafond_pct": round(plafond_ok / total * 100, 1) if total > 0 else 0,
        "franchise_remplie": int(franchise_ok),
        "franchise_pct": round(franchise_ok / total * 100, 1) if total > 0 else 0,
    }


def check_referential_integrity(xls: pd.ExcelFile) -> dict:
    """Vérifie l'intégrité référentielle."""
    matrice = pd.read_excel(xls, "MATRICE_GARANTIES", header=0)
    cartes = pd.read_excel(xls, "CARTES", header=0)
    ref_garanties = pd.read_excel(xls, "REF_GARANTIES", header=0)
    ref_zones = pd.read_excel(xls, "REF_ZONES", header=0)

    issues = []

    # Cartes orphelines
    cartes_matrice = set(matrice["id_carte"].unique())
    cartes_ref = set(cartes["id_carte"].unique())
    orphans_m = cartes_matrice - cartes_ref
    orphans_c = cartes_ref - cartes_matrice
    if orphans_m:
        issues.append(f"Cartes dans MATRICE mais pas CARTES: {orphans_m}")
    if orphans_c:
        issues.append(f"Cartes dans CARTES sans données MATRICE: {orphans_c}")

    # Garanties orphelines
    gar_matrice = set(matrice["id_garantie"].unique())
    gar_ref = set(ref_garanties["id_garantie"].unique())
    orphans_g = gar_matrice - gar_ref
    if orphans_g:
        issues.append(f"{len(orphans_g)} garanties dans MATRICE absentes de REF: {sorted(orphans_g)[:5]}...")

    # Zones orphelines
    zones_matrice = set(matrice["zone"].dropna().unique())
    zones_ref = set(ref_zones["code_zone"].unique())
    orphans_z = zones_matrice - zones_ref
    if orphans_z:
        issues.append(f"Zones orphelines: {orphans_z}")

    # est_incluse NaN
    null_incluse = matrice["est_incluse"].isna().sum()
    if null_incluse > 0:
        issues.append(f"{null_incluse} lignes avec est_incluse=NaN")

    # Doublons
    dupes = matrice.duplicated(subset=["id_carte", "id_garantie", "zone"], keep=False).sum()
    if dupes > 0:
        issues.append(f"{dupes} doublons (carte+garantie+zone)")

    return {
        "issues_count": len(issues),
        "issues": issues,
        "orphan_cartes_matrice": list(orphans_m),
        "orphan_cartes_nodata": list(orphans_c),
        "orphan_garanties": len(orphans_g),
        "orphan_zones": list(orphans_z),
        "null_est_incluse": int(null_incluse),
        "duplicates": int(dupes),
    }


def check_corrections(corrections: pd.DataFrame) -> dict:
    """Vérifie l'état des corrections IMA."""
    statuts = corrections["statut"].value_counts().to_dict()
    pending = int(corrections["statut"].isin(["À CORRIGER", "A_CORRIGER"]).sum())
    return {"statuts": statuts, "pending": pending}


def main():
    json_output = "--json" in sys.argv

    if not EXCEL_PATH:
        msg = "Aucun fichier Excel trouvé dans data/"
        if json_output:
            print(json.dumps({"error": msg}))
        else:
            console.print(f"[red]{msg}[/red]")
        return

    if not json_output:
        console.print(f"\n[bold]🔍 Audit qualité — {EXCEL_PATH.name}[/bold]\n")

    xls = pd.ExcelFile(EXCEL_PATH)
    matrice = pd.read_excel(xls, "MATRICE_GARANTIES", header=0)
    corrections = pd.read_excel(xls, "SUIVI_CORRECTIONS_IMA", header=0)

    # 1. Complétude
    completeness = check_completeness(matrice)

    # 2. Intégrité référentielle
    integrity = check_referential_integrity(xls)

    # 3. Corrections
    corr_status = check_corrections(corrections)

    # Rapport
    report = {
        "fichier": str(EXCEL_PATH),
        "completeness": completeness,
        "integrity": integrity,
        "corrections": corr_status,
        "score_global": "OK" if integrity["issues_count"] == 0 and corr_status["pending"] == 0 else "ATTENTION",
    }

    if json_output:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    # Affichage
    if Table:
        table = Table(title="Complétude des données")
        table.add_column("Métrique")
        table.add_column("Valeur", justify="right")
        table.add_column("Taux", justify="right")
        table.add_row(
            "Plafonds remplis",
            f"{completeness['plafond_rempli']} / {completeness['total_garanties_incluses']}",
            f"{completeness['plafond_pct']}%",
        )
        table.add_row(
            "Franchises remplies",
            f"{completeness['franchise_remplie']} / {completeness['total_garanties_incluses']}",
            f"{completeness['franchise_pct']}%",
        )
        console.print(table)
    else:
        console.print(f"  Plafonds remplis   : {completeness['plafond_rempli']} / {completeness['total_garanties_incluses']} ({completeness['plafond_pct']}%)")
        console.print(f"  Franchises remplies: {completeness['franchise_remplie']} / {completeness['total_garanties_incluses']} ({completeness['franchise_pct']}%)")

    if integrity["issues"]:
        console.print(f"\n[bold yellow]⚠ {integrity['issues_count']} problèmes d'intégrité :[/bold yellow]")
        for issue in integrity["issues"]:
            console.print(f"  • {issue}")

    console.print(f"\n[bold]Corrections IMA :[/bold] {corr_status['pending']} en attente")
    for statut, count in corr_status["statuts"].items():
        console.print(f"  {statut}: {count}")

    if report["score_global"] == "OK":
        console.print(f"\n[bold green]✅ Score global : OK[/bold green]")
    else:
        console.print(f"\n[bold yellow]⚠ Score global : ATTENTION[/bold yellow]")


if __name__ == "__main__":
    main()
