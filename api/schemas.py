"""Validation des données envoyées à l'API (Pydantic).

L'utilisateur décrit son bâtiment avec des informations simples, sans connaître l'encodage des features.
Chaque règle empêche une valeur incohérente, ou hors du domaine sur lequel le modèle a été entraîné.
Les surfaces sont en pieds² (sf), comme dans les données de Seattle (1 pied² ≈ 0,093 m²).

Pydantic vérifie automatiquement chaque requête reçue : si une règle n'est pas respectée, l'API refuse
la requête (code 400) et renvoie un message expliquant l'erreur, sans jamais appeler le modèle.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ---------------------------------------------------------------------------------------------------------
# Valeurs autorisées
# Un « Literal » n'accepte que les valeurs listées : ce sont celles présentes dans les données d'entraînement.
# Une valeur inconnue (ex. « Château ») est refusée, car le modèle ne saurait pas l'interpréter.
# ---------------------------------------------------------------------------------------------------------

# Les 20 types de bâtiments (PrimaryPropertyType) du jeu nettoyé
TypeBatiment = Literal[
    "Distribution Center", "Hospital", "Hotel", "K-12 School", "Laboratory", "Large Office", "Medical Office",
    "Mixed Use Property", "Other", "Refrigerated Warehouse", "Residence Hall", "Restaurant", "Retail Store",
    "Self-Storage Facility", "Senior Care Community", "Small- and Mid-Sized Office", "Supermarket / Grocery Store",
    "University", "Warehouse", "Worship Facility",
]

# Les 13 quartiers de Seattle (Neighborhood)
Quartier = Literal[
    "BALLARD", "CENTRAL", "DELRIDGE", "DOWNTOWN", "EAST", "GREATER DUWAMISH", "LAKE UNION",
    "MAGNOLIA / QUEEN ANNE", "NORTH", "NORTHEAST", "NORTHWEST", "SOUTHEAST", "SOUTHWEST",
]

# Les 65 usages possibles (ListOfAllPropertyUseTypes), sans le texte entre parenthèses
Usage = Literal[
    "Adult Education", "Automobile Dealership", "Bank Branch", "Bar/Nightclub", "College/University",
    "Convenience Store without Gas Station", "Courthouse", "Data Center", "Distribution Center", "Enclosed Mall",
    "Fast Food Restaurant", "Financial Office", "Fire Station", "Fitness Center/Health Club/Gym", "Food Sales",
    "Food Service", "Hospital", "Hotel", "K-12 School", "Laboratory", "Library", "Lifestyle Center",
    "Manufacturing/Industrial Plant", "Medical Office", "Movie Theater", "Multifamily Housing", "Museum",
    "Non-Refrigerated Warehouse", "Office", "Other", "Other - Education", "Other - Entertainment/Public Assembly",
    "Other - Lodging/Residential", "Other - Mall", "Other - Public Services", "Other - Recreation",
    "Other - Restaurant/Bar", "Other - Services", "Other - Technology/Science", "Other - Utility",
    "Other/Specialty Hospital", "Outpatient Rehabilitation/Physical Therapy", "Parking", "Performing Arts",
    "Personal Services", "Police Station", "Pre-school/Daycare", "Prison/Incarceration", "Refrigerated Warehouse",
    "Repair Services", "Residence Hall/Dormitory", "Residential Care Facility", "Restaurant", "Retail Store",
    "Self-Storage Facility", "Senior Care Community", "Single Family Home", "Social/Meeting Hall", "Strip Mall",
    "Supermarket/Grocery Store", "Swimming Pool", "Urgent Care/Clinic/Other Outpatient", "Vocational School",
    "Wholesale Club/Supercenter", "Worship Facility",
]

# ---------------------------------------------------------------------------------------------------------
# Seuils de cohérence, tirés du domaine des données d'entraînement (notebooks 01 et 02)
# ---------------------------------------------------------------------------------------------------------
SURFACE_TOTALE_MIN, SURFACE_TOTALE_MAX = 10_000, 2_500_000  # surfaces observées : de 11 285 à 2,2 millions de pieds²
SURFACE_PAR_ETAGE_MIN = 1_000                                # plus petite valeur observée : 1 818 pieds² par étage
TOLERANCE_USAGE_PRINCIPAL = 1.1                              # même tolérance de 10 % que lors du nettoyage

# Bâtiment d'exemple affiché (et modifiable) dans l'interface Swagger
EXEMPLE = {
    "type_batiment": "Small- and Mid-Sized Office",
    "quartier": "DOWNTOWN",
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


class Batiment(BaseModel):
    """Description d'un bâtiment non résidentiel de Seattle : ce que l'utilisateur envoie à l'API."""

    # extra="forbid" : un champ inconnu (ex. « couleur_facade ») est refusé au lieu d'être ignoré en silence.
    # « example » au singulier : format OpenAPI 3.0 attendu par BentoML pour pré-remplir l'interface Swagger.
    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": EXEMPLE})

    # Chaque champ a un type (texte, entier, nombre, booléen…) et des bornes :
    # ge = « supérieur ou égal », gt = « strictement supérieur », le = « inférieur ou égal ».
    # La description s'affiche dans Swagger pour guider l'utilisateur.
    type_batiment: TypeBatiment = Field(description="Usage principal du bâtiment")
    quartier: Quartier = Field(description="Quartier de Seattle (majuscules ou minuscules acceptées)")
    annee_construction: int = Field(ge=1900, le=2016, description="Année de construction (entre 1900 et 2016)")
    nombre_batiments: int = Field(ge=1, le=30, description="Nombre de bâtiments de la propriété")
    nombre_etages: int = Field(ge=1, le=80, description="Nombre d'étages (le plus haut immeuble de Seattle en compte 76)")
    surface_batiment: float = Field(gt=0, description="Surface bâtie hors parking, en pieds²")
    surface_parking: float = Field(ge=0, description="Surface de parking, en pieds² (0 si aucun)")
    surface_usage_principal: float = Field(gt=0, description="Surface occupée par l'usage principal, en pieds²")
    usages: list[Usage] = Field(min_length=1, max_length=15,
                                description="Tous les usages présents dans le bâtiment, y compris l'usage principal")
    utilise_gaz: bool = Field(description="Le bâtiment est-il équipé au gaz naturel (chauffage, cuisson) ?")
    utilise_vapeur: bool = Field(description="Le bâtiment est-il raccordé au réseau de vapeur urbain ?")

    # -----------------------------------------------------------------------------------------------------
    # Règles sur un seul champ (field_validator)
    # -----------------------------------------------------------------------------------------------------

    @field_validator("quartier", mode="before")
    @classmethod
    def quartier_en_majuscules(cls, valeur):
        """Accepte « downtown » ou « Downtown » : on met en majuscules avant de comparer à la liste."""
        # mode="before" : cette étape s'exécute AVANT la vérification de la liste des quartiers
        return valeur.strip().upper() if isinstance(valeur, str) else valeur

    @field_validator("usages")
    @classmethod
    def usages_sans_doublon(cls, usages):
        """Refuse un même usage cité deux fois, qui fausserait le nombre d'usages du bâtiment."""
        if len(set(usages)) != len(usages):  # un ensemble (set) ne garde qu'un exemplaire de chaque valeur
            raise ValueError("un même usage est indiqué plusieurs fois")
        return usages

    # -----------------------------------------------------------------------------------------------------
    # Règles qui croisent plusieurs champs (model_validator)
    # mode="after" : elles s'exécutent une fois que chaque champ a été vérifié individuellement
    # -----------------------------------------------------------------------------------------------------

    @model_validator(mode="after")
    def surfaces_coherentes(self):
        """Vérifie que les surfaces sont cohérentes entre elles et avec le nombre d'étages."""
        # Dans les données, la surface totale vaut toujours surface bâtie + surface de parking :
        # on la calcule nous-mêmes plutôt que de la demander (impossible d'envoyer un total incohérent)
        surface_totale = self.surface_batiment + self.surface_parking

        # 1. Bâtiment trop petit ou trop grand : le modèle n'a jamais vu de tels bâtiments
        if not SURFACE_TOTALE_MIN <= surface_totale <= SURFACE_TOTALE_MAX:
            raise ValueError(
                f"la surface totale (bâtiment + parking = {surface_totale:,.0f} pieds²) doit être comprise entre "
                f"{SURFACE_TOTALE_MIN:,} et {SURFACE_TOTALE_MAX:,} pieds², le domaine sur lequel le modèle a été entraîné"
            )

        # 2. L'usage principal ne peut pas occuper plus de place que le bâtiment entier (10 % de tolérance)
        if self.surface_usage_principal > TOLERANCE_USAGE_PRINCIPAL * surface_totale:
            raise ValueError("la surface de l'usage principal ne peut pas dépasser la surface totale du bâtiment")

        # 3. Surface par étage absurde (ex. 40 étages pour 20 000 pieds² = 500 pieds² par étage)
        if self.surface_batiment / self.nombre_etages < SURFACE_PAR_ETAGE_MIN:
            raise ValueError(
                f"la surface par étage ({self.surface_batiment / self.nombre_etages:,.0f} pieds²) est trop faible : "
                f"vérifiez le nombre d'étages et la surface bâtie"
            )
        return self


class Prediction(BaseModel):
    """Ce que l'API renvoie : la consommation d'énergie annuelle estimée pour le bâtiment."""

    consommation_kbtu: float = Field(description="Consommation annuelle estimée, en kBtu")
    consommation_kwh: float = Field(description="Consommation annuelle estimée, en kWh (1 kBtu ≈ 0,293 kWh)")
