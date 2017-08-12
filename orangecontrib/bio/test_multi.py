from orangecontrib.bio.ppi import *
import networkx as nx
import time
import multiprocessing as mp

num_cores = mp.cpu_count()
print(num_cores)

start = time.clock()
string = STRING('4896')
print(time.clock()-start)

start = time.clock()
network = string.extract_network('4896')
print(time.clock()-start)

def shortest_path_length(G,source):
    seen={}                  # level (number of hops) when seen in BFS
    level=0                  # the current level
    nextlevel={source:1}  # dict of nodes to check at next level
    while nextlevel:
        thislevel=nextlevel  # advance to next level
        nextlevel={}         # and start a new list (fringe)
        for v in thislevel:
            if v not in seen:
                seen[v]=level # set the level of vertex v
                nextlevel.update(G[v]) # add neighbors of v
        level=level+1
    return seen  # return all path lengths as dictionary


def worker(G, sources, return_dict):
    for n in sources:
        return_dict[n] = shortest_path_length(G, n)


# start = time.clock()
# pool = mp.Pool(processes=num_cores)
# results = [pool.apply_async(shortest_path_length, args=(network, n)) for n in network]
# output = [p.get() for p in results]
# print(time.clock()-start)

# start = time.clock()
# dist_matrix = [shortest_path_length(network, n) for n in network]
# print(time.clock()-start)

def chunkIt(seq, num):
  avg = len(seq) / float(num)
  out = []
  last = 0.0

  while last < len(seq):
    out.append(seq[int(last):int(last + avg)])
    last += avg

  return out

print()
start = time.clock()
manager = mp.Manager()
return_dict = manager.dict()
jobs = []
for c in chunkIt(network.nodes(), num_cores):
    j = mp.Process(target=worker, args=(network, c, return_dict))
    jobs.append(j)
    j.start()

for j in jobs:
    j.join()
print(return_dict)
print(time.clock()-start)
