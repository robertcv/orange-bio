from __future__ import absolute_import

import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from math import erf, sqrt


class SANTA(object):
    def __init__(self, network, node_weights):
        self.network = network
        self.node_weights = node_weights

        self.dist_matrix = None
        self.nodes = None
        self.all_node_weights = None
        self.w_index = None

        self.number_of_nodes = None
        self.max_dist = None
        self.mean_node_weight = None

    def _calc_network_properties(self):
        if self.dist_matrix is None:
            self.dist_matrix = nx.all_pairs_shortest_path_length(self.network)

        if self.nodes is None:
            self.nodes = self.network.nodes()

        if self.number_of_nodes is None:
            self.number_of_nodes = self.network.number_of_nodes()

        if self.max_dist is None:
            self.max_dist = nx.diameter(self.network)

        if self.mean_node_weight is None:
            self.mean_node_weight = sum(self.node_weights.values()) / self.number_of_nodes

    def _set_all_node_weights(self):
        if self.all_node_weights is None:
            self.all_node_weights = np.zeros(self.number_of_nodes)
            self.w_index = {self.nodes[i]:i for i in range(self.number_of_nodes)}
            for n, w in self.node_weights.items():
                self.all_node_weights[self.w_index[n]] = w

    def _k_net(self, s):
        k_net_s = 0

        for i in self.nodes:
            if self.all_node_weights[self.w_index[i]] != 0:
                tmp = 0

                for j in self.nodes:
                    if self.dist_matrix[i][j] <= s:
                        tmp += self.all_node_weights[self.w_index[j]] - self.mean_node_weight

                k_net_s += tmp * self.all_node_weights[self.w_index[i]]

        return k_net_s

    def k_net(self):
        self._calc_network_properties()
        self._set_all_node_weights()

        k_net = np.zeros(self.max_dist)

        for s in range(self.max_dist):
            k_net[s] = self._k_net(s)

        k_net = k_net * (2 / (self.mean_node_weight * self.number_of_nodes)**2)
        auk_k_net = np.trapz(k_net)
        return k_net, auk_k_net

    def auk_p_value(self, permutations):
        _, obs_auk = self.k_net()
        auk_perm = np.zeros(permutations)
        original_node_weights = np.copy(self.all_node_weights)

        for i in range(permutations):
            np.random.shuffle(self.all_node_weights)
            auk_perm[i] = self.k_net()[1]

        self.all_node_weights = original_node_weights

        auk_perm_mean = np.mean(auk_perm)
        auk_perm_std = np.std(auk_perm)

        z = (auk_perm_mean - obs_auk) / auk_perm_std
        p = 0.5 * (1 + erf(z / sqrt(2)))

        return p

    def k_node(self, s):
        self._calc_network_properties()
        self._set_all_node_weights()

        pn = (2 / (self.mean_node_weight * self.number_of_nodes)**2)
        k_node = []

        for i in self.nodes:
            if self.all_node_weights[self.w_index[i]] == 0:
                tmp = [i, 0]
                for j in self.nodes:
                    if self.dist_matrix[i][j] <= s:
                        tmp[1] += self.all_node_weights[self.w_index[j]] - self.mean_node_weight
                tmp[1] *= pn
                k_node.append(tmp)

        return sorted(k_node, key=lambda n: -n[1])

