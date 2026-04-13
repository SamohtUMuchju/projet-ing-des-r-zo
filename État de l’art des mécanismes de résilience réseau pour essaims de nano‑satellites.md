# État de l’art des mécanismes de résilience réseau pour essaims de nano‑satellites

## Résumé exécutif

Les essaims de nano‑satellites (SANET/FANET spatiales) opèrent dans des environnements fortement dynamiques, sujets à des défaillances critiques de nœuds et à des partitionnements fréquents, ce qui rend insuffisants les mécanismes de robustesse classiques (sur‑provisionnement, simple redondance de liens). La littérature récente converge vers trois familles complémentaires de solutions de résilience : (i) des protocoles de routage adaptatifs limitant les tempêtes de mises à jour en environnement très dynamique, (ii) des mécanismes d’auto‑cicatrisation pour recomposer la topologie logique et réélire des leaders après la perte de nœuds à forte centralité, et (iii) l’adoption de l’architecture Delay/Disruption Tolerant Networking (DTN) et du Bundle Protocol pour survivre aux partitionnements prolongés via le paradigme store‑carry‑and‑forward.[^1][^2][^3]


## 1. Contexte : résilience, dégradation gracieuse et auto‑cicatrisation

La résilience d’un essaim de nano‑satellites se distingue de la simple robustesse par sa capacité à maintenir un niveau de service dégradé mais fonctionnel malgré la perte de nœuds centraux, les partitions et des délais de communication extrêmes. La théorie des graphes montre que les graphes sans échelle typiques des réseaux spatiaux sont vulnérables à la suppression ciblée de nœuds à forte centralité (hubs), ce qui motivera l’usage de topologies logiques multi‑chemins et de mécanismes de reconstruction locale auto‑organisés.[^4][^5]

Dans les SANETs, les contraintes spécifiques incluent la mobilité déterministe (orbites), la visibilité périodique, la capacité radio limitée et parfois l’absence durable de connectivité bout‑en‑bout, ce qui invalide les hypothèses des protocoles IP et MANET classiques. Les approches state‑of‑the‑art combinent alors des couches de routage packet‑switched (MANET géographique, clustering, SDN distribué) avec une surcouche DTN message‑oriented chargée d’assurer la livraison différée à travers les partitions.[^2][^3][^6]


## 2. Survivre à la fin du broadcast naïf : routage résilient sans tempêtes d’updates

### 2.1 Limites du flooding et des protocoles de type broadcast

Les protocoles de diffusion naïfs (flooding simple, broadcast périodique d’état de liens) provoquent rapidement des tempêtes de mises à jour (update storms) dans des topologies mobiles ou en cours de panne massive, saturant le canal radio et accélérant la chute du réseau. Dans les MANETs, cette problématique est bien documentée : les inondations de messages de contrôle ne passent pas à l’échelle en densité ni en fréquence de changement de topologie, et interagissent mal avec les collisions radio.[^7][^8][^9]

Plusieurs travaux proposent de limiter ces tempêtes via des optimisations de flooding dans les protocoles de type état de lien (OLSR), en réduisant drastiquement le nombre de relais nécessaires à la diffusion globale tout en maintenant la connectivité de la structure de routage. Les mécanismes de MultiPoint Relays (MPR) d’OLSR et de ses variantes en sont l’exemple le plus important.[^8][^10][^7]


### 2.2 Protocoles MANET optimisés : OLSR, MPR et variantes QoS/énergie

L’Optimized Link State Routing (OLSR) est l’un des protocoles de MANET proactifs les plus étudiés et sert de base à de nombreuses optimisations de flooding. Il sélectionne un sous‑ensemble de nœuds, appelés MPR, qui seuls retransmettent les messages de contrôle, réduisant fortement la redondance du broadcast tout en garantissant que tous les nœuds sont atteints.[^9][^8]

Des travaux ultérieurs étendent OLSR avec des critères de QoS et d’interférences radio afin d’optimiser simultanément la consommation de bande passante de contrôle et la qualité de service : la sélection des MPR est alors contrainte par la bande passante disponible et les interférences locales, ce qui améliore le taux de livraison tout en maintenant un flooding optimisé, même sous forte charge de signalisation.[^10][^7]

