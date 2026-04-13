import numpy as np
import pandas as pd
from tqdm import tqdm
from dataclasses import dataclass
from swarm_sim import *
import networkx as nx
import random
from prophet_sim import ProphetSimulator

# Chemin vers le fichier source des donnes
PATH = './Traces.csv'
# Nombre de temps a analyser
MAXTEMPS = 100
# Constantes de distance
MAX_RANGE = 60000
MID_RANGE = 40000
MIN_RANGE = 20000

###
### Manipulation du fichier source.
###

print("### Importation des données ### ")
df = pd.read_csv(PATH, header=0)

print("### Reformatage des données : ajout d'un index sur le temps ### ")
#On genere un tableau qui servira d'index de temps pour chaque echantillon
names = ['1']
i=2
while len(names)<10000 :
  names.append(''+ str(i))
  i=i+1

#On modifie le df pour ajouter en tete de colone notre index de temps
save = df.columns
df.columns = names
df.loc[-1] = save
df.index = df.index + 1 
df = df.sort_index()
print("### Reformatage des données : ajout d'un index sur les satelites ### ")
# On genere les noms des satelite 
satnames = ['satx1']
i=1
while len(satnames)<300 :
  if (i !=1):
    satnames.append('satx'+ str(i))
  satnames.append('saty'+ str(i))
  satnames.append('satz'+ str(i))
  i=i+1
# On applique notre index
df['coords'] = satnames
df = df.set_index('coords', drop=True)

# On transpose notre df pour avoir le temps en ligne et les coordonees de satelites en colonnes
dft = df.transpose()


###
### Mise en forme de la donnee en memoire (Creation des structures de donnees necessaires)
###

# On itère sur les elements de notre df pour en extraire des Node comme implantes dans swarm_sim
def GetNodes(time):
  nodes = {}
  id = 1
  while id < 101:
    node = Node(id - 1, dft.loc[str(time)]['satx'+str(id)], dft.loc[str(time)]['saty'+str(id)], dft.loc[str(time)]['satz'+str(id)])
    nodes[id - 1] = node
    id = id +1
  return nodes  

# Cette fonction permet, a partir du swarm, d'extraire une matrice d'adjaceance qui prend en compte le cout des differents liens.
def GetWeightedMatrix(Swarm):
  # On prend comme base le reseau avec une portee minimale puis on vient ajouter les chemins necessitant plus de portee en multipliant par un coefficient.
  matrix20 = Swarm.neighbor_matrix(MIN_RANGE)
  matrix40 = Swarm.neighbor_matrix(MID_RANGE)
  matrix60 = Swarm.neighbor_matrix(MAX_RANGE)
  x=0
  y=0 
  while x < len(matrix20) :
    y=0
    while y < len(matrix20):
      if (matrix20[x][y] == 0 and matrix40[x][y] == 1) :
        matrix20[x][y]=2
      if (matrix20[x][y] == 0 and matrix40[x][y] == 0 and matrix60[x][y] == 1):
        matrix20[x][y]=3 
      y=y+1
    x=x+1
  return matrix20

print("### Génération des tableaux de nodes en fonction du temps ### ")
def GetPositions(): 
  Positions = {}
  temps = 0
  while temps < MAXTEMPS:
    Positions[temps] = GetNodes(temps+1)
    temps = temps+1
  return Positions
Positions = GetPositions()

print("### Génération des swarms correspondants a chaque instants ###")
def InitSwarms(Positions):
  Swarms = {}
  temps = 0
  while temps < MAXTEMPS:
    Swarms[temps] = Swarm(MAX_RANGE, list(Positions[temps].values()))
    temps = temps+1
  return Swarms
Swarms = InitSwarms(Positions)

print("### Génération des matrices d'adjacence ###")
def GenerateWeightedMatrix(Swarms):
  Matrixes = {}
  temps = 0
  while temps < MAXTEMPS:
    Matrixes[temps] = GetWeightedMatrix(Swarms[temps])
    temps = temps+1
  return Matrixes
