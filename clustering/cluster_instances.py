###########################################################################
# Given two clusters, finds sample average and mean of distances of two
# vectors, one from each list.
# Created: AA 2019-01-28
# tags: numpy argparse sys pandas pyclustering xmeans csv
###########################################################################
import numpy as np
import pdb
import argparse
import pandas as pd
import logging
import time
from pyclustering.cluster.xmeans import xmeans
from pyclustering.cluster.kmeans import kmeans
from pyclustering.cluster.agglomerative import agglomerative
from pyclustering.cluster.agglomerative import type_link
from pyclustering.cluster.center_initializer import kmeans_plusplus_initializer
from pyclustering.utils.metric import euclidean_distance
INFINITY=1000000

#SIM_FILE="../obj/cell_rank_BD_model_params.csv"
#SIM_FILE="../obj/expected_time_BD.csv"
SIM_FILE="../obj/infection_vector_BD.csv"
CELL_START_IND=11
START_NUM_CENTERS=2
KMAX=20
DESC="""Clustering simulation output using different algorithms. The
distance metric is Euclidean."""

def clusterSimulationData(algo,simulationData,k):
    # Prepare data (clipping to remove model parameters)
    selectedColumns=simulationData.columns.tolist()[CELL_START_IND:]
    simulationData=simulationData.loc[:,selectedColumns]

    logging.info("Clustering (%s) ..." %algo)
    start=time.time()

    # Cluster
    if algo=="xmeans":
        ## initialization
        initialCenters = kmeans_plusplus_initializer(simulationData.values.tolist(),START_NUM_CENTERS).initialize()
        clusterInstance = xmeans(simulationData.values.tolist(),tolerance=.00001,initial_centers=initialCenters,kmax=k)
    elif algo=="kmeans":
        ## initialization
        initialCenters = kmeans_plusplus_initializer(simulationData.values.tolist(),k).initialize()
        clusterInstance = kmeans(simulationData.values.tolist(),tolerance=.00001,initial_centers=initialCenters)
    elif algo=="agglomerative":
        clusterInstance = agglomerative(simulationData.values.tolist(),k,link=type_link.CENTROID_LINK)

    ## cluster
    clusterInstance.process()
    clusters = clusterInstance.get_clusters()

    assignedClusters=np.zeros(simulationData.shape[0],dtype=int)
    clusterIndex=1
    for cluster in clusters:
        for cell in cluster:
            assignedClusters[cell]=clusterIndex 
        clusterIndex+=1

    # check if every vector belongs to a cluster
    if np.any(assignedClusters==0):
        logging.warning("At least one object does not belong to any cluster.")

    logging.info("done. %g minutes" %((time.time()-start)/60))

    # compute minimum distance between centers
    centroids = clusterInstance.get_centers()
    minDist=INFINITY
    for c1 in centroids:
        for c2 in centroids:
            if c1==c2:
                continue
            dist=euclidean_distance(c1,c2)
            if dist < minDist:
                minDist=dist

    return assignedClusters,len(clusters),minDist

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=DESC,
    formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("-a","--algorithm",default="xmeans",help="xmeans/kmeans/agglomerative",action="store")
    parser.add_argument("-k","--num_of_clusters",type=int,default=KMAX,help="max. number of clusters",action="store")
    parser.add_argument("-o","--output_file",default="clusters.csv",help="output file of cluster assignments",action="store")

    args=parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    # read simulation outputs
    simData = pd.read_csv(SIM_FILE)
    #simData = simData.sample(100)

    # filter
    # simData=simData[(simData["start_month"]==5) & (simData["seed"]==0)]
    logging.info("Shape of data:")
    logging.info(simData.shape)

    # cluster
    [clusters,numClusters,minDist]=clusterSimulationData(args.algorithm,simData,args.num_of_clusters)

    # write outputt
    selectedColumns=simData.columns.tolist()[:CELL_START_IND]
    simData=simData.loc[:,selectedColumns]
    simData["cluster"]=np.asarray(clusters)
    
    simData.to_csv(args.output_file,index=False,float_format="%g")
    logging.info("(Number of clusters,Minimum distance between centroids): %d,%g" %(numClusters,minDist))
