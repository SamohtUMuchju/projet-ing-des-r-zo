import math
import copy

class Protocol:
    """
    Classe de base (interface) pour définir les protocoles de routage DTN.
    """
    def compute_distance(self, n1, n2):
        """
        Calcule la distance euclidienne spatiale absolue entre 2 nœuds d'après le système de coordonnées de simu.py.
        """
        return math.sqrt((n2.x-n1.x)**2 + (n2.y-n1.y)**2 + (n2.z-n1.z)**2)

class DirectDelivery(Protocol):
    """
    Protocole Naïf (Direct Delivery): Aucun relais n'est utilisé. 
    Les messages restent dans la file de la source jusqu'à ce qu'elle croise directement la destination finale.
    C'est la base servant de borne inférieure en tolérance réseau (Latency extrême mais 0 overhead).
    """
    def route(self, active_nodes, pos_t, max_range, dtn_nodes, time, use_bandwidth=False):
        forwards = 0
        for i in range(len(active_nodes)):
            for j in range(i+1, len(active_nodes)):
                id1, id2 = active_nodes[i], active_nodes[j]
                dist = self.compute_distance(pos_t[id1], pos_t[id2])
                if dist <= max_range:
                    n1, n2 = dtn_nodes[id1], dtn_nodes[id2]
                    if use_bandwidth:
                        quota = (max_range / max(1.0, dist)) * 2.5
                        forwards += self.exchange_bandwidth(n1, n2, quota) + self.exchange_bandwidth(n2, n1, quota)
                    else:
                        forwards += self.exchange(n1, n2) + self.exchange(n2, n1)
        return forwards
        
    def exchange(self, sender, receiver):
        fwds = 0
        for msg in list(sender.buffer):
            if msg.dst == receiver.id:
                if receiver.receive(msg):
                    sender.buffer.remove(msg)
                    fwds += 1
        return fwds

    def exchange_bandwidth(self, sender, receiver, quota_data_disponible):
        fwds = 0
        quota_restant = quota_data_disponible
        for msg in list(sender.buffer):
            if quota_restant < msg.size:
                continue
            if msg.dst == receiver.id:
                if receiver.receive(msg):
                    quota_restant -= msg.size
                    sender.buffer.remove(msg)
                    fwds += 1
        return fwds

class Epidemic(Protocol):
    """
    Protocole Epidemic: Inonde le réseau. 
    Copie aveuglément le message sur chaque nœud rencontré afin d'explorer de force tous les chemins réseaux potentiels.
    Très haut taux de livraison mais engendre une surcharge colossale (overhead max).
    """
    def route(self, active_nodes, pos_t, max_range, dtn_nodes, time, use_bandwidth=False):
        forwards = 0
        for i in range(len(active_nodes)):
            for j in range(i+1, len(active_nodes)):
                id1, id2 = active_nodes[i], active_nodes[j]
                dist = self.compute_distance(pos_t[id1], pos_t[id2])
                if dist <= max_range:
                    n1, n2 = dtn_nodes[id1], dtn_nodes[id2]
                    if use_bandwidth:
                        quota = (max_range / max(1.0, dist)) * 2.5
                        forwards += self.exchange_bandwidth(n1, n2, quota) + self.exchange_bandwidth(n2, n1, quota)
                    else:
                        forwards += self.exchange(n1, n2) + self.exchange(n2, n1)
        return forwards
        
    def exchange(self, sender, receiver):
        fwds = 0
        for msg in list(sender.buffer):
             if msg.dst == receiver.id:
                 if receiver.receive(msg):
                     sender.buffer.remove(msg) 
                     fwds += 1
             elif msg.id not in receiver.seen_msgs: 
                 if receiver.receive(msg):
                     fwds += 1
        return fwds

    def exchange_bandwidth(self, sender, receiver, quota_data_disponible):
        fwds = 0
        quota_restant = quota_data_disponible
        for msg in list(sender.buffer):
             if quota_restant < msg.size:
                 continue
             if msg.dst == receiver.id:
                 if receiver.receive(msg):
                     quota_restant -= msg.size
                     sender.buffer.remove(msg) 
                     fwds += 1
             elif msg.id not in receiver.seen_msgs: 
                 if receiver.receive(msg):
                     quota_restant -= msg.size
                     fwds += 1
        return fwds

class SprayAndWait(Protocol):
    """
    Protocole Spray and Wait (Généralement en mode binaire): Compromis Epidemic/Direct.
    1. Phase Spray: Limite le nombre de copies distribuées globalement dans le réseau en divisant le "crédit" par deux à chaque contact.
    2. Phase Wait: Typée relai direct, une fois réduit à une seule copie, le porteur ne donne le message qu'au destinataire réel.
    """
    def __init__(self, initial_copies=6):
        self.initial_copies = initial_copies

    def route(self, active_nodes, pos_t, max_range, dtn_nodes, time, use_bandwidth=False):
        forwards = 0
        for i in range(len(active_nodes)):
            for j in range(i+1, len(active_nodes)):
                id1, id2 = active_nodes[i], active_nodes[j]
                dist = self.compute_distance(pos_t[id1], pos_t[id2])
                if dist <= max_range:
                    n1, n2 = dtn_nodes[id1], dtn_nodes[id2]
                    if use_bandwidth:
                        quota = (max_range / max(1.0, dist)) * 2.5
                        forwards += self.exchange_bandwidth(n1, n2, quota) + self.exchange_bandwidth(n2, n1, quota)
                    else:
                        forwards += self.exchange(n1, n2) + self.exchange(n2, n1)
        return forwards

    def exchange(self, sender, receiver):
        fwds = 0
        for msg in list(sender.buffer):
            if msg.dst == receiver.id:
                 if receiver.receive(msg):
                     sender.buffer.remove(msg)
                     fwds += 1
            elif msg.copies > 1 and msg.id not in receiver.seen_msgs:
                 give = msg.copies // 2
                 keep = msg.copies - give
                 msg.copies = keep
                 new_msg = copy.copy(msg)
                 new_msg.copies = give
                 if receiver.receive(new_msg):
                     fwds += 1
        return fwds

    def exchange_bandwidth(self, sender, receiver, quota_data_disponible):
        fwds = 0
        quota_restant = quota_data_disponible
        for msg in list(sender.buffer):
            if quota_restant < msg.size:
                continue
            if msg.dst == receiver.id:
                 if receiver.receive(msg):
                     quota_restant -= msg.size
                     sender.buffer.remove(msg)
                     fwds += 1
            elif msg.copies > 1 and msg.id not in receiver.seen_msgs:
                 give = msg.copies // 2
                 keep = msg.copies - give
                 msg.copies = keep
                 new_msg = copy.copy(msg)
                 new_msg.copies = give
                 if receiver.receive(new_msg):
                     quota_restant -= msg.size
                     fwds += 1
        return fwds

