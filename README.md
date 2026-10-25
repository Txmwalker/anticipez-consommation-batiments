# Anticipez les besoins en consommation de bâtiments

Projet OpenClassrooms — parcours Data Engineer.

La ville de Seattle vise la neutralité carbone en 2050. Les relevés de consommation des bâtiments étant coûteux, l'objectif est de
**prédire la consommation totale d'énergie** (`SiteEnergyUse(kBtu)`) des bâtiments **non destinés à l'habitation** à partir de leurs
**données structurelles** (taille, usage, année de construction, localisation…).

- **Partie 1** : analyse exploratoire, feature engineering, comparaison de modèles supervisés, optimisation et interprétation.
- **Partie 2** : exposition du modèle via une API hébergée dans le cloud.

## Données

`data/2016_Building_Energy_Benchmarking.csv` — relevés 2016 du *Building Energy Benchmarking* de Seattle
([source](https://data.seattle.gov/Built-Environment/Building-Energy-Benchmarking-Data-2015-Present/teqw-tu6e/about_data)) :
3 376 bâtiments, 46 colonnes.

`data/building_consumption_clean.csv` — jeu nettoyé exporté par le notebook 01 : 1 454 bâtiments non résidentiels
(relevés conformes, valeurs cohérentes), 12 colonnes structurelles + la cible. Les colonnes issues du relevé de consommation
(fuite de données) sont exclues ; la présence de gaz et de vapeur est conservée sous forme d'indicateurs 0 / 1.

## Démarche

1. **Analyse exploratoire** (notebook 01) : choix de la cible, filtrage des logements et des relevés non conformes, correction des
   incohérences (journal des filtrages), étude des liens entre consommation, surface, usage, âge et localisation, sélection des colonnes.
2. **Feature engineering** (notebook 02) : 20 features couvrant la temporalité, la structure, les usages, les sources d'énergie
   et la localisation, toutes calculables sans relevé de consommation.
3. **Préparation des features** (notebook 02) : retrait de 16 valeurs extrêmes (seuils de quantiles 0,5 % / 99,5 %), passage de la cible
   au log, suppression des features redondantes, séparation X / y et encodage (`OneHotEncoder`, `StandardScaler` dans un `ColumnTransformer`).
   Jeu final : 1 434 bâtiments, 19 features.

## Structure

```
.
├── data/
│   ├── 2016_Building_Energy_Benchmarking.csv     # données brutes
│   └── building_consumption_clean.csv            # jeu nettoyé (export du notebook 01)
├── notebooks/
│   ├── template_modelistation_supervisee.ipynb   # template fourni
│   ├── 01_analyse_exploratoire.ipynb             # analyse exploratoire, nettoyage et sélection des colonnes
│   └── 02_modelisation.ipynb                     # feature engineering, préparation des features et modélisation
├── requirements.txt
└── README.md
```

## Installation

Python 3.13 :

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Exécuter ensuite, dans l'ordre, `notebooks/01_analyse_exploratoire.ipynb` (qui exporte le jeu nettoyé) puis `notebooks/02_modelisation.ipynb`
(VS Code ou Jupyter, noyau `.venv`).

## Avancement

- [x] Analyse exploratoire
- [x] Feature engineering
- [x] Préparation des features
- [ ] Comparaison des modèles
- [ ] Optimisation et interprétation
- [ ] API et déploiement cloud
