import os
import numpy as np
import math
import pdb
import sys
import copy
import time
import argparse
import logging
import pickle
from random import *

from cellular_automata import Cell, CA
from shutil import rmtree
import pandas as pd
try:
   import shapefile as shp
   import matplotlib.pyplot as plt
   from matplotlib.patches import Rectangle
except:
   pass
from create_ca import load_object, dump_object
from fill_data_ca import get_cities, create_locality
from evaluate_output import evaluate

# hardcoded stuff
NDVI_THRESH=.3
KEY = pd.read_csv('../data/lut_cell_orig.txt', delimiter = '\t', index_col = 'CELL5M', usecols = ['ISO3','CELL5M','X','Y','Name'],header = 0)
KEY2 = 'country_key.csv'

#SEED_FILE='../data/seed_Sarawak.csv'
SHAPEFILE = '../data/world_grid_1_degree_clipped_by_countries_adcw72/world_grid_1_degree_clipped_by_countries_adcw72.shp'
GRID_ADC_ID_MAP='../data/south_east_asia_adc_id_p25xp25.csv'
PROD_FILE = '../data/crop_harvest_area.csv'
city_to_grid_file = '../data/city_grid_map.csv'


def natural_diffusion(cell, time, probs):
    # JM: A short distance function that simply takes probability of state transitions
    s_to_e = probs[0]
    e_to_i = probs[1]
    if cell.state == 'S':
        for neighbor in cell.neighbors:
	    if neighbor.state == 'I' and random() < s_to_e:
	        cell.state = 'E'
    elif cell.state == 'E':
	if random() < e_to_i:
	    cell.state = 'I'

def update_ca_plus(ca, index, cell, loc_data, moore_nbd, time, par_sd, par_vor, par_ld_out, ndvi_t, prod_t): 
    if cell.state == 'I':
	return 'I'
    elif cell.state == 'E':
	return 'I'
    elif cell.state == 'S':
	sums, F = infectivity(ca, index, cell, loc_data, time, moore_nbd)
	if sums['sd'] > 0:
	    state = short_distance(cell, time, par_sd, sums['sd'], prod_t)
	    if state == 'E':
		return 'E'
	if sums['fm'] > 0:
	    state = farm_to_market(cell, time, par_vor, sums['fm'][0], prod_t)
	    if state == 'E':
		return 'E'
	if sums['mm'] > 0:
	    state = market_to_market(cell, time, par_ld_out, sums['mm'], prod_t, F)
	    if state == 'E':
		return 'E'
	    else:
		return cell.state

def short_distance(cell, time, par, sum, prod_t):
    p = par * suitability(cell.production['vege'], prod_t) * (1-math.exp(-sum))
    if random() < p:
        return 'E'
    else:
	return cell.state


def farm_to_market(cell, time, par, sum, prod_t):
    p = par * suitability(cell.production['vege'], prod_t) * (1-math.exp(-sum))
    if random() < p:
        return 'E'
    else:
        return cell.state

def market_to_market(cell, time, par, sum, prod_t, F):
    p = par * suitability(cell.production['vege'], prod_t) * (F*(1-math.exp(-sum)))
    if random() < p:
        return 'E'
    else:
        return cell.state


def suitability(value, threshold):
    if value >= threshold:
	return 1
    else:
	return 0

def infectivity(ca, index, cell, loc_data, time, moore_nbd):
    sum = {'sd' : 0, 'fm' : 0, 'mm' : 0}
    F = 0

    ## JM: here it is short distance
    for nb in cell.neighbors:
	vor_cells = 0
	if type(nb) == int:
	    continue
	
	nb_id = nb[0]
	neighbor = ca.cells[nb_id]
	if nb[1] > moore_nbd or neighbor.state != 'I':
	    continue
	
	sum['sd'] += 1
    
    ## JM: now it is farm to market
    try: city = ca.localities[index]
    except: return sum, F
    if type(city) == int:
        sum['fm'] = loc_data[city]
    else:
	sum['fm'] = loc_data[index]	

    ### JM: and here it is market to market
    for key, value in ca.network.iteritems():
	print key
	print value
	if ca.localities[index] == key[1]:
            F += F_ij(ca, key[0], cell, ca.cells[key[0]])
	try: ca.localities[key[1]]
	except: continue

	for cell_id in ca.localities[key[1]]:
	    if ca.cells[cell_id].state == 'I':
		sum['mm'] += 1
    return sum, F

