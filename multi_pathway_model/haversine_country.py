import argparse
import logging
import os
from os import listdir
from evaluate_probs import seasonInd2Int
import math
import pandas as pd
import pdb
import numpy as np
from fill_data_ca import haversine, load_object
#from plot_ca import cumulate

COORD_FILE="../obj/ca_mapspam_pop.csv"
HIST_STEP = 200.0
MIN_DISTANCE = 100000

def seed_distance(cell_coord_df,seed_df,cell):
   min_distance=MIN_DISTANCE
   cell_coord=(cell_coord_df.loc[cell]['lat'],cell_coord_df.loc[cell]['lon'])
   for index, value in seed_df.iterrows():
      seed_coord=(cell_coord_df.loc[value[0]]['lat'],cell_coord_df.loc[value[0]]['lon'])
      min_distance = min(haversine(seed_coord,cell_coord),min_distance)

   return min_distance

def cumulate(csvfile, time, start):
    df = pd.read_csv(csvfile, header=0, index_col = 'cell_id')
    for index, item in df.iterrows():
       prob_list = [item[str(j)] for j in range(start, time+1)]
       cumulated_sum = sum(prob_list)
       df.at[index, str(time)] = cumulated_sum
    return df

def create_file(country, seed_file, csv_file, time):

    parList=os.path.basename(csv_file).split('_')
    seasonInd=seasonInd2Int(parList[1])
    beta=float(parList[2][1:])
    kappa=int(parList[3][1:])
    seed=int(parList[4][1:])
    start_month=int(parList[5][2:])
    moore=int(parList[6][1:])
    suit_thresh=float(parList[7][2:])
    exp_delay=int(parList[8][2:])
    alphas=parList[9].rstrip('.csv').split('-')
    alpha_sd=float(alphas[1])
    alpha_fm=float(alphas[2])
    alpha_ld=float(alphas[3])

    prob_str = 'probability'
    simulation = cumulate(csv_file, time, start_month)
    output_dict = {}
    
    # load seed file
    seed_df = pd.read_csv(seed_file, skiprows=[0], header=None, names=['cell_id','adc_id','country'])
    # load coordinates file
    coord_df = pd.read_csv(COORD_FILE, index_col = 'cell id')

    for index, row in simulation.iterrows():
       try:
          if country not in coord_df.loc[index]['admin_id']:
             continue
       except KeyError:
          logging.warning("Index %d not in coordinates file." %index)
          continue

       # find distance from nearest seed cell
       sd=seed_distance(coord_df,seed_df,index)
       binned_value = math.ceil(sd/HIST_STEP)*HIST_STEP
       try:
           output_dict[binned_value] += row[str(time)]
       except:
           output_dict[binned_value] = row[str(time)]

    for key, value in output_dict.items():
        # AA: use below line for obtaining number of cells
        # print "%d,%d" %(key,value)
        print "INSERT INTO dist_inf_country (country,season_ind,beta,kappa,seed,start_month,moore,suit_thresh,latency_period,alpha_sd,alpha_fm,alpha_ld,distance,time,cumprob) VALUES ('%s',%d,%g,%g,%d,%d,%d,%g,%d,%g,%g,%g,%d,%g,%g);" %(\
            country,\
            seasonInd,\
            beta,\
            kappa,\
            seed,\
            start_month,\
            moore,\
            suit_thresh,\
            exp_delay,\
            alpha_sd,\
            alpha_fm,\
            alpha_ld,\
            key,\
            time,\
            value)

if __name__ == "__main__":
    parser=argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("sim_file",help="Simulation file",type=str)
    parser.add_argument("time", help ="Time for which probabilities need to be calculated", type=int)
    parser.add_argument("country")
    parser.add_argument("seed_file")
    args = parser.parse_args()

    create_file(args.country, args.seed_file, args.sim_file, args.time)
