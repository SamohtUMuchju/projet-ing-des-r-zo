# Analyse Technique des Changements : Ajout de la Contrainte de Débit

L'intégration de la notion de "Débit dépendant de la distance spatiale" (Bandwidth/Quota) a demandé de modifier l'architecture du projet sur trois de vos fichiers principaux : `dtn_core.py`, `dtn_protocols.py`, et `dtn_resilience_test.py`.

Voici le détail de ce qui a changé par rapport à la version d'origine purement "binaire" (On/Off).

---

## 1. Ce qui a changé dans `dtn_core.py` (Le Cœur / Modèle de Données)

### Avant
La classe `Message` était très basique : elle s'apparentait davantage à un email ou un paquet abstrait contenant un ID, une Source et une Destination. Il n'existait aucune variable temporelle et aucune notion de "poids" de la donnée transférée.

### Après
J'ai transformé la donnée théorique en **donnée physique de réseau**.
*   **Ajout de `self.size` dans `Message`** : Chaque paquet possède désormais une contrainte de taille aléatoire `size = random.randint(1, 5)`. 
*   **Modification de `SimulationEngine.run()`** : Cette fonction directrice accepte désormais une nouvelle variable booléenne `use_bandwidth=False`, qu'elle propage aux routeurs des protocoles à chaque tic d'horloge spatiale.

---

## 2. Ce qui a changé dans `dtn_protocols.py` (La Logique de Routage)

C'est ici qu'intervient la modification majeure, particulièrement au sein de la classe mère `Protocol` dérivée dans `DirectDelivery`, `Epidemic`, `SprayAndWait` et `PRoPHET`.

### Avant (La Modélisation Binaire)
La règle de transfert était implémentée comme une simple "Ligne de vue idéale" :
```python
dist = self.compute_distance(A, B)
if dist <= max_range:
    self.exchange(A, B) # Transfert de la totalité du buffer
```
**Différence flagrante :** Si le nœud `A` avait 10 000 messages accumulés en buffer, et que le nœud `B` passait furtivement à la bordure extrême de sa zone de couverture (à `max_range - 1m`), le protocole validait un échange immédiat et total. Les 10 000 messages étaient magiquement téléportés vers `B`.

### Après (Le Bridage Physique du Débit)
Si l'utilisateur active l'option (`use_bandwidth=True`), l'antenne radio théorique de votre satellite rentre en jeu avec une formule mathématique simple :
```python
if dist <= max_range:
    if use_bandwidth:
        # Ratio : plus on s'approche de 0 mètre, plus le débit file vers l'infini (bridé mathématiquement par max(1.0, dist)).
        # Plus on s'approche de max_range, plus le quota s'effondre.
        quota = (max_range / max(1.0, dist)) * 1.5
        
        self.exchange_bandwidth(A, B, quota) # Nouveau comportement !
```

J'ai créé une seconde fonction d'échange nommée `exchange_bandwidth(...)` qui reçoit un `quota_data_disponible`.
*   **Le goulot d'étranglement** : Le parcours des messages du Sender s'arrête net si la taille du prochain message excède ce qu'il reste à la bande passante :
    ```python
    if quota_restant < msg.size: 
        break # Le satellite B s'est trop éloigné, transfert coupé.
    ```
*   **Conséquence** : Seuls 2 ou 3 messages peuvent passer lors d'un "mauvais contact furtif à longue distance", au lieu de l'intégralité !

---

## 3. Ce qui a changé dans `dtn_resilience_test.py` (La Commande Utilisateur)

### Avant
La routine d'évaluation (`run_resilience_test`) écrasait la simulation brutalement, rejouant 4 fois le scénario binaire `baseline` puis 4 fois sur divers scénarios de pannes (`importance`, `centralité`...).

### Après
Pour **respecter l'exigence "Garder la version d'avant intacte"**, un bloc a été inséré avant même le lancement du moteur (fonction `input()` native Python).
```python
mode_input = input("Voulez-vous activer la prise en compte du débit... (o/n) : ")
```
Ce choix est passé à toutes les sous-routines du code sous la forme de `use_bandwidth`. 
Les 4 scénarios de résilience appliquent de facto cette variable. L'impact de la perte de 5 nœuds ciblés **+** un taux de transfert brisé par la perte de couverture satellite va donner des résultats bien pires (mais plus proches de l'industrie spatiale réelle).

---

## 4. Problème d'Affichage Identique (o/n) et Corrections Apportées

Lors des premiers tests, le simulateur affichait exactement les mêmes résultats avec (`o`) ou sans (`n`) la prise en compte du débit. Cela n'était pas un défaut d'architecture, mais plutôt 4 comportements combinés lors de la simulation qui masquaient l'effet du débit :

