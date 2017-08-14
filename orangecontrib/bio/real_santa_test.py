from orangecontrib.bio.ppi import *
from orangecontrib.bio.santa import *


biogrid = BioGRID()

pt = biogrid.proteins_table(taxid='9606', attr='experimental_system_type', attr_value=['genetic'])
lt = biogrid.links_table(taxid='9606', attr='experimental_system_type', attr_value=['genetic'])
net = biogrid.extract_network('9606', 'experimental_system_type', ['genetic'])

node = ['ACVRL1', 'ADA', 'ADAM10', 'ADCY6', 'ADCY8', 'ADD1', 'PARP1', 'ADRBK2', 'AP2A1', 'AGTR2', 'AKT1', 'ABCD1', 'ALDH3B1', 'ABCD2', 'ALDOA', 'AKR1B1', 'ALK', 'AMFR', 'AMPH', 'BIN1', 'SLC25A6', 'ANXA1', 'ANXA5', 'APBB1', 'APC', 'XIAP', 'BIRC5', 'APP', 'FAS', 'AR', 'RHOA', 'ARL3', 'ATM', 'RERE', 'ATP5D', 'ATR', 'B2M', 'BAG1']
node_weights = {}
for i in range(len(node)):
    node_weights[node[i]] = 1

santa = SANTA(net, node_weights)

k_net, auc_k_net = santa.k_net()