Matrixes=GenerateWeightedMatrix(Swarms)

###
### Analyse de la donnee pour en extraire des metriques
###


print("### Analyse des metriques pour chaque graphe ###")
@dataclass
class Metric:
  MeanDegree: float
  MeanClusterCoef : float
  Connexity : float #Nous prenon un float et non un boolen pour plus facilement calculer des statistiques comme le taux de connexite de l'essain au fil du temps
  Efficiency: float

@dataclass 
class NodeMetric: 
  Degree: int
  ClusteringCoef : float
  Centrality: float
  Mincycle: int # Plus petit cycle dont le noeud fait parti.
  NumberOfSP: int #Nombre de ShortestPath passant par le noeud.

# On itere sur tout les noeud d'un swarm et on moyenne leur coefficient de clustering
def GetMeanClusterCoef(Swarm):
  MeanClusterCoef = 0
  ClusterCoeffs = Swarm.cluster_coef()
  for f in ClusterCoeffs:
    MeanClusterCoef = MeanClusterCoef +f
  MeanClusterCoef = MeanClusterCoef/len(ClusterCoeffs)
  return MeanClusterCoef

# On itere sur tout les noeud d'un swarm et on moyenne leur degre
def GetMeanDegree(Swarm):
  MeanDegree = 0
  # Ici des resultats incoherents nous ont pousses a passer par l'intermediaire de networkx pour calculer le degre.
  Degrees = Swarm.swarm_to_nxgraph().degree()
  for f in Degrees:
    MeanDegree = MeanDegree + f[1]
  MeanDegree = MeanDegree/len(Degrees)
  return MeanDegree

# Les swarm etant initialises a partir de la plus grande portee, 
# un graphe disposant de plusieurs composante connectees est forcement non connexe
def GetConnexity(Swarm):
  if (len(Swarm.connected_components()) <= 1):
    return 1
  else:
    return 0

def GetCentrality(Swarm, Matrix):
  listCentrality = []
  degrees = Swarm.swarm_to_nxgraph().degree()
  for f in range(0,len(Matrix)):
    centrality = 0
    node = Swarm.get_node_by_id(f)
    neighbors = node.getNeighborsId();
    for d in degrees:
      if d[0] == f or neighbors.__contains__(d[0]):
        centrality+=d[1]
    listCentrality.append(centrality)

  return listCentrality

''' Renvoie id du noeud qui a la meilleure centralité '''
def topCentrality(Swarm, Matrix, NumberOfNode):
  listCentrality = GetCentrality(Swarm, Matrix)

  mapCentrality = {}
  for id in range(0,len(listCentrality)):
    mapCentrality[id] = listCentrality[id]
    
  sortedCentrality = {k: v for k, v in sorted(mapCentrality.items(), key=lambda item: item[1], reverse = True)}
  ordreSuppression = list(sortedCentrality.keys())
  idNoeud = ordreSuppression[0:NumberOfNode]

  return idNoeud

#testTopCentrality = topCentrality(Swarms[7], Matrixes[7])
#print("Noeud top centralité : ", testTopCentrality)

def GetClusterCoeffByNode(Swarm):
  return Swarm.cluster_coef()

# Cette fonction permet de traduire une matrice d'adjacence coefficientee en un graph networkx. 
# Cette forme est necessaire car swarm_sim ne prend pas en compte les poids dans ses fonctions. 
def MatrixtoNxGraph(Matrix):
  G = nx.Graph()
  x=0
  y=0 
  while x < len(Matrix) :
    y=0
    while y < len(Matrix):
      if x>y:
        if Matrix[x][y] != 0:
          G.add_edge(x, y, weight=Matrix[x][y])
      y=y+1
    x=x+1
  return G

