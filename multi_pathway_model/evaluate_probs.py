import csv
from os import listdir
import math
import pandas as pd
import argparse
import pdb
import sys
import os
import numpy as np

UNCERTAINTY_PERIOD = 1
DATA_FILE = "../data/reporting_times.csv"
#DATA_FILE = "../obj/random_reports1.csv"

def seasonInd2Int(seasonInd):
   if seasonInd=="precip1":
      return 2
   elif seasonInd=="uniform":
      return 1
   elif seasonInd=="precip1-20-100":
      return 3
   elif seasonInd=="precip1-out-50":
      return 4
   elif seasonInd=="precip1-out-100":
      return 5
   else:
      print "ERROR: undefined season indicator %s" %seasonInd
      sys.exit(1)

def cumulate(csvfile):
    df = pd.read_csv(csvfile, header=0, index_col = 'cell_id')
    for index, item in df.iterrows():
       for i in range(len(item)):
	  try: item[str(i)]
	  except: 
	     item[str(i)] = 0
	     print df
	  prob_list = [item[str(j)] for j in range(i+1)]
	  #except: continue
	  cumulated_sum = sum(prob_list)
	  df.at[index, str(i)] = cumulated_sum 
          #prob_list = [1-item[j] for j in range(i+1)]
          #prob = 1-np.prod(prob_list) 
          #item[i] = prob
	  
    return df

def evaluate_probs(simFile, timeWindow,spatialWindow):
   sim_output = pd.read_csv(simFile, header=0, index_col = 'cell_id')
   ground_data = pd.read_csv(DATA_FILE)

   parList=os.path.basename(simFile).split('_')
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

   likelihood=0
   for_not_inf_sum = {}
   for_inf_sum = {}

   # keeping track of deficit in infection probability
   deficit_inf_prob=len(ground_data.cell_id.unique())
   relative_time=0

   # reset accumulation probabilities
   for loc in ground_data.cell_id.unique():
      for_inf_sum[loc]=0
      for_not_inf_sum[loc]=0

   for i in sim_output.columns.values:
      timeStep=int(i)

      # accumulate probabilities for spatial window
      for index, row in ground_data.iterrows():
         # check if inside spatial window
         if row['range']>spatialWindow:
            continue

         # get probability
         try: 
            prob = sim_output.loc[row['moore']][i]
            deficit_inf_prob-=prob
         except: 
            continue
         
         # check if inside time window for infection
         if timeStep>=row['month']-timeWindow and timeStep<=row['month']+timeWindow:
         #if timeStep>=row['month']-timeWindow and timeStep<=row['month']:
            for_inf_sum[row['cell_id']]+=prob
            #for_not_inf_sum[row['cell_id']]=0
         else:
            for_not_inf_sum[row['cell_id']]+=prob
            #for_inf_sum[row['cell_id']]=0

         if timeStep<row['month']:
            relative_time-=prob
         elif timeStep>row['month']:
            relative_time+=prob

   # add likelihood for current time step
   # print for_inf_sum, for_not_inf_sum
   for loc in ground_data.cell_id.unique():
      likelihood+=for_inf_sum[loc] + 1-for_not_inf_sum[loc]
   likelihood-=deficit_inf_prob
   likelihood/=2.0
   relative_time+=deficit_inf_prob

         ## # check if inside time window for infection
         ## if timeStep >= row['month']-timeWindow-1 and timeStep< row['month']+timeWindow:
         ##    # if yes then accumulate for prob of infection
         ##    try: 
         ##       for_inf_sum[index]*=1-prob
         ##    except: 
         ##       for_inf_sum[index]=1-prob
         ## else:
         ##    # if no then accumulate for prob of susceptibility
         ##    try: 
         ##       for_not_inf_sum[index]*=1-prob
         ##    except: 
         ##       for_not_inf_sum[index]=1-prob
   ## # accumulate for every index
   ## likelihood = 0
   ## for ind in for_inf_sum:
   ##    likelihood += 1-value
   ## total_sum = likelihood + non_inf_sum
   print "INSERT INTO eval_BGD (season_ind,beta,kappa,seed,start_month,moore,suit_thresh,latency_period,alpha_sd,alpha_fm,alpha_ld,time_window,likelihood,relative_time) VALUES (%d,%g,%g,%d,%d,%d,%g,%d,%g,%g,%g,%d,%g,%g);" %(seasonInd,\
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
            timeWindow,\
            likelihood,\
            relative_time)
   #return total_sum