De nombreuses variantes prennent aussi en compte l’énergie résiduelle, la mobilité ou la stabilité des liens pour limiter la surcharge de mises à jour lors de topologies très dynamiques. Des approches récentes comme EASP‑AODV introduisent par exemple la notion de chemin stable et énergétiquement conscient afin de réduire les ruptures de liens et la fréquence de reconvergence, ce qui réduit indirectement les tempêtes de mises à jour.[^11]


### 2.3 Routage géographique et position‑based pour limiter l’état global

Le routage géographique, illustré par le protocole GPSR (Greedy Perimeter Stateless Routing), contourne le problème de la maintenance d’un état global de la topologie en prenant des décisions de forwarding basées uniquement sur la position du prochain saut et de la destination. Chaque nœud ne maintient que la liste de ses voisins, et applique un forwarding greedy puis un mode perimeter en cas de cul‑de‑sac topologique.[^12][^13][^14]

Cette approche réduit le volume de trafic de contrôle et la taille des tables de routage, ce qui la rend attractive pour les SANETs où l’état global devient rapidement obsolète. Des variantes comme MGPSR ou E‑GPSR introduisent des métriques d’énergie ou de délai pour équilibrer la charge de forwarding et améliorer la connectivité, tout en restreignant les messages de mise à jour à des informations de localisation périodiques plutôt qu’à des cartes complètes de topologie.[^15][^16]

Geographic routing est particulièrement adapté aux essaims de satellites où les positions relatives sont prévisibles grâce aux éphémérides : les plans d’orbite peuvent être exploités pour calculer des voisinages et des chemins de manière implicite, limitant les échanges de contrôle aux seules corrections ou anomalies, ce qui réduit la probabilité de tempêtes d’updates en situation de panne massive.[^3][^6]


### 2.4 Techniques d’atténuation des tempêtes d’updates

Outre les MPR et le routage géographique, plusieurs stratégies génériques permettent de contenir les tempêtes de mises à jour en MANET/SANET :

- Flooding probabiliste : chaque nœud retransmet un message de contrôle avec une probabilité P adaptée à la densité, ce qui économise des transmissions tout en conservant une forte probabilité de couverture.[^17]
- Flooding avec portée limitée (scoped flooding) : les mises à jour sont restreintes à un rayon de quelques sauts, souvent suffisant pour le recalcul de routes locales après panne d’un nœud, réduisant ainsi le coût global.[^9][^17]
- Différentiel et agrégation de mises à jour : plutôt que d’envoyer des cartes complètes, seuls les changements (delta) sont diffusés, et des agrégations sont réalisées en chemin pour limiter les doublons et la taille des messages.[^9]
- Contrôle adaptatif de fréquence : la période d’émission des messages HELLO/TC est ajustée en fonction de la stabilité topologique (par exemple, moins fréquente en orbite stationnaire, plus fréquente en manœuvre ou en phase de panne).[^7][^10]

Ces techniques sont utilisées pour garantir une dégradation gracieuse : même en cas de pertes massives de nœuds, le trafic de contrôle reste borné et ne sature pas le médium, ce qui laisse de la capacité pour les données applicatives critiques de l’essaim.


## 3. Auto‑cicatrisation après crash de leader ou de nœuds centraux

### 3.1 Auto‑réparation locale des chemins : SHORT, multipath et redondance topologique

Les algorithmes de routage auto‑cicatrisants cherchent à reconfigurer les routes de manière localisée après une panne, sans recomputation globale, en exploitant la redondance inhérente à l’essaim. Des travaux introduisent le cadre SHORT (Self‑Healing and Optimizing Routing Techniques) où les nœuds voisins surveillent les chemins actifs et, en cas de détérioration ou de rupture, substituent de manière opportuniste des sous‑chemins locaux plus courts ou plus fiables, tout en prenant en compte l’énergie et la charge pour éviter la surutilisation de certains nœuds.[^4]

