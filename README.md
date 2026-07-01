# 🛰️ Étude de la Robustesse d'un Essaim de Nano-Satellites (DTN)

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Network Simulation](https://img.shields.io/badge/Simulation-Network-green.svg)
![DTN](https://img.shields.io/badge/Protocol-DTN-orange.svg)

Ce projet propose une modélisation et une simulation avancées d'un réseau de **nano-satellites** s'appuyant sur les principes des réseaux tolérants aux délais et aux perturbations (**DTN - Delay-Tolerant Networks**). Son objectif principal est d'étudier l'impact des contraintes physiques (bande passante variable selon la distance) et la résilience du réseau face à la perte ciblée ou aléatoire de nœuds critiques.

---

## ✨ Fonctionnalités Principales

- **Modélisation Spatiale Dynamique** : Analyse des traces de 100 satellites en mouvement, transformant l'espace physique en graphes mathématiques évolutifs.
- **Protocoles DTN (Store-Carry-and-Forward)** : Implémentation complète et comparaison de 4 stratégies de routage : *Direct Delivery*, *Epidemic*, *Spray and Wait* et *PRoPHET*.
- **Contraintes Physiques Réalistes** : Gestion dynamique de la bande passante. Le débit de transfert entre deux satellites dépend de leur distance spatiale euclidienne, créant des congestions de réseau réalistes (étranglement de bout de portée).
- **Tests de Résilience et Théorie des Graphes** : Simulation d'attaques ou de pannes sur l'essaim. Identification des maillons faibles (Centralité, Hubs d'Importance) et évaluation de la dégradation des performances réseau (Delivery Ratio, Latency, Overhead).
- **Outils d'Analyse et de Visualisation** : Calcul de métriques complexes (Degré moyen, Connexité, Efficacité, Clustering) et génération automatique de graphiques comparatifs.

---

## 🏗️ Architecture du Projet

Notre solution est conçue de manière modulaire, séparée en phases distinctes facilitant son exécution de bout en bout et l'analyse de données (transposable sur Jupyter Notebook ou Google Colab).

1. **Extraction de la donnée** : Importation des traces spatiales et conversion des coordonnées physiques en nœuds virtuels.
2. **Construction des Graphes (`simu.py`)** : Création des matrices d'adjacence basées sur la portée radio (`MAX_RANGE`).
3. **Analyse Réseau** : Calcul continu des métriques pour évaluer l'état topologique de l'essaim.
4. **Moteur DTN (`dtn_core.py`)** : Cœur de la simulation gérant les paquets physiques (taille variable), les buffers satellitaires et l'horloge spatiale.
5. **Logique de Routage (`dtn_protocols.py`)** : Implémentation des règles d'échange et du bridage mathématique du débit.
6. **Tests de Résilience (`dtn_resilience_test.py`)** : Orchestrateur évaluant les algorithmes sous diverses conditions de pannes (Baseline vs Scénarios de destruction ciblant l'Importance ou la Centralité).
7. **Visualisation (`plot_results.py`)** : Génération des graphiques d'impact et de performances globaux.

---

## 🚀 Les Protocoles de Routage Évalués

| Protocole | Stratégie | Avantages | Inconvénients |
| :--- | :--- | :--- | :--- |
| **Direct Delivery** | Livraison directe uniquement à la destination finale. | Aucun overhead, économie d'énergie et de tampon maximale. | Taux de livraison faible, latence extrême. |
| **Epidemic** | Inondation du réseau (diffusion massive à chaque rencontre). | Taux de livraison et latence mathématiquement optimaux (sans contrainte physique). | Overhead colossal, congestion totale du réseau satellitaire sous contrainte de débit. |
| **Spray & Wait** | Diffusion contrôlée (quota de copies distribuées en arbre, suivi de livraison directe). | Excellent compromis, borne la surcharge réseau. | Moins réactif qu'Epidemic sur des routes inattendues. |
| **PRoPHET** | Heuristique probabiliste basée sur l'historique des rencontres et l'inférence transitive. | Intelligence adaptative, très résilient, excellent ratio de livraison pour un overhead maîtrisé. | Calcul cognitif local permanent plus complexe pour les nano-satellites. |

---

## ⚙️ Configuration

Le comportement de la simulation peut être affiné via plusieurs paramètres majeurs situés en tête de script :

- `PATH` : Emplacement du fichier source contenant les traces spatiales (`Traces.csv`).
- `MAXTEMPS` : Limite temporelle de la simulation pour écourter les calculs lors des tests.
- `MIN_RANGE`, `MID_RANGE`, `MAX_RANGE` : Portées opérationnelles des antennes satellites. Permettent de simuler différents matériels de communication.
- **Activation du Débit** : Choix interactif (`use_bandwidth`) au lancement pour prendre en compte (ou non) la perte de débit lointaine afin de simuler la congestion réseau physique.

---

## 📖 Guide d'Utilisation Avancé (Cheat Sheet)

Voici quelques commandes utiles destinées aux développeurs ou analystes souhaitant manipuler directement les objets de la simulation (directement exploitables depuis `simu.py`) :

```python
# Afficher les positions de tous les points au temps 70
print(Positions[70])

# Afficher la coordonnée X du noeud 1 au temps 70
print(Positions[70][1].x)

# Afficher la matrice d'adjacence au temps 70
print(Matrixes[70])

# Afficher le coût / la distance entre les satellites 2 et 3 au temps 70
print(Matrixes[70][2][3])

# Afficher l'objet graphe "Swarm" à l'instant 70
print(Swarms[70])

# Afficher les métriques réseau globales pour l'instant 75 (Connexité, Efficacité, etc.)
print(AnalyzeGraph(Positions, Swarms, Matrixes)[75])

# Identifier le scénario disposant de la meilleure efficacité réseau
print(GetBestCase(Stats))

# Trouver les 6 nœuds ayant la plus grande "Importance" (Betweenness Centrality) au temps 78
print(GetTopImportanceNoeud(Matrixes[78], 6))

# Simuler une panne de 6 nœuds critiques basés sur leur Centralité et évaluer l'impact
print(StrategieCentralite(6))
```

---

## 📊 Résultats et Traces

L'ensemble des résultats de la simulation, des métriques calculées et des logs du routage DTN sont générés automatiquement et exportés sous plusieurs formats pour analyse :
- **Fichier de logs console** : `output.txt`
- **Graphes visuels (Réseau et Protocoles)** : Les graphiques `.png` (`plot_1_protocoles.png`, `plot_2_impact_debit.png`, etc.)
- **Analyses tableur complètes** : Données brutes disponibles dans `Resultats analyse.xlsx` et le tableur en ligne associé.
