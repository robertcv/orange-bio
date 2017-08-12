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
    tax = [t[0]+' - '+t[1] for t in tax_list]
    return org, tax


class OWSTRING(OWWidget):
    name = "STRING data set"
    description = "Returns an Orange network object"
    icon = "icons/STRING.png"

    want_main_area = False

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

        gui.button(self.controlArea, self, "Commit", callback=self.update)

    def update(self):
        if self.organism_id != 0:
            self.string = obiSTRING.STRING(taxid=self.organisms[self.organism_id])
        self.progressBarInit()
        self.proteins = self.biogrid.proteins_table(taxid=self.organisms[self.organism_id])
        self.Outputs.table.send(self.proteins)
        self.progressBarSet(33)

        self.network = self.string.extract_network(self.organisms[self.organism_id])
        self.info.setText('number of nodes: {}\nnumber of edges: {}'.format(
            self.network.number_of_nodes(),
            self.network.number_of_edges()))
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