D’autres approches s’appuient sur le multipath et les chemins de secours pré‑calculés, de sorte que la détection de la mort d’un nœud central déclenche simplement l’activation d’un chemin alternatif pré‑négocié, réduisant la fenêtre de discontinuité de service. Le principe général est de maintenir des structures logiques (arbres, chemins virtuels) « pardonnables » (forgiving trees/graphs) qui tolèrent un nombre borné de pannes tout en conservant des diamètres raisonnables grâce à des reconnections locales.[^18][^19]


### 3.2 Auto‑organisation en clusters et rotation de rôles

Une autre stratégie consiste à structurer l’essaim en clusters hiérarchiques, avec des nœuds « leaders » ou cluster‑heads responsables de la collecte, de l’agrégation et du routage inter‑cluster. Les algorithmes d’auto‑organisation SANET/FANET choisissent souvent des leaders en fonction de critères de position, d’énergie et de connectivité, puis organisent une rotation périodique des rôles pour prévenir la création de goulots d’étranglement permanents.[^5][^20]

En cas de crash d’un leader, les protocoles de clustering déclenchent une re‑élection locale au sein du cluster ou à partir d’un « house of elite nodes » pré‑sélectionné afin de réduire la latence de reconfiguration et le trafic de signalisation. Des travaux sur les MANETs mobiles proposent des algorithmes d’élection hiérarchiques à haute disponibilité qui maintiennent toujours un leader dans chaque composant connexe et bornent le nombre de messages d’élection, ce qui est directement applicable à des essaims satellitaires.[^21]


### 3.3 Élection de leader en réseaux dynamiques et partitionnés

La littérature sur l’élection de leader dans des réseaux dynamiques fournit des algorithmes capables de garantir qu’une fois les changements de topologie stabilisés, chaque composant connexe contient exactement un leader, même si des partitions et des fusions se produisent. Un exemple est l’algorithme d’élection pour réseaux dynamiques dérivé de TORA et d’algorithmes de type wave, qui tolère des changements asynchrones, des pannes de nœuds et ne suppose pas de configuration initiale spécifique.[^22]

D’autres travaux proposent des algorithmes d’élection spécifiquement optimisés pour les MANETs larges, qui minimisent la complexité en messages et le temps de convergence grâce à la sélection préalable d’un sous‑ensemble d’« élites » susceptibles de devenir leader. Ce type de mécanisme permet de contenir les tempêtes de messages d’élection lors de la mort d’un leader central, en focalisant le processus de reconfiguration sur un petit sous‑ensemble de nœuds.[^23][^21]


### 3.4 Vers des SANET auto‑cicatrisants : SDN distribué et contrôle basé sur politiques

Dans le contexte spatial, des approches plus récentes envisagent l’usage de Software‑Defined Networking (SDN) distribué ou hybride pour orchestrer la reconfiguration de l’essaim : des contrôleurs logiques embarqués (potentiellement redondants) calculent des politiques de routage et de placement de service, tandis que les satellites appliquent localement des règles simplifiées. La perte d’un contrôleur est compensée par la promotion d’un autre nœud selon une logique d’élection de leader tolérante aux partitions, combinée à un plan de repli DTN.[^24][^3]

Cette tendance s’appuie sur des mécanismes de monitoring distribués, de détection d’anomalies et d’auto‑configuration inspirés des réseaux terrestres auto‑organisés (SON), mais adaptés aux contraintes de latence et de prédictibilité orbitale des constellations.


## 4. Résilience au partitionnement via Delay‑/Disruption‑Tolerant Networking (DTN)

### 4.1 Architecture DTN et Bundle Protocol (RFC 4838, RFC 9171, CCSDS 734.2)

L’architecture DTN, formalisée dans l’RFC 4838, définit un overlay message‑oriented au‑dessus des couches de transport ou de liaison existantes, conçu pour des réseaux caractérisés par l’absence fréquente de chemin bout‑en‑bout, des délais longs et variables, et des taux d’erreur élevés. Le Bundle Protocol (BP) met en œuvre cette architecture en encapsulant les données applicatives dans des « bundles » routés en mode store‑carry‑and‑forward à travers des régions hétérogènes (IP, liaisons radio spécifiques, liaisons spatiales).[^1][^2]

