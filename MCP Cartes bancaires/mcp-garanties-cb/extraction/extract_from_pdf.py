"""
Extrait les données manquantes (plafonds, franchises) depuis les PDF
de conditions générales en utilisant l'API Gemini.

Le script :
  1. Identifie les données manquantes dans MATRICE_GARANTIES
  2. Trouve les PDF correspondants via INDEX_PDF
  3. Envoie chaque PDF à Gemini avec un prompt ciblé
  4. Met à jour la base de données avec les valeurs extraites

Usage :
    python -m extraction.extract_from_pdf
    python -m extraction.extract_from_pdf --carte CRA-VISA-PREMIER   # Une carte
    python -m extraction.extract_from_pdf --garantie dommages_vehicule_location  # Une garantie
    python -m extraction.extract_from_pdf --enrichir-rc              # Extraction enrichie RC
    python -m extraction.extract_from_pdf --enrichir-rc --carte BNP-VISA-PREMIER  # RC une carte
    python -m extraction.extract_from_pdf --dry-run  # Affiche sans modifier
"""

import json
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress

load_dotenv()
console = Console()

# Chemins
PDF_BASE_PATH = Path(os.getenv("PDF_BASE_PATH", "data/pdfs"))
OUTPUT_PATH = Path(os.getenv("OUTPUT_PATH", "data/Migration_INEKTO_V2_2_ENRICHI.xlsx"))

# Chaîne de priorité : enrichi > corrigé > normalisé > source brut
EXCEL_PATH = None
for candidate in [
    "data/Migration_INEKTO_V2_2_ENRICHI.xlsx",
    "data/Migration_INEKTO_V2_2_CORRIGE.xlsx",
    "data/Migration_INEKTO_V2_2_NORMALISE.xlsx",
    "data/Migration_INEKTO_V2_2.xlsx",
]:
    if Path(candidate).exists():
        EXCEL_PATH = Path(candidate)
        break

if EXCEL_PATH is None:
    EXCEL_PATH = Path(os.getenv("EXCEL_PATH", "data/Migration_INEKTO_V2_2.xlsx"))

# Écrire dans le même fichier pour rendre l'extraction incrémentale
if EXCEL_PATH.name in ("Migration_INEKTO_V2_2_CORRIGE.xlsx", "Migration_INEKTO_V2_2_ENRICHI.xlsx"):
    OUTPUT_PATH = EXCEL_PATH

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ─────────────────────────────────────────────────────────────
# Prompt d'extraction
# ─────────────────────────────────────────────────────────────

EXTRACTION_PROMPT = """Tu es un expert en assurance analysant un PDF de conditions générales
d'une carte bancaire. Tu dois extraire des données PRECISES pour les garanties suivantes.

CARTE : {carte_id}
BANQUE : {banque}

DONNÉES MANQUANTES À TROUVER :
{missing_data}

INSTRUCTIONS :
1. Cherche dans le PDF les sections correspondant à chaque garantie demandée
2. Extrais les valeurs EXACTES (plafonds en euros, franchises en euros)
3. Note la page du PDF où tu as trouvé l'information
4. Si une valeur n'est pas trouvée, indique "NON_TROUVE"
5. Si c'est "frais réels" (pas de plafond chiffré), indique "FRAIS_REELS"
6. Attention aux franchises en % : note le pourcentage ET le min/max si présents

Réponds UNIQUEMENT en JSON valide avec cette structure :
{{
  "carte_id": "{carte_id}",
  "extractions": [
    {{
      "id_garantie": "nom_de_la_garantie",
      "champ": "plafond_montant|franchise_montant",
      "valeur": 5000,
      "unite": "EUR|POURCENT|FRAIS_REELS",
      "page_source": 12,
      "texte_source": "citation exacte courte du PDF",
      "confiance": "HAUTE|MOYENNE|BASSE"
    }}
  ],
  "notes": "observations éventuelles"
}}
"""