# Cette fonction permet de calculer l'efficacite du reseaux. 
# L'efficacite est definie comme etant l'inverse de la moyenne de la longeur du plus court chemin entre toute les paire de noeuds.
def GetEfficiency(Swarm, Matrix):
  if (GetConnexity(Swarm) == 0):
    return 0
  # Deux options pour le calcul des plus courts chemins : 
  # soit on prend en compte les poids et on passe par networkx 
  # soit on ne les prend pas en compte et on passe par swarm_sim (option commentee ci dessous)
  G = MatrixtoNxGraph(Matrix)
  Pathlist = nx.all_pairs_dijkstra_path(G)
  #Pathlist = swarm.number_of_shortest_path_through_node()
  SommeSP=0
  for i in Pathlist:
    destination = 0
    while destination < len(Matrix):
      # On parcours la matrice des shortest path triangulairement en ajoutant leur longeur au fur et a mesure
      if i[0] < destination:
        # Dans l'eventualite ou le chemin serait de longeur 1, on evite les platage avec le test suivant
        if type(i[1][destination]) is int:
            SommeSP = SommeSP+1
        else:
          c=0
          while c < len(i[1][destination])-1:
              # Cette terrifante serie d'indexation permet simplement de recuperer le cout d'un lien entre deux noeuds du chemin.
              SommeSP=SommeSP+G[i[1][destination][c]][i[1][destination][c+1]]["weight"]
              c+=1
      destination= destination+1
  MedianSP = SommeSP/(len(Matrix)*len(Matrix))
  Efficiency = 1/MedianSP
  return Efficiency

# Retourne l'importance des noeuds sous forme d'un dictionnaire avec l'id (id de 1 à 100 vu que l'on utilise la matrice)
def GetNumberOfShorthestPathByNode(Matrix):
  G = MatrixtoNxGraph(Matrix)
  #listConnectedComponents = list(nx.connected_components(G));
  listShortestPath = list(nx.all_pairs_dijkstra_path(G))
  #listShortestPath = list(Swarm.number_of_shortest_path_through_node()); 
  # Tableau du nombre de plus court chemin pour chaque satellite
  NumberOfSP = {}
  for i in listShortestPath:
    SourceNode = i[0]
    # Nombre de plus court chemin pour le satellite observé
    NumberOfSPForNode = 0
    #a activer si on ne veut pas calculer les shortest path dans les groupes non connectés
    #if(listConnectedComponents[0].__contains__(SourceNode)):
    for j in listShortestPath:
      TargetNode = j[0]
      # Graph non orienté, donc aller et retour = même chemin 
      # (ne se compte qu'une fois)
      for k in j[1]:
          if(k < TargetNode and not(TargetNode == SourceNode and k == TargetNode) and j[1][k].__contains__(SourceNode)):
            NumberOfSPForNode+=1
    NumberOfSP[SourceNode + 1] = NumberOfSPForNode
  return NumberOfSP

# Retourne l'id du noeud le plus important
def GetTopImportanceNoeud(Matrix, NumberOfNode):
  ImportanceByNode = GetNumberOfShorthestPathByNode(Matrix)
  # tri de l'importance des noeuds
  SortedImportance = dict(sorted(ImportanceByNode.items(), key=lambda item: item[1]))
  # [::-1] : on met dans l'ordre décroissant
  # puis on retourne le nombre de noeuds voulus
  return list(SortedImportance.keys())[::-1][0:NumberOfNode]

# Cette fonction permet de faire tourner toutes les fonctions d'analyse de metrique definie plus haut sur un temps.
def AnalyzeSingleGraph(Position, Swarm, Matrix):
  MeanDegree = GetMeanDegree(Swarm)
  MeanClusterCoef = GetMeanClusterCoef(Swarm)
  Connexity = GetConnexity(Swarm)
  Efficiency = GetEfficiency(Swarm, Matrix)
  return Metric(MeanDegree,MeanClusterCoef,Connexity,Efficiency)

