import sys
from Orange.widgets.widget import OWWidget, Output, Input
from Orange.widgets import gui
from orangecontrib.bio import obiSANTA
from orangecontrib.network.network import Graph
from Orange.base import Table


class OWSANTA(OWWidget):
    name = "SANTA"
    description = "Spatial Analysis of Network Associations"
    icon = "icons/SANTA.png"

    want_main_area = False

    class Inputs:
        graph = Input("Network", Graph)
        proteins = Input("Data", Table)

    class Outputs:
        table = Output("Data", Table)

    def __init__(self):
        super().__init__()

        self.santa = None
        self.network = None
        self.proteins = None

        self.protein_col = ''

        self.calc_p_value = False
        self.p_value_iterations = 0

        self.calc_k_node = False
        self.k_node_s = 0

        box_info = gui.widgetBox(self.controlArea, "Info")
        self.network_info = gui.widgetLabel(box_info, 'Network:\n  No network.')
        self.proteins_info = gui.widgetLabel(box_info, 'Proteins:\n  No proteins.')

        box_santa = gui.widgetBox(self.controlArea, "SANTA")
        gui.widgetLabel(box_santa, 'Select proteins id column.')
        self.cb_p = gui.comboBox(box_santa, self, "protein_col")

        self.k_net = gui.widgetLabel(box_santa, 'Knet: no data')
        self.auc_k_net = gui.widgetLabel(box_santa, 'ACU for Knet: no data')

        gui.checkBox(box_santa, self, 'calc_p_value',
                     'Calculate p-value for Knet')
        box_p_value = gui.widgetBox(box_santa)
        gui.spin(box_p_value, self, 'p_value_iterations',
                 minv=0, maxv=1000, step=20, label='Number of iterations:')
        self.p_value = gui.widgetLabel(box_p_value, 'P-value: no data')

        gui.checkBox(box_santa, self, 'calc_k_node',
                     'Calculate Knode')
        box_k_node = gui.widgetBox(box_santa)
        gui.spin(box_k_node, self, 'k_node_s', minv=1, maxv=100,
                 step=1, label='Select node of distance:')
        self.k_node = gui.widgetLabel(box_k_node, 'Knode: no data')

        gui.button(box_santa, self, "Calculate", callback=self.calc)

    @Inputs.graph
    def set_graph(self, graph):
        if graph is not None:
            self.network = graph
            self.network_info.setText('Network:\n  Number of nodes: {}\n  Number of edges: {}'.format(
                self.network.number_of_nodes(),
                self.network.number_of_edges()))
        else:
            self.network = None
            self.network_info.setText('Network:\n  No network.')

    @Inputs.proteins
    def set_proteins(self, proteins):
        if proteins is not None:
            self.proteins = proteins
            self.proteins_info.setText('Proteins:\n  Number of proteins: {}'.format(len(self.proteins)))
            self.cb_p.clear()
            self.cb_p.addItems(str(d) for d in self.proteins.domain)
        else:
            self.proteins = None
            self.proteins_info.setText('Proteins:\n  No proteins.')
            self.cb_p.clear()

    def calc(self):
        c_i = self.proteins.domain.index(self.protein_col)
        node_weights = {}
        for i in range(len(self.proteins)):
            id = str(int(self.proteins[i][c_i].value))
            node_weights[id] = 1

        self.santa = obiSANTA.SANTA(self.network, node_weights)

        k_net, auc_k_net = self.santa.k_net()
        self.k_net.setText('Knet: {}'.format(k_net))
        self.auc_k_net.setText('ACU for Knet: {}'.format(auc_k_net))

        if self.calc_p_value:
            p_value = self.santa.auk_p_value(self.p_value_iterations)
            self.p_value.setText('P-value: {}'.format(p_value))

        if self.calc_k_node:
            k_node = self.santa.k_node(self.k_node_s)
            self.k_node.setText('Knode: {}'.format(k_node[:5]))


def test_main():
    from AnyQt.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = OWSANTA()
    w.show()
    r = app.exec_()
    w.saveSettings()
    return r

if __name__ == "__main__":
    sys.exit(test_main())