RC_EXTRACTION_PROMPT = """Tu es un expert en assurance analysant un PDF de conditions générales
d'une carte bancaire. Tu dois extraire TOUTES les informations relatives à la garantie
RESPONSABILITÉ CIVILE.

CARTE : {carte_id}
BANQUE : {banque}

Cherche dans le PDF les sections « Responsabilité Civile », « RC », « RC Vie Privée »,
« RC à l'étranger » ou toute section couvrant la responsabilité civile du porteur.

EXTRAIS PRÉCISÉMENT :

1. PLAFONDS : le plafond global d'indemnisation et tout sous-plafond
   (dommages corporels, dommages matériels, dommages immatériels)
2. FRANCHISE : montant ou pourcentage à la charge de l'assuré
3. CONDITIONS D'ACTIVATION : ex. paiement du voyage avec la carte, durée max,
   zone géographique, délai de déclaration
4. EXCLUSIONS MAJEURES : ex. dommages causés par un véhicule à moteur,
   activités professionnelles, pays exclus, pratique de sports dangereux
5. PERSONNES COUVERTES : titulaire, conjoint, enfants, etc. avec les plafonds
   par personne si différents du plafond global

Réponds UNIQUEMENT en JSON valide avec cette structure :
{{
  "carte_id": "{carte_id}",
  "extractions": [
    {{
      "id_garantie": "responsabilite_civile",
      "champ": "plafond_montant|franchise_montant",
      "valeur": 1500000,
      "unite": "EUR|POURCENT|FRAIS_REELS",
      "page_source": 12,
      "texte_source": "citation exacte courte du PDF",
      "confiance": "HAUTE|MOYENNE|BASSE"
    }}
  ],
  "conditions_activation": [
    "Paiement partiel ou total du voyage avec la carte",
    "Voyage de 90 jours maximum"
  ],
  "exclusions": [
    "Dommages causés par un véhicule à moteur",
    "Activité professionnelle",
    "Pays sous embargo"
  ],
  "personnes_couvertes": [
    {{
      "type": "titulaire|conjoint|enfant",
      "couvert": true,
      "plafond_specifique": null,
      "age_max": null,
      "conditions": "description courte"
    }}
  ],
  "sous_plafonds": {{
    "dommages_corporels": null,
    "dommages_materiels": null,
    "dommages_immateriels": null
  }},
  "zone_geographique": "MONDE|EUROPE|HORS_RESIDENCE",
  "page_source": 12,
  "notes": "observations éventuelles"
}}
"""

GARANTIES_WITH_CUSTOM_PROMPT = {
    "responsabilite_civile": RC_EXTRACTION_PROMPT,
}


def find_missing_data(matrice: pd.DataFrame, cartes: pd.DataFrame) -> pd.DataFrame:
    """Identifie les données manquantes exploitables."""
    incluses = matrice[matrice["est_incluse"] == True].copy()

    # Plafonds manquants (hors frais réels et hors garanties binaires)
    missing_plafond = incluses[
        incluses["plafond_montant"].isna()
        & (incluses["plafond_frais_reels"] != True)
        & ~incluses["id_garantie"].isin(["rachat_franchise_location", "teleconsultation"])
    ].copy()
    missing_plafond["champ_manquant"] = "plafond_montant"

    # Franchises manquantes (hors garanties binaires)
    missing_franchise = incluses[
        incluses["franchise_montant"].isna()
        & ~incluses["id_garantie"].isin(["rachat_franchise_location", "teleconsultation"])
    ].copy()
    missing_franchise["champ_manquant"] = "franchise_montant"

    missing = pd.concat([missing_plafond, missing_franchise]).drop_duplicates(
        subset=["id_carte", "id_garantie", "champ_manquant"]
    )

    return missing


def load_pdf_bytes(pdf_path: Path) -> bytes | None:
    """Charge un PDF et retourne son contenu brut."""
    if not pdf_path.exists():
        return None
    with open(pdf_path, "rb") as f:
        return f.read()


GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-pro-preview")


