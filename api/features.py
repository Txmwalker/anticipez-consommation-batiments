"""Feature engineering de l'API : reproduit exactement celui du notebook 02_modelisation.ipynb.

L'utilisateur de l'API envoie des informations brutes sur son bâtiment (type, quartier, surfaces…) ;
ce module les transforme en features, dans le même ordre que celles vues par le modèle à l'entraînement.
Si le calcul différait du notebook, le modèle recevrait des données différentes de celles qu'il a apprises
et ses prédictions seraient fausses, sans aucun message d'erreur.
"""
import re

import numpy as np
import pandas as pd

# Année des relevés : sert à calculer l'âge du bâtiment, comme dans le notebook
ANNEE_RELEVE = 2016

# ---------------------------------------------------------------------------------------------------------
# Règles métier fixées à l'avance (copiées du notebook 02)
# ---------------------------------------------------------------------------------------------------------

# Usages très énergivores : une feature 0 / 1 par famille (« le bâtiment contient-il un restaurant ? »…)
USAGES_INTENSIFS = {
    "UsageRestauration": ["Restaurant", "Fast Food Restaurant", "Food Service", "Other - Restaurant/Bar", "Bar/Nightclub"],
    "UsageAlimentaire": ["Supermarket/Grocery Store", "Food Sales", "Convenience Store without Gas Station", "Wholesale Club/Supercenter"],
    "UsageSante": ["Hospital", "Other/Specialty Hospital", "Urgent Care/Clinic/Other Outpatient", "Laboratory"],
    "UsageDataCenter": ["Data Center"],
    "UsagePiscineSport": ["Swimming Pool", "Fitness Center/Health Club/Gym"],
    "UsageFroid": ["Refrigerated Warehouse"],
    "UsageParking": ["Parking"],
}

# Regroupement des 20 types de bâtiments en 9 familles d'usage
FAMILLES = {
    "Bureau": ["Large Office", "Small- and Mid-Sized Office", "Office"],
    "Santé": ["Hospital", "Medical Office", "Laboratory", "Senior Care Community"],
    "Alimentation": ["Supermarket / Grocery Store", "Restaurant"],
    "Commerce": ["Retail Store"],
    "Logistique": ["Warehouse", "Distribution Center", "Refrigerated Warehouse", "Self-Storage Facility"],
    "Enseignement": ["K-12 School", "University"],
    "Hébergement": ["Hotel", "Residence Hall"],
    "Culte": ["Worship Facility"],
    "Mixte / Autre": ["Mixed Use Property", "Other"],
}

# Regroupement des 13 quartiers en 3 zones de la ville
ZONES = {
    "Centre": ["DOWNTOWN", "LAKE UNION", "EAST", "CENTRAL"],
    "Nord": ["NORTH", "NORTHEAST", "NORTHWEST", "BALLARD", "MAGNOLIA / QUEEN ANNE"],
    "Sud": ["GREATER DUWAMISH", "SOUTHEAST", "SOUTHWEST", "DELRIDGE"],
}

# Dictionnaires « inversés » pour retrouver directement la famille d'un type et la zone d'un quartier
# ex. TYPE_VERS_FAMILLE["Hotel"] = "Hébergement", QUARTIER_VERS_ZONE["DOWNTOWN"] = "Centre"
TYPE_VERS_FAMILLE = {t: famille for famille, types in FAMILLES.items() for t in types}
QUARTIER_VERS_ZONE = {q: zone for zone, quartiers in ZONES.items() for q in quartiers}

# ---------------------------------------------------------------------------------------------------------
# Ordre des 19 features vu par le modèle à l'entraînement (notebook 02, section « Sélection finale »)
# Le préprocesseur du modèle repère les colonnes par leur nom : cet ordre doit rester identique.
# ---------------------------------------------------------------------------------------------------------
FEATURES_CONTINUES = ["LogSurfaceTotale", "LogSurfaceParEtage", "NumberofFloors", "BuildingAge",
                      "PartParking", "PartUsagePrincipal", "NbUsages"]
FEATURES_BINAIRES = ["MultiBatiments", "UtiliseGaz", "UtiliseVapeur", *USAGES_INTENSIFS]
FEATURES_CATEGORIELLES = ["FamilleUsage", "ZoneVille"]
FEATURES = FEATURES_CONTINUES + FEATURES_BINAIRES + FEATURES_CATEGORIELLES


def lister_usages(texte):
    """Découpe ListOfAllPropertyUseTypes en liste d'usages.

    Sert à reproduire le notebook à partir des données brutes (l'API, elle, reçoit directement une liste).
    Le texte entre parenthèses est retiré d'abord, car il contient lui-même des virgules :
    « Repair Services (Vehicle, Shoe, Locksmith, etc) » doit compter pour un seul usage.
    """
    if pd.isna(texte):
        return []
    texte = re.sub(r"\([^)]*\)", "", texte)  # supprime « (…) »
    return [usage.strip() for usage in texte.split(",") if usage.strip()]


def construire_features(batiments: pd.DataFrame) -> pd.DataFrame:
    """Construit les 19 features du modèle à partir des colonnes brutes (une ligne par bâtiment).

    Colonnes attendues : PrimaryPropertyType, Neighborhood, YearBuilt, NumberofBuildings, NumberofFloors,
    PropertyGFABuilding(s), PropertyGFAParking, LargestPropertyUseTypeGFA, UtiliseGaz, UtiliseVapeur,
    et Usages (liste des usages du bâtiment).
    """
    b = batiments
    surface_totale = b["PropertyGFABuilding(s)"] + b["PropertyGFAParking"]
    usages = b["Usages"]

    X = pd.DataFrame(index=b.index)

    # Structure : surfaces en log (relation linéaire en log-log avec la consommation) et ratios
    X["LogSurfaceTotale"] = np.log(surface_totale)
    X["LogSurfaceParEtage"] = np.log(b["PropertyGFABuilding(s)"] / b["NumberofFloors"])
    X["NumberofFloors"] = b["NumberofFloors"]
    X["PartParking"] = b["PropertyGFAParking"] / surface_totale

    # Temporalité : âge du bâtiment en 2016
    X["BuildingAge"] = ANNEE_RELEVE - b["YearBuilt"]

    # Usages : part de l'usage principal (bornée à 1) et nombre d'usages (au moins 1)
    X["PartUsagePrincipal"] = (b["LargestPropertyUseTypeGFA"] / surface_totale).clip(upper=1)
    X["NbUsages"] = usages.str.len().clip(lower=1)

    # Features binaires (0 / 1)
    X["MultiBatiments"] = (b["NumberofBuildings"] > 1).astype(int)
    X["UtiliseGaz"] = b["UtiliseGaz"].astype(int)
    X["UtiliseVapeur"] = b["UtiliseVapeur"].astype(int)
    for colonne, liste in USAGES_INTENSIFS.items():
        # 1 si au moins un des usages du bâtiment fait partie de la famille énergivore
        X[colonne] = usages.apply(lambda u: int(any(usage in liste for usage in u)))

    # Features catégorielles : famille d'usage et zone (encodées ensuite par le OneHotEncoder du modèle)
    X["FamilleUsage"] = b["PrimaryPropertyType"].map(TYPE_VERS_FAMILLE)
    X["ZoneVille"] = b["Neighborhood"].map(QUARTIER_VERS_ZONE)

    # On renvoie les colonnes dans l'ordre exact vu par le modèle à l'entraînement
    return X[FEATURES]
