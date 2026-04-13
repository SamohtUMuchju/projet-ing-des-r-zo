import sys
from io import StringIO

def run_all_simulations():
    print("======================================================================")
    print("          LANCEMENT DU BANC DE SIMULATION SATELLITAIRE DTN          ")
    print("======================================================================")
    
    print("\n[ÉTAPE 1] Chargement des données spatiales (Traces.csv) et "
          "génération de la topologie locale...")
    
    # On occulte l'impression console lourde générée par l'initialisation de simu.py
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    from simu import Positions, MAXTEMPS, Matrixes
    sys.stdout = old_stdout
    
    print("--> [SUCCÈS] Topologies temporelles importées en mémoire !\n")
    
    # Lancement Partie 1 : Résilience Multi-protocoles
    print("----------------------------------------------------------------------")
    print("  SIMULATION 1 : TEST DE RÉSILIENCE MULTI-PROTOCOLES")
    print("----------------------------------------------------------------------")
    print(">> Objectif : Comparer la robustesse de 4 protocoles lors de la destruction")
    print("              de certains nœuds satellitaires identifiés par divers algorithmes.")
    print(">> Protocoles évalués : Direct Delivery, Spray & Wait, PRoPHET, Epidemic\n")
    
    # On importe et lance le module de résilience
    import dtn_resilience_test
    dtn_resilience_test.run_resilience_test()
    
    # Lancement Partie 2 : PRoPHET+ avec prise en compte des ressources
    print("\n----------------------------------------------------------------------")
    print("  SIMULATION 2 : ÉVALUATION AVANCÉE DU PROTOCOLE PRoPHET+ ")
    print("----------------------------------------------------------------------")
    print(">> Objectif : Introduire des contraintes réalistes sur les drones/satellites.")
    print(">> Paramètres ajoutés : Décroissance de Batterie & Occupation du Buffer\n")
    
    from prophet_sim import ProphetSimulator
    # Initialisation du framework PROPHET+ avec 100 satellites
    prophet_engine = ProphetSimulator(num_nodes=100, max_temps=MAXTEMPS, matrixes=Matrixes)
    prophet_engine.run()
    
    print("======================================================================")
    print("               FIN TOTALE DE LA CHAÎNE DE SIMULATION                  ")
    print("======================================================================")

if __name__ == "__main__":
    run_all_simulations()
