from __future__ import absolute_import

from santa import *
import networkx as nx
import matplotlib.pyplot as plt

g = nx.Graph()
g.nodes_iter()

nodes = [str(i) for i in range(1,13)]
edges = [('1','2'), ('1','3'), ('1','4'), ('2','3'), ('2','4'), ('3','4'), ('1','5'), ('5','6'), ('2','7'),
         ('7','8'), ('4','9'), ('9','10'), ('3','11'), ('11','12')]

for n in nodes:
    g.add_node(n)
for n1, n2 in edges:
    g.add_edge(n1, n2)

plt.figure(1)
nx.draw_networkx(g)

node_w = {'1':1, '2':1}
test_santa1 = SANTA(g, node_w)
k_net, auc_k_net = test_santa1.k_net()
print('Knet:')
print(k_net)
print('AUK for Knet: ', auc_k_net)

p_value = test_santa1.auk_p_value(1000)
print('P-value for Knet: ', p_value)

k_node = test_santa1.k_node(1)
print('Knode:')
for n in k_node:
    print(n)

print()
node_w = {'5':1, '6':1}
test_santa2 = SANTA(g, node_w)
k_net, auc_k_net = test_santa2.k_net()
print('Knet:')
print(k_net)
print('AUK for Knet: ', auc_k_net)

p_value = test_santa2.auk_p_value(1000)
print('P-value for Knet: ', p_value)

k_node = test_santa2.k_node(1)
print('Knode:')
for n in k_node:
    print(n)


plt.show()

