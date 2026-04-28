# Protocoles de Routage DTN et Test de Résilience Satellitaire

Ce document détaille les concepts fondamentaux, le vocabulaire et les stratégies de routage utilisés dans l'évaluation de notre réseau de Delay-Tolerant Network (DTN). Il présente également les conclusions tirées des simulations de résilience face aux pannes.

---

## 0. Contexte, Hypothèses et Objectifs

Avant d'analyser les protocoles réseaux et leur comportement, il est nécessaire de poser le cadre d'étude de cette simulation sur la résilience d'un essaim satellitaire.

### Hypothèses de Modélisation du Moteur
*   **Satellites non géostationnaires** : La topologie visée est dynamique ; les coordonnées (x,y,z) des nœuds évoluent continuellement de façon déterministe dans le temps.
*   **Modulation du Débit vs Distance** : Le "coût" intrinsèque spatial (distance) change entre chaque nœud. Dans les couches de calculs, un relais trop éloigné aura un coût prohibitif ou sortira de la portée d'antenne (portée maximale).
*   **Broadcast et Diffusion Massive** : Une hypothèse centrale du transfert DTN testé postule que dans des solutions comme **Epidemic**, toute donnée envoyée par un satellite inondera l'intégralité du reste du réseau (en saturant parfois artificiellement les capacités de l'essaim).

### C. Objectif et Plan de Travail
L'objectif du modèle est d'**étudier l'impact d'une panne ciblée (ou aléatoire) sur les caractéristiques brutes de l'essaim** (comme le Degré Moyen ou les Plus Courts Chemins) et la façon dont **ces pannes affectent concrètement la latence et les taux de livraison de la donnée finale**.

Le plan se décompose en 5 phases :
1. Prise en main des ressources (Traces spatiales, code noyau de simulation).
2. Extraction des Graphes : conversion physique $\rightarrow$ nœuds virtuels.
3. Calcul des métriques de base et de robustesse (Connexité, Efficacité, Clustering).
4. Définition des stratégies de suppression (qui cibler et comment ?).
5. Étude comparative des impacts réseau réels.

---

## 1. Vocabulaire et Concepts Fondamentaux

*   **DTN (Delay-Tolerant Network)** : Réseau tolérant aux délais conçu pour faire face à une connectivité intermittente, aux fortes latences et à l'absence de chemin continu de bout en bout (ligne de vue rompue entre satellites).
*   **Store-Carry-and-Forward (SCF)** : Modèle de transfert asynchrone fondamental du DTN. Un nœud (satellite) **stocke** (*store*) le message dans sa mémoire, le **transporte** (*carry*) au gré de sa trajectoire orbitale, et le **retransmet** (*forward*) lorsqu'il rencontre une opportunité de connexion (un autre nœud).
*   **Buffer** : File d'attente locale embarquée limitant le nombre de messages qu'un nœud peut transporter.
*   **Delivery Predictability P(a,b)** : Entité cognitive (probabiliste) qu'un nœud maintient pour estimer ses chances futures de rencontrer le destinataire final.
*   **Overhead (Surcharge réseau)** : Nombre total de retransmissions (copies ou transferts). Un *overhead* trop grand encombre la bande-passante et épuise l'énergie.
*   **Rapport de livraison (Delivery Ratio)** : Pourcentage de messages correctement acheminés de la source jusqu’à leur destination finale.
*   **Latence (Latency)** : Temps total écoulé entre la création du paquet et sa livraison finale.

---

## 2. Définition des Stratégies de Routage Évaluées

### Protocole 1 : Direct Delivery (La ligne de base)
C'est la stratégie la plus économe mais la plus asociale. La source ne transfère **jamais** son paquet à un nœud intermédiaire. Le message s'accumule dans son "bundle" (buffer) jusqu'à ce qu'elle rencontre **directement** la destination.
*   **Avantages** : Aucune surcharge réseau (*0 overhead*), ne consomme que très peu d'énergie et d'espace tampon local.
*   **Inconvénients** : Taux de livraison statistiquement catastrophique et latence extrême dans un essaim satellitaire complexe.