class PRoPHET(Protocol):
    """
    Protocole PRoPHET: Routage heuristique basé sur l'historique cognitif des rencontres passées.
    L'agent évalue la "Delivery Predictability", le message n'est répliqué que si le nœud interrogé a 
    une meilleure probabilité de rencontre ultérieure avec la destination.
    """
    def __init__(self, p_init=0.75, gamma=0.98, beta=0.25):
        self.p_init = p_init   # P_init: Probabilité initiale définie lors d'un nouveau contact ponctuel
        self.gamma = gamma     # Gamma: Facteur de détérioration temporelle de la confiance du contact (vieillissement)
        self.beta = beta       # Beta: Pondération inférentielle pour le calcul associatif transitif 

    def route(self, active_nodes, pos_t, max_range, dtn_nodes, time, use_bandwidth=False):
        forwards = 0
        # 1. Vieillissement : affaiblissement progressif des informations passées non ressourcées 
        for id in active_nodes:
            node = dtn_nodes[id]
            delta = time - node.last_age_update
            if delta > 0:
                for k in node.prophet_P:
                    node.prophet_P[k] = node.prophet_P[k] * (self.gamma ** delta)
                node.last_age_update = time

        # 2. Phase de renconre, calcul des réseaux transitifs
        for i in range(len(active_nodes)):
            for j in range(i+1, len(active_nodes)):
                id1, id2 = active_nodes[i], active_nodes[j]
                dist = self.compute_distance(pos_t[id1], pos_t[id2])
                if dist <= max_range:
                    n1, n2 = dtn_nodes[id1], dtn_nodes[id2]
                    
                    # 2.1 Renforcement positif réciproque par présence physique
                    p12 = n1.prophet_P.get(id2, 0.0)
                    n1.prophet_P[id2] = p12 + (1 - p12) * self.p_init
                    
                    p21 = n2.prophet_P.get(id1, 0.0)
                    n2.prophet_P[id1] = p21 + (1 - p21) * self.p_init
                    
                    # 2.2 Propriété transitive : A connaît B qui connaît C => A induit C via B.
                    for dest_k, p2k in n2.prophet_P.items():
                        if dest_k != id1:
                            p1k = n1.prophet_P.get(dest_k, 0.0)
                            n1.prophet_P[dest_k] = max(p1k, n1.prophet_P.get(id2,0) * p2k * self.beta)
                    
                    for dest_k, p1k in n1.prophet_P.items():
                        if dest_k != id2:
                            p2k = n2.prophet_P.get(dest_k, 0.0)
                            n2.prophet_P[dest_k] = max(p2k, n2.prophet_P.get(id1,0) * p1k * self.beta)

                    # Échange algorithmique des paquets validés par la base de connaissance Prophet
                    if use_bandwidth:
                        quota = (max_range / max(1.0, dist)) * 2.5
                        forwards += self.forward_prophet_bandwidth(n1, n2, quota)
                        forwards += self.forward_prophet_bandwidth(n2, n1, quota)
                    else:
                        forwards += self.forward_prophet(n1, n2)
                        forwards += self.forward_prophet(n2, n1)
        return forwards

    def forward_prophet(self, sender, receiver):
        fwds = 0
        for msg in list(sender.buffer):
            if msg.dst == receiver.id:
                 if receiver.receive(msg):
                     sender.buffer.remove(msg) # Livraison Finale
                     fwds += 1
            # Condition exclusive PRoPHET : Ne transmettre au relais que si son score cognitif de destination le bat
            elif sender.prophet_P.get(msg.dst, 0.0) < receiver.prophet_P.get(msg.dst, 0.0):
                if msg.id not in receiver.seen_msgs:
                    if receiver.receive(msg):
                        fwds += 1
        return fwds

    def forward_prophet_bandwidth(self, sender, receiver, quota_data_disponible):
        fwds = 0
        quota_restant = quota_data_disponible
        for msg in list(sender.buffer):
            if quota_restant < msg.size:
                continue
            if msg.dst == receiver.id:
                 if receiver.receive(msg):
                     quota_restant -= msg.size
                     sender.buffer.remove(msg) # Livraison Finale
                     fwds += 1
            elif sender.prophet_P.get(msg.dst, 0.0) < receiver.prophet_P.get(msg.dst, 0.0):
                if msg.id not in receiver.seen_msgs:
                    if receiver.receive(msg):
                        quota_restant -= msg.size
                        fwds += 1
        return fwds
