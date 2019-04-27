# tags: argparse pandas csv pandas python map
import argparse
import pandas as pd
import pdb
import os

DESC="""description: 
This function does the following given a simulation output file (format
given below). In each case, a different output file is generated.
1. Computes expected time of infection for each cell.
2. Sorts cells in ascending order by their expected time of infection.
3. Concatenates infection probabilities into one vector ordered by cell id.
In addition, it can also filter cells by country/region and output a subset
of relevant cells.
"""
## TYPE="""sort: 1st output type (as mentioned in description).
## expected_time: 2nd output type.
## """
CELL_COUNTRY_MAP="../../cellular_automata/obj/ca_mapspam_pop.csv"

def filterCells(filename,countryFilter="",monitoredCellsFilter=False):
    """
    Filters cells based on constraints. This is where cells corresponding
    to a country can be selected.
    """

    ### read simulation output file
    infectionTimeline = pd.read_csv(filename,index_col="cell_id")

    ### apply country filter
    if countryFilter != "":
        cellCountryMap=pd.read_csv(CELL_COUNTRY_MAP,index_col="cell id")
        cellCountryMap=cellCountryMap[cellCountryMap['admin_id'].str.contains(countryFilter)] 
        infectionTimeline=infectionTimeline[infectionTimeline.index.isin(cellCountryMap.index)]
        
    ### apply monitored cells filter
    return infectionTimeline

def sortByInfected(infectionTimeline):

    ### add an extra time step to account for probability that a cell is
    ### not infected within the time interval. The value is the residual
    ### probability.
    timeSteps=map(int,infectionTimeline.columns.values.tolist())
    timeSteps+=[timeSteps[-1]+1]
    infectionTimeline['%d' %(timeSteps[-1])]=1-infectionTimeline.sum(axis=1)

    ### expected time
    expectedTimes=infectionTimeline.dot(timeSteps).to_frame()
    expectedTimes.columns=['t']

    ### sort
    sortedCells=expectedTimes.sort_values(by=['t'])

    ### concat
    dim=infectionTimeline.shape
    timelineVec=infectionTimeline.sort_index().values.reshape((1,dim[0]*dim[1]))[0]

    return expectedTimes.sort_index(), sortedCells.index.tolist(), timelineVec

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=DESC,
    formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("input_sim_file",help="simulation file: <cell_id,t1,t2,...> where each column ti contains the empirical probability of infection at ti.")
    #parser.add_argument("-m","--mode",help=TYPE,default="sort")
    parser.add_argument("-o","--out_prefix",default="out",help="output file name prefix: <prefix>_time.csv and <prefix>_sorted.csv ")
    parser.add_argument("-c","--country_filter",default="", help= \
"""This can be used to choose cells of a particular country or region. It is
specified by the code or its prefix in the This can be used to choose
cells of a particular country or region. It is specified by the code or
its prefix in the admin_id\"admin_id\" field of %s.""" %CELL_COUNTRY_MAP)
    #parser.add_argument("--step", default=0, type=float)

    args=parser.parse_args()
    selectedCells=filterCells(args.input_sim_file,args.country_filter)
    [expectedTimes,sortedCells,infVec]=sortByInfected(selectedCells)
    
    # expected times file
    with open(args.out_prefix+"_time.csv",'w') as f:
        f.write("instance")
        for i in expectedTimes.index.tolist():
            f.write(",%d" %i)
        f.write("\n")
        f.write(os.path.basename(args.input_sim_file).lstrip("res_").rstrip(".csv")) # This step should ideally come as input.
        for e in expectedTimes["t"].tolist():
            f.write(",%g" %e)
        f.write("\n")

    # sorted cells file
    with open(args.out_prefix+"_sorted.csv",'w') as f:
        f.write(os.path.basename(args.input_sim_file).lstrip("res_").rstrip(".csv")) # This step should ideally come as input.
        for e in sortedCells:
            f.write(",%d" %e)
        f.write("\n")

    # infection vector file
    with open(args.out_prefix+"_infvec.csv",'w') as f:
        f.write(os.path.basename(args.input_sim_file).lstrip("res_").rstrip(".csv").replace('_',',').replace('-',',').replace('a,','')) # This step should ideally come as input.
        for e in infVec:
            f.write(",%g" %e)
        f.write("\n")
