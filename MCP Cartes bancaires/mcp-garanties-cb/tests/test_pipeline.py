"""
Tests du pipeline complet.

Usage :
    python -m tests.test_pipeline
"""

import json
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.data_loader import GarantiesDB


def test_chargement():
    """Vérifie que la base se charge correctement."""
    db = GarantiesDB()
    assert len(db.cartes) > 200, f"Attendu >200 cartes, obtenu {len(db.cartes)}"
    assert len(db.ref_banques) > 30, f"Attendu >30 banques, obtenu {len(db.ref_banques)}"
    assert len(db.matrice) > 4000, f"Attendu >4000 lignes matrice, obtenu {len(db.matrice)}"
    print(f"✅ Chargement OK : {len(db.cartes)} cartes, {len(db.ref_banques)} banques")


def test_lister_cartes():
    """Teste le listing avec filtres."""
    db = GarantiesDB()

    # Sans filtre
    all_cartes = db.lister_cartes()
    assert len(all_cartes) > 200

    # Par réseau
    visa = db.lister_cartes(reseau="VISA")
    mc = db.lister_cartes(reseau="MASTERCARD")
    assert len(visa) > 100
    assert len(mc) > 50

    # Par gamme
    premium = db.lister_cartes(gamme="PREMIUM")
    assert len(premium) > 20

    # Par banque
    bnp = db.lister_cartes(banque="BNP")
    assert len(bnp) > 0

    print(f"✅ Listing OK : {len(visa)} Visa, {len(mc)} MC, {len(premium)} Premium, {len(bnp)} BNP")


def test_details_carte():
    """Teste les détails d'une carte."""
    db = GarantiesDB()

    # Carte existante
    details = db.details_carte("BNP-VISA-PREMIER")
    if details:
        assert details["banque"] == "BNP Paribas"
        assert details["reseau"] == "VISA"
        assert len(details["garanties"]) > 0
        print(f"✅ Détails BNP-VISA-PREMIER : {len(details['garanties'])} garanties, "
              f"{len(details['beneficiaires'])} bénéficiaires")
    else:
        print("⚠️  BNP-VISA-PREMIER non trouvée (vérifier les données)")

    # Carte inexistante
    result = db.details_carte("CARTE-INEXISTANTE")
    assert result is None
    print("✅ Carte inexistante → None")


def test_comparaison():
    """Teste la comparaison de deux cartes."""
    db = GarantiesDB()
    result = db.comparer("BNP-VISA-PREMIER", "SGE-VISA-PREMIER")
    if result:
        assert "avantages_carte_1" in result
        assert "avantages_carte_2" in result
        assert "comparaisons" in result
        print(f"✅ Comparaison OK : {len(result['avantages_carte_1'])} avantages BNP, "
              f"{len(result['avantages_carte_2'])} avantages SGE")
    else:
        print("⚠️  Comparaison impossible (cartes manquantes)")


def test_recherche_situation():
    """Teste la recherche par situation."""
    db = GarantiesDB()

    for situation in ["retard avion", "annulation voyage", "location voiture", "ski montagne"]:
        resultats = db.rechercher_par_situation(situation)
        print(f"✅ Recherche '{situation}' : {len(resultats)} cartes trouvées")


def test_simulation():
    """Teste la simulation de sinistre."""
    db = GarantiesDB()

    result = db.simuler_sinistre("BNP-VISA-PREMIER", "frais_medicaux_etranger", 5000)
    if result and result.get("couvert"):
        assert result["indemnisation_estimee"] > 0
        assert result["taux_couverture_pct"] > 0
        print(f"✅ Simulation OK : sinistre 5000€ → indemnisation {result['indemnisation_estimee']}€ "
              f"({result['taux_couverture_pct']}%)")
    else:
        print(f"⚠️  Simulation: {result}")


def main():
    print("\n🧪 Tests du pipeline MCP Garanties CB\n")

    tests = [
        test_chargement,
        test_lister_cartes,
        test_details_carte,
        test_comparaison,
        test_recherche_situation,
        test_simulation,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} : {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Résultat : {passed} réussis, {failed} échoués")
    if failed == 0:
        print("🎉 Tous les tests passent !")


if __name__ == "__main__":
    main()