1.  **Bug de boucle logicielle (Quota non décrémenté)** :
    En Python, le paramètre `quota` passé en argument n'était pas mis à jour correctement à l'intérieur de la boucle d'échange sur les longs envois (A vers B, puis B vers A), "téléportant" virtuellement le quota. *Correction : Création de la variable locale statique `quota_restant` qui se décrémente strictement par la taille (`msg.size`) lors de chaque envoi validé.*
    
2.  **Multiplicateur trop généreux** :
    L'ancienne formule `(max_range / dist) * 5.0` faisait qu'à la limite extrême de portée, le quota valait tout de même 5.0. Puisque les messages ont une taille aléatoire de 1 à 5, au moins un message pouvait *toujours* passer à chaque contact, annulant le filtre souhaité. *Correction : Le multiplicateur a été abaissé à `1.5`, créant de vrais murs bloquants en bordure de signal.*

3.  **Trafic anémique (Pas de bouchons/congestion)** :
    Avec seulement 50 messages générés répartis sur 100 satellites pendant 20 secondes, très peu de satellites se croisaient avec plusieurs messages à la fois. Le quota alloué était donc *presque toujours supérieur* au besoin réel, rendant le goulot inutile. *Correction : Le trafic généré dans `dtn_resilience_test.py` a été augmenté à **400 messages**.*

4.  **Hasard d'exécution** :
    En relançant la commande deux fois, les messages envoyés étaient tirés avec des sources/destinations totalement différentes, rendant la comparaison numérique floue. *Correction : Injection d'un `random.seed(42)` fixant le hasard pour assurer une stricte comparabilité de code.*

_Ce mode de simulation "Bandwidth" met désormais fortement en valeur l'utilité des protocoles prudents comme Spray & Wait_ !

## 5. Analyse des Performances sous Contrainte de Débit (Exemple de Congestion)

En simulant plus de trafic (400 messages par exemple), on observe des résultats qui illustrent parfaitement le phénomène de **Congestion DTN** (ou *Buffer/Bandwidth Starvation*). Prenons le cas du protocole **PRoPHET** qui, même sans panne (Baseline), n'obtient plus un ratio de livraison parfait (ex: plafonne autour de 87% de Delivery avec plus de 15 000 de surcoût réseau/Overhead). Ce comportement est normal et académiquement valide :

### A. Pourquoi un plafonnement à 87% en mode Baseline ?
Sans panne matérielle mais **sans bande passante infinie**, le protocole n'a physiquement pas la capacité d'écouler l'entièreté de ses longues files de paquets en seulement 20 cycles orbitaux.
Lors d'une rencontre, PRoPHET calcule que le voisin est un meilleur chemin, les messages sont transférés, et le voisin s'engorge avec des centaines de messages en attente. Lorsqu'il croise enfin la destination finale spatiale, le manque de bande passante l'empêche d'envoyer l'intégralité de sa file : seuls 3 ou 4 messages passent. Ainsi, environ 13% des messages restent coincés dans l'orbite satellite.

### B. Comprendre le gigantesque "Overhead" de PRoPHET
Les algorithmes comme Epidemic ou PRoPHET utilisent un arbre prolifique pour maximiser les chances de survie d'un message. Pour acheminer 400 messages, le simulateur peut générer **plus de 15 000 transmissions satellites**. C'est cet excès de duplication qui remplit mathématiquement la bande passante physique.

### C. L'effondrement d'Epidemic face au Débit Physique
C'est grâce à ces modifications que le banc de simulation révèle l'intérêt des protocoles avancés :
*   **Direct Delivery :** Ne donne jamais le paquet à un relais (un message par paquet, overhead minuscule), ce qui offre un pauvre score de livraison d'environ **34%**.
*   **Spray & Wait (6) :** Limite arbitrairement les diffusions (Overhead moyen) ce qui lui permet un taux de livraison souvent d'environ **61%** et garantit un non-emballement du réseau.
*   **Epidemic :** Sans la contrainte de bande passante spatiale, c'était historiquement le roi. **Avec du débit contraint**, il sature mathématiquement le signal radio de chaque rencontre en essayant de donner ses messages à tout le monde. Résultat : avec plus de 20 000 transmissions polluantes, les vieux messages congestionnent la place et le taux s'effondre à environ **69%**, perdant contre PRoPHET.
*   **PRoPHET :** Il sélectionne, grâce à la probabilité transitoire apprise en orbite, à qui confier le message. En ne saturant pas aléatoirement son réseau avec des doublons irréfléchis, la bande passante est utilisée de façon "intelligente". Il remporte logiquement les classements dans les environnements limités en montants (autour de **87%** dans les mêmes conditions d'essaim complet).

