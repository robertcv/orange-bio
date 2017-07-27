from Orange.widgets.widget import OWWidget, Output
from Orange.widgets import gui
from .. import obiBioGRID, obiTaxonomy
from orangecontrib.network.network import Graph


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

class OWBioGRID(OWWidget):
    name = "BioGRID data set"
    description = "Returns an Orange network object"
    icon = "icons/BioGRID.png"

    want_main_area = False

    class Outputs:
        graph = Output("BioGRID network", Graph)

    def __init__(self):
        super().__init__()

        self.biogrid = obiBioGRID.BioGRID()
        self.organisms, self.taxonomy = org_to_tax(self.biogrid.organisms())

        self.organism_id = 0
        self.network = None

        gui.comboBox(self.controlArea, self, "organism_id",
                     label="Choose an organism",
                     callback=self.update,
                     items=self.taxonomy)

        box = gui.widgetBox(self.controlArea, "Info")
        self.info = gui.widgetLabel(box, 'No organism yet chosen.')

    def update(self):
        self.network = self.biogrid.extract_network(self.organisms[self.organism_id])
        self.info.setText('number of nodes: {}\nnumber of edges: {}'.format(
            self.network.number_of_nodes(),
            self.network.number_of_edges()))
        self.Outputs.graph.send(self.network)