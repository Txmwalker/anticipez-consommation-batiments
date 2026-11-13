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
4. **Comparaison des modèles** (notebook 02) : DummyRegressor, régression linéaire, SVR, arbre de décision, Random Forest et XGBoost,
   évalués dans les mêmes conditions (séparation train / test 80 / 20, validation croisée à 5 plis, R², MAE, RMSE).
5. **Optimisation et interprétation** (notebook 02) : `GridSearchCV` sur XGBoost (144 combinaisons), R² de 0,75 sur le jeu de test.
   La surface et la famille d'usage sont les deux principaux facteurs utilisés par le modèle.

## Structure

```
.
├── data/
│   ├── 2016_Building_Energy_Benchmarking.csv     # données brutes
│   └── building_consumption_clean.csv            # jeu nettoyé (export du notebook 01)
├── notebooks/
│   ├── template_modelistation_supervisee.ipynb   # template fourni
│   ├── 01_analyse_exploratoire.ipynb             # analyse exploratoire, nettoyage et sélection des colonnes
│   └── 02_modelisation.ipynb                     # feature engineering, préparation, modélisation et sauvegarde BentoML
├── api/
│   ├── features.py                               # feature engineering (identique au notebook 02)
│   ├── schemas.py                                # validation des données envoyées à l'API (Pydantic)
│   ├── service.py                                # service BentoML et endpoint /predire
│   └── tester_api.py                             # requêtes de test (valide et incohérentes)
├── bentofile.yaml                                # construction du Bento et de l'image Docker
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
(VS Code ou Jupyter, noyau `.venv`). Le notebook 02 sauvegarde le modèle retenu dans le *model store* de BentoML.

## API de prédiction (BentoML)

L'API reçoit les informations brutes d'un bâtiment (type, quartier, année, étages, surfaces, usages, équipements gaz / vapeur),
vérifie leur cohérence, construit les features et renvoie la consommation annuelle estimée (kBtu et kWh).

```bash
bentoml serve api.service:PredictionConsommation
```

Interface Swagger : http://localhost:3000. Tests en ligne de commande, l'API étant lancée :

```bash
python api/tester_api.py
```

Exemple de requête :

```bash
curl -X POST http://localhost:3000/predire -H "Content-Type: application/json" -d "{\"type_batiment\": \"Hotel\", \"quartier\": \"DOWNTOWN\", \"annee_construction\": 1985, \"nombre_batiments\": 1, \"nombre_etages\": 10, \"surface_batiment\": 90000, \"surface_parking\": 0, \"surface_usage_principal\": 90000, \"usages\": [\"Hotel\", \"Restaurant\"], \"utilise_gaz\": true, \"utilise_vapeur\": false}"
```

### Image Docker et déploiement sur Render

Le `bentofile.yaml` décrit le Bento : le service, le code de l'API, le modèle et les dépendances de production.

```bash
bentoml build
bentoml containerize consommation_batiments:latest --image-tag consommation-batiments:latest
docker run --rm -p 3000:3000 consommation-batiments:latest
```

L'image est publiée sur Docker Hub (`tomwalker05/consommation-batiments:latest`), puis déployée sur Render
(*Web Service* depuis une image existante, variable d'environnement `PORT=3000`, *health check* sur `/readyz`) :

```bash
docker tag consommation-batiments:latest tomwalker05/consommation-batiments:latest
docker push tomwalker05/consommation-batiments:latest
```

API déployée : https://consommation-batiments.onrender.com (interface Swagger). Sur l'offre gratuite de Render, le service se met
en veille après 15 minutes sans requête : la première requête suivante prend environ une minute.

```bash
python api/tester_api.py https://consommation-batiments.onrender.com
```

## Avancement

- [x] Analyse exploratoire
- [x] Feature engineering
- [x] Préparation des features
- [x] Comparaison des modèles
- [x] Optimisation et interprétation
- [x] API et déploiement cloud
