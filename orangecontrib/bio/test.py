from orangecontrib.bio.ppi import *
from santa import SANTA
import networkx as nx
import matplotlib.pyplot as plt

biogrid = BioGRID()
org = list(biogrid.organisms())
print(org)

ids = biogrid.ids(org[0])
print(ids)

synonyms = biogrid.synonyms(ids[1])
print(synonyms)

edges = biogrid.edges(ids[0])
print(edges)

network = biogrid.extract_network(org[0])
test_santa = SANTA(network, {ids[i]: 1 for i in range(50)})
k_net, auc_k_net = test_santa.k_net()
print(k_net)

plt.figure(1)
plt.plot(k_net)

plt.figure(2)
nx.draw_networkx(network)
plt.show()