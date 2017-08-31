import sys
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
    name = "STRING database"
    description = "Returns an Orange network object"
    icon = "icons/string.png"

    want_main_area = False

    ATTRIBUTES = [
        ('', None),
        ('Combined score', 'score'),
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
        self.auto_commit = False

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
                     items=[a[0] for a in self.ATTRIBUTES])

        self.condition = 0
        gui.spin(box2, self, 'condition',
                 minv=0, maxv=1000, step=10, label='Minimum score:')

        gui.button(self.controlArea, self, "Check numbers", callback=self.update_info)
        gui.auto_commit(self.controlArea, self, 'auto_commit', "Commit", commit=self.commit)

    def organism_update_info(self):
        self.string = obiSTRING.STRINGDetailed(taxid=self.organisms[self.organism_id])
        node_n = self.string.number_of_nodes()
        edge_n = self.string.number_of_edges()
        self.info.setText('Nodes: {}\nEdges: {}'.format(node_n, edge_n))
        if self.auto_commit:
            self.commit()

    def update_info(self):
        node_n = self.string.number_of_nodes(attr=self.ATTRIBUTES[self.attribute_id][1],
                                              attr_value=self.condition)
        edge_n = self.string.number_of_edges(attr=self.ATTRIBUTES[self.attribute_id][1],
                                              attr_value=self.condition)
        self.info.setText('Nodes: {}\nEdges: {}'.format(node_n, edge_n))
        if self.auto_commit:
            self.commit()

    def commit(self):
        self.progressBarInit()
        self.proteins = self.string.proteins_table(attr=self.ATTRIBUTES[self.attribute_id][1],
                                                   attr_value=self.condition)
        self.Outputs.table.send(self.proteins)
        self.progressBarSet(33)

        self.interactions = self.string.links_table(attr=self.ATTRIBUTES[self.attribute_id][1],
                                                    attr_value=self.condition)
        self.Outputs.interactions.send(self.interactions)
        self.progressBarSet(66)

        self.network = self.string.extract_network(attr=self.ATTRIBUTES[self.attribute_id][1],
                                                    attr_value=self.condition)
        self.Outputs.graph.send(self.network)
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