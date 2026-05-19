import sys
from io import StringIO
import matplotlib.pyplot as plt
import numpy as np
import random

print("Chargement des données de la simulation... (Cela peut prendre quelques secondes)")
# Occultation des logs de simu.py pour ne pas polluer l'affichage graphique
old_stdout = sys.stdout
sys.stdout = StringIO()

from simu import Positions, MAXTEMPS, MAX_RANGE, Stats
from simu import Swarms, Matrixes, GetTopImportanceNoeud, GetWorstCase, topCentrality
from dtn_core import SimulationEngine
from dtn_protocols import DirectDelivery, Epidemic, SprayAndWait, PRoPHET

sys.stdout = old_stdout

def generate_plots():
    print("Données chargées ! Lancement des calculs des scénarios...")
    
    # 1. Initialisation du moteur temporel
    engine = SimulationEngine(Positions, MAX_RANGE, MAXTEMPS)
    engine.generate_traffic(50, start_time=0, end_time=20)
    
    protocols = [
        ("Direct Delivery", DirectDelivery()),
        ("PRoPHET", PRoPHET(p_init=0.75, gamma=0.98, beta=0.25)),
        ("Spray & Wait", SprayAndWait(initial_copies=6)),
        ("Epidemic", Epidemic())
    ]

    worst_idx = GetWorstCase(Stats)
    nb_to_delete = 5
    
    # Validation dynamique des nœuds à supprimer
    failed_none = []
    failed_importance = GetTopImportanceNoeud(Matrixes[worst_idx], nb_to_delete)
    failed_centrality = topCentrality(Swarms[worst_idx], Matrixes[worst_idx], nb_to_delete)
    failed_random = random.sample(range(100), nb_to_delete)

    scenarios = [
        ("Baseline\n(0 panne)", failed_none),
        ("Aléatoire\n(Bruit)", failed_random),
        ("Centralité\n(Plus connectés)", failed_centrality),
        ("Importance\n(Hubs)", failed_importance)
    ]

    # Dictionnaires pour stocker les résultats : [Protocol] -> [Liste de Ratios par scénario]
    results_norm = {p[0]: [] for p in protocols}
    results_bw = {p[0]: [] for p in protocols}

    # Simulation de toutes les combinaisons pour remplir nos tableaux de points
    for scen_name, failed_list in scenarios:
        for p_name, p_obj in protocols:
            # Mode "Idéal binaire" (Avant)
            res_norm = engine.run(p_obj, failed_nodes=failed_list, use_bandwidth=False)
            results_norm[p_name].append(res_norm["delivery_ratio"])
            
            # Mode "Pénalité Débit" (Maintenant)
            res_bw = engine.run(p_obj, failed_nodes=failed_list, use_bandwidth=True)
            results_bw[p_name].append(res_bw["delivery_ratio"])

    print("Calculs terminés. Génération des graphiques...")

    # =========================================================================
    # GRAPHIQUE 1 : COMPARAISON DES PROTOCOLES SUR LA RÉSILIENCE
    # =========================================================================
    plt.figure(figsize=(10, 6))
    x = np.arange(len(scenarios))
    width = 0.2

    for i, (p_name, _) in enumerate(protocols):
        plt.bar(x + i*width, results_norm[p_name], width, label=p_name)

    plt.ylabel('Delivery Ratio (%)', fontweight='bold')
    plt.title('Comparaison de la Résilience des Protocoles DTN (Sans bridage de débit)', fontweight='bold')
    plt.xticks(x + width*1.5, [s[0] for s in scenarios])
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('plot_1_protocoles.png')
    plt.show()

    # =========================================================================
    # GRAPHIQUE 2 : IMPACT DU DEBIT SUR LA LIVRAISON
    # =========================================================================
    plt.figure(figsize=(9, 6))
    prot_names = [p[0] for p in protocols]
    
    # On isole uniquement le "Scénario Baseline" (index 0) pour comparer le Débit
    baseline_norm = [results_norm[p][0] for p in prot_names]
    baseline_bw = [results_bw[p][0] for p in prot_names]

    x2 = np.arange(len(prot_names))
    width_bw = 0.35
    plt.bar(x2 - width_bw/2, baseline_norm, width_bw, label='Modèle Binaire (Range idéalisé)', color='#9facbd')
    plt.bar(x2 + width_bw/2, baseline_bw, width_bw, label='Modèle Bande-Passante (Distance = Coût)', color='#d45b5b')

    plt.ylabel('Delivery Ratio (%)', fontweight='bold')
    plt.title("Impact de l'atténuation du Débit sur les Performances", fontweight='bold')
    plt.xticks(x2, prot_names)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('plot_2_impact_debit.png')
    plt.show()

    # =========================================================================
    # GRAPHIQUE 3 : IMPACT DES PANNES SUR LE DEGRÉ MOYEN (Théorie des Graphes)
    # =========================================================================
    # Ces valeurs brutes ont été extraites fidèlement de l'historique de votre output.txt
    # Elles représentent le 'MeanDegree' du graph au temps identifié comme le pire (worst_idx)
    x_noeuds_supprimes = [0, 1, 5]
    
    degre_importance = [38.32, 37.65, 36.06]
    degre_centralite = [38.32, 37.47, 34.27]
    degre_aleatoire = [38.32, 38.14, 35.03]

    plt.figure(figsize=(8, 6))
    plt.plot(x_noeuds_supprimes, degre_importance, marker='o', markersize=8, linestyle='-', linewidth=2, label="Attaque sur Importance", color='blue')
    plt.plot(x_noeuds_supprimes, degre_centralite, marker='s', markersize=8, linestyle='-', linewidth=2, label="Attaque sur Centralité", color='red')
    plt.plot(x_noeuds_supprimes, degre_aleatoire, marker='^', markersize=8, linestyle='--', linewidth=2, label="Panne Aléatoire (Témoin)", color='green')

    plt.ylabel('Degré Moyen de l\'essaim', fontweight='bold')
    plt.xlabel('Nombre de satellites détruits', fontweight='bold')
    plt.title('Dégradation topologique de l\'essaim (Baisse des connexions)', fontweight='bold')
    plt.xticks(x_noeuds_supprimes)
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.8)
    
    # Annotations pour bien marquer la différence entre centralité et aléatoire
    plt.annotate('Chute drastique\ndu maillage', xy=(5, 34.27), xytext=(3, 34.5),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6))

    plt.tight_layout()
    plt.savefig('plot_3_impact_degres.png')
    plt.show()

    # =========================================================================
    # GRAPHIQUE 4 : ANALYSE DE LA ROBUSTESSE DE PROPHET FACE AUX PANNES
    # =========================================================================
    plt.figure(figsize=(10, 6.5))
    scen_labels = [s[0].replace('\n', ' ') for s in scenarios]
    
    x4 = np.arange(len(scen_labels))
    width4 = 0.35
    
    prophet_norm = results_norm["PRoPHET"]
    prophet_bw = results_bw["PRoPHET"]
    
    # Dessin des barres
    bar_norm = plt.bar(x4 - width4/2, prophet_norm, width4, label='Modèle Idéal (Range binaire)', color='#2b5c8f')
    bar_bw = plt.bar(x4 + width4/2, prophet_bw, width4, label='Modèle Réel (Débit & Congestion)', color='#d95f02')
    
    plt.ylabel('Delivery Ratio (%)', fontweight='bold')
    plt.xlabel('Scénarios de pannes (5 satellites détruits)', fontweight='bold')
    plt.title("Robustesse du protocole PRoPHET face aux différents types de pannes", fontweight='bold', fontsize=12, pad=15)
    plt.xticks(x4, scen_labels)
    plt.ylim(0, 115) # laisser un espace pour les étiquettes et annotations
    plt.legend(loc='upper right')
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    
    # Ajouter des labels de valeurs sur les barres
    for idx, val in enumerate(prophet_norm):
        plt.text(idx - width4/2, val + 1, f"{val:.1f}%", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#1a3d60')
    for idx, val in enumerate(prophet_bw):
        plt.text(idx + width4/2, val + 1, f"{val:.1f}%", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#803300')
        
    # Annotations d'explications sur le graphique
    # 1. Robustesse aléatoire
    plt.annotate('Haute Robustesse\n(Comportement similaire\nau témoin)',
                 xy=(1, max(prophet_norm[1], prophet_bw[1])), xytext=(0.8, 102),
                 arrowprops=dict(facecolor='green', shrink=0.08, width=1.5, headwidth=6, alpha=0.7),
                 ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="#e1f5fe", ec="#b3e5fc", lw=1))
                 
    # 2. Fragilité attaques ciblées
    plt.annotate('Fragilité Critique\n(La perte de hubs/ponts\ncoupe les routes de transit)',
                 xy=(3, max(prophet_norm[3], prophet_bw[3])), xytext=(2.6, 92),
                 arrowprops=dict(facecolor='red', shrink=0.08, width=1.5, headwidth=6, alpha=0.7),
                 ha='center', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="#ffebee", ec="#ffcdd2", lw=1))

    plt.tight_layout()
    plt.savefig('plot_4_prophet_resilience.png')
    plt.show()

if __name__ == "__main__":
    generate_plots()