# Cette fonction permet de faire tourner toutes les fonctions d'analyse de metrique definie plus haut sur les differents temps.
def AnalyzeGraph(Positions, Swarms, Matrixes):
  Metrics = {}
  temps = 0
  while temps < MAXTEMPS:
    Metrics[temps] = AnalyzeSingleGraph(Positions[temps], Swarms[temps], Matrixes[temps])
    temps= temps+1
  return Metrics
Stats = AnalyzeGraph(Positions, Swarms, Matrixes)

###
### Selection des elements d'interet au sein de la donnee 
###

print("### Analyse des metriques moyennes de l'ensemble ###")
def AnalyzeMetrics(Stats):
  MeanDegree = 0
  MeanClusterCoef=0
  Connexity=0
  Efficiency=0

  for f in Stats: 
    MeanDegree = MeanDegree + Stats[f].MeanDegree
    MeanClusterCoef=MeanClusterCoef+Stats[f].MeanClusterCoef
    Connexity = Connexity + Stats[f].Connexity
    if Stats[f].Connexity == 1:
      Efficiency = Efficiency+Stats[f].Efficiency
  MeanDegree = MeanDegree/MAXTEMPS
  MeanClusterCoef=MeanClusterCoef/MAXTEMPS
  Efficiency=Efficiency/MAXTEMPS# Connexity
  Connexity=Connexity/MAXTEMPS
  TotalMetric = Metric(MeanDegree, MeanClusterCoef, Connexity, Efficiency)
  return TotalMetric
print(AnalyzeMetrics(Stats))

def GetWorstCase(Stats):
  counter=0
  worstEffi=1
  worstEffiIndex=0
  for Stat in Stats:
    if Stats[Stat].Connexity == 1:
      if Stats[Stat].Efficiency < worstEffi:
        worstEffi = Stats[Stat].Efficiency
        worstEffiIndex=counter
    counter += 1
  return worstEffiIndex

def GetBestCase(Stats):
  counter=0
  BestEffi=0
  BestEffiIndex=0
  for Stat in Stats:
    if Stats[Stat].Connexity == 1:
      if Stats[Stat].Efficiency >= BestEffi:
        BestEffi = Stats[Stat].Efficiency
        BestEffiIndex=counter
    counter += 1
  return BestEffiIndex


###
### Analyse approfondie des metriques pour les cas d'interet.
###

def topClusterNodeCoeff(Swarm):
  listCluster = GetClusterCoeffByNode(Swarm)
  sumCluster = 0
  for i in range(len(listCluster)):
    sumCluster = sumCluster + listCluster[i]
  
  average = sumCluster / len(listCluster)
  bestCluster = {}
  for i in range(1, len(listCStatsluster) + 1):
    #if(listCentrality[i] > average):
    bestCluster[i] = listCluster[i-1]
  _max = max(list(bestCluster.values()))

  return list(bestCluster.values()).index(_max)

###
### Creation de scenarios en l'absence de noeuds en fonction des differentes strategies
###
# Cette fonction permet de retourner un tableau de node dans lequel ne figure pas les node d'index fournis
def CreateAlterWithout(Position, IndexList):
  UpdatedPosition = []
  for node in range(len(Position)):
    if not node in IndexList:
      UpdatedPosition.append(Position[node])
  return UpdatedPosition

def StatFromPosition(Position):
  NewSwarm = Swarm(MAX_RANGE, Position)
  NewMatrix = GetWeightedMatrix(NewSwarm)
  return AnalyzeSingleGraph(Position, NewSwarm, NewMatrix)
  
def StrategieCentralite(nbToDelete):
  WorstCase = GetWorstCase(Stats)
  NewWorst = CreateAlterWithout(Positions[WorstCase], topCentrality(Swarms[WorstCase], Matrixes[WorstCase], nbToDelete))
  StatWorst = StatFromPosition(NewWorst)

  BestCase = GetBestCase(Stats)
  NewBest = CreateAlterWithout(Positions[BestCase], topCentrality(Swarms[BestCase], Matrixes[BestCase], nbToDelete))
  StatBest = StatFromPosition(NewBest)
  
  return [StatBest, StatWorst]

