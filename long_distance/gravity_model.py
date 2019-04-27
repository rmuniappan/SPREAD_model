import networkx as nx
import argparse
import math
import time
import sys
import pprint as pp
import numpy as np
import pandas as pd
import logging
import pdb

INFINITY=100000000000
DESC="""Generates a flow network through gravity model.
This is version 2. It assumes that all pairs of distances are given.
Therefore, computation of shortest path length was removed. Also, commented
out is network version of the output file.

AA 4/12/18:
   - Assigned infinity to pairs without distance
   - Capability to deal with more than one connected component in the
   distance network
"""

def gravityFlows(G,beta,kappa,tolerance,frictionDistance,flowFile):
    nodelist = sorted(G.nodes())

    net_in = sum([G.node[x]['inflow'] for x in nodelist])
    net_out = sum([G.node[x]['outflow'] for x in nodelist])

    if net_in != net_out:
        ratio = net_out/net_in
        for x in nodelist:
            G.node[x]['inflow'] *=ratio

    dist_func = {}
    for i in nodelist:
        dist_func[i]={}
        for j in nodelist:
            if i==j:
                d=0
            else:
                try:
                  d=G[i][j]['weight']
                except:
                  d=INFINITY

            dist_func[i][j]=compute_dist_func(d,beta,kappa,frictionDistance)

    #Initialize correction factors
    for x in nodelist:
        G.node[x]['b'] = np.random.random()
    flow = {}
    for i in nodelist:
        flow[i]={}
        for j in nodelist:
            flow[i][j]=0.0
    netflow=0

    #Flow computation
    c = 0
    while True:
        c+=1
        for i in nodelist:
            sumterm = 0
            for j in nodelist:
                sumterm += G.node[j]['b']*G.node[j]['inflow']*dist_func[i][j]
            G.node[i]['a'] = 1.0/sumterm
        #print [G.node[x]['a'] for x in nodelist]

        for j in nodelist:
            sumterm = 0
            for i in nodelist:
                sumterm += G.node[i]['a']*G.node[i]['outflow']*dist_func[i][j]
            G.node[j]['b'] = 1.0/sumterm

        for i in nodelist:
            flow[i]={}
            for j in nodelist:
                flow[i][j]=G.node[i]['a']*G.node[j]['b']*G.node[i]['outflow']*G.node[j]['inflow']*dist_func[i][j]
                if i=='Rangpur' and j=='Jakarta':
                   print G.node[i]['a'],G.node[j]['b'],flow[i][j]

        netflow=0
        for x in nodelist:
            netflow+=sum(flow[x].values())

        obj_fn = sum([abs(sum([flow[x][y] for x in nodelist])-G.node[y]['inflow']) for y in nodelist]) \
                 + sum([abs(sum(flow[x].values())-G.node[x]['outflow']) for x in nodelist])

        if obj_fn < tolerance:
            break

    for i in nodelist:
        for j in nodelist:
            if flow[i][j]<tolerance:
                continue
            flowFile.write('{},{},{}\n'.format(i,j,flow[i][j]))
    return

def compute_dist_func(d,beta,kappa,fd):
    if d == 0:
        d = fd
    if kappa == 0:
        return 0
    else:
        try:
            return d**(-beta)*math.exp(-d/kappa)
        except ZeroDivisionError:
            print "WARNING: Infinity used"
            return INFINITY

##############################

def main():
    ap = argparse.ArgumentParser(description=DESC)

    ap.add_argument('node_attributes',action="store",help='csv file <node,prod,consumption>')
    ap.add_argument('distance_network',action="store",help='csv file <node1,node2,time taken/distance>')
    # ap.add_argument('edge_scale_file',action="store",help='csv file <node1,node2,weight')
    ap.add_argument('-b','--beta',action="store",type=float,default=2,help='distance exponent')
    ap.add_argument('-k','--kappa',action="store",type=float,default=1000,help='Cut off')
    ap.add_argument('-f','--friction_distance',action="store",type=float,default=1e-2,help='Friction distance')
    ap.add_argument('-t','--tolerance',action="store",type=float,default=1e-2,help='Tolerance')
    ap.add_argument('-o','--output_file',action="store",default='out.csv',help='Prefix for output files.')

    ap.add_argument('--seed',action="store_true",help='random number seed for test purposes')
    ap.add_argument('--seed_value',action="store",default=12345,type=int,help='random number value for seed')
    args = ap.parse_args()

    if args.seed:
        np.random.seed(seed=args.seed_value)

    # Read distance network
    G = nx.read_weighted_edgelist(args.distance_network, delimiter=',')
    ### To remove all isolated nodes from the NetworkFile
    G.remove_nodes_from(nx.isolates(G))

    ## # Read edge scale file
    ## Ge = nx.read_weighted_edgelist(args.edge_scale_file, delimiter=',')
    ## ### To remove all isolated nodes from the NetworkFile
    ## G.remove_nodes_from(nx.isolates(G))

    # checking for connected components
    connComp=nx.connected_components(G)

    # read node attributes
    with open(args.node_attributes,'r') as f:
        f.readline()
        attribList=[]
        for line in f:
            x,I_x,O_x = line.strip().split(',')
            if x not in G.nodes():
               logging.warning("'%s' not in distance network. Skipping ..." %x)
               continue
            G.node[x]['outflow'] = float(O_x)
            G.node[x]['inflow'] = float(I_x)
            attribList.append(x)
    nodesAbsentInAttribList=set(G.nodes()).difference(set(attribList))
    for i in nodesAbsentInAttribList:
       logging.warning("'%s' not in attributes list. Removing from network ..." %i)
       G.remove_node(i)

    # prepare each component
    with open(args.output_file,'w') as fflow:
        i=1
        for comp in connComp:
           logging.info("Component %d" %i)
           i+=1
           H=G.subgraph(comp)
           gravityFlows(H,args.beta,args.kappa,args.tolerance,args.friction_distance,fflow)

###############################
if __name__ == "__main__":
    main()