def F_ij(ca, nb_id, source, destination):
    beta = 1
    kappa = 1
    a_i = 1
    b_j = 1
    exports = 0
    imports = 0
    processing = 0
    O_i = source.production['vege'] + exports
    I_j = destination.population + imports + processing
    try: value = a_i * b_j * O_i * I_j * f(destination.weights[nb_id][3], beta, kappa)
    except: value = 0    
    return value


def f(distance, beta, kappa):
    return distance ** (-beta) * math.exp(-distance/kappa)

def update_ca_guimapi(cell,time,temp_t,humidity_t,ndvi_t1,ndvi_t2,prod_t):
    
    # JM: Function based on Guimapi paper

    if cell.state == 'I':
	return
    if cell.ndvi[time] >= ndvi_t1:
	if cell.temperature[time] >= temp_t and cell.humidity[time] >= humidity_t:
	    cell.state = 'I'
	    return
	else:
	    cell.state = 'E'
	    return
    # JM: Below on production, the production will need to be changed. From Guimapi parameters, each country fulfills the required threshold
    elif cell.ndvi[time] >= ndvi_t2: # and cell.production['yield'] >= prod_t:
	cell.state = 'I'
	return
	    

def update_ca1(cell,time,temp_t,humidity_t,ndvi_t):
    """
    deterministic SI based on NDVI
    """

    if cell.state == 'I': # if invaded, do nothing
        return
    

    if cell.ndvi[time]>=ndvi_t and cell.ndvi[time]<=1:
        cell.state = 'I'

def update_ca2(cell,time,temp_t,humidity_t,ndvi_t,prod_t):
    """
    ca1 + production
    """
 
    wheat = cell.production.get('wheat')
    rice = cell.production.get('rice')
    maize = cell.production.get('maize')
    sugarcane = cell.production.get('sugarcane')
    sorghum = cell.production.get('sorghum')
    tomato = cell.production.get('vege')


    if cell.state == 'I': # if invaded, do nothing: SI part
        return

    #if tomato > prod_t:
	cell.state= 'I'

    if cell.ndvi[time]>=ndvi_t and cell.ndvi[time]<=1 and tomato > prod_t:
        cell.state = 'I'
    #if cell.ndvi[time] > NDVI_THRESH and cell.ndvi[time]<=1:
    #    cell.state = 'I'

def update_ca3(cell,time,temp_t,humidity_t,ndvi_t,prod_t):
    """
    ca2 with SIS model
    """
 
    wheat = cell.production.get('wheat')
    rice = cell.production.get('rice')
    maize = cell.production.get('maize')
    sugarcane = cell.production.get('sugarcane')
    sorghum = cell.production.get('sorghum')

    if cell.ndvi[time]>=ndvi_t and (wheat > prod_t or rice > prod_t or maize > prod_t or sugarcane > prod_t or sorghum > prod_t):
        cell.state = 'I'
    else:
        cell.state = 'S' # SIS part

def update_ca4(cell,time,temp_t,humidity_t,ndvi_t,prod_t):
    """
    NEVER USED
    """

    wheat = cell.production.get('wheat')
    rice = cell.production.get('rice')
    maize = cell.production.get('maize')
    sugarcane = cell.production.get('sugarcane')
    sorghum = cell.production.get('sorghum')

    if cell.state == 'I': # if invaded, do nothing
        return

    if cell.ndvi[time]>=ndvi_t and (wheat+rice+maize+sugarcane+sorghum > prod_t):
        cell.state = 'I'


def create_region_grid_map(csvfile=GRID_ADC_ID_MAP):
    df = pd.read_csv(csvfile)
    region_to_grid = {}
    grid_to_region = {}
    for index, row in df.iterrows():
        region_id = row['adc_id']
        cell_id = row['#cell_id']
        try:
            region_to_grid[region_id].append(cell_id)
            grid_to_region[cell_id].append(region_id)
        except:
            region_to_grid[region_id]=[cell_id]
            grid_to_region[cell_id]=[region_id]
    return region_to_grid,grid_to_region

def create_country_grid_map(csvfile='../data/grid_country_map.csv'):
    df = pd.read_csv(csvfile)
    country_to_grid = dict()
    for index, row in df.iterrows():
        country_id = row['adc_id']
        cell_id = row['#cell_id']
        if not country_id in country_to_grid:
            country_to_grid[country_id] = [cell_id]
        else:
            country_to_grid[country_id].append(cell_id)
    return country_to_grid