def StrategieImportance(nbToDelete):
  WorstCase = GetWorstCase(Stats)
  NewWorst = CreateAlterWithout(Positions[WorstCase],GetTopImportanceNoeud(Matrixes[WorstCase], nbToDelete))
  StatWorst = StatFromPosition(NewWorst)

  BestCase = GetBestCase(Stats)
  NewBest = CreateAlterWithout(Positions[BestCase],GetTopImportanceNoeud(Matrixes[BestCase], nbToDelete))
  StatBest = StatFromPosition(NewBest)
  return [StatBest, StatWorst]

def StrategieAleatoire(nbToDelete):
  
  WorstCase = GetWorstCase(Stats)

  RandomNumbers = []
  for i in range(nbToDelete):
    RandomNumber = random.randint(0,len(Matrixes[WorstCase]))
    while RandomNumbers.__contains__(RandomNumber):
      RandomNumber = random.randint(0,len(Matrixes[WorstCase]))
    RandomNumbers.append(RandomNumber)
  
  NewWorst = CreateAlterWithout(Positions[WorstCase],RandomNumbers)
  StatWorst = StatFromPosition(NewWorst)

  BestCase = GetBestCase(Stats)
  NewBest = CreateAlterWithout(Positions[BestCase],RandomNumbers)
  StatBest = StatFromPosition(NewBest)
  return [StatBest, StatWorst]

StatsStrategieImportance1 = StrategieImportance(1)
StatsStrategieImportance5 = StrategieImportance(5)
StatsStrategieCentralite1 = StrategieCentralite(1)
StatsStrategieCentralite5 = StrategieCentralite(5)
StatsStrategieAleatoire1= StrategieAleatoire(1)
StatsStrategieAleatoire5= StrategieAleatoire(5)

#WorstCase = GetWorstCase(Stats)
#print("Top Importance Worst")
#print(GetTopImportanceNoeud(Matrixes[WorstCase], 10))
#print("Top Centralite Worst")
#print(topCentrality(Swarms[WorstCase], Matrixes[WorstCase], 10))

#BestCase = GetBestCase(Stats)
#print("Top Importance Best")
#print(GetTopImportanceNoeud(Matrixes[BestCase], 10))
#print("Top Centralite Best")
#print(topCentrality(Swarms[BestCase], Matrixes[BestCase], 10)) 

#print("Importance 1")
#print(StatsStrategieImportance1)
#print("Importance 3")
#print(StrategieImportance(3))
#print("Importance 5")
#print(StatsStrategieImportance5)
#print("Importance 7")
#print(StrategieImportance(7))
#print("Importance 10")
#print(StrategieImportance(10))

#print("Centralite 1")
#print(StatsStrategieCentralite1)
#print("Centralite 3")
#print(StrategieCentralite(3))
#print("Centralite 5")
#print(StatsStrategieCentralite5)
#print("Centralite 7")
#print(StrategieCentralite(7))
#print("Centralite 10")
#print(StrategieCentralite(10))

#print("Aleatoire 1")
#print(StatsStrategieAleatoire1)
#print("Aleatoire 3")
#print(StrategieAleatoire(3))
#print("Aleatoire 5")
#print(StatsStrategieAleatoire5)
#print("Aleatoire 7")
#print(StrategieAleatoire(7))
#print("Aleatoire 10")
#print(StrategieAleatoire(10))

