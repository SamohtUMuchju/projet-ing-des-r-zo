import random

class Message:
    """
    Représente un message (ou paquet de données) dans le réseau DTN.
    """
    def __init__(self, msg_id, source, destination, creation_time, ttl=30):
        self.msg_id = msg_id
        self.source = source
        self.destination = destination
        self.creation_time = creation_time
        self.ttl = ttl                  # Time To Live : Durée de vie du message
        self.delivered = False          # Indique si le message a été livré à sa destination finale
        self.delivery_time = -1         # Temps auquel le message a été livré

class ProphetNode:
    """
    Représente un nœud du réseau avec la logique métier du protocole de routage PRoPHET+.
    PRoPHET+ ajoute des considérations de ressources réelles : la batterie et la disponibilité du buffer.
    """
    def __init__(self, node_id, max_buffer=50, max_battery=100.0):
        self.id = node_id
        self.predictability = {}        # Dictionnaire: {dst_id -> probabilité de rencontre}
        self.buffer = {}                # file d'attente locale: {msg_id -> Message}
        self.max_buffer = max_buffer    # Capacité maximale de stockage (en nombre de messages)
        self.battery = max_battery      # Niveau actuel d'énergie
        self.max_battery = max_battery  # Capacité maximale de la batterie

        # Constantes fondamentales du protocole PRoPHET original
        self.P_init = 0.75  # Probabilité octroyée lors d'un nouveau contact ponctuel
        self.gamma = 0.98   # Facteur de vieillissement (Aging) pour réduire la confiance avec le temps
        self.beta = 0.25    # Poids de la transitivité (A rencontre B, B rencontre C => A induit C)

        # PRoPHET+ Weights (Pondérations)
        # Ratio appliqué pour évaluer la qualité réelle du relai:
        # 50% basé sur la Prédictabilité, 25% l'Espace Libre, 25% la Batterie restante
        self.W_p = 0.5
        self.W_b = 0.25
        self.W_e = 0.25

    def get_predictability(self, dest_id):
        """Récupère la probabilité mémorisée de rencontrer dest_id."""
        return self.predictability.get(dest_id, 0.0)

    def update_encounter(self, other_id):
        """Met à jour la "predictability" suite à une rencontre directe."""
        old_pred = self.get_predictability(other_id)
        # Formule PRoPHET: P(a,b) = P(a,b)_old + (1 - P(a,b)_old) * P_init
        self.predictability[other_id] = old_pred + (1.0 - old_pred) * self.P_init

    def update_aging(self):
        """Applique l'usure du temps (Aging) sur les prédictabilités connues."""
        for dst in self.predictability:
            self.predictability[dst] *= self.gamma

    def update_transitivity(self, other_id, other_table):
        """
        Met à jour la matrice de décision selon le principe de transitivité (Les amis de mes amis...).
        """
        p_ab = self.get_predictability(other_id)
        # Pour tout nœud tiers que "other" connaît
        for dest_id, p_bc in other_table.items():
            if dest_id != self.id:
                old_pac = self.get_predictability(dest_id)
                # Formule PRoPHET de transitivité: P(a,c) = P(a,c)_old + (1 - P(a,c)_old) * P(a,b) * P(b,c) * beta
                new_pac = old_pac + (1.0 - old_pac) * p_ab * p_bc * self.beta
                self.predictability[dest_id] = max(old_pac, new_pac)

    def get_deliverability(self, dest_id):
        """
        Calcule le score global heuristique (Deliverability) PRoPHET+.
        Le score prend en compte le réseau mais aussi la survie et l'encombrement du relai.
        """
        P = self.get_predictability(dest_id)
        # Ratio du buffer disponible : plus il est vide, mieux c'est
        buf_ratio = (self.max_buffer - len(self.buffer)) / max(1, self.max_buffer)
        # Ratio de batterie disponible
        bty_ratio = self.battery / self.max_battery
        
        # Le score de Deliverability composite
        return self.W_p * P + self.W_b * buf_ratio + self.W_e * bty_ratio
    
    def can_receive(self):
        """Vérifie si le nœud possède les ressources pour recevoir un nouveau message (buffer non plein et en vie)."""
        return len(self.buffer) < self.max_buffer and self.battery > 0

    def receive_message(self, msg):
        """Traite la réception d'un message avec la décroissance d'énergie associée."""
        self.buffer[msg.msg_id] = msg
        self.battery = max(0.0, self.battery - 0.1) # Coût simulé d'une réception (Tx/Rx hardware loss)

    def send_message(self):
        """Traite l'envoi matériel d'un message avec la décroissance d'énergie associée (L'envoi est plus coûteux)."""
        self.battery = max(0.0, self.battery - 0.2) # Coût simulé d'un envoi

    def age_messages(self, current_time):
        """Purge le buffer des messages non délivrés dont le TTL est dépassé (poubelle mémoire)."""
        expired = []
        for msg_id, msg in self.buffer.items():
            # Si le message n'est pas finalisé et que sa date d'expiration est atteinte
            if current_time - msg.creation_time >= msg.ttl and not msg.delivered:
                expired.append(msg_id)
        # Suppression effective
        for msg_id in expired:
            del self.buffer[msg_id]


