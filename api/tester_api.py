"""Teste l'API avec une requête valide et des requêtes incohérentes.

Usage, l'API étant lancée (en local ou déployée) :
    python api/tester_api.py                                        # API locale : http://localhost:3000
    python api/tester_api.py https://consommation-batiments.onrender.com   # API déployée sur Render

Résultat attendu :
    - la requête valide renvoie le code 200 et une prédiction ;
    - chaque requête incohérente renvoie le code 400 et le message expliquant le refus.
"""
import sys

import httpx  # bibliothèque pour envoyer des requêtes HTTP (installée avec BentoML)

# Adresse de l'API : celle passée en argument, sinon l'API locale. On y ajoute la route /predire.
URL = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000").rstrip("/") + "/predire"

# Un bâtiment cohérent : un bureau de 6 étages à Downtown, avec parking et restaurant
VALIDE = {
    "type_batiment": "Small- and Mid-Sized Office",
    "quartier": "downtown",  # en minuscules exprès : l'API doit l'accepter
    "annee_construction": 1985,
    "nombre_batiments": 1,
    "nombre_etages": 6,
    "surface_batiment": 60000,
    "surface_parking": 10000,
    "surface_usage_principal": 55000,
    "usages": ["Office", "Parking", "Restaurant"],
    "utilise_gaz": True,
    "utilise_vapeur": False,
}

# Requêtes incohérentes : chacune reprend le bâtiment valide en changeant un ou plusieurs champs.
# Elles doivent toutes être refusées par la validation Pydantic (code 400).
INCOHERENTS = {
    "Type de bâtiment inconnu": {"type_batiment": "Château"},
    "Quartier inconnu": {"quartier": "PARIS"},
    "Année dans le futur": {"annee_construction": 2050},
    "Zéro étage": {"nombre_etages": 0},
    "Surface négative": {"surface_parking": -500},
    "Bâtiment trop petit": {"surface_batiment": 2000, "surface_parking": 0, "surface_usage_principal": 2000},
    "Usage principal plus grand que le bâtiment": {"surface_usage_principal": 200000},
    "99 étages (record de Seattle : 76)": {"nombre_etages": 99},
    "40 étages pour 20 000 pieds²": {"nombre_etages": 40, "surface_batiment": 20000, "surface_usage_principal": 20000},
    "Usage inconnu": {"usages": ["Office", "Spaceport"]},
    "Usage en double": {"usages": ["Office", "Office"]},
    "Champ manquant": {"utilise_gaz": None},  # None = le champ est retiré de la requête
    "Champ en trop": {"couleur_facade": "rouge"},
}


def envoyer(donnees):
    """Envoie un bâtiment à l'API ; une valeur None retire le champ de la requête."""
    donnees = {cle: valeur for cle, valeur in donnees.items() if valeur is not None}
    return httpx.post(URL, json=donnees, timeout=30)  # requête POST, données au format JSON


# 1. Requête valide : on affiche le code de réponse et la prédiction
reponse = envoyer(VALIDE)
print(f"Requête valide → {reponse.status_code} : {reponse.json()}\n")

# 2. Requêtes incohérentes : on affiche le code de réponse et le message d'erreur renvoyé par l'API
for nom, modification in INCOHERENTS.items():
    reponse = envoyer({**VALIDE, **modification})  # {**a, **b} : copie de a, avec les champs de b remplacés
    message = reponse.json()["detail"][0]["msg"] if reponse.status_code == 400 else reponse.text
    print(f"{nom:45s} → {reponse.status_code} : {message}")
