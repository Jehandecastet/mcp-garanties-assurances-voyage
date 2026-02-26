"""
🏦 Serveur MCP — Comparateur de Garanties Cartes Bancaires IMA
===============================================================

Expose les données de la base INEKTO via le Model Context Protocol.
Compatible Claude Desktop, Cursor, et tout client MCP.

Usage :
    python -m server.server                          # stdio (Claude Desktop / Cursor)
    python -m server.server --transport sse --port 8000  # HTTP SSE
"""

import json
import sys
from typing import Optional

from fastmcp import FastMCP

from server.data_loader import get_db

# ─────────────────────────────────────────────────────────────
# Initialisation
# ─────────────────────────────────────────────────────────────

mcp = FastMCP(
    name="Garanties Cartes Bancaires IMA",
    instructions="""
    Tu es un assistant expert en garanties d'assurance et d'assistance
    des cartes bancaires, travaillant pour IMA (Inter Mutuelles Assistance).

    Ta base de données couvre 211 cartes bancaires de 38 banques françaises
    (Visa, Mastercard, American Express), avec 26 types de garanties.

    Règles :
    - Cite toujours la banque et le nom commercial exact de la carte
    - Précise les plafonds, franchises et conditions
    - Rappelle que le paiement avec la carte est souvent requis
    - Mentionne les bénéficiaires (titulaire, conjoint, enfants...)
    - Pour les cas complexes, oriente vers un conseiller IMA
    - Ne compare que des cartes présentes dans la base
    """,
)


