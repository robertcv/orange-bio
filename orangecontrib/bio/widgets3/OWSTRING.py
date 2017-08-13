import sys
from AnyQt.QtWidgets import QListWidget
from Orange.widgets.widget import OWWidget, Output
from Orange.widgets import gui
from orangecontrib.bio import obiSTRING, obiTaxonomy
from orangecontrib.network.network import Graph
from Orange.base import Table

ORGANISMS_TAXID = ['3055', '3702', '4896', '4932', '5833', '6239', '7227', '7955',
                   '9606', '9913', '10090', '10116', '31033', '39947', '44689', '272634']


def org_to_tax(organisms):
    tax_list = []
    for o in organisms:
        try:
            tax_name = obiTaxonomy.name(o)
        except:
            try:
                tax_name = obiTaxonomy.other_names(o)
            except:
                tax_name = o
        tax_list.append((tax_name, o))
    tax_list = sorted(tax_list)
    org = [o[1] for o in tax_list]
    tax = [t[0] for t in tax_list]
    return org, tax


class OWSTRING(OWWidget):
    name = "STRING data set"
    description = "Returns an Orange network object"
    icon = "icons/STRING.png"

    want_main_area = False

    ATTRIBUTES = [
        ('Action', 'action'),
        ('Action mode', 'mode'),
        ('Action score', 'score'),
        ('Neighborhood score', 'neighborhood'),
        ('Fusion score', 'fusion'),
        ('Cooccurence score', 'cooccurence'),
        ('Coexpression score', 'coexpression'),
        ('experimental score', 'experimental'),
        ('Database score', 'database'),
        ('Textmining score', 'textmining'),
    ]

    class Outputs:
        graph = Output("Network", Graph)
        table = Output("Node Data", Table)
        interactions = Output("Edge Data", Table)

    def __init__(self):
        super().__init__()

        self.string = None
        self.organisms, self.taxonomy = org_to_tax(ORGANISMS_TAXID)

        self.organism_id = 0
        self.attribute_id = 0

        self.network = None

        self.proteins = []
        self.interactions = []

        box1 = gui.widgetBox(self.controlArea, "Info")
        self.info = gui.widgetLabel(box1, 'No database subset yet chosen.')

        box2 = gui.widgetBox(self.controlArea, "Select database subset")
        gui.widgetLabel(box2, 'Select organism.')
        gui.comboBox(box2, self, "organism_id",
                     callback=self.organism_update_info,
                     items=self.taxonomy)
        gui.widgetLabel(box2, 'Select attribute.')
        gui.comboBox(box2, self, "attribute_id",
                     callback=self.attribute_update,
                     items=[a[0] for a in self.ATTRIBUTES])

        self.conditions = []
        self.conditions_index = []
        self.conditions_box = gui.listBox(box2, self, "conditions_index",
                                          selectionMode=QListWidget.MultiSelection)
        self.conditions_box.itemClicked.connect(self.attribute_update_info)

        gui.button(self.controlArea, self, "Commit", callback=self.commit)

    def organism_update_info(self):
        self.string = obiSTRING.STRINGDetailed(taxid=self.organisms[self.organism_id])
        self.info.setText('Processing ...')
        self.conditions_box.clear()
        node_n = self.string.number_of_nodes()
        edge_n = self.string.number_of_edges()
        self.info.setText('Number of nodes: {}\nNumber of edges: {}'.format(node_n, edge_n))

    def attribute_update(self):
        pass
        # self.conditions_box.clear()
        # self.conditions_box.addItem('Processing ...')
        # self.conditions = self.biogrid.attribute_unique_value(self.ATTRIBUTES[self.attribute_id][1],
        #                                                       taxid=self.organisms[self.organism_id])
        # self.conditions_box.clear()
        # self.conditions_box.addItems(self.conditions)

    def attribute_update_info(self):
        pass
        # self.info.setText('Processing ...')
        # node_n = self.biogrid.number_of_nodes(taxid=self.organisms[self.organism_id],
        #                                       attr=self.ATTRIBUTES[self.attribute_id][1],
        #                                       attr_value=[self.conditions[i] for i in self.conditions_index])
        # edge_n = self.biogrid.number_of_edges(taxid=self.organisms[self.organism_id],
        #                                       attr=self.ATTRIBUTES[self.attribute_id][1],
        #                                       attr_value=[self.conditions[i] for i in self.conditions_index])
        # self.info.setText('Number of nodes: {}\nNumber of edges: {}'.format(node_n, edge_n))

    def commit(self):
        self.progressBarInit()
        self.proteins = self.string.proteins_table()
        self.Outputs.table.send(self.proteins)
        self.progressBarSet(33)

        self.interactions = self.string.links_table()
        self.Outputs.interactions.send(self.interactions)
        self.progressBarSet(66)
        #
        # self.network = self.biogrid.extract_network(self.organisms[self.organism_id],
        #                                             self.ATTRIBUTES[self.attribute_id][1],
        #                                             [self.conditions[i] for i in self.conditions_index])
        # self.Outputs.graph.send(self.network)
        self.progressBarFinished()




def test_main():
    from AnyQt.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = OWSTRING()
    w.show()
    r = app.exec_()
    w.saveSettings()
    return r

if __name__ == "__main__":
    sys.exit(test_main())