def fill_localities(ca, month):
    loc_data_dict = {}
    vege_prod = 0
    vege_yield_total = 0
    infections = 0
    total = float(len(ca.localities))
    for key, value in ca.localities.iteritems():
	if type(value) == np.array:
	    for id in value:
		vege_prod += ca.cells[id].production['vege']
		vege_yield_total += ca.cells[id].production['yield']
		if ca.cells[id].state == 'I':
		    infections += 1
        loc_data_dict[key] = [vege_prod, vege_yield_total / total, infections / total]

    return loc_data_dict
		

def run_ca(ca, seed, step, output, grid_to_region, step_scale, moore_nbd, func_name, var_array):
    border = True
    possibles = globals().copy()
    possibles.update(locals())
    ca_func = possibles.get(func_name)

    start=1
    for s in seed:
       	ca.cell_dict[int(s)].state = 'I'
       	ca.cell_dict[int(s)].time = 0
    invaded = seed
    
    system_state = list()
    initial_state = record_output(ca)
    system_state.append(initial_state)
    simulationSteps=int(step/step_scale) # step is always in months

    for i in range(simulationSteps):
	
	print 'time: ' + str(i)
        time = int(i*step_scale)+1
        if time%12 == 0:
            month = 12
        else:
            month = time%12
	
	if func_name == 'update_ca_plus':
	    loc_data = fill_localities(ca,month)	    
	    invaded = []
	    exposed = []
	    for index, cell in ca.cells.items():
	        new_state = update_ca_plus(ca, index, cell, loc_data, moore_nbd, month-1, *var_array)
		if new_state == 'I' and cell.state != 'I':
		    invaded.append(index)
		elif new_state == 'E' and cell.state != 'E':
		    exposed.append(index)
	    
	    for index in invaded:
		ca.cell_dict[index].state = 'I'
		ca.cell_dict[index].time = time
	    for index in exposed:
		ca.cell_dict[index].state = 'E'
	    cur_state = record_output(ca)
	    system_state.append(cur_state)

	else:
            cur_invaded = copy.deepcopy(invaded)  
            for ci in cur_invaded:
                for i, nb in enumerate(ca.cell_dict[int(ci)].neighbors):
		    if type(nb) == int:
			continue
                    weights = ca.cell_dict[int(ci)].weights[nb]
	    	    ############################### This is where update ca is called
                    if nb[1]<= moore_nbd:
	    	        ca_func(ca.cell_dict[int(nb[0])],month-1,*var_array)
                        if ca.cell_dict[nb[0]].state == 'I' and nb[0] not in invaded:
                            invaded.append(nb[0])
                            ca.cell_dict[nb[0]].time=time
            cur_state = record_output(ca)
            system_state.append(cur_state)

    ## #read Grid to Adc, check the cells and change to adc, write to csv
    ## df = pd.read_csv(GRID_ADC_ID_MAP)
    ## new_df = pd.DataFrame(columns=['cell_id','adc_id','time'])  
    ## index=0
    ## cells = pd.DataFrame(columns=['cell_id','time'])
    #outFile=output+"output_" + str(moore_nbd) +"_"+str(int(100*ndvi_t))+"_"+str(prod_t)+"_"+str(step_scale)+".csv"

    
    with open(output,'w') as f:
       f.write('cell_id,adc_id,time\n')
       for index, cell in ca.cells.items():
          if index in grid_to_region:
	     for adc_id in grid_to_region[index]:
                f.write('%d,%d,%d\n' %(index,adc_id,cell.time))
    print output

    #plot_ca_heatmap(ca, step, output+"heatmap_"+str(moore_nbd)+"_"+str(int(100*ndvi_t))+"_"+str(prod_t)+"_"+str(step_scale)+".pdf")
             
	
	## cells.loc[index] = [cell.ID,cell.time] 
	# index+=1
	##     
   ##  new_df=df.loc[df['#cell_id'].isin(cells['cell_id'])]	    
   ##  new_df.reset_index(inplace=True)
   ##  #print new_df
   ##  times = pd.Series() 
   ##  for i in range(0,len(new_df)):
	## #times.append(cells.loc[cells['cell_id']==new_df.loc[i,'#cell_id'],'time'].iloc[0])
	## new_df.loc[i,'time']=cells.loc[cells['cell_id']==new_df.loc[i,'#cell_id'],'time'].iloc[0]
	## i += 1
   ##  #new_df.loc['time']=times
   ##  cells.to_csv(output + "cells.csv")
   ##  new_df = new_df[['#cell_id','adc_id','time']]
   ##  new_df.to_csv(output+"output_" + str(moore_nbd) +"_"+str(int(100*ndvi_t))+"_"+str(prod_t)+".csv")
   ##  dump_object('exp', system_state)


