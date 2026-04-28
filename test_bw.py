import random
import sys
from io import StringIO

sys.stdout = StringIO()
from simu import Positions, MAXTEMPS, MAX_RANGE
from dtn_core import SimulationEngine
from dtn_protocols import Epidemic
sys.stdout = sys.__stdout__

def run_test():
    seed = 42
    
    # Run WITHOUT bandwidth
    random.seed(seed)
    engine1 = SimulationEngine(Positions, MAX_RANGE, MAXTEMPS)
    engine1.generate_traffic(200, start_time=0, end_time=20)
    res_no_bw = engine1.run(Epidemic(), failed_nodes=[], use_bandwidth=False)
    
    # Run WITH bandwidth
    random.seed(seed)
    engine2 = SimulationEngine(Positions, MAX_RANGE, MAXTEMPS)
    engine2.generate_traffic(200, start_time=0, end_time=20)
    res_bw = engine2.run(Epidemic(), failed_nodes=[], use_bandwidth=True)
    
    print("=== RESULTATS ===")
    print(f"Sans Limite de Débit : {res_no_bw['delivery_ratio']:.2f}% (Latence moy: {res_no_bw['avg_latency']:.2f})")
    print(f"Avec Limite de Débit : {res_bw['delivery_ratio']:.2f}% (Latence moy: {res_bw['avg_latency']:.2f})")

if __name__ == '__main__':
    run_test()