def _call_gemini(pdf_bytes: bytes, prompt: str) -> dict | None:
    """Envoie un PDF et un prompt à Gemini, retourne le JSON parsé."""
    try:
        from google import genai
        from google.genai.types import Part
    except ImportError:
        console.print("[red]pip install google-genai requis[/red]")
        return None

    client = genai.Client(api_key=GEMINI_API_KEY)

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                prompt,
            ],
        )

        text = response.text
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        return json.loads(text.strip())

    except Exception as e:
        console.print(f"  [red]Erreur API : {e}[/red]")
        return None


def extract_with_gemini(
    pdf_bytes: bytes,
    carte_id: str,
    banque: str,
    missing_items: list[dict],
) -> dict | None:
    """Appelle l'API Gemini pour extraire les données manquantes d'un PDF."""
    missing_desc = "\n".join(
        f"  - {item['id_garantie']} → {item['champ_manquant']}"
        for item in missing_items
    )

    prompt = EXTRACTION_PROMPT.format(
        carte_id=carte_id,
        banque=banque,
        missing_data=missing_desc,
    )

    return _call_gemini(pdf_bytes, prompt)


def extract_rc_with_gemini(
    pdf_bytes: bytes,
    carte_id: str,
    banque: str,
) -> dict | None:
    """Extraction enrichie de la garantie responsabilité civile."""
    prompt = RC_EXTRACTION_PROMPT.format(
        carte_id=carte_id,
        banque=banque,
    )

    return _call_gemini(pdf_bytes, prompt)


def apply_extractions(
    matrice: pd.DataFrame,
    extractions: list[dict],
    carte_id: str,
) -> tuple[pd.DataFrame, int]:
    """Applique les valeurs extraites dans la matrice."""
    applied = 0
    for ext in extractions:
        garantie = ext.get("id_garantie")
        champ = ext.get("champ")
        valeur = ext.get("valeur")
        confiance = ext.get("confiance", "BASSE")
        page = ext.get("page_source")
        texte = ext.get("texte_source", "")

        if valeur == "NON_TROUVE" or valeur is None:
            continue

        if valeur == "FRAIS_REELS":
            mask = (matrice["id_carte"] == carte_id) & (matrice["id_garantie"] == garantie)
            matrice.loc[mask, "plafond_frais_reels"] = True
            applied += 1
            continue

        try:
            val_num = float(valeur)
        except (ValueError, TypeError):
            continue

        mask = (matrice["id_carte"] == carte_id) & (matrice["id_garantie"] == garantie)
        if mask.any() and champ in matrice.columns:
            matrice.loc[mask, champ] = val_num
            if page and pd.notna(page):
                matrice.loc[mask, "page_source"] = str(page)
            if texte:
                matrice.loc[mask, "texte_source"] = str(texte)[:200]
            applied += 1
            symbol = "✓" if confiance == "HAUTE" else "~" if confiance == "MOYENNE" else "?"
            console.print(
                f"    [{confiance}] {symbol} {garantie}.{champ} = {val_num} (p.{page})"
            )

    return matrice, applied


def _ensure_column(df: pd.DataFrame, col: str) -> None:
    """Ajoute une colonne au DataFrame si elle n'existe pas encore."""
    if col not in df.columns:
        df[col] = pd.NA