def gen_seed(ca, region_to_grid, seed_file):
    region_df = pd.read_csv(seed_file)
    #south_america_df = pd.read_csv('../data/south_american_countries.csv')
    #country_to_grid = create_country_grid_map()
    invaded_region = region_df['#cell_id']
    #south_america = south_america_df['adc_id']
    seeds = list()
    #print region_df
    for seed in invaded_region:
	seeds.append(seed)

    ## for r in invaded_region:
    ##     for seed in region_to_grid[r]:
    ##         seeds.append(seed)

    ## for sm in south_america:
    ##     for seed in country_to_grid[sm]:
    ##         seeds.append(seed)
    print seeds
    return seeds

def create_seed_file(grid_to_region,seed_file):
    df = pd.DataFrame(columns = ['#cell_id','adc_id','country'])
    # regions is list
    region_df = pd.read_csv(GRID_ADC_ID_MAP)
    for index, cell in region_df.iterrows():
	id = cell['#cell_id']
	country = cell['admin_name']
	if type(country) != str:
	    continue
	print country
	if country == 'MY-13':
	    adc_id = grid_to_region[id][0]
	    df = df.append({'#cell_id':id, 'adc_id':adc_id, 'country': str(cell['admin_name'])[:2]}, ignore_index = True)
    df.to_csv(seed_file, index = False)


## def plot_ca(ca=None, step=None, output='out.png'):
##     sf = shp.Reader(SHAPEFILE)
##     plt.figure(figsize=(15,15))
##     plt.axis('off')
##     records = sf.records()
##     
##     cell_in_s = list()
##     cell_in_e = list()
##     cell_in_i = list()
## 
##     for cell in ca.cells:
##         if cell.state == 'S':
##             cell_in_s.append(str(cell.ID))
##         elif cell.state == 'E':
##             cell_in_e.append(str(cell.ID))
##         elif cell.state == 'I':
##             cell_in_i.append(str(cell.ID))
## 
##     for index, shape in enumerate(sf.shapeRecords()):
##     #Name of the district
##         x = [i[0] for i in shape.shape.points[:]]
##         y = [i[1] for i in shape.shape.points[:]]
##         if str(records[index][1]) in cell_in_s:
##             plt.fill(x,y,alpha=0.3,color='k')
##         elif str(records[index][1]) in cell_in_e:
##             plt.fill(x,y,alpha=0.5,color= '#FFC0CB')
##         elif str(records[index][1]) in cell_in_i:
##             plt.fill(x,y,alpha=0.5,color='r')
## 	
##     plt.savefig(output)
## 
## def plot_ca_heatmap(ca=None, step=None, output=None):
##    sf = shp.Reader(SHAPEFILE)
##    fig1=plt.figure(figsize=(15,15))
##    plt.axis('off')
##    plt.tight_layout()
##    ax1=fig1.add_subplot(111)
##    records = sf.records()
##    ## cell_in={}
##    ## cell_in[0] = list()
##    ## for i in range(1,10):
##    ##    cell_in[i] = list()
## 
##    indexCellIDMap={}
##    for ind in xrange(len(ca.cells)):
##       indexCellIDMap[ca.cells[ind].ID]=ind
##       
##    colors = ['#D7301F','#EF6548','#FC8D59','#FDBB84','#FDD49E','#FEE8C8','#FFF7EC','#CCCCCC'] 
##    numColors=len(colors)
##    borderColor='#777777'
##    t_step = int(math.ceil(step/(numColors-1)))
##    timeSteps=[i*t_step+1 for i in xrange(numColors)]
##    timeSteps[-1]="Not invaded"
##    timeSteps[0]="1 (Jan 2016)"
## 
##    for index, shape in enumerate(sf.shapeRecords()):
##       try:
##          cellIndex=indexCellIDMap[records[index][1]]
##       except:
##          continue
## 
##       x = [i[0] for i in shape.shape.points[:]]
##       y = [i[1] for i in shape.shape.points[:]]
##    
##       plt.plot(x,y,color=borderColor,linewidth=.2)
## 
##       if ca.cells[cellIndex].time==-1:
##          plt.fill(x,y,alpha=1,color=colors[-1])
##       else:
##          colorBin=ca.cells[cellIndex].time/t_step
##          plt.fill(x,y,alpha=1,color=colors[colorBin]) 
##             
##    # legend
##    height=4.5
##    width=2
##    xoffset=-12
##    yoffset=-35
##    for i in xrange(numColors):
##       ax1.add_patch(Rectangle((xoffset,yoffset+height*i),width,height,fc=colors[i]))
##       ax1.text(xoffset+width+.5,yoffset+height*.2-.5+height*i,timeSteps[i],fontsize=20)
## 
##    plt.savefig(output)

