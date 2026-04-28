import math
import random
from typing import List, Dict, Set

class Message:
    """
    Représente un message (ou paquet de données) dans le réseau DTN.
    """
    def __init__(self, id: str, src: int, dst: int, created_at: int, copies: int = 1, size: int = 1):
        self.id = id                # Identifiant unique du message
        self.src = src              # Nœud source (ID)
        self.dst = dst              # Nœud destination (ID)
        self.created_at = created_at # Temps de création (timestamp)
        self.copies = copies        # Nombre de copies autorisées (utilisé spécifiquement par Spray & Wait)
        self.size = size            # Taille du message (utilisé pour simuler le débit/bande passante)

class DTNNode:
    """
    Représente un nœud du réseau (ex: un satellite) capable de stocker et transférer des messages (Store-Carry-and-Forward).
    """
    def __init__(self, id: int, capacity: int = 200):
        self.id = id
        self.capacity = capacity    # Capacité maximale du buffer de messages (en nombre de messages)
        self.buffer: List[Message] = [] # Mémoire de stockage local des messages en transit
        self.delivered_msgs: Set[str] = set() # Historique des messages ayant atteint CE nœud comme destination finale
        self.seen_msgs: Set[str] = set()      # Historique des messages vus afin d'éviter les boucles de routage
        
        # État spécifique pour le protocole de routage probabiliste PRoPHET
        self.prophet_P: Dict[int, float] = {}   # Dictionnaire de prédictibilité de livraison P(a, b)
        self.last_age_update: int = 0           # Dernier instant de mise à jour due au vieillissement

    def receive(self, message: Message) -> bool:
        """
        Gère la réception d'un message par le nœud.
        Retourne True si le message a été accepté, False sinon (déjà vu ou buffer plein).
        """
        # Si le message a déjà été livré ou vu, on le rejette
        if message.id in self.delivered_msgs or message.id in self.seen_msgs:
            return False
            
        # Si ce nœud est la destination finale du message, on l'accepte
        if message.dst == self.id:
            self.delivered_msgs.add(message.id)
            self.seen_msgs.add(message.id)
            return True # Succès de la livraison
            
        # Sinon, le nœud agit comme relais, on vérifie s'il y a de la place
        if len(self.buffer) < self.capacity:
            self.buffer.append(message)
            self.seen_msgs.add(message.id)
            return True
        return False

class SimulationEngine:
    """
    Moteur de simulation principal pour tester les réseaux de tolérance aux délais (DTN)
    appliqué aux topologies dynamiques générées par simu.py.
    """
    def __init__(self, positions_dict: dict, max_range: float, max_temps: int):
        self.positions = positions_dict # Position des nœuds par intervalle de temps, importé de simu.py
        self.max_range = max_range      # Portée de communication maximale inter-satellites
        self.max_temps = max_temps      # Durée totale de la simulation
        self.num_nodes = len(positions_dict[0]) # Nombre total de nœuds
        self.messages: List[Message] = []
        
    def generate_traffic(self, num_messages: int, start_time: int, end_time: int):
        """
        Génère un trafic aléatoire uniforme de messages entre les nœuds.
        """
        random.seed(42) # Seed fixe pour garantir la reproductibilité des scénarios entre protocoles
        self.messages = []
        for i in range(num_messages):
            src = random.randint(0, self.num_nodes - 1)
            dst = random.randint(0, self.num_nodes - 1)
            while dst == src: # Éviter que source = destination
                dst = random.randint(0, self.num_nodes - 1)
            t = random.randint(start_time, end_time)
            size = random.randint(1, 5) # Taille aléatoire de 1 à 5 "unités"
            self.messages.append(Message(id=f"M{i}", src=src, dst=dst, created_at=t, copies=1, size=size))
            
    def run(self, protocol, failed_nodes: List[int] = [], use_bandwidth: bool = False) -> dict:
        """
        Exécute la simulation réseau au travers du temps avec le protocole spécifié.
        Intègre une couche de résilience permettant d'exclure (simuler la panne de) des nœuds.
        """
        # Initialisation des nœuds DTN
        nodes = {i: DTNNode(id=i) for i in range(self.num_nodes)}
        
        # Tri des messages par date de création
        pending_msgs = sorted(self.messages, key=lambda x: x.created_at)
        msg_idx = 0
        total_forwards = 0 # Mesure de surcharge et de coût bando-passante (overhead)
        
        # Mémorise le temps de livraison pour chaque message [msg_id -> temps]
        delivery_times: Dict[str, int] = {} 
        
        # Boucle principale de temps discrétisé
        for time in range(self.max_temps):
            # Noeuds restants et valides (mécanisme de panne)
            active_nodes = [i for i in range(self.num_nodes) if i not in failed_nodes]
            
            # Injection des messages générés par la charge de trafic configurée
            while msg_idx < len(pending_msgs) and pending_msgs[msg_idx].created_at == time:
                msg = pending_msgs[msg_idx]
                if msg.src in active_nodes:
                    # Injection du paramètre 'copies' si nécessaire (utile pour Spray and Wait)
                    msg.copies = getattr(protocol, 'initial_copies', 1) 
                    nodes[msg.src].buffer.append(msg)
                    nodes[msg.src].seen_msgs.add(msg.id)
                msg_idx += 1
                
            pos_t = self.positions[time] # Topologie spatiale courante issue de la trace
            
            # Application de la logique de routage du protocole
            forwards = protocol.route(active_nodes, pos_t, self.max_range, nodes, time, use_bandwidth)
            total_forwards += forwards
            
            # Suivi des messages livrés pour calculer la latence temporelle
            for node_id in active_nodes:
                for msg_id in nodes[node_id].delivered_msgs:
                    if msg_id not in delivery_times:
                        delivery_times[msg_id] = time
        
        # Calcul des métriques globales de performance de fin de course
        delivered_count = len(delivery_times)
        # On ne calcule le pourcentage de livraison que sur les messages générés par les nœuds en état de marche
        total_created = len([m for m in self.messages if m.src not in failed_nodes])
        
        latencies = []
        for msg in self.messages:
            if msg.id in delivery_times:
                latencies.append(delivery_times[msg.id] - msg.created_at)
                
        avg_latency = (sum(latencies) / len(latencies)) if latencies else 0
        delivery_ratio = (delivered_count / total_created * 100) if total_created > 0 else 0
        
        return {
            "delivered": delivered_count,
            "created": total_created,
            "delivery_ratio": delivery_ratio,
            "avg_latency": avg_latency,
            "overhead": total_forwards
        }