### Protocole 2 : Epidemic (L'inondation de force brute)
Modèle à diffusion totale. Lors de chaque contact bilatéral (rencontre entre deux nœuds), l'agent copie l'intégralité des messages qu'il possède et que l'autre n'a pas. 
*   **Avantages** : Garantie d'obtenir le meilleur délai de livraison possible (optimal routing bounds) car il explore nativement **tous** les chemins spatio-temporels. Taux de livraison maximal.
*   **Inconvénients** : L'*overhead* est astronomique. Provoque la saturation rapide des buffers, rendant cette stratégie irréaliste pour des nano-satellites sous forte contrainte énergétique.

### Protocole 3 : Spray and Wait (Heuristique contrôlée)
Conçu pour pallier l'inflation d'Epidemic. On alloue un quota prédéfini de copies (Ex : 6 copies, `initial_copies`).
*   **Phase "Spray"** : À chaque rencontre, le nœud transfère la moitié de ses "droits de copie" à son pair (diffusion binaire en arbre).
*   **Phase "Wait"** : Lorsqu'il ne lui reste plus qu'un seul crédit, il bascule sur une stratégie de *Direct Delivery* et ne cède le message qu'au destinataire réel.
*   **Avantages** : Compromis robuste et configurable. Borne la surcharge tout en garantissant un bon taux de livraison.

### Protocole 4 : PRoPHET (Routage Probabiliste Cognitif)
Stratégie sophistiquée (Heuristique probabiliste). Ce protocole profile les comportements du graphe. Un relais ne reçoit le paquet **que si** sa popularité (sa probabilité mathématique de croiser le destinataire prochainement) est supérieure au porteur actuel.
Il s'appuie sur le calcul d'Historique de Rencontres, le renforcement du lien (si A voit B souvent), l'inférence transitive (A connaît B qui connaît C) et le vieillissement (la probabilité décroit avec l'absence de visibilité).
*   **Avantages** : Très intelligent face à des graphes intermittents persistants. Overhead limité avec des performances approchant Epidemic. 

---

## 3. Méthodologie des tests de Résilience

La résilience est évaluée en soumettant le réseau spatial (l'essaim) à l'éviction de nœuds critiques identifiés par deux métriques issues de la Théorie des Graphes :

*   **Pannes Ciblées par l'Importance** : Les nœuds situés sur le plus grand nombre de "plus courts chemins" (Hubs de transit).
*   **Pannes Ciblées par la Centralité** : Les nœuds possédant le plus de voisins persistants.
*   **Panne Aléatoire** : Retrait sans stratégie heuristique (témoin "bruit de fond").

---

## 4. Conclusions et Résultats des Simulations

*L'analyse comparée des logs orbitaux révèle les dynamiques suivantes propres aux essaims non-connectés de type DTN :*

1.  **L'Effondrement de Direct Delivery face aux hubs** : 
    Direct Delivery n'offre qu'un *Delivery Ratio* médiocre lors du Baseline (absence de panne), car l'espace et les fenêtres de contacts étroits interdisent statistiquement la rencontre directe de tous les pairs. Si l'on ajoute des pannes, le protocole pénalise encore davantage le réseau.
    
2.  **Epidemic : La limite des Buffers** : 
    Bien qu'Epidemic conserve d'excellentes métriques de *Delivery Ratio* post-destruction grâce au fait de couvrir instantanément les "routes de contournement" du réseau qui reste actif, l'indicateur d'*Overhead* (sur les retransmissions) tend de facto vers l'infini, prouvant qu'en termes physiques cette solution n'est pas "scalable" pour un essaim de nano-satellites.
    
3.  **La Solidité Adaptative de PRoPHET et Spray & Wait** : 
    Face à l'élimination des hubs par la "Centralité" (les points d'agglutinations de connexions les plus prisés), *PRoPHET* amortit drastiquement la perte grâce à l'apprentissage transitif. Les agents non-détruits redirigent habilement de nouvelles routes au fur et à mesure que PRoPHET recalcule les probabilités.
    