def apply_rc_extractions(
    matrice: pd.DataFrame,
    rc_result: dict,
    carte_id: str,
) -> tuple[pd.DataFrame, int]:
    """Applique les extractions enrichies de responsabilité civile."""
    applied = 0
    mask = (matrice["id_carte"] == carte_id) & (matrice["id_garantie"] == "responsabilite_civile")
    if not mask.any():
        return matrice, 0

    for ext in rc_result.get("extractions", []):
        champ = ext.get("champ")
        valeur = ext.get("valeur")
        confiance = ext.get("confiance", "BASSE")
        page = ext.get("page_source")

        if valeur == "NON_TROUVE" or valeur is None:
            continue
        if valeur == "FRAIS_REELS":
            matrice.loc[mask, "plafond_frais_reels"] = True
            applied += 1
            continue

        try:
            val_num = float(valeur)
        except (ValueError, TypeError):
            continue

        if champ in matrice.columns:
            matrice.loc[mask, champ] = val_num
            applied += 1
            symbol = "✓" if confiance == "HAUTE" else "~" if confiance == "MOYENNE" else "?"
            console.print(f"    [{confiance}] {symbol} responsabilite_civile.{champ} = {val_num} (p.{page})")

    # Stocker chaque section RC dans une colonne dédiée
    conditions = rc_result.get("conditions_activation", [])
    exclusions = rc_result.get("exclusions", [])
    personnes = rc_result.get("personnes_couvertes", [])
    sous_plafonds = rc_result.get("sous_plafonds", {})
    zone = rc_result.get("zone_geographique")

    if conditions:
        cond_text = " ; ".join(conditions)
        _ensure_column(matrice, "rc_conditions")
        matrice.loc[mask, "rc_conditions"] = cond_text
        _ensure_column(matrice, "conditions")
        matrice.loc[mask, "conditions"] = cond_text

    if exclusions:
        excl_text = " ; ".join(exclusions)
        _ensure_column(matrice, "rc_exclusions")
        matrice.loc[mask, "rc_exclusions"] = excl_text

    if personnes:
        pers_strs = []
        for p in personnes:
            s = p.get("type", "?")
            if p.get("plafond_specifique"):
                s += f" ({p['plafond_specifique']}€)"
            if p.get("age_max"):
                s += f" <{p['age_max']}ans"
            if p.get("conditions"):
                s += f" [{p['conditions']}]"
            pers_strs.append(s)
        _ensure_column(matrice, "rc_personnes_couvertes")
        matrice.loc[mask, "rc_personnes_couvertes"] = " ; ".join(pers_strs)

    sp_parts = []
    for k, v in sous_plafonds.items():
        if v is not None:
            sp_parts.append(f"{k}={v}€")
    if sp_parts:
        _ensure_column(matrice, "rc_sous_plafonds")
        matrice.loc[mask, "rc_sous_plafonds"] = " ; ".join(sp_parts)

    if zone:
        _ensure_column(matrice, "rc_zone_geographique")
        matrice.loc[mask, "rc_zone_geographique"] = zone

    page_src = rc_result.get("page_source")
    if page_src:
        matrice.loc[mask, "page_source"] = str(page_src)

    if rc_result.get("notes"):
        console.print(f"    📝 {rc_result['notes']}")

    n_cond, n_excl, n_pers = len(conditions), len(exclusions), len(personnes)
    if any([conditions, exclusions, personnes]):
        console.print(f"    [dim]RC enrichie : {n_cond} conditions, "
                       f"{n_excl} exclusions, {n_pers} personnes couvertes[/dim]")

    return matrice, applied


