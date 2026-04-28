import sys
import codecs
from io import StringIO
import random

# ==============================================================================
# LIAISON AVEC L'ARCHITECTURE CENTRALE (simu.py & swarm_sim.py)
# ==============================================================================
print("Initialisation des données de Traces.csv (via simu.py)...")

# Capture du stdout/affichage console de routine pour ne pas inonder le terminal avec 
# l'intégralité des logs générés nativement par la boucle d'analyse métier de simu.py
old_stdout = sys.stdout
sys.stdout = StringIO()
from simu import Positions, MAXTEMPS, MAX_RANGE, Stats
from simu import Swarms, Matrixes, GetTopImportanceNoeud, GetWorstCase, topCentrality
sys.stdout = old_stdout

# ==============================================================================
# INJECTION DES AGENTS ET MODULES DTN (Delay Tolerant Network)
# ==============================================================================
from dtn_core import SimulationEngine
from dtn_protocols import DirectDelivery, Epidemic, SprayAndWait, PRoPHET


def display_metrics(name, res):
    """
    Formateur de logs métier, extrait un compte rendu rapide de la performance du routing testé.
    """
    print(f"[{name.ljust(15)}] Delivery: {res['delivery_ratio']:>6.2f}% ({res['delivered']}/{res['created']}) | Latency: {res['avg_latency']:>5.1f} pas | Overhead: {res['overhead']:>6} trans.")


def run_resilience_test():
    """
    Fonction pilote intégratrice (Orchestrateur Supérieur).
    Ici on relie la cinématique satellitaire brute de Traces.csv aux méthodes réseau DTN.
    L'objectif est d'étudier la dégradation des ratios de livraisons (tolérance de panne)
    au travers de la destruction théorique des nœuds critiques préalablement calculés par 
    les propriétés de théorie des graphes de l'agent `simu.py`.
    """
    
    # Demande de l'utilisateur pour le mode de simulation
    mode_input = input("Voulez-vous activer la prise en compte du débit en fonction de la distance ? (o/n) : ").strip().lower()
    use_bandwidth = mode_input == 'o'
    
    # Fixer la graine aléatoire pour que les exécutions (o/n) soient strictement comparables
    random.seed(42)
    
    # 1. Montage du moteur sur base du dictionnaire dynamique temporel
    engine = SimulationEngine(Positions, MAX_RANGE, MAXTEMPS)
    
    # Afin de ressentir la limite de bande passante, 50 messages étaient insuffisants.
    # On génère un fort trafic (400 messages) pour forcer les buffers à saturer !
    engine.generate_traffic(400, start_time=0, end_time=20)
    
    # Enregistrement des configurations des 4 algorithmes concurrents évalués
    protocols = [
        ("DirectDelivery", DirectDelivery()),
        ("PRoPHET", PRoPHET(p_init=0.75, gamma=0.98, beta=0.25)),
        ("SprayAndWait(6)", SprayAndWait(initial_copies=6)),
        ("Epidemic", Epidemic())
    ]
    
    print("\n" + "="*80)
    print("SCENARIO 1 : BASELINE (Aucune Panne - Résilience Initiale)".center(80))
    print("="*80)
    baseline_stats = {}
    for name, p in protocols:
        res = engine.run(p, failed_nodes=[], use_bandwidth=use_bandwidth)
        baseline_stats[name] = res
        display_metrics(name, res)
        
    worst_idx = GetWorstCase(Stats) # Récupération de l'instant identifié comme "le pire" temporellement pour le test
    nb_to_delete = 5
    
    print("\n" + "="*80)
    print(f"SCENARIO 2 : ATTAQUE / PANNE SUR IMPORTANCE ({nb_to_delete} NOEUDS)".center(80))
    print("="*80)
    # Lier l'analyse originelle (Nombre de Shortest Path élevés ou nœud charnière) à la panne logicielle
    failed_importance = GetTopImportanceNoeud(Matrixes[worst_idx], nb_to_delete)
    print(f"--> Nœuds HS identifiés dynamiquement par simu.py : {failed_importance}")
    for name, p in protocols:
        res = engine.run(p, failed_nodes=failed_importance, use_bandwidth=use_bandwidth)
        display_metrics(name, res)
        
    print("\n" + "="*80)
    print(f"SCENARIO 3 : ATTAQUE / PANNE SUR CENTRALITE ({nb_to_delete} NOEUDS)".center(80))
    print("="*80)
    # Lier l'analyse centralisée de simu.py (Forte Centralité = Potentiels hub orbitaux)
    failed_centrality = topCentrality(Swarms[worst_idx], Matrixes[worst_idx], nb_to_delete)
    print(f"--> Nœuds HS identifiés dynamiquement par simu.py : {failed_centrality}")
    for name, p in protocols:
        res = engine.run(p, failed_nodes=failed_centrality, use_bandwidth=use_bandwidth)
        display_metrics(name, res)
        
    print("\n" + "="*80)
    print(f"SCENARIO 4 : PANNE ALEATOIRE ({nb_to_delete} NOEUDS)".center(80))
    print("="*80)
    # Simulation d'une défaillance environnementale aléatoire non ciblée.
    failed_random = random.sample(range(100), nb_to_delete)
    print(f"--> Nœuds HS aléatoirement définis en témoin biais : {failed_random}")
    for name, p in protocols:
        res = engine.run(p, failed_nodes=failed_random, use_bandwidth=use_bandwidth)
        display_metrics(name, res)
        
if __name__ == "__main__":
    run_resilience_test()