###
### Analyse de l'evolution des metriques sur les reseaux ou des noeuds ont etes supprimes.
### 
print("\n\n##### RESULTATS #####")
WorstIndex = GetWorstCase(Stats)
print("### Statistiques initiales du pire essaim connexe, l'essaim : " + str(WorstIndex))
print(Stats[WorstIndex])
print("\n## Statistiques du pire essaim une fois le noeud de plus haute 'importance' supprime ")
print(StatsStrategieImportance1[1])
print("# Variation de degre moyen :" + str((Stats[WorstIndex].MeanDegree - StatsStrategieImportance1[1].MeanDegree)))
print("# Variation de coefficient de clustering moyen :"+ str((Stats[WorstIndex].MeanClusterCoef - StatsStrategieImportance1[1].MeanClusterCoef)))
print("# Variation d'efficacite :" + str((Stats[WorstIndex].Efficiency - StatsStrategieImportance1[1].Efficiency)))

print("\n## Statistiques du pire essaim une fois les 5 noeud de plus haute 'importance' supprimes ")
print(StatsStrategieImportance5[1])
print("# Variation de degre moyen :" + str((Stats[WorstIndex].MeanDegree - StatsStrategieImportance5[1].MeanDegree)))
print("# Variation de coefficient de clustering moyen :"+ str((Stats[WorstIndex].MeanClusterCoef - StatsStrategieImportance5[1].MeanClusterCoef)))
print("# Variation d'efficacite :" + str((Stats[WorstIndex].Efficiency - StatsStrategieImportance5[1].Efficiency)))

print("\n## Statistiques du pire essaim une fois le noeud de plus haute centralite supprime ")
print(StatsStrategieCentralite1[1])
print("# Variation de degre moyen :" + str((Stats[WorstIndex].MeanDegree - StatsStrategieCentralite1[1].MeanDegree)))
print("# Variation de coefficient de clustering moyen :"+ str((Stats[WorstIndex].MeanClusterCoef - StatsStrategieCentralite1[1].MeanClusterCoef)))
print("# Variation d'efficacite :" + str((Stats[WorstIndex].Efficiency - StatsStrategieCentralite1[1].Efficiency)))

print("\n## Statistiques du pire essaim une fois les 5 noeud de plus haute centralite supprimes ")
print(StatsStrategieCentralite5[1])
print("# Variation de degre moyen :" + str((Stats[WorstIndex].MeanDegree - StatsStrategieCentralite5[1].MeanDegree)))
print("# Variation de coefficient de clustering moyen :"+ str((Stats[WorstIndex].MeanClusterCoef - StatsStrategieCentralite5[1].MeanClusterCoef)))
print("# Variation d'efficacite :" + str((Stats[WorstIndex].Efficiency - StatsStrategieCentralite5[1].Efficiency)))

print("\n## Statistiques du pire essaim une fois un noeud aleatoire supprime")
print(StatsStrategieAleatoire1[1])
print("# Variation de degre moyen :" + str((Stats[WorstIndex].MeanDegree - StatsStrategieAleatoire1[1].MeanDegree)))
print("# Variation de coefficient de clustering moyen :"+ str((Stats[WorstIndex].MeanClusterCoef - StatsStrategieAleatoire1[1].MeanClusterCoef)))
print("# Variation d'efficacite :" + str((Stats[WorstIndex].Efficiency - StatsStrategieAleatoire1[1].Efficiency)))

print("\n## Statistiques du pire essaim une fois 5 noeuds aleatoires supprimes ")
print(StatsStrategieAleatoire5[1])
print("# Variation de degre moyen :" + str((Stats[WorstIndex].MeanDegree - StatsStrategieAleatoire5[1].MeanDegree)))
print("# Variation de coefficient de clustering moyen :"+ str((Stats[WorstIndex].MeanClusterCoef - StatsStrategieAleatoire5[1].MeanClusterCoef)))
print("# Variation d'efficacite :" + str((Stats[WorstIndex].Efficiency - StatsStrategieAleatoire5[1].Efficiency)))

