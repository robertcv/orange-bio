from orangecontrib.bio.ppi import *

string_d = STRINGDetailed('272634')

print(string_d.sql('select count(*) from links'))

#print(string_d.links_table())