La version expérimentale BPv6 a été spécifiée dans l’RFC 5050, puis une version normalisée plus robuste, BPv7, a été publiée dans l’RFC 9171, clarifiant le format des bundles, les mécanismes de sécurité et le modèle d’extension. Le CCSDS a adopté le Bundle Protocol pour les missions spatiales via la recommandation 734.2‑B‑1, et prépare une révision alignée sur BPv7, spécifiant le profil et les services de BP pour les environnements spatiaux (SIS‑DTN).[^25][^26][^1]


### 4.2 Paradigme store‑carry‑and‑forward et survie aux partitions

Le paradigme store‑carry‑and‑forward est central à la résilience DTN : chaque nœud DTN stocke les bundles de manière persistante, les transporte physiquement pendant les périodes de déconnexion, puis les retransmet lors de l’apparition d’opportunités de contact, qu’elles soient planifiées, prédictibles ou opportunistes. Cette persistance brise l’hypothèse IP d’un chemin bout‑en‑bout disponible au moment de l’émission, et permet de tolérer des partitions prolongées de l’essaim.[^27][^2]

Le Bundle Protocol s’appuie sur des convergence layers adaptés (TCPCL, LTP, UDP‑based CL) pour transporter les bundles sur différents médias, et propose des mécanismes de custody transfer où des nœuds intermédiaires acceptent la responsabilité de livraison, ce qui augmente la probabilité d’acheminement malgré les pannes de nœuds et les pertes de liens. La gestion des rapports de statut, des timers de durée de vie et des politiques de stockage permet de contrôler finement la rétention et la diffusion des bundles pendant et après une partition.[^26][^28][^1]


### 4.3 Routage DTN pour constellations et essaims : Contact Graph Routing et extensions

Dans les environnements spatiaux où la mobilité est largement déterministe (orbites), la technique de Contact Graph Routing (CGR) est devenue la solution de référence pour le routage DTN. CGR exploite un contact plan décrivant les fenêtres de visibilité et capacités de liens entre nœuds pour construire un graphe de contacts, sur lequel un plus court chemin temporel (earliest arrival path) est calculé pour chaque bundle.[^29][^6][^3]

CGR a été largement évalué pour des constellations distribuées, montrant qu’il permet des taux de livraison élevés et des temps de traversée maîtrisés, tout en restant robuste à certaines incertitudes sur les contacts. Des travaux récents proposent des améliorations de CGR prenant en compte explicitement les contraintes de capacité des liens et de buffers, via des opérations telles que le « contact splitting » et l’« edge pruning » pour s’assurer que les routes choisies respectent ces contraintes et évitent les congestions, ce qui renforce la résilience aux surcharges et aux pertes en cas de partition partielle.[^3][^24]


### 4.4 Routage opportuniste DTN : Epidemic, PRoPHET, Spray and Wait

Pour des essaims très dynamiques ou peu planifiables, la littérature DTN recourt à des protocoles opportunistes basés sur des modèles de mobilité probabilistes. L’epidemic routing de Vahdat et Becker réplique les messages vers tous les nœuds rencontrés, maximisant la probabilité de livraison au prix d’une consommation extrême de ressources (bande passante, énergie, mémoire).[^30][^27]

Le protocole PRoPHET, normalisé par le groupe de recherche DTN de l’IETF, améliore ce schéma en utilisant une métrique de « delivery predictability » basée sur l’historique des contacts et la transitivité pour décider vers quels voisins répliquer, réduisant fortement l’overhead tout en conservant de bonnes performances de livraison. Des extensions comme PRoPHET++ et des variantes à deux sauts affinent cette prédiction et adaptent la réplication aux contraintes d’énergie ou de charge.[^31][^32][^33][^34]

