# TODO: Popravi moznost izbire enrichanih termov. Namesto tresholda daj funkcijo.
# TODO: Buffering za izbiro termov. Dodaj optimizacijo, ki uposteva vsebovanost.
# TODO: Dodaj callback pri iskanju MeSH termov.

import orange
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from math import log,exp
from urllib import urlopen
from sgmllib import SGMLParser
import os.path

class obiMeSH(object):
    def __init__(self):
        self.path = "data\MeSH"
        self.reference = None
        self.cluster = None
        self.ratio = 1
        self.statistics = None
        self.calculated = False
        
        self.ref_att = "Unknown"
        self.clu_att = "Unknown"
        self.solo_att = "Unknown"
		
        #we calculate log(i!)
        self.lookup = [0]
        for i in range(1, 8000):
            self.lookup.append(self.lookup[-1] + log(i))
        self.dataLoaded = self.__loadOntologyFromDisk()

    def setDataDir(self, dataDir):
        self.path = dataDir
        self.dataLoaded = self.dataLoaded or self.__loadOntologyFromDisk()
 
    def getDataDir(self):
        """Default for dataDir is "data", by calling these two methods the user can change the directory of the local "fast" data base.
        This influences downloadGO() and downloadAnnotation(...). above directory also buffers compound annotation"""
        return self.path

    def downloadOntology(self,callback=None):
        # ftp://nlmpubs.nlm.nih.gov/online/mesh/.meshtrees/mtrees2008.bin
        # ftp://nlmpubs.nlm.nih.gov/online/mesh/.asciimesh/d2008.bin
        if callback:
            callback(1)
        
        ontology = urlopen("ftp://nlmpubs.nlm.nih.gov/online/mesh/.asciimesh/d2008.bin")
        size = int(ontology.info().getheader("Content-Length"))
        rsize = 0

        results = list()

        for i in ontology:
            rsize += len(i)
            line = i.rstrip("\t\n")
            if(line == "*NEWRECORD"):
                if(len(results) > 0 and results[-1][1] == []):	# we skip nodes with missing mesh id
                    results[-1] = ["",[],"No description."]
                else:
                    results.append(["",[],"No description."])	
                if(len(results)%40 == 0):
                    if callback:
                        callback(1+int(rsize*94/size))	
	
            parts = line.split(" = ")
            if(len(parts) == 2 and len(results)>0):
                if(parts[0] == "MH"):
                    results[-1][0] = parts[1].strip("\t ") 

                if(parts[0] == "MN"):
                    results[-1][1].append(parts[1].strip("\t "))

                if(parts[0] == "MS"):
                    results[-1][2] = parts[1].strip("\t ")

        ontology.close()

        __dataPath = os.path.join(os.path.dirname(__file__), self.path)
        print "XXX", __dataPath
        output = file(os.path.join(__dataPath,'mesh-ontology.dat'), 'w')

        if callback:
            callback(98)
        
        for i in results:
            #			print i[0] + "\t"
            output.write(i[0] + "\t")
            g=len(i[1])			
            for k in i[1]:
                g -= 1
                if(g > 0):
                    #					print k + ";"
                    output.write(k + ";")
                else:
                    #					print k + "\t" + i[2]			
                    output.write(k + "\t" + i[2] + "\n")

        output.close()
        self.__loadOntologyFromDisk()
        if callback:
            callback(100)
        print "Ontology database has been updated."

    def findSubset(self,examples,meshTerms, callback = None):
        """ function examples which have at least one node on their path from list meshTerms
            findSubset(all,['Aspirine']) will return a dataset with examples annotated as Aspirine """
        # clone        
        newdata = orange.ExampleTable(examples.domain)
        self.solo_att = self.__findMeshAttribute(examples)
        ids = list()
        l = len(examples)
        c = 0.0

        # we couldn't find any mesh attribute
        if self.solo_att == "Unknown":
            return newdata

        for i in meshTerms:
            ids.extend(self.toID[i])

        for e in examples:
            try:
                if callback:
                    callback(int(c*100.0/l))
                c = c + 1.0
                ends = eval(e[self.solo_att].value)
            except SyntaxError:
                #print "Error in parsing ", e[self.solo_att].value
                continue
            endids = list()
            for i in ends:
                if self.toID.has_key(i):
                    endids.extend(self.toID[i])
            allnodes = self.__findParents(endids)

            # calculate intersection            
            isOk = False            
            for i in allnodes:
                if ids.count(i) > 0:
                    isOk = True
                    break

            if isOk:      # intersection between example mesh terms and observed term group is None
                newdata.append(e)

        return newdata

    def findTerms(self,ids, idType="cid", callback = None):
        """ returns a dictionary with terms (term id) that apply to ids (cids or pmids). """

        ret = dict()
        if(not self.dataLoaded):
            print "Annotation and ontology has never been loaded! Use function setDataDir(path) to fix the problem."
            return ret

        if idType=="cid": 
            for i in ids:
                if self.fromCID.has_key(i): # maybe it is on our database
                    ret[int(i)] = self.fromCID[i]
                else:   # no it is not, let's go in the internet    
                    l = self.findTermsForCID(i)
                    self.fromCID[int(i)] = l
                    ret[int(i)] = l
                    
                    if len(l)>0:
                        # if we found something lets save it to a file
                        __dataPath = os.path.join(os.path.dirname(__file__), self.path)
                        fileHandle = open(os.path.join(__dataPath,'cid-annotation.dat'), 'a')
                        for s in l:
                            fileHandle.write('\n' + str(i) + ';' + s )
                        fileHandle.close()
                    
            return ret
        elif idType == "pmid":  #FIXME PMID annotation
            database = self.fromPMID
        else:
            return ret
        
        for i in ids:
            if(database.has_key(int(i))):
                ret[i] = database[int(i)]
        return ret
        
    def findTermsForCID(self,cid):
        """ functions tries to find MeSH terms for given CID on the internet """
        usock = urlopen("http://pubchem.ncbi.nlm.nih.gov/summary/summary.cgi?cid="+ str(cid)  +"&viewopt=PubChem&hcount=100&tree=t#MeSH")
        parser = PubChemMeSHParser()
        
        text = usock.read()
        #print text
        parser.feed(text)

        usock.close()
        parser.close()

        allTerms = parser.directTerms

        for (k,i) in parser.indirectTerms:
            usock = urlopen(i)
            parser = MappedMeSHParser()
            parser.feed(usock.read())
            allTerms.extend(parser.terms)     
            usock.close()
            parser.close()

        # from allTerms make a set
        allTerms = list(set(allTerms))

        return allTerms
   
    def findCIDSubset(self,examples,meshTerms, callback = None):
        """ function examples which have at least one node on their path from list meshTerms
            findSubset(['Aspirine'],[1,2,3]) will return a dataset with examples annotated as Aspirine"""

        newdata = []
        ids = list()

        for i in meshTerms:
                if self.toID.has_key(i):
                    ids.extend(self.toID[i])

        for e in examples:
            if not self.fromCID.has_key(e):
               continue

            ends = self.fromCID[e]
            endids = list()
            for i in ends:
                if self.toID.has_key(i):
                    endids.extend(self.toID[i])
            allnodes = self.__findParents(endids)

            # calculate intersection            
            isOk = False            
            for i in allnodes:
                if ids.count(i) > 0:
                    isOk = True
                    break

            if isOk:      # intersection between example mesh terms and observed term group is None
                newdata.append(e)
        return newdata
    
    def findFrequentTerms(self,data,minSizeInTerm, treeData = False, callback=None):
        """ Function iterates thru examples in data. For each example it computes a list of associated terms. At the end we get (for each term) number of examples which have this term. """
        # we build a dictionary 		meshID -> [description, noReference, [cids] ]
        self.statistics = dict()
        self.calculated = False
        self.solo_att = self.__findMeshAttribute(data)

        # post processing variables
        ret = dict()
        ids = []
        succesors = dict()		# for each term id -> list of succesors
        succesors["tops"] = []
        
        # if we can't identify mesh attribute we return empty data structures
        if self.solo_att == "Unknown":
            if treeData:
                return succesors, ret
            else:
                return ret

        # plain frequency
        t = 0.0
        n = len(data)
        for i in data:
            t = t + 1
            if callback:
                callback(int(t*100/n))
                
            try:
                endNodes = eval(i[self.solo_att].value)	# for every CID we look up for end nodes in mesh. for every end node we have to find its ID	
            except SyntaxError:
                #print "Error in parsing ",i[self.solo_att].value
                continue
            # we find ID of end nodes
            endIDs = []
            for k in endNodes:
                if(self.toID.has_key(k)):					# this should be always true, but anyway ...
                    endIDs.extend(self.toID[k])
                else:
                    print "Current ontology does not contain MeSH term ", k, "." 

            # we find id of all parents
            allIDs = self.__findParents(endIDs)
			
            for k in allIDs:						        # for every meshID we update statistics dictionary
                if(not self.statistics.has_key(k)):		    # first time meshID
                    self.statistics[k] = 0
                self.statistics[k] += 1				        # counter increased

        # post processing
        for i in self.statistics.iterkeys():

            if(self.statistics[i] >= minSizeInTerm ): 
                ret[i] = self.statistics[i]
                ids.append(i)

        # we can also return tree data
        if treeData: #we return also compulsory data for tree printing 
            return self.__treeData(ids), ret 
        else:
            return ret
    
    def __treeData(self,ids):
        succesors = dict()
        succesors["tops"]= []
        # we build a list of succesors. for each node we know which are its succesors in mesh ontology
        for i in ids:
            succesors[i] = []
            for j in ids:
                if(i != j and self.__isPrecedesor(i,j)):
                    succesors[i].append(j)
        
        # for each node from list above we remove its indirect succesors
        # only  i -1-> j   remain
        for i in succesors.iterkeys():
            succs = succesors[i]
            second_level_succs = []
            for k in succs:     
                second_level_succs.extend(succesors[k])
            for m in second_level_succs:
                if succesors[i].count(m)>0:
                    succesors[i].remove(m)
		
        # we make a list of top nodes
        tops = list(ids)
        for i in ids:
            for j in succesors[i]:
                tops.remove(j)

        # we pack tops table and succesors hash
        succesors["tops"] = tops
        return succesors  
        
    def findEnrichedTerms(self,reference, cluster, pThreshold=0.015, treeData = False, callback=None):
        """ like above, but only includes enriched terms (with p value equal or less than pThreshold). Returns a list of (term_id,  term_description, countRef, countCluster, p-value,	enrichment/deprivement, list of corrensponding cids ... anything else necessary). It printOrder is true function returns results in nested lists. This means that at printing time we know if there is any relationship betwen terms"""

        self.clu_att = self.__findMeshAttribute(cluster)
        self.ref_att = self.__findMeshAttribute(reference)
	
        if((not self.calculated or self.reference != reference or self.cluster != cluster) and self.ref_att != "Unknown" and self.clu_att != "Unknown"):	# Do have new data? Then we have to recalculate everything.
            self.reference = reference
            self.cluster = cluster			
            self.__calculateAll(callback)

        # declarations
        ret = dict()
        ids = []
        succesors = dict()		# for each term id -> list of succesors
        succesors["tops"] = []
        
        # if some attributes were unknown
        if (self.clu_att == "Unknown" or self.ref_att == "Unknown"):
            if treeData:
                return  succesors, ret
            else:
                return  ret

        for i in self.statistics.iterkeys():
            if(self.statistics[i][2] <= pThreshold ) :#or self.statistics[i][4] <= pThreshold ): # 
                ret[i] = self.statistics[i]
                ids.append(i)
    
        if treeData:
            return self.__treeData(ids),ret 
        else:
            return ret

    def printMeSH(self,data, selection = ["term","r","c", "p"], func = None):
        """for a dictinary of terms prints a MeSH ontology. Together with ontology should print things like number
        of compounds, p-values (enrichment), ... see Printing the Tree in orngTree documentation for example of such
        an implementation. The idea is to have only function for printing out the nested list of terms. """
        # first we calculate additional info for printing MeSH ontology
        info = self.__treeData(data.keys())
        for i in info["tops"]:
            self.__pp(0,i,info,data, selection, funct = func)

    def __pp(self, offset, item, relations, data, selection, funct = None):
        mapping = {"term":0,"desc":1,"r":2,"c":3, "p":4, "fold":5, "func":6} 
        for i in range(0,offset):
            print " ",

        if type(data[item]) == list:
            pval = "%.4g" % data[item][2]
            fold = "%.4g" % data[item][3]
            print_data = [self.toName[item], self.toDesc[self.toName[item]], str(data[item][0]), str(data[item][1]), str(pval), str(fold)]
            for i in selection:
                if i != "term":
                    print i + "=" + print_data[mapping[i]],
                else:
                    print print_data[mapping[i]],

            if funct != None:
                print " ", funct(print_data[0]),

            #print self.toName[item], " r=" + str(data[item][1])  +" c="+ str(data[item][2])  ," p=" + str(pval) + " fold=" + str(fold)
            print ""
        else:
            print self.toName[item], " freq=" + str(data[item])

        for i in relations[item]:
            self.__pp(offset + 2, i, relations, data, selection, funct = funct) 

    def printHtmlMeSH(self,data, selection = ["term","r","c", "p"], func = None):
        """for a dictinary of terms prints a MeSH ontology. Together with ontology should print things like number
        of compounds, p-values (enrichment), ... see Printing the Tree in orngTree documentation for example of such
        an implementation. The idea is to have only function for printing out the nested list of terms. """
        # first we calculate additional info for printing MeSH ontology
        info = self.__treeData(data.keys())
        print "<table>\n<tr>"
        for i in selection:
            print "<th width='55px' align='left'>" + i  +"</th>"
        
        if func != None:
            func("header")
            
        print "</tr>\n"
        for i in info["tops"]:
            self.__htmlpp(0,i,info,data, selection, funct = func)
        print "</table>"

    def __htmlpp(self, offset, item, relations, data, selection, funct = None):
        mapping = {"term":0,"desc":1,"r":2,"c":3, "p":4, "fold":5, "func":6} 
        print "<tr>"
        if type(data[item]) == list:
            pval = "%.4g" % data[item][2]
            fold = "%.4g" % data[item][3]
            print_data = [self.toName[item], self.toDesc[self.toName[item]], str(data[item][0]), str(data[item][1]), str(pval), str(fold)]
            for i in selection:
                print "<td>"
                
                if i == "term":
                    for l in range(0,offset):
                        print "&nbsp;",
                elif i == "p":
                    print '%(#)2.3e' % {'#':float(print_data[mapping[i]])} + "</td>",
                    continue
                print print_data[mapping[i]] + "</td>",

            if funct != None:
                print funct(print_data[0]),

            #print self.toName[item], " r=" + str(data[item][1])  +" c="+ str(data[item][2])  ," p=" + str(pval) + " fold=" + str(fold)
            print "</tr>"
        else:
            print self.toName[item], " freq=" + str(data[item])

        for i in relations[item]:
            self.__htmlpp(offset + 2, i, relations, data, selection, funct = funct)

    def findCompounds(self,terms, CIDs):
        """from CIDs found those compounds that match terms from the list"""
        # why do we need such a specialized function?
        
    def parsePubMed(self,filename, attributes = ["pmid", "title","abstract","mesh"], skipExamplesWithout = ["mesh"]):
        parser = make_parser()
        handler = pubMedHandler()
        parser.setContentHandler(handler)
        
        parser.parse(open(filename))

        atts = []
        for i in attributes:
            atts.append(orange.StringVariable(i))
        
        domain = orange.Domain(atts,0)
        data = orange.ExampleTable(domain)
        print data.domain.attributes
        mapping = {"pmid":0, "title":1, "abstract":2, "mesh":3, "affilation":4}
        
        for i in handler.articles:
            r=[]
            skip = False
            for f in attributes:
                if skipExamplesWithout.count(f) > 0:
                    if (f == "mesh" and len(i[mapping[f]]) == 0) or str(i[mapping[f]]) == "":
                        skip = True
                r.append(str(i[mapping[f]]))
            if not skip:
                data.append(r)
        return data       

    def __findParents(self,endNodes):
        """for each end node in endNodes function finds all nodes on the way up to the root"""		
        res = []
        for n in endNodes:
            tmp = n
            res.append(tmp)
            for i in range(n.count(".")):
                tmp = tmp.rstrip("1234567890").rstrip(".")
                if(tmp not in res):
                    res.append(tmp)
        return res

    def __findMeshAttribute(self,data):
        """ function tries to find attribute which contains list os mesh terms """
        # we get a list of attributes
        dom = data.domain.attributes
        for k in data:              # for each example
            for i in dom:           # for each attribute
                att = str(i.name)
                try:                                         # we try to use eval()
                    r = eval(str(k[att].value))
                    if type(r) == list:         # attribute type should be list
                        if self.dataLoaded:         # if ontology is loaded we perform additional test
                            for i in r:
                                if self.toID.has_key(i): return att
                        else:               # otherwise we return list attribute
                            return att
                except SyntaxError:
                    continue
                except NameError:
                    continue   
        print "Program was unable to determinate MeSH attribute."
        return "Unknown"

    def __isPrecedesor(self,a,b):
        """ function returns true if in Mesh ontology exists path from term id a to term id b """
        if b.count(a) > 0:
            return True
        return False
		
    def __calculateAll(self, callback):
        """calculates all statistics"""
        # we build a dictionary 		meshID -> [description, noReference,noCluster, enrichment, deprivement, [cids] ]
        self.statistics = dict()
        n = len(self.reference) 										# reference size
        cln = len(self.cluster)											# cluster size
        # frequency from reference list
        r = 0.0
        for i in self.reference:
            if callback:
                r += 1.0
                callback(int(100*r/(n+cln)))
            try:
                endNodes = eval(i[self.ref_att].value)	    # for every CID we look up for end nodes in mesh. for every end node we have to find its ID	
            except SyntaxError:                     # where was a parse error
                #print "Error in parsing ",i[self.ref_att].value
                n=n-1
                continue
            #we find ID of end nodes
            endIDs = []
            for k in endNodes:
                if(self.toID.has_key(k)):					# this should be always true, but anyway ...
                    endIDs.extend(self.toID[k])
                else:
                    print "Current ontology does not contain MeSH term ", k, "." 

            # endIDs may be empty > in this case we can skip this example
            if len(endIDs) == 0:
                n = n-1
                continue

            # we find id of all parents
            allIDs = self.__findParents(endIDs)
			
            for k in allIDs:						        # for every meshID we update statistics dictionary
                if(not self.statistics.has_key(k)):		    # first time meshID
                    self.statistics[k] = [ 0, 0, 0.0, 0.0 ]
                self.statistics[k][0] += 1				    # increased noReference
		
        # frequency from cluster list
        r=0.0
        for i in self.cluster:
            try:
                if callback:
                    r += 1.0
                    callback(int(100*r/(n+cln)))
                endNodes = eval(i[self.clu_att].value)	# for every CID we look up for end nodes in mesh. for every end node we have to find its ID	
            except SyntaxError:
                #print "Error in parsing ",i[self.clu_att].value
                cln = cln - 1
                continue
            # we find ID of end nodes
            endIDs = []
            for k in endNodes:
                if(self.toID.has_key(k)):				
                    endIDs.extend(self.toID[k])	# for every endNode we add all corensponding meshIDs
					
            # endIDs may be empty > in this case we can skip this example
            if len(endIDs) == 0:
                cln = cln-1
                continue
					
            # we find id of all parents
            allIDs = self.__findParents(endIDs)								

            for k in allIDs:						# for every meshID we update statistics dictionary
                self.statistics[k][1] += 1				# increased noCluster 

        self.ratio = float(cln)/float(n)
        
        # enrichment
        for i in self.statistics.iterkeys():
            self.statistics[i][2] = self.__calcEnrichment(n,cln,self.statistics[i][0],self.statistics[i][1])    # p enrichment
            self.statistics[i][3] = float(self.statistics[i][1]) / float(self.statistics[i][0] ) / self.ratio   # fold enrichment

        self.calculated = True		

    def __calcEnrichment(self,n,c,t,tc):
        """n - total number of chemicals ie. size(cluster + reference)
        c - cluster size ie. size(cluster)
        t - number of all chemicals in observed term group
        tc - number of cluster chemicals in observed term group"""
        #print "choose ", n, " ", c, " ", t, " ", tc		
        
        # FIXME: Popravi cudno racunanje enrichmenta v mejnih primerih.
        
        result=0
        for i in range(0,tc):
            result = result + exp(self.log_comb(t,i) + self.log_comb(n-t,c-i))
        result = result*1.0 / exp(self.log_comb(n,c))
        return (1.0-result)

    def log_comb(self,n, m): # it returns log(nCr(n,m))
        return self.lookup[n] - self.lookup[n-m] - self.lookup[m]

    def __loadOntologyFromDisk(self):
        """ Function loads MeSH ontology (pair cid & MeSH term) and MeSH graph data (graph structure) """
        self.toID = dict()  				#   name -> [IDs] Be careful !!! One name can match many IDs!
        self.toName = dict()				#   ID -> name
        self.toDesc = dict()				# 	name -> description
        self.fromCID = dict()               #   cid -> term id
        self.fromPMID = dict()              #   pmid -> term id

        __dataPath = os.path.join(os.path.dirname(__file__), self.path)

        try:		
            # reading graph structure from file
            d = file(os.path.join(__dataPath,'mesh-ontology.dat'))
        except IOError:
            print os.path.join(__dataPath,'mesh-ontology.dat') + " does not exist! Please use function setDataDir(path) to fix this problem."
            return False
            
        try:		
            # reading cid annotation from file
            f = file(os.path.join(__dataPath,'cid-annotation.dat'))
        except IOError:
            print os.path.join(__dataPath,'cid-annotation.dat') + " does not exist! Please use function setDataDir(path) to fix this problem."
            #return False
            
        try:		
            # reading pmid annotation from file
            g = file(os.path.join(__dataPath,'pmid-annotation.dat'))
        except IOError:
            #print os.path.join(__dataPath,'pmid-annotation.dat') + " does not exist! Please use function setDataDir(path) to fix this problem."
            #return False
			
        # loading ontology graph
		t=0
        for i in d:
            t += 1
            parts = i.split("\t")		# delimiters are tabs
            if(len(parts) != 3):
                print "error reading ontology ", parts[0]

            parts[2] = parts[2].rstrip("\n\r")
            ids = parts[1].split(";")

            self.toID[parts[0]] = ids	# append additional ID
            self.toDesc[parts[0]] = parts[2]

            for r in ids:
                self.toName[r] = parts[0]
        
        # loading cid -> mesh
        for i in f:
            parts = i.split(";")		# delimiters are tabs
            if(len(parts) != 2):
                print "error reading ontology ", parts[0]

            parts[1] = parts[1].rstrip("\n\r")
            cid = int(parts[0])
            
            if self.fromCID.has_key(cid):
                self.fromCID[cid].append(parts[1])
            else:
                self.fromCID[cid] = [parts[1]]
			                        
        # loading pmid -> mesh
				
        print "Current MeSH ontology contains ", t, " mesh terms."
        return True