4.  **Influence du Type d'Attaque (Théorie des Graphes)** : 
    Les résultats (`output.txt` et statistiques orbitaux) valident que retirer un nœud identifié par sa haute **Centralité** / **Importance** dégrade la connexité et l'efficacité globale du réseau de manière significativement plus importante (`Variation d'efficacité élevée`) que la perte aléatoire de 5 nœuds banals. C'est dans ces "Worst Case Scenarios" que *Spray & Wait* (bornant l'énergie) et *PRoPHET* (routant par anticipation) prouvent la pertinence des algorithmes DTN.

**Conclusion Globale** : Un réseau DTN par satellite est hautement vulnérable à la perte ciblée de quelques de ses "ponts". Ainsi, pour garantir la survie d'un trafic pertinent sans puiser fatalement sur les batteries, **PRoPHET** et **Spray and Wait** s'attestent être les protocoles combinant la meilleure résilience à l'isolation sans payer la lourde facture énergétique et de saturation de buffer imposée par **Epidemic**.

---

## 5. Mise en relation du Plan de Travail avec l'Implémentation Python

Voici comment les 5 étapes du plan de travail se traduisent techniquement dans les scripts du projet :

### Étape 1 : Prise en main des ressources (Traces des positions)
*   **Localisation** : Principalement au début de `simu.py`. 
*   **Implémentation** : Le script utilise la librairie `pandas` (`pd.read_csv('Traces.csv')`) pour parser les coordonnées spatiales de 100 satellites. Il nettoie ces données et construit un grand dictionnaire mémoire `Positions[temps] = {id: (x,y,z)}` représentant l'espace physique à chaque instant discret.

### Étape 2 : Extraction des graphes
*   **Localisation** : Dans `simu.py` (construction de la variable `Matrixes` et `Swarms`).
*   **Implémentation** : Pour chaque intervalle de temps, le code calcule la distance euclidienne entre chaque paire de satellites. Si cette distance est inférieure ou égale à la limite `MAX_RANGE` (portée d'antenne), une arête (connexion) est créée dans la matrice d'adjacence. L'essaim spatial devient alors un graphe mathématique connexe (ou morcelé).

### Étape 3 : Calcul des métriques
*   **Localisation** : Dans `simu.py` avec enregistrement des logs dans `output.txt`.
*   **Implémentation** : Le logiciel instancie des objets de classe `Metric` comprenant :
    *   *Degré moyen (MeanDegree)* : le nombre moyen de relais à portée.
    *   *Connexité (Connexity)* : évalue si le réseau est d'un seul bloc ou s'il est partitionné en sous-réseaux isolés.
    *   *Coefficient de clustering et Efficacité (Efficiency)* : mesure de la compacité de l'essaim, qui va naturellement chuter lors d'une attaque.

### Étape 4 : Définition des algorithmes de suppression
*   **Localisation** : Dans `simu.py` (fonctions d'analyse) et `dtn_resilience_test.py` (pour l'attaque aléatoire).
*   **Implémentation** : Le code est capable de déterminer mathématiquement les maillons faibles du graphe :
    *   `GetTopImportanceNoeud()` : Supprime les "Hubs" en se basant sur le nombre de plus courts chemins traversant un nœud (*Betweenness Centrality*).
    *   `topCentrality()` : Cible et supprime les nœuds ayant le plus de voisins persistants.
    *   L'utilisation de `random.sample()` pour supprimer un échantillon aléatoire de nœuds afin de servir de point de comparaison.

### Étape 5 : Étude des impacts sur la transmission (Résilience)
*   **Localisation** : Dans `dtn_resilience_test.py` et le moteur `dtn_core.py`.
*   **Implémentation** : L'orchestrateur rejoue l'intégralité du routage des messages (trafic généré de 50 messages) en "désactivant" dynamiquement les nœuds identifiés lors de l'étape 4 (`failed_nodes=[...]`). L'impact réel est alors affiché dans la console à travers les métriques DTN de *Delivery Ratio*, *Latency*, et *Overhead* pour chacun des 4 protocoles simulés (Direct Delivery, Epidemic, Spray & Wait, PRoPHET).