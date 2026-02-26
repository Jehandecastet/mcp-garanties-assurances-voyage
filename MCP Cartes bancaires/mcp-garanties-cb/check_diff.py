"""Compare le fichier Excel d'origine et sa version corrigée.

Affiche pour chaque différence : la feuille, l'identifiant de la ligne
(carte + garantie si applicable) et la colonne modifiée.
"""

import sys
from pathlib import Path

import pandas as pd
from rich.console import Console
from rich.table import Table

ORIGINAL = Path("data/Migration_INEKTO_V2_2.xlsx")
CORRIGE = Path("data/Migration_INEKTO_V2_2_CORRIGE.xlsx")

MAX_VAL_LEN = 40

SHEET_KEYS = {
    "CARTES": ["id_carte"],
    "MATRICE_GARANTIES": ["id_carte", "id_garantie", "zone"],
    "DEFINITIONS_ASSURES": ["id_carte", "type_assure"],
    "CONDITIONS_APPLICATION": ["id_carte"],
    "EXCLUSIONS": ["id_carte", "id_garantie", "code_exception"],
    "INDEX_PDF": ["id_carte"],
    "DETAILS_RC_LOCATION": ["id_carte"],
    "REF_BANQUES": ["id_banque"],
    "REF_GARANTIES": ["id_garantie"],
    "REF_PARTENAIRES": ["banque"],
}


def normalize(val):
    if pd.isna(val):
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        if val == 1.0:
            return True
        if val == 0.0:
            return False
        if isinstance(val, float) and val == int(val):
            return int(val)
    if isinstance(val, str):
        s = val.strip()
        if s.lower() in ("true", "vrai", "1"):
            return True
        if s.lower() in ("false", "faux", "0"):
            return False
        return s
    return val


def truncate(val, max_len=MAX_VAL_LEN):
    s = str(val) if val is not None else "∅"
    return s if len(s) <= max_len else s[:max_len - 1] + "…"


def add_seq_column(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Ajoute un compteur séquentiel par groupe de clés pour désambiguïser les doublons."""
    df = df.copy()
    df["_seq"] = df.groupby(keys).cumcount()
    return df


def diff_sheet(name: str, df_orig: pd.DataFrame, df_corr: pd.DataFrame) -> list[dict]:
    keys = SHEET_KEYS.get(name)
    if not keys:
        return []

    missing_keys = [k for k in keys if k not in df_orig.columns or k not in df_corr.columns]
    if missing_keys:
        return []

    for k in keys:
        df_orig[k] = df_orig[k].astype(str).str.strip()
        df_corr[k] = df_corr[k].astype(str).str.strip()

    has_dupes = df_orig.duplicated(subset=keys, keep=False).any()
    if has_dupes:
        df_orig = add_seq_column(df_orig, keys)
        df_corr = add_seq_column(df_corr, keys)
        merge_keys = keys + ["_seq"]
    else:
        merge_keys = keys

    value_cols = [
        c for c in df_orig.columns
        if c in df_corr.columns and c not in merge_keys
    ]

    merged = df_orig.merge(
        df_corr, on=merge_keys, suffixes=("__orig", "__corr"),
        how="outer", indicator=True,
    )

    diffs = []

    for _, row in merged[merged["_merge"] == "right_only"].iterrows():
        label = " | ".join(str(row[k]) for k in keys)
        diffs.append({"feuille": name, "ligne": label, "colonne": "(ligne ajoutée)", "avant": "", "après": "+"})

    for _, row in merged[merged["_merge"] == "left_only"].iterrows():
        label = " | ".join(str(row[k]) for k in keys)
        diffs.append({"feuille": name, "ligne": label, "colonne": "(ligne supprimée)", "avant": "-", "après": ""})

    for _, row in merged[merged["_merge"] == "both"].iterrows():
        label = " | ".join(str(row[k]) for k in keys)
        for col in value_cols:
            v_o = normalize(row.get(f"{col}__orig"))
            v_c = normalize(row.get(f"{col}__corr"))
            if v_o != v_c:
                diffs.append({
                    "feuille": name,
                    "ligne": label,
                    "colonne": col,
                    "avant": v_o,
                    "après": v_c,
                })

    return diffs


def main():
    console = Console()

    if not ORIGINAL.exists():
        console.print(f"[red]Fichier introuvable : {ORIGINAL}[/red]")
        sys.exit(1)
    if not CORRIGE.exists():
        console.print(f"[red]Fichier introuvable : {CORRIGE}[/red]")
        sys.exit(1)

    console.print(f"\n[bold]Comparaison[/bold]")
    console.print(f"  Original : {ORIGINAL}")
    console.print(f"  Corrigé  : {CORRIGE}\n")

    xls_o = pd.ExcelFile(ORIGINAL)
    xls_c = pd.ExcelFile(CORRIGE)

    all_diffs: list[dict] = []

    for sheet in xls_o.sheet_names:
        if sheet not in xls_c.sheet_names or sheet.startswith("_"):
            continue
        df_o = pd.read_excel(xls_o, sheet, header=0)
        df_c = pd.read_excel(xls_c, sheet, header=0)
        sheet_diffs = diff_sheet(sheet, df_o, df_c)
        if sheet_diffs:
            console.print(f"  [dim]{sheet}[/dim] : {len(sheet_diffs)} diff(s)")
        all_diffs.extend(sheet_diffs)

    if not all_diffs:
        console.print("[green]Aucune différence détectée.[/green]")
        return

    console.print()
    table = Table(title=f"{len(all_diffs)} différence(s) trouvée(s)")
    table.add_column("Feuille", style="cyan", max_width=22)
    table.add_column("Ligne (carte)", max_width=55, no_wrap=True)
    table.add_column("Colonne", style="yellow", max_width=25)
    table.add_column("Avant", style="red", max_width=MAX_VAL_LEN)
    table.add_column("Après", style="green", max_width=MAX_VAL_LEN)

    for d in all_diffs:
        table.add_row(
            d["feuille"],
            str(d["ligne"]),
            d["colonne"],
            truncate(d["avant"]),
            truncate(d["après"]),
        )

    console.print(table)


if __name__ == "__main__":
    main()