class pubMedHandler(ContentHandler):
	def __init__(self):
		self.state = 0 		# 		0 start state, 1 pmid, 2 title, 3 abstract, 4 mesh 
		self.articles = []
 		self.pmid = "0"
		self.title = ""
		self.mesh = list()
		self.abstract = ""
		self.affiliation = ""

	def startElement(self, name, attributes):
		# print "parsam ", name
		if name == "PubmedArticle":
			self.pmid = ""
			self.abstract = ""
			self.title = ""
			self.mesh = []
		if name == "PMID":
			self.state = 1
		if name == "ArticleTitle":
			self.state = 2
		if name == "AbstractText":
			self.state = 3
		if name == "DescriptorName":
			self.state = 4
			self.mesh.append("")
		if name == "Affiliation":
		    self.state = 5

	def characters(self, data):
		if self.state == 1:
			self.pmid += data
		if self.state == 2:
			self.title += data.encode("utf-8")
		if self.state == 3:
			self.abstract += data.encode("utf-8")
		if self.state == 4:
			self.mesh[-1] += data.encode("utf-8")
		if self.state == 5:
		    self.affiliation += data.encode("utf-8")

	def endElement(self, name):
		#print "   koncujem ", name
		self.state = 0
		if name == "PubmedArticle":
			self.articles.append([self.pmid,self.title,self.abstract,self.mesh, self.affiliation])
			
