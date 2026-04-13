# Etude de la robustesse d'un essaim de nano satellites

Pour le détail des objectifs du projet, se referrer a la présentation.

## Configuration
Le programme comporte 5 paramètres:
PATH qui permet d'indiquer l'emplacement et le nom du fichier source
MAXTEMPS qui permet de poser une limite de temps afin de ne pas s'éterniser dans les calculs pendant d'eventuels tests.
MIN_RANGE,MID_RANGE,MAX_RANGE Permettent de jouer sur la portée des satellites. Cela permetrai par exemple de faire de l'aide a la décision entre plusieurs types d'antennes pour les satellites.

La librairie swarm_sim a été modifiée pour disposer d'éléments nécéssaires a la réalisation du projet, comme par exemples des fonctions de visualisation (plot_nodes, plot_edges).

## Architecture
Le programme est séparé en phases pour faciliter sa transposition dans un notebook comme jupyter ou collab.
Notre solution suit le schéma suivant :

1 - Manipulation du fichier source.
2 - Mise en forme de la donnee en memoire (Creation des structures de donnees necessaires)
3 - Analyse de la donnee pour en extraire des metriques
4 - Selection des elements d'interet au sein de la donnee
5 - Analyse approfondie des metriques pour les cas d'interet.
6 - Creation de scenarios en l'absence de noeuds en fonction des differentes strategies
7 - Analyse de l'evolution des metriques sur les reseaux ou des noeuds ont etes supprimes.

Note: Nous avons laissé en commentaire entre les points 6 et 7 tout les afichages desquels nous avons extrait les données pour construire nos graphiques. Les données sont retrouvables dans le google sheet fourni avec ce programme ainsi que dans le fichier output.txt.

# GUIDE A DESTINATION DES PROCHAINS UTILISATEURS

## Afficher les positions de tous les points au temps 70
print(Positions[70])
## Afficher la position du noeud 1 au temps 70
print(Positions[70][1])
## Afficher la coordonée x du noeud 1 au temps 70
print(Positions[70][1].x)
## Afficher la coordonée y du noeud 5 au temps 75
print(Positions[75][5].y)
## Afficher la matrice d'adjacence au temps 70
print(Matrixes[70])
## Afficher le cout entre le sat 2 et 3 au temps 70
print(Matrixes[70][2][3])
## Afficher le swarm a l'instant 70
print(Swarms[70])
## Afficher les métriques pour chacuns des graphs
print(AnalyzeGraph(Positions, Swarms, Matrixes))
## Afficher les métriques pour le temps 75
print(AnalyzeGraph(Positions, Swarms, Matrixes)[75])
## Afficher le scenario disposant de la meilleure efficacite
print(GetBestCase(Stats))
## Afficher les 6 noeuds disposant de la plus grande "importance" au temps 78
print(GetTopImportanceNoeud(Matrixes[78], 6))
## Supprimer 6 noeuds du meilleur et pire scénario en utilisant la strategie centralité
print(StrategieCentralite(6))