class ProphetSimulator:
    """
    Simulateur de réseau DTN ciblé sur le protocole PRoPHET+.
    Il s'appuie sur une série temporelle de matrices d'adjacence pour modéliser les rencontres.
    """
    def __init__(self, num_nodes, max_temps, matrixes):
        self.num_nodes = num_nodes
        self.max_temps = max_temps
        self.matrixes = matrixes # Map[time -> List[List[Int]]] issue du traitement temporel de simu.py
        self.nodes = {i: ProphetNode(i) for i in range(num_nodes)}
        self.all_messages = []
        self.msg_counter = 0

    def generate_traffic(self, current_time, msgs_per_tick=5):
        """Génère du nouveau trafic de façon continue à chaque tic de simulation."""
        for _ in range(msgs_per_tick):
            src = random.randint(0, self.num_nodes - 1)
            dst = random.randint(0, self.num_nodes - 1)
            while dst == src:
                dst = random.randint(0, self.num_nodes - 1)
            
            # Paramétrage d'un TTL pour contrecarrer l'encombrement réseau "mort"
            msg = Message(self.msg_counter, src, dst, current_time, ttl=40)
            self.msg_counter += 1
            if self.nodes[src].can_receive():
                self.nodes[src].receive_message(msg)
                self.all_messages.append(msg)

    def run(self):
        """
        Orchestrateur asynchrone itératif du framework PRoPHET+.
        Execute pas-à-pas les changements environnementaux, les calculs de topologie transitive
        et le routage multicritère des messages en attente.
        """
        print("\n\n=== Démarrage de la simulation PROPHET+ ===")
        # Seed fixe pour rejouer de façon déterministe le même scénario (facilite la validation)
        random.seed(42)  

        for t in range(self.max_temps):
            self.generate_traffic(t, msgs_per_tick=3) # Injection continue dans le tissu local de 3 msgs
            
            # 1. Phase Temporelle : Mise à jour du temps (aging) des probabilités et nettoyage des buffers (TTL)
            for node in self.nodes.values():
                node.update_aging()
                node.age_messages(t)
            
            if t not in self.matrixes:
                continue
            
            matrix = self.matrixes[t] # Observation du ciel spatial à l'instant T
            
            # Reconstruction des rencontres effectives depuis la matrice d'adjacence symétrique
            encounters = []
            for x in range(len(matrix)):
                for y in range(x+1, len(matrix)):
                    if matrix[x][y] != 0: # La portée (Range) est assurée
                        encounters.append((x, y))

            # 2. Phase Topologique : Mise à jour des nœuds en contact direct
            for a_id, b_id in encounters:
                a = self.nodes[a_id]
                b = self.nodes[b_id]
                a.update_encounter(b_id)
                b.update_encounter(a_id)
                
                # Mise en mémoire des tables avant mutation transitive (Isolation)
                table_a = a.predictability.copy()
                table_b = b.predictability.copy()
                
                a.update_transitivity(b_id, table_b)
                b.update_transitivity(a_id, table_a)

            # 3. Phase Opérationnelle : Transfert de données opportuniste bi-directionnel
            random.shuffle(encounters)
            transfers_this_tick = 0
            for a_id, b_id in encounters:
                a = self.nodes[a_id]
                b = self.nodes[b_id]
                
                # Identification des paquets éligibles de A vers B
                msgs_a_to_b = []
                for msg in a.buffer.values():
                    if msg.delivered: continue # Ignorer les paquets dont la mission est finie
                    # Condition 1: Livraison finale
                    if msg.destination == b_id:
                        msgs_a_to_b.append(msg)
                    # Condition 2: Routage PRoPHET+ (B est-il un garant de succès globalement "mieux" que A ?)
                    elif b.get_deliverability(msg.destination) > a.get_deliverability(msg.destination):
                        if msg.msg_id not in b.buffer: # Empêcher le ping-pong en duplex
                            msgs_a_to_b.append(msg)
                
                # Identification des paquets éligibles de B vers A
                msgs_b_to_a = []
                for msg in b.buffer.values():
                    if msg.delivered: continue
                    if msg.destination == a_id:
                        msgs_b_to_a.append(msg)
                    elif a.get_deliverability(msg.destination) > b.get_deliverability(msg.destination):
                        if msg.msg_id not in a.buffer:
                            msgs_b_to_a.append(msg)

                # Opération des transferts A -> B
                for msg in msgs_a_to_b:
                    if not b.can_receive() or a.battery <= 0: break # Epuisement des ressources
                    b.receive_message(msg)
                    a.send_message()
                    transfers_this_tick += 1
                    
                    if msg.destination == b_id:
                        msg.delivered = True
                        msg.delivery_time = t
                
                # Opération des transferts B -> A
                for msg in msgs_b_to_a:
                    if not a.can_receive() or b.battery <= 0: break # Epuisement des ressources
                    a.receive_message(msg)
                    b.send_message()
                    transfers_this_tick += 1
                    
                    if msg.destination == a_id:
                        msg.delivered = True
                        msg.delivery_time = t

        # ==============================================================================
        # METRIQUES & REPORTING
        # ==============================================================================
        total_msgs = len(self.all_messages)
        delivered_msgs = [m for m in self.all_messages if m.delivered]
        total_delivered = len(delivered_msgs)
        delivery_ratio = total_delivered / total_msgs if total_msgs > 0 else 0
        avg_delay = sum(m.delivery_time - m.creation_time for m in delivered_msgs) / total_delivered if total_delivered > 0 else 0
        
        avg_energy_left = sum(n.battery for n in self.nodes.values()) / self.num_nodes
        
        print(f"Simulation terminée (Messages générés : {total_msgs})")
        print(f" => Total Livrés : {total_delivered}")
        print(f" => Taux de Livraison (Delivery Ratio) : {delivery_ratio*100:.2f}%")
        print(f" => Latence Moyenne : {avg_delay:.2f} itérations")
        print(f" => Batterie Moyenne Restante : {avg_energy_left:.2f}%\n")

# NOTE D'INTEGRATION POUR LE DEVELOPPEUR:
# Pour lier ce framework 'prophet_sim.py' contenant PRoPHET+ avec les matrices extraites
# depuis 'simu.py' (comme pour 'dtn_resilience_test.py'), vous pouvez importer 
# 'Matrixes' et 'MAXTEMPS' de 'simu.py', puis exécuter:
# 
# from simu import Matrixes, MAXTEMPS
# simulator = ProphetSimulator(100, MAXTEMPS, Matrixes) 
# simulator.run()