class MappedMeSHParser(SGMLParser):
    def reset(self):
        self.pieces = []
        self.terms = []
        self.foundMeSH = False
        self.nextIsTerm = False
        self.endTags = ['Display','Write to the Help Desk', 'Previous Indexing:', 'Entry Terms:','Pharmacologic Action:' ]
        SGMLParser.reset(self)

    def unknown_starttag(self, tag, attrs): 
        strattrs = "".join([' %s="%s"' % (key, value) for key, value in attrs])

        if self.foundMeSH and tag=='a':
            self.nextIsTerm = True

    def handle_data(self, text):
        text = text.strip()
        if text == '':
            return

        if text == 'Heading Mapped to:':
            self.foundMeSH = True

        if self.endTags.count(text)>0:
            self.foundMeSH = False
        elif self.nextIsTerm:
            self.terms.append(text)
            self.nextIsTerm = False

class PubChemMeSHParser(SGMLParser):
    def reset(self):
        self.next = 0
        self.nextLink = ''
        self.directTerms = []
        self.indirectTerms = []
        self.foundMeSH = False
        SGMLParser.reset(self)
    
    # strategy as follows
    # Beetween strings "Drug and Chemical Info" and ("Pharmalogical Action" or "PubMed via MeSH" or "PubMed MeSH Keyword Summary") find hyperlinks. Based on title attribute we can distingue direct MeSH terms beetween mapped terms.

    def unknown_starttag(self, tag, attrs): 
        if self.foundMeSH and tag=='a' and len(attrs) > 2 and attrs[0][0] == 'name' and attrs[0][1] == 'gomesh':
    #        print attrs
            self.nextLink = attrs[1][1]
            if attrs[2][1] == 'MeSH Heading':
                self.next = 1
            elif attrs[2][1] == 'MeSH Substance Name':
                self.next = 2


    def handle_data(self, text):
        text = text.strip()
        if text == '':
            return
        
        # print text
        
        if self.next == 1:
            self.directTerms.append(text)
            self.next = 0
        elif self.next == 2:
            self.indirectTerms.append((text,self.nextLink))
            self.next = 0

        if text == "Drug and Chemical Info:":
            self.foundMeSH = True
        elif (text == "Pharmacological Action" or text == "Classification" or text == "PubMed via MeSH" or text == "PubMed MeSH Keyword Summary"):
            self.foundMeSH = False


"""  
        if text == 'Medical Subject Annotations:' or text == 'PubMed MeSH Keyword Summary':
            self.foundMeSH = True
            self.current_term = ''
            self.nextLink = ''
            self.nextIsTerm = 0

        if self.foundMeSH and (text == 'PubMed via MeSH' or text == 'Pharmacological Action:'):
            self.foundMeSH = False
            self.nextIsTerm = 3
            self.indirectTerms.append((self.current_term, self.nextLink))

        elif self.nextIsTerm == 1:
            self.current_term = text
            self.nextIsTerm = 2 # term waiting to be saved

        elif text == 'Hide MeSH Tree Structure':
            self.foundMeSH = False
            self.directTerms.append(self.current_term)
            self.nextIsTerm = 3 """
            

#load data
#reference_data = orange.ExampleTable("data/D06-reference.tab")
#cluster_data = orange.ExampleTable("data/D06-cluster.tab")

#testing code
#t = MeshBrowser()
#res = t.findEnrichedTerms(reference_data,cluster_data,0.02)
#print res
#t.downloadOntology()
#res = t.findEnrichedTerms(reference_data,cluster_data,0.02)