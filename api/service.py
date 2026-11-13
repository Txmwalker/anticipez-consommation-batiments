"""API de prédiction de la consommation d'énergie des bâtiments non résidentiels de Seattle.

Lancement en local, depuis la racine du projet :
    bentoml serve api.service:PredictionConsommation
puis interface Swagger sur http://localhost:3000

Parcours d'une requête :
    1. l'utilisateur envoie la description de son bâtiment (JSON) à la route /predire ;
    2. Pydantic vérifie les données (schemas.py) : en cas d'incohérence, l'API répond 400 avec un message ;
    3. les features sont construites comme dans le notebook (features.py) ;
    4. le modèle prédit le log de la consommation, que l'on ramène en kBtu et en kWh.
"""
import bentoml
import numpy as np
import pandas as pd

from api.features import FEATURES, construire_features
from api.schemas import Batiment, Prediction

KBTU_VERS_KWH = 0.29307  # 1 kBtu ≈ 0,293 kWh


# @bentoml.service transforme la classe en service web. timeout : une requête est abandonnée après 30 secondes.
@bentoml.service(name="consommation_batiments", traffic={"timeout": 30})
class PredictionConsommation:
    """Prédit la consommation annuelle d'énergie d'un bâtiment à partir de ses caractéristiques."""

    # Référence au modèle sauvegardé par le notebook 02 dans le « model store » de BentoML.
    # « latest » = la dernière version sauvegardée. BentoML l'inclut aussi dans l'image Docker.
    modele_bento = bentoml.models.BentoModel("consommation_batiments:latest")

    def __init__(self):
        """Exécuté une seule fois, au démarrage de l'API : on charge le modèle en mémoire."""
        # Pipeline complet : préprocesseur (OneHotEncoder + StandardScaler) + XGBoost
        self.modele = bentoml.sklearn.load_model(self.modele_bento)

        # Liste ordonnée des features, sauvegardée avec le modèle (custom_objects)
        self.features = self.modele_bento.custom_objects["features"]

        # Garde-fou : si features.py ne correspond plus au modèle sauvegardé, l'API refuse de démarrer
        # plutôt que de renvoyer des prédictions fausses
        if self.features != FEATURES:
            raise RuntimeError("Les features de l'API ne correspondent pas à celles du modèle sauvegardé")

    # @bentoml.api crée la route POST /predire.
    # input_spec=Batiment : le corps de la requête est validé par Pydantic AVANT d'arriver ici
    # (une donnée incohérente est refusée avec un code 400, sans appeler le modèle).
    @bentoml.api(input_spec=Batiment)
    def predire(self, **batiment) -> Prediction:
        """Estime la consommation annuelle d'énergie d'un bâtiment."""
        b = Batiment(**batiment)

        # On traduit les noms de champs de l'API (en français, simples) vers les noms des colonnes
        # du jeu de données, utilisés par le feature engineering
        brut = pd.DataFrame([{
            "PrimaryPropertyType": b.type_batiment,
            "Neighborhood": b.quartier,
            "YearBuilt": b.annee_construction,
            "NumberofBuildings": b.nombre_batiments,
            "NumberofFloors": b.nombre_etages,
            "PropertyGFABuilding(s)": b.surface_batiment,
            "PropertyGFAParking": b.surface_parking,
            "LargestPropertyUseTypeGFA": b.surface_usage_principal,
            "UtiliseGaz": b.utilise_gaz,
            "UtiliseVapeur": b.utilise_vapeur,
            "Usages": list(b.usages),
        }])

        # Construction des 19 features, dans l'ordre vu par le modèle
        X = construire_features(brut)[self.features]

        # Le modèle a appris à prédire le LOG de la consommation : l'exponentielle (np.exp) la ramène en kBtu
        consommation_kbtu = float(np.exp(self.modele.predict(X)[0]))

        return Prediction(
            consommation_kbtu=round(consommation_kbtu),
            consommation_kwh=round(consommation_kbtu * KBTU_VERS_KWH),
        )
