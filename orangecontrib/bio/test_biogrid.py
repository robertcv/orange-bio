from orangecontrib.bio.ppi import *
from santa import SANTA
import networkx as nx
import matplotlib.pyplot as plt

biogrid = BioGRID()
org = biogrid.organisms()

att = biogrid.attribute_unique_value('tags', taxid=org[0])
print(att)




#
# import time
# s=0
# N=1
#
# for _ in range(N):
#     start = time.clock()
#     number = biogrid.number_of_edges(org[0])
#     s += time.clock()-start
#
# print(s/N)

# links_table = biogrid.proteins_table(org[2])
#
#
# a = links_table[links_table.domain[0]]
# print(a)
#
# proteins_table = biogrid.proteins_table(org[0])
# print(proteins_table)

# heders = [h[0] for h in proteins_table.description]
# print(heders)
# data = proteins_table.fetchall()
# print(data)

# heder_values = [list({str(d[i]) for d in data}) for i, h in enumerate(heders)]
#
# from Orange.base import Table
# from Orange.data.domain import Domain
# from Orange.data.variable import DiscreteVariable
# import numpy
#
# dom = Domain([DiscreteVariable(name=h, values=heder_values[i]) for i, h in enumerate(heders)])
#
# arr = numpy.array(data, dtype=str)
#
# ot = Table(dom, data)
#
# print(ot)

# edges = biogrid.edges(ids[0])
# print(edges)
#
# print(len(biogrid.proteins_table(org[2])))
# network = biogrid.extract_network(org[2])
# max_dist = network.nodes()
# print(max_dist)



# print(network.nodes_iter())
# test_santa = SANTA(network, {ids[i]: 1 for i in range(50)})
# k_net, auc_k_net = test_santa.k_net()
# print(k_net)
#
# plt.figure(1)
# plt.plot(k_net)
#
# plt.figure(2)
# nx.draw_networkx(network)
# plt.show()