def expected_infections(simFile, time,threshold):
   parList=os.path.basename(simFile).split('_')
   seasonInd=seasonInd2Int(parList[1][1:])
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

   sim_output = pd.read_csv(simFile, header=0,index_col='cell_id') 
   #expected_value = 0
   numCellsAboveThresh=0
   for index, row in sim_output.iterrows():
      #expected_value += row[str(time)]
      cumProb=row[str(time)]
      for i in range(time):
         try:   # So that we don't have to track start month
            #expected_value += row[str(i)]
            cumProb += row[str(i)]
         except:
            continue
      if cumProb>=threshold:
          numCellsAboveThresh+=1

   print "INSERT INTO exp_inf (season_ind,beta,kappa,seed,start_month,moore,suit_thresh,latency_period,alpha_sd,alpha_fm,alpha_ld,time,threshold,num_cells) VALUES (%d,%g,%g,%d,%d,%d,%g,%d,%g,%g,%g,%d,%g,%g);" %(seasonInd,\
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
            time,\
            threshold,\
            numCellsAboveThresh)

def evaluate_tonnang(simFile,timeWindow, spatialWindow):
   sim_output = pd.read_csv(simFile, header=0,index_col='cell_id')
   ground_data = pd.read_csv(DATA_FILE)
   non_inf_sum = 0.0
   inf_sum = {}
   relative_time = 0
   for index, row in ground_data.iterrows():
      if row['range'] != 0:
         continue
      try: inf_sum[row['moore']]
      except: inf_sum[row['moore']] = 1
      time = sim_output.get_value(int(row['moore']),'time')
      if time < row['month']:
         relative_time -= 1
      elif time > row['month']:
         relative_time += 1

      try: int(time)
      except:
         time = time[0]
      print time
      if time in range(int(row['month']-timeWindow - 1), int(row['month']+timeWindow)):
         inf_sum[row['moore']] *= 0
	 print 'in'
      elif time == -1:
         non_inf_sum += 1
	 print 'nin'
   sum = 0
   for i, value in inf_sum.items():
      sum += 1 - value
   total_sum = sum + non_inf_sum
   print "INSERT INTO eval_BGD (season_ind,beta,kappa,start_month,moore,suit_thresh,latency_period,alpha_sd,alpha_fm,alpha_ld,time_window,likelihood,relative_time) VALUES (%d,%g,%g,%d,%d,%g,%d,%g,%g,%g,%d,%g,%g);" %(seasonInd,\
            beta,\
            kappa,\
            start_month,\
            moore,\
            suit_thresh,\
            exp_delay,\
            alpha_sd,\
            alpha_fm,\
            alpha_ld,\
            timeWindow,\
            likelihood,\
            relative_time)

   #return total_sum

if __name__ == "__main__":
    # read in arguments
    parser=argparse.ArgumentParser(
    formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("input_sim_file", help="a simulation output directory")
    parser.add_argument("-t","--time_window", default=0,type=float,help="Uncertainty window in months")
    parser.add_argument('-s','--spatial_window',default = 0,type=int,help="Spatial window to consider")
    parser.add_argument('--threshold',default = 0,type=float,help="threshold probability")
    #parser.add_argument('-s','--timesteps',default = 16, type = int, help="Total timesteps")
    parser.add_argument('--tonnang', action='store_true')
    parser.add_argument('--spread', action='store_true')
    parser.add_argument('--time', default=6, type=int, help="Time to look at the expected cells infected")
    args=parser.parse_args()

    if args.tonnang:
        evaluate_tonnang(args.input_sim_file, args.time_window, args.spatial_window)
    elif args.spread:
        expected_infections(args.input_sim_file, args.time,args.threshold)
    else:
        evaluate_probs(args.input_sim_file,args.time_window,args.spatial_window)


