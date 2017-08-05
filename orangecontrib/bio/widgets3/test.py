import sys
import Orange
from orangecontrib.bio.widgets3.OWBioGRID import OWBioGRID

def main(argv=None):
    ow = OWBioGRID()
    ow.show()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
