# Analyse du Respect de la Règle de Broadcast et Plan d'Implémentation du Débit

## 1. Respect de la consigne "Toute donnée envoyée devra être reçue par tout le reste du réseau"

Cette contrainte correspond très exactement à la définition de l'**Inondation (Flooding)** dans les réseaux DTN. Voici comment se positionnent les 4 protocoles que vous avez implémentés :

### Protocoles qui RESPECTENT cette consigne ✅
*   **Epidemic Routing** : C'est le seul protocole qui répond *stricto sensu* à cette définition. Son comportement natif est de dupliquer chaque message vers **absolument tous** les nœuds rencontrés qui ne l'ont pas encore. Si le réseau n'est pas définitivement partitionné, une donnée émise finira indéniablement par être stockée par 100% des satellites de l'essaim.

### Protocoles qui NE RESPECTENT PAS cette consigne ❌
*   **Direct Delivery** : À l'opposé total de la consigne. La donnée envoyée n'est reçue **que** par la destination finale. Aucun autre satellite du réseau n'en verra la couleur.
*   **Spray and Wait** : Ne respecte pas la consigne car il contraint mathématiquement la diffusion. Si `initial_copies = 6`, alors au maximum absolu, seulement 6 satellites du réseau (sur les 100 de l'essaim) recevront la donnée envoyée.
*   **PRoPHET** : Ce protocole est "sélectif" de manière probabiliste. Il ne transfère la donnée qu'aux satellites ayant un bon score fonctionnel. De nombreux nœuds "périphériques" ou à l'opposé de la destination ne recevront jamais la donnée.

---

## 2. Plan d'Implémentation : Ajout de la Contrainte de Débit vs Distance

Actuellement, dans `dtn_protocols.py`, vous faites le test binaire suivant :
```python
if compute_distance(A, B) <= max_range:
    # On échange TOUS les messages du buffer instantanément (fwds += 1)
```
Pour rendre cela réaliste et répondre à l'hypothèse de changement de coût, l'échange des paquets ne doit plus être "gratuit" temporellement. Un canal lointain aura un faible débit, limitant le nombre de messages transférables pendant le court contact.

### 2.1 Concept Mathématique à choisir pour le débit
Généralement, en environnement spatial libre (Free Space Path Loss), la puissance du signal (et donc le rapport Signal/Bruit et le Débit théorique du canal) décroit avec le **carré de la distance**.
On peut modéliser le Débit $D$ (en Mbits/s ou en nombre d'unités de messages par tic logique) par une fonction inverse :
> $Debit_{theorique} = \frac{K}{distance^2}$
*(où K est une constante d'étalonnage pour le simulateur).*

### 2.2 Étapes des modifications à apporter au Projet

#### Étape 1 : Mettre à jour la définition d'un Message (`dtn_core.py`)
Vos messages n'ont actuellement pas de "poids".
*   Dans `Message.__init__`, ajoutez un attribut `self.size` (ex: taille aléatoire entre 1 et 10 Mo).

#### Étape 2 : Calcul du taux de transfert dynamique (`dtn_protocols.py`)
Dans les fonctions de type `route(...)` de **chaque protocole** :
*   Remplacez la vérification binaire `if distance <= max_range:` par le vrai calcul d'une variable de "Bande Passante Disponible" (ou d'un "Quota de données").
*   Exemple de refactoring algorithmique :
    ```python
    dist = self.compute_distance(n1, n2)
    if dist <= max_range:
        # Calcul du débit en fonction de la distance "changement du cout"
        debit_mbps = CONSTANTE_PUISSANCE / (dist ** 2) 
        
        # Notre "fenêtre de temps" est de 1 tick (ex: 1 minute dans simu.py)
        quota_data_disponible = debit_mbps * DUREE_DU_TICK 
        
        # On passe ce quota à la fonction d'échange !
        forwards += self.exchange(n1, n2, quota_data_disponible)
    ```

#### Étape 3 : Restriction de la boucle d'envoi (`dtn_protocols.py`)
La fonction `exchange()` de la classe de base ne doit plus simplement vider le buffer.
*   Passez en paramètre la `bande_passante_restante` calculée dynamiquement ci-dessus.
*   Ajoutez une condition dans la boucle :
    ```python
    def exchange(self, sender, receiver, quota_data_disponible):
        for msg in list(sender.buffer):
            # Si le cout de transfert dépasse le débit qu'il nous reste, on stoppe les envois !
            if quota_data_disponible < msg.size:
                break # Fin des transferts pour ce tick spatial
                
            if msg.dst == receiver.id:
                if receiver.receive(msg):
                    quota_data_disponible -= msg.size # On paye le coût
                    sender.buffer.remove(msg)
    ```

### Résultat du Plan
Grâce à ce plan, si un satellite est à 500 km d'un autre (proche de la limite physique), le débit frôlera zéro et le système ne transfèrera qu'un seul petit message avant d'être à court de quota. À l'inverse, si deux satellites sont à 10 km (passage très rapproché), la variable de `quota` allouée sera gigantesque et ils pourront transférer l'intégralité du buffer.
Vous aurez ainsi répondu avec élégance à l'hypothèse de changement de coût de communication !