def record_output(ca):
    result = list()
    for index, cell in ca.cells.items():
        if cell.state == 'S':
            result.append(0)
        elif cell.state == 'E':
            result.append(1)
        elif cell.state == 'I':
            result.append(2)
    return result



if __name__ == "__main__":
   # read in arguments
   parser=argparse.ArgumentParser(
     formatter_class=argparse.RawTextHelpFormatter)

   parser.add_argument("-l", '--input_list', nargs='+', default=[22,55,0.1,0.3,10], type=float, help='function parameter list. For update_ca_guimapi, format is: temp_t humidity_t ndvi_t1 ndvi_t2 prod_t. For update_ca_plus, format is: par_sd par_vor par_ld_out par_ld_in ndvi_t prod_t')

   #parser.add_argument("-p", '--model_pars', nargs=3, default = [3, 16, 1], type=float)
   #parser.add_argument("-s", '--file_names', nargs= )
   # JM: sample update_ca_plus 1 1 1 0.2 100
   # JM: Above is used if we want to skip the individual entries and only input a list
   #     Guimapi is temp_t,humidity_t,ndvi_t1,ndvi_t2,prod_t
   #     update_ca_plus: par_sd, par_vor, par_ld_out, ndvi_t, prod_t


   parser.add_argument("--grid_file",help="Pickle file created by 'create_ca.py'.", default="ca_model_moore_6_filled.pkl")
   parser.add_argument("--seed_file",help="File chosen to seed", default="seed_Johor.csv")
   parser.add_argument("-m", "--moore", default=3, type=int)
   parser.add_argument("-n", "--time_steps", help="in months", default=16, type=int)
   parser.add_argument("-o", "--output", default="out/output.csv")
   parser.add_argument("-v", "--verbose", action="store_true")
   parser.add_argument("-f", "--function", default="update_ca_guimapi", type = str)
   parser.add_argument("-s", "--step_scale", default=1, type=float,
         help='scaling factor to obtain simulation time steps from \
         time_steps; 1 means simulation proceeds in one month steps, 0.5 means 15 days')
   args=parser.parse_args()

   # set logger
   if args.verbose:
      logging.basicConfig(level=logging.DEBUG)
   else:
      logging.basicConfig(level=logging.INFO)

   ## ca = load_object(args.grid_file+str(args.moore)+".pkl")

   print 'loading ' + args.grid_file
   ca = load_object(args.grid_file)
   print 'loaded'

   ## with open("tp",'w') as f: 
   ##    for i in xrange(len(ca.cells)): 
   ##       cell=ca.cells[i]
   ##       f.write("%d,%d,%g,%g\n" %(i,cell.ID,cell.vertices[-1][0],cell.vertices[-1][1]))

   start_time=time.time()
   print "running ca..."
   region_to_grid,grid_to_region = create_region_grid_map()
   

   # create_seed_file(grid_to_region)
   seeds = gen_seed(ca, region_to_grid, args.seed_file)

   output = args.output
   # output = "single_city_seed/output_moore_" + str(args.moore) + ".csv"
   var_array = args.input_list
   print var_array

   run_ca(ca, seeds, args.time_steps, output, grid_to_region, args.step_scale, args.moore, args.function, var_array)
   fill_data_time = time.time()
   print "simulation ended. Time used: %s" %(str(fill_data_time-start_time))

   # evaluate(args.moore, str(int(100*args.ndvi_t)), args.prod_t)