def main():
    dry_run = "--dry-run" in sys.argv
    enrichir_rc = "--enrichir-rc" in sys.argv
    filter_carte = None
    filter_garantie = None

    if "--carte" in sys.argv:
        idx = sys.argv.index("--carte")
        filter_carte = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None

    if "--garantie" in sys.argv:
        idx = sys.argv.index("--garantie")
        filter_garantie = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None

    if not EXCEL_PATH.exists():
        console.print(f"[red]Fichier introuvable : {EXCEL_PATH}[/red]")
        return

    if not GEMINI_API_KEY and not dry_run:
        console.print("[red]GEMINI_API_KEY manquante dans .env[/red]")
        return

    console.print(f"\n[bold]📄 Extraction des données manquantes depuis les PDF[/bold]")
    console.print(f"Modèle : [cyan]{GEMINI_MODEL}[/cyan]")
    console.print(f"Source : {EXCEL_PATH}")
    console.print(f"PDF : {PDF_BASE_PATH}")

    xls = pd.ExcelFile(EXCEL_PATH)
    matrice = pd.read_excel(xls, "MATRICE_GARANTIES", header=0)
    cartes = pd.read_excel(xls, "CARTES", header=0)
    index_pdf = pd.read_excel(xls, "INDEX_PDF", header=0)

    # ── Mode enrichissement RC ─────────────────────────────────
    if enrichir_rc:
        rc_cartes = matrice[
            (matrice["id_garantie"] == "responsabilite_civile")
            & (matrice["est_incluse"] == True)
        ]["id_carte"].unique()

        if filter_carte:
            rc_cartes = [c for c in rc_cartes if c == filter_carte]

        console.print(f"\n[bold magenta]Mode enrichissement RC[/bold magenta]")
        console.print(f"Cartes avec RC incluse : [bold]{len(rc_cartes)}[/bold]\n")

        if dry_run:
            for cid in rc_cartes:
                b = cartes[cartes["id_carte"] == cid]["banque"].values
                b_name = b[0] if len(b) > 0 else "?"
                pdf_row = index_pdf[index_pdf["id_carte"] == cid]
                pdf_path = pdf_row["chemin_pdf_assurance"].values[0] if len(pdf_row) > 0 else "?"
                has_pdf = (PDF_BASE_PATH / str(pdf_path)).exists() if pdf_path != "?" else False
                console.print(f"  {'✓' if has_pdf else '✗'} {cid:40s} ({b_name})")
            console.print(f"\n[yellow]Dry-run terminé. {len(rc_cartes)} cartes à enrichir.[/yellow]")
            return

        total_applied = 0
        with Progress() as progress:
            task = progress.add_task("Enrichissement RC...", total=len(rc_cartes))
            for cid in rc_cartes:
                progress.update(task, description=f"[magenta]{cid}[/magenta]")
                pdf_row = index_pdf[index_pdf["id_carte"] == cid]
                if pdf_row.empty:
                    progress.advance(task)
                    continue
                pdf_rel = pdf_row["chemin_pdf_assurance"].values[0]
                pdf_path = PDF_BASE_PATH / str(pdf_rel)
                if not pdf_path.exists():
                    console.print(f"  [yellow]⚠ PDF introuvable : {pdf_path}[/yellow]")
                    progress.advance(task)
                    continue

                pdf_bytes = load_pdf_bytes(pdf_path)
                if not pdf_bytes:
                    progress.advance(task)
                    continue

                b = cartes[cartes["id_carte"] == cid]["banque"].values
                b_name = b[0] if len(b) > 0 else "?"
                console.print(f"\n  🔍 RC enrichie : {cid} ({b_name})")

                rc_result = extract_rc_with_gemini(pdf_bytes, cid, b_name)
                if rc_result:
                    matrice, count = apply_rc_extractions(matrice, rc_result, cid)
                    total_applied += count
                else:
                    console.print(f"    [red]Extraction RC échouée[/red]")
                progress.advance(task)

        console.print(f"\n[bold]Résultat RC : {total_applied} valeurs extraites/enrichies[/bold]")

        if total_applied > 0:
            console.print(f"\n💾 Sauvegarde dans {OUTPUT_PATH}...")
            all_sheets = {}
            for sheet_name in xls.sheet_names:
                if sheet_name == "MATRICE_GARANTIES":
                    all_sheets[sheet_name] = matrice
                else:
                    all_sheets[sheet_name] = pd.read_excel(xls, sheet_name, header=0)
            with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
                for sheet_name, df in all_sheets.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            console.print(f"[green]✅ Fichier enrichi sauvegardé : {OUTPUT_PATH}[/green]")
        return

    # ── Mode standard (données manquantes) ─────────────────────
    missing = find_missing_data(matrice, cartes)

    if filter_carte:
        missing = missing[missing["id_carte"] == filter_carte]
    if filter_garantie:
        missing = missing[missing["id_garantie"] == filter_garantie]

    console.print(f"\nDonnées manquantes : [bold]{len(missing)}[/bold] valeurs")

    grouped = missing.groupby("id_carte")
    console.print(f"Cartes à traiter : [bold]{len(grouped)}[/bold]\n")

    if dry_run:
        for carte_id, group in grouped:
            banque = cartes[cartes["id_carte"] == carte_id]["banque"].values
            b_name = banque[0] if len(banque) > 0 else "?"
            pdf_row = index_pdf[index_pdf["id_carte"] == carte_id]
            pdf_path = pdf_row["chemin_pdf_assurance"].values[0] if len(pdf_row) > 0 else "?"
            has_pdf = (PDF_BASE_PATH / str(pdf_path)).exists() if pdf_path != "?" else False

            console.print(
                f"  {'✓' if has_pdf else '✗'} {carte_id:40s} ({b_name:20s}) "
                f"— {len(group)} valeurs manquantes"
            )
        console.print(f"\n[yellow]Dry-run terminé.[/yellow]")
        return

    total_applied = 0

    with Progress() as progress:
        task = progress.add_task("Extraction...", total=len(grouped))

        for carte_id, group in grouped:
            progress.update(task, description=f"[cyan]{carte_id}[/cyan]")

            # Trouver le PDF
            pdf_row = index_pdf[index_pdf["id_carte"] == carte_id]
            if pdf_row.empty:
                console.print(f"  [yellow]⚠ Pas d'entrée INDEX_PDF pour {carte_id}[/yellow]")
                progress.advance(task)
                continue

            pdf_rel_path = pdf_row["chemin_pdf_assurance"].values[0]
            pdf_path = PDF_BASE_PATH / str(pdf_rel_path)

            if not pdf_path.exists():
                console.print(f"  [yellow]⚠ PDF introuvable : {pdf_path}[/yellow]")
                progress.advance(task)
                continue

            # Charger le PDF
            pdf_bytes = load_pdf_bytes(pdf_path)
            if not pdf_bytes:
                progress.advance(task)
                continue

            banque = cartes[cartes["id_carte"] == carte_id]["banque"].values
            b_name = banque[0] if len(banque) > 0 else "?"

            # Préparer les items manquants
            all_items = [
                {"id_garantie": row["id_garantie"], "champ_manquant": row["champ_manquant"]}
                for _, row in group.iterrows()
            ]

            rc_items = [i for i in all_items if i["id_garantie"] in GARANTIES_WITH_CUSTOM_PROMPT]
            std_items = [i for i in all_items if i["id_garantie"] not in GARANTIES_WITH_CUSTOM_PROMPT]

            console.print(f"\n  📄 {carte_id} ({b_name}) — {len(all_items)} valeurs à extraire")

            if std_items:
                result = extract_with_gemini(pdf_bytes, carte_id, b_name, std_items)
                if result and "extractions" in result:
                    matrice, count = apply_extractions(matrice, result["extractions"], carte_id)
                    total_applied += count
                    if result.get("notes"):
                        console.print(f"    📝 {result['notes']}")
                else:
                    console.print(f"    [red]Extraction standard échouée[/red]")

            for rc_item in rc_items:
                gar_id = rc_item["id_garantie"]
                console.print(f"    🔍 Extraction enrichie : {gar_id}")
                rc_result = extract_rc_with_gemini(pdf_bytes, carte_id, b_name)
                if rc_result:
                    matrice, count = apply_rc_extractions(matrice, rc_result, carte_id)
                    total_applied += count
                else:
                    console.print(f"    [red]Extraction RC échouée[/red]")

            progress.advance(task)

    console.print(f"\n[bold]Résultat : {total_applied} valeurs extraites et appliquées[/bold]")

    if total_applied > 0:
        console.print(f"\n💾 Sauvegarde dans {OUTPUT_PATH}...")
        all_sheets = {}
        for sheet_name in xls.sheet_names:
            if sheet_name == "MATRICE_GARANTIES":
                all_sheets[sheet_name] = matrice
            else:
                all_sheets[sheet_name] = pd.read_excel(xls, sheet_name, header=0)

        with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
            for sheet_name, df in all_sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        console.print(f"[green]✅ Fichier enrichi sauvegardé : {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    main()
