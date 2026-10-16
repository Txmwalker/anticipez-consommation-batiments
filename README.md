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

## Structure

```
.
├── data/
│   └── 2016_Building_Energy_Benchmarking.csv
├── notebooks/
│   ├── template_modelistation_supervisee.ipynb   # template fourni (non modifié)
│   └── analyse_consommation_batiments.ipynb      # notebook du projet
├── quiz_*.py                                     # scripts des quiz du cours
├── fiche_revision_machine_learning.md            # fiche de révision du cours
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

Ouvrir ensuite `notebooks/analyse_consommation_batiments.ipynb` (VS Code ou Jupyter) et exécuter les cellules dans l'ordre.

## Avancement

- [x] Analyse exploratoire
- [ ] Feature engineering et préparation des features
- [ ] Comparaison des modèles
- [ ] Optimisation et interprétation
- [ ] API et déploiement cloud
