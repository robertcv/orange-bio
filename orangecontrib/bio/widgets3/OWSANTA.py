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
        k_net_table = Output("Knet Data", Table)
        k_node_table = Output("Knode Data", Table)

    def __init__(self):
        super().__init__()

        self.santa = None
        self.network = None
        self.proteins = None
        self.not_matched = 0

        self.protein_col = 0

        self.calc_p_value = False
        self.p_value_iterations = 0

        self.calc_k_node = False

        box_info = gui.widgetBox(self.controlArea, "Info")
        self.network_info = gui.widgetLabel(box_info, 'Network:\n  No network.')
        self.proteins_info = gui.widgetLabel(box_info, 'Proteins:\n  No proteins.')

        box_santa = gui.widgetBox(self.controlArea, "SANTA")
        gui.widgetLabel(box_santa, 'Select proteins id column.')
        self.cb_p = gui.comboBox(box_santa, self, "protein_col")

        self.auc_k_net = gui.widgetLabel(box_santa, 'ACU for Knet: no data')

        gui.checkBox(box_santa, self, 'calc_k_node',
                     'Calculate Knode')

        gui.checkBox(box_santa, self, 'calc_p_value',
                     'Calculate p-value for Knet')
        box_p_value = gui.widgetBox(box_santa)
        gui.spin(box_p_value, self, 'p_value_iterations',
                 minv=0, maxv=1000, step=20, label='Number of iterations:')
        self.p_value = gui.widgetLabel(box_p_value, 'P-value: no data')

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
            self.cb_p.addItems(str(d) for d in list(self.proteins.domain) + list(self.proteins.domain.metas))
        else:
            self.proteins = None
            self.proteins_info.setText('Proteins:\n  No proteins.')
            self.cb_p.clear()

    def calc(self):
        self.progressBarInit()
        self.net_nodes = self.network.items()
        n_domain = len(self.net_nodes.domain)
        if self.protein_col < n_domain:
            self.n_col = self.protein_col
        else:
            self.n_col = -self.protein_col + n_domain - 1

        self.santa = obiSANTA.SANTA(self.network, self.get_node_weights())
        self.proteins_info.setText(self.proteins_info.text() +
                                   '\n  {} proteins could not be matched!'.format(self.not_matched))

        k_net, auc_k_net = self.santa.k_net()
        self.Outputs.k_net_table.send(self.santa.k_net_table(k_net))
        self.auc_k_net.setText('ACU for Knet: {}'.format(auc_k_net))
        self.progressBarSet(33)

        if self.calc_p_value:
            p_value = self.santa.auk_p_value(self.p_value_iterations)
            self.p_value.setText('P-value: {}'.format(p_value))
        self.progressBarSet(66)
        if self.calc_k_node:
            k_node = [[str(self.net_nodes[n[0]][self.n_col].value), n[1]] for n in self.santa.k_node()]
            self.Outputs.k_node_table.send(self.santa.k_node_table(k_node))
        self.progressBarFinished()

    def get_node_weights(self):
        self.not_matched = 0
        node_weights = {}
        for p in self.proteins:
            for i, row in enumerate(self.net_nodes):
                if p[self.n_col] in list(row) + list(row.metas):
                    node_weights[i] = 1
                    break
            else:
                self.not_matched += 1
        return node_weights


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