Le schéma Spray and Wait, proposé par Spyropoulos et al., contrôle explicitement le nombre de copies en « pulvérisant » un nombre L de copies limitées dans le réseau puis en attendant qu’une de ces copies rencontre la destination. Les analyses théoriques et simulations montrent qu’il atteint des délais proches de l’optimal tout en limitant drastiquement le nombre de transmissions, ce qui en fait une solution intéressante pour des essaims où l’énergie et la mémoire sont limitées mais où des partitions fréquentes doivent être tolérées.[^35][^36]


### 4.5 Comparaison des stratégies DTN pour la résilience d’un essaim

| Famille de protocole | Principe | Résilience au partitionnement | Coût en ressources |
|----------------------|----------|------------------------------|--------------------|
| Epidemic routing | Réplication vers tous les contacts | Très élevée (robuste aux partitions imprévues) | Très élevée (fort usage bande/stockage) |
| PRoPHET/PRoPHET++ | Réplication probabiliste basée sur historique | Élevée, dépend de la stabilité des patterns de mobilité | Modérée à élevée |
| Spray & Wait / DS&W | Nombre de copies borné, phase de spray puis attente | Élevée si L bien dimensionné | Contrôlée, scalable |
| CGR DTN spatial | Routage déterministe sur contact plan | Très élevée si le contact plan reste valable | Modéré, calcul plus complexe |

[^6][^37][^27][^31][^35][^3]

Pour un essaim de nano‑satellites, la combinaison d’un routage CGR pour les contacts prévisibles avec des mécanismes Spray‑and‑Wait ou PRoPHET‑like pour les contacts opportunistes offre un compromis robuste entre résilience à la partition et contrôle de l’overhead.


### 4.6 Déploiements et validations en environnement spatial

DTN et le Bundle Protocol ont été validés dans plusieurs démonstrations spatiales, notamment sur des missions en orbite terrestre et lors d’expériences proches de l’ISS, montrant la faisabilité opérationnelle du paradigme store‑carry‑and‑forward pour les opérations spatiales. Ces essais ont conforté le choix de BP par le CCSDS et les agences comme NASA et ESA pour les communications inter‑satellites et sol‑espace disruptives.[^2][^6][^3]

Les travaux récents sur « Space Internet » et constellations LEO massives utilisent CGR et ses extensions comme routage de référence, et s’intéressent aux problématiques de gestion de capacité, de buffer et de robustesse aux incertitudes de contact, renforçant la pertinence de DTN pour des essaims de nano‑satellites faiblement connectés.[^24][^3]


## 5. Synthèse des mécanismes clés pour un SANET résilient

L’état de l’art montre qu’aucun protocole unique ne suffit à assurer la résilience complète d’un essaim de nano‑satellites ; les solutions robustes combinent plusieurs niveaux de mécanismes. Au niveau du routage packet‑switched, l’usage de protocoles MANET optimisés (OLSR/MPR, AODV énergétiquement conscient) ou géographiques (GPSR et variantes) limite le trafic de contrôle et les tempêtes d’updates, tout en permettant une reconvergence rapide après des pannes locales.[^16][^8][^15][^11][^7]

Sur le plan de l’auto‑cicatrisation, des techniques comme SHORT, le multipath, les clusters auto‑organisés avec rotation de rôle et les algorithmes d’élection de leader pour réseaux dynamiques permettent de reconfigurer la topologie logique après la mort de nœuds centraux, en bornant le volume de messages de reconfiguration et le temps sans leader. Ces approches s’intègrent naturellement dans des architectures SANET/FANET hiérarchiques ou SDN‑hybrides.[^20][^22][^21][^5][^4]

Enfin, l’adoption d’une couche DTN conforme à l’architecture de l’RFC 4838, au Bundle Protocol BPv7 (RFC 9171) et au profil CCSDS 734.2 fournit un mécanisme de résilience structurelle au partitionnement de l’essaim, en assurant la livraison différée des bundles via store‑carry‑and‑forward et des algorithmes de routage spécialisés (CGR, PRoPHET, Spray and Wait). Les travaux récents sur l’amélioration de CGR sous contraintes de capacité et de buffers, ainsi que sur les variantes opportunistes à overhead borné, ouvrent la voie à des essaims réellement auto‑cicatrisants et tolérants aux pannes critiques.[^25][^26][^6][^27][^35][^1][^3][^24]

---

## References

1. [[PDF] RFC 9171: Bundle Protocol Version 7](https://www.rfc-editor.org/rfc/rfc9171.pdf) - This document describes BP version 7 (BPv7). Delay-Tolerant Networking is a network architecture pro...

2. [RFC 4838 - Delay-Tolerant Networking Architecture - IETF Datatracker](https://datatracker.ietf.org/doc/html/rfc4838) - This document describes an architecture for delay-tolerant and disruption-tolerant networks, and is ...

3. [Assessing Contact Graph Routing Performance and Reliability in ...](https://onlinelibrary.wiley.com/doi/10.1155/2017/2830542) - This work provides the first examination of the performance and robustness of Contact Graph Routing ...

4. [[PDF] Self-Healing and Optimizing Routing Techniques for Mobile Ad Hoc ...](https://www.sigmobile.org/mobihoc/2003/papers/p279-gui.pdf) - ABSTRACT. On demand routing protocols provide scalable and cost- effective solutions for packet rout...

5. [A Novel Self Organizing Framework for SANETs](https://www.eurecom.fr/en/publication/1928/download/cm-munimu-060502.pdf)

6. [[PDF] Routing in the Space Internet: A contact graph routing tutorial - HAL](https://hal.science/hal-03494106/file/2020-JNCA-CGR-Tutorial.pdf) - DTN protocols were successfully validated early in 2008 as part of the near-Earth spacecraft operati...

7. [Quality of Service Routing in a MANET with OLSR](https://www.jucs.org/jucs_13_1/quality_of_service_routing/jucs_13_1_0056_0086_nguyen.html)

8. [Ad hoc routing protocols with multipoint relaying](https://dept-info.labri.fr/~gavoille/algotel03/CameraReady/36.pdf)

9. [International Journal of Computer Applications Technology and Research](http://www.ijcat.com/archives/volume5/issue2/ijcatr05021010.pdf)

10. [newjucs05.dvi](https://www.jucs.org/jucs_13_1/quality_of_service_routing/jucs_13_1_0056_0086_nguyen.pdf)

11. [Energy aware stable path ad hoc on-demand distance vector ...](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0320897) - This paper proposed a novel routing protocol, the Energy Aware Stable Path Ad Hoc On-Demand Distance...

12. [GPSR: Greedy Perimeter Stateless Routing for Wireless](https://dl.acm.org/doi/pdf/10.1145/345910.345953)

13. [[PDF] GPSR: Greedy Perimeter Stateless Routing for Wireless Networks](https://www.eecs.harvard.edu/~htk/publication/2000-mobi-karp-kung.pdf)

14. [Geographic Routing for Wireless Networks](https://www.comp.nus.edu.sg/~bleong/geographic/related/karp00geographic.pdf)

15. [Microsoft Word - ICS-30-...Z..-new.doc](https://jise.iis.sinica.edu.tw/JISESearch/fullText;jsessionid=623d783b7bfa7593d893e2c4fe13?pId=1069&code=01B3FE85C438951)

16. [An Energy-aware Greedy Perimeter Stateless Routing Protocol for Mobile Ad hoc Networks](https://www.ijcaonline.org/volume9/number6/pxc3871871.pdf)

17. [IJSART - Volume 4 Issue 4 – APRIL 2018                                                                                       ISSN [ONLINE]: 2395-1052](http://ijsart.com/public/storage/paper/pdf/IJSARTV4I423047.pdf)

18. [A Secure Ad-hoc Routing Approach](http://hong.cs.ua.edu/papers/MOBIHOC05-selfheal.pdf)

19. [ICWN Papers.pdf](http://worldcomp-proceedings.com/proc/p2015/ICW2759.pdf)

20. [Routing protocols strategies for flying Ad-Hoc network (FANET)](https://www.sciencedirect.com/science/article/pii/S1110016824010469) - The purpose of this paper is to provide a comprehensive analysis of the most important FANET charact...

21. [[PDF] An Election Algorithm to Ensure the High Availability of Leader in ...](https://web.njit.edu/~ss797/publications/16-An_Election_Algorithm_to_Ensure_the_High_Availability_of_Leader_in_Large_Mobile_Ad_Hoc_Networks.pdf)

22. [A Leader Election Algorithm for Dynamic Networks with ...](https://groups.csail.mit.edu/tds/papers/Radeva/Radeva-etal.pdf)

23. [arXiv:1911.00759v2 [cs.DC] 28 Jun 2020](https://arxiv.org/pdf/1911.00759.pdf)

24. [Improved Contact Graph Routing in Delay Tolerant ...](https://arxiv.org/html/2410.15546v1)

25. [[PDF] draft recommended standard ccsds 734.2-p-1.1](https://ccsds.org/wp-content/uploads/gravity_forms/9-6f599803174a64f5da08b9814720b5c4/2025/02/734x2p11e1.pdf) - The purpose of this document is to establish a CCSDS Recommended Standard for Bundle. Protocol (BP),...

26. [[PDF] CCSDS Bundle Protocol Specification](https://ccsds.org/Pubs/734x2b1.pdf) - This document defines a Recommended Standard for the CCSDS Bundle Protocol (BP), based on the Bundle...

27. [New Strategy to Optimize the Performance of Epidemic Routing Protocol](https://research.ijcaonline.org/volume92/number7/pxc3895060.pdf)

28. [[PDF] Delay/Disruption Tolerant Networking (DTN) Implementer's Guide](https://ntrs.nasa.gov/api/citations/20260000898/downloads/450_2-DTN-DIG-L6-Preliminary%20Release_3%2020260128.pdf?attachment=true) - DTN is a network architecture designed to provide internetworking functionality and standardized aut...

29. [[PDF] Contact Multigraph Routing: Overview and Implementation](https://ntrs.nasa.gov/api/citations/20230002637/downloads/AeroConf_2023___Contact_Multigraph_Routing-20230221.pdf) - Abstract—In Delay Tolerant Networking (DTN), the standard routing algorithm used to navigate time-va...

30. [ACHIEVING LOW END-TO-END LATENCY WITH A](https://www.scitepress.org/papers/2010/29878/29878.pdf)

31. [Probabilistic Routing Based on Two-Hop Information in Delay/Disruption Tolerant Networks](https://dl.acm.org/doi/10.1155/2015/918065) - We investigate an opportunistic routing protocol in delay/disruption tolerant networks (DTNs) where ...

32. [International Research Journal of Engineering and Technology (IRJET)               e-ISSN: 2395-0056](https://www.irjet.net/archives/V2/i8/IRJET-V2I8185.pdf)

33. [International Research Journal of Engineering and Technology (IRJET)      e-ISSN: 2395 -0056](https://www.irjet.net/archives/V3/i6/IRJET-V3I694.pdf)

34. [draft-irtf-dtnrg-prophet-09.txt](https://www.ietf.org/archive/id/draft-irtf-dtnrg-prophet-09.txt)

35. [[PDF] Spray and wait: an efficient routing scheme for intermittently ...](https://www.semanticscholar.org/paper/Spray-and-wait:-an-efficient-routing-scheme-for-Spyropoulos-Psounis/44ecb60efb44bd83e256c7a7e0f6b4e3825a18d2) - A new routing scheme, called Spray and Wait, that "sprays" a number of copies into the network, and ...

36. [[PDF] Spray and Wait: An Efficient Routing Scheme for Intermittently ...](https://chants.cs.ucsb.edu/2005/papers/paper-SpyPso.pdf) - ABSTRACT. Intermittently connected mobile networks are sparse wire- less networks where most of the ...

37. [[PDF] Dynamic Spray and Wait Routing Protocol for Delay Tolerant Networks](https://inria.hal.science/hal-01551307v1/document) - DS&W routing protocol can dramatically reduce the overhead ratio in DTNs. Simulation results also ev...