def _json(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


# ─────────────────────────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────────────────────────


@mcp.tool()
def lister_cartes(
    reseau: Optional[str] = None,
    gamme: Optional[str] = None,
    banque: Optional[str] = None,
) -> str:
    """
    Liste les cartes bancaires disponibles avec filtres optionnels.

    Args:
        reseau: Filtrer par réseau (VISA, MASTERCARD, AMEX)
        gamme: Filtrer par gamme (BASIQUE, STANDARD, PREMIUM, ULTRA_PREMIUM)
        banque: Filtrer par nom de banque (recherche partielle)
    """
    db = get_db()
    cartes = db.lister_cartes(reseau=reseau, gamme=gamme, banque=banque)
    return _json({"nombre": len(cartes), "cartes": cartes})


@mcp.tool()
def details_carte(carte_id: str) -> str:
    """
    Retourne les détails complets d'une carte : garanties, plafonds,
    franchises, bénéficiaires et conditions d'application.

    Args:
        carte_id: Identifiant de la carte (ex: "BNP-VISA-PREMIER", "CRA-MASTERCARD-GOLD")
    """
    db = get_db()
    result = db.details_carte(carte_id)
    if not result:
        cartes = db.lister_cartes()
        ids = [c["id_carte"] for c in cartes[:20]]
        return _json({"erreur": f"Carte '{carte_id}' non trouvée", "exemples": ids})
    return _json(result)


@mcp.tool()
def comparer_cartes(carte_id_1: str, carte_id_2: str) -> str:
    """
    Compare deux cartes côte à côte : garanties, plafonds, franchises,
    bénéficiaires. Identifie les avantages de chaque carte.

    Args:
        carte_id_1: Identifiant de la première carte
        carte_id_2: Identifiant de la deuxième carte
    """
    db = get_db()
    result = db.comparer(carte_id_1, carte_id_2)
    if not result:
        return _json({"erreur": "Une ou plusieurs cartes non trouvées"})
    return _json(result)


@mcp.tool()
def rechercher_par_situation(situation: str) -> str:
    """
    Recherche les cartes couvrant une situation donnée.
    Retourne les cartes pertinentes classées par niveau de couverture.

    Args:
        situation: Description de la situation en français
                   (ex: "retard d'avion de 4h", "accident de ski",
                    "annulation voyage maladie", "location voiture étranger",
                    "vol de bagages", "frais médicaux à l'étranger")
    """
    db = get_db()
    resultats = db.rechercher_par_situation(situation)
    return _json({
        "situation": situation,
        "nombre_cartes": len(resultats),
        "resultats": resultats[:20],  # Limiter à 20 résultats
    })


@mcp.tool()
def simuler_sinistre(carte_id: str, garantie_id: str, montant_eur: float) -> str:
    """
    Simule un sinistre et calcule l'indemnisation estimée.

    Args:
        carte_id: Identifiant de la carte (ex: "BNP-VISA-PREMIER")
        garantie_id: Type de garantie (ex: "frais_medicaux_etranger", "annulation",
                     "bagages", "retard_de_vol", "dommages_vehicule_location",
                     "responsabilite_civile", "sport")
        montant_eur: Montant du sinistre en euros
    """
    db = get_db()
    result = db.simuler_sinistre(carte_id, garantie_id, montant_eur)
    return _json(result)


@mcp.tool()
def lister_garanties_disponibles() -> str:
    """
    Liste toutes les garanties référencées dans la base avec leur catégorie.
    Utile pour connaître les identifiants exacts des garanties.
    """
    db = get_db()
    garanties = []
    for _, row in db.ref_garanties.iterrows():
        garanties.append({
            "id": row["id_garantie"],
            "nom": row["nom"],
            "categorie": row["categorie"],
            "est_binaire": bool(row["est_binaire"]) if not (isinstance(row["est_binaire"], float) and str(row["est_binaire"]) == "nan") else None,
        })
    return _json(garanties)


# ─────────────────────────────────────────────────────────────
# RESOURCES
# ─────────────────────────────────────────────────────────────


@mcp.resource("garanties://catalogue")
def resource_catalogue() -> str:
    """Catalogue complet des 211 cartes bancaires."""
    db = get_db()
    return _json(db.lister_cartes())


@mcp.resource("garanties://ref-garanties")
def resource_ref_garanties() -> str:
    """Référentiel des 26 garanties avec catégories et descriptions."""
    db = get_db()
    return db.ref_garanties.to_json(orient="records", force_ascii=False)


@mcp.resource("garanties://ref-banques")
def resource_ref_banques() -> str:
    """Liste des 38 banques avec leurs identifiants."""
    db = get_db()
    return db.ref_banques.to_json(orient="records", force_ascii=False)


@mcp.resource("garanties://statistiques")
def resource_stats() -> str:
    """Statistiques de la base de données."""
    db = get_db()
    return _json({
        "banques": len(db.ref_banques),
        "cartes": len(db.cartes),
        "garanties_ref": len(db.ref_garanties),
        "lignes_matrice": len(db.matrice),
        "exclusions": len(db.exclusions),
        "repartition_reseau": db.cartes["reseau"].value_counts().to_dict(),
        "repartition_gamme": db.cartes["gamme_normalisee"].value_counts().to_dict(),
    })


# ─────────────────────────────────────────────────────────────
# PROMPTS
# ─────────────────────────────────────────────────────────────


@mcp.prompt()
def conseiller_carte(profil: str, budget_max: str = "200") -> str:
    """
    Recommande une carte adaptée au profil du client.

    Args:
        profil: Description du profil (ex: "famille avec 2 enfants, 3 voyages/an en Europe")
        budget_max: Budget max cotisation annuelle en euros
    """
    return f"""
    En tant qu'expert IMA en assurances cartes bancaires, recommande la carte
    la plus adaptée à ce profil.

    Profil client : {profil}
    Budget max : {budget_max}€/an

    Démarche :
    1. `lister_garanties_disponibles` pour connaître les garanties
    2. `lister_cartes` avec différents filtres pour identifier les candidates
    3. `details_carte` sur les 3-4 meilleures options
    4. `comparer_cartes` entre les 2 finalistes
    5. Recommandation argumentée :
       - Rapport couverture/prix
       - Bénéficiaires couverts (critique si famille)
       - Points forts ET lacunes de la carte recommandée
       - Alternative si budget flexible
    """


@mcp.prompt()
def audit_couverture_voyage(carte_id: str, destination: str, duree_jours: str = "14") -> str:
    """
    Analyse complète de la couverture pour un voyage spécifique.

    Args:
        carte_id: Identifiant de la carte
        destination: Pays de destination
        duree_jours: Durée du voyage en jours
    """
    return f"""
    Analyse la couverture complète de la carte {carte_id} pour ce voyage.

    Destination : {destination}
    Durée : {duree_jours} jours

    Démarche :
    1. `details_carte("{carte_id}")` pour voir toutes les garanties
    2. Vérifier la durée max de voyage (conditions d'application)
    3. Pour chaque garantie pertinente pour ce voyage, donner :
       - Plafond et franchise
       - Si le paiement CB est requis
       - Les exclusions principales
    4. Identifier les lacunes de couverture
    5. Recommander des assurances complémentaires si nécessaire
    6. Rappeler les réflexes en cas de sinistre (numéro IMA, délais, documents)
    """


# ─────────────────────────────────────────────────────────────
# Point d'entrée
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    transport = "stdio"
    port = 8000

    if "--transport" in sys.argv:
        idx = sys.argv.index("--transport")
        transport = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "stdio"

    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        port = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else 8000

    import sys as _sys
    print(f"🏦 Serveur MCP Garanties CB IMA démarré (transport: {transport})", file=_sys.stderr)

    if transport == "sse":
        mcp.run(transport=transport, port=port)
    else:
        mcp.run(transport=transport)