BestIndex = GetBestCase(Stats)
print("\n### Statistiques initiales du meilleur essaim connexe, l'essaim : " + str(BestIndex))
print(Stats[BestIndex])
print("\n## Statistiques du meilleur essaim une fois le noeud de plus haute 'importance' supprime ")
print(StatsStrategieImportance1[0])
print("# Variation de degre moyen :" + str((Stats[BestIndex].MeanDegree - StatsStrategieImportance1[0].MeanDegree)))
print("# Variation de coefficient de clustering moyen :"+ str((Stats[BestIndex].MeanClusterCoef - StatsStrategieImportance1[0].MeanClusterCoef)))
print("# Variation d'efficacite :" + str((Stats[BestIndex].Efficiency - StatsStrategieImportance1[0].Efficiency)))

print("\n## Statistiques du meilleur essaim une fois les 5 noeud de plus haute 'importance' supprime ")
print(StatsStrategieImportance5[0])
print("# Variation de degre moyen :" + str((Stats[BestIndex].MeanDegree - StatsStrategieImportance5[0].MeanDegree)))
print("# Variation de coefficient de clustering moyen :"+ str((Stats[BestIndex].MeanClusterCoef - StatsStrategieImportance5[0].MeanClusterCoef)))
print("# Variation d'efficacite :" + str((Stats[BestIndex].Efficiency - StatsStrategieImportance5[0].Efficiency)))

print("\n## Statistiques du meilleur essaim une fois le noeud de plus haute centralite supprime ")
print(StatsStrategieCentralite1[0])
print("# Variation de degre moyen :" + str((Stats[BestIndex].MeanDegree - StatsStrategieCentralite1[0].MeanDegree)))
print("# Variation de coefficient de clustering moyen :"+ str((Stats[BestIndex].MeanClusterCoef - StatsStrategieCentralite1[0].MeanClusterCoef)))
print("# Variation d'efficacite :" + str((Stats[BestIndex].Efficiency - StatsStrategieCentralite1[0].Efficiency)))

print("\n## Statistiques du meilleur essaim une fois les 5 noeud de plus haute centralite supprime ")
print(StatsStrategieCentralite5[0])
print("# Variation de degre moyen :" + str((Stats[BestIndex].MeanDegree - StatsStrategieCentralite5[0].MeanDegree)))
print("# Variation de coefficient de clustering moyen :"+ str((Stats[BestIndex].MeanClusterCoef - StatsStrategieCentralite5[0].MeanClusterCoef)))
print("# Variation d'efficacite :" + str((Stats[BestIndex].Efficiency - StatsStrategieCentralite5[0].Efficiency)))

print("\n## Statistiques du meilleur essaim une fois un noeud aleatoire supprime")
print(StatsStrategieAleatoire1[0])
print("# Variation de degre moyen :" + str((Stats[BestIndex].MeanDegree - StatsStrategieAleatoire1[0].MeanDegree)))
print("# Variation de coefficient de clustering moyen :"+ str((Stats[BestIndex].MeanClusterCoef - StatsStrategieAleatoire1[0].MeanClusterCoef)))
print("# Variation d'efficacite :" + str((Stats[BestIndex].Efficiency - StatsStrategieAleatoire1[0].Efficiency)))

print("\n## Statistiques du meilleur essaim une fois 5 noeuds aleatoires supprimes ")
print(StatsStrategieAleatoire5[0])
print("# Variation de degre moyen :" + str((Stats[BestIndex].MeanDegree - StatsStrategieAleatoire5[0].MeanDegree)))
print("# Variation de coefficient de clustering moyen :"+ str((Stats[BestIndex].MeanClusterCoef - StatsStrategieAleatoire5[0].MeanClusterCoef)))
print("# Variation d'efficacite :" + str((Stats[BestIndex].Efficiency - StatsStrategieAleatoire5[0].Efficiency)))

print("\n\n### LANCEMENT DE LA SIMULATION PROPHET+ ###")
# L'essaim contient 100 noeuds (id de 0 à 99)
num_nodes = 100
simulator = ProphetSimulator(num_nodes=num_nodes, max_temps=MAXTEMPS, matrixes=Matrixes)
simulator.run()