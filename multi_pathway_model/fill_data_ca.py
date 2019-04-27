import sys
import math
import pdb
from os import listdir
from os.path import isfile, join
import copy
import time
import argparse
import logging
#from grid import grid
import pickle
from cellular_automata import Cell, CA
try:
    import read_tiff
except ImportError:
    pass
import glob
import scipy.spatial
import pandas as pd
import numpy as np

# Constants and key files
LANDSCAN_CELL_SIZE_DEGREES = 0.008333333
KEY = pd.read_csv('../data/lut_cell_orig.txt', delimiter = '\t', index_col = 'CELL5M', usecols = ['ISO3','CELL5M','X','Y','Name'],header = 0)
KEY2 = '../data/country_key.csv'
EARTH_RADIUS=6371

# Data paths
# AA: hard coding of file names
data_folder = '../data/'
temperature_folder = data_folder + 'temperature/'
ndvi_folder = data_folder + 'NDVI_2012/'
population_folder = data_folder + 'populations/'
city_distance_folder = '../../distance_matrix/results/'

# Data files
# AA: hard coding of file names
temperature_files = glob.glob(temperature_folder+'tmin[0-9]*.bil')
ndvi_files = glob.glob(ndvi_folder+'*')
humidity_file = data_folder + 'humidity.csv'
commodity_flow_file = data_folder + 'updated_city_to_city_commodity_flow.csv'
airline_travel_file = data_folder + 'air_travel.csv'
city_to_grid_file = data_folder + 'city_grid_map.csv'
production_file = data_folder + 'spam2005V3r2_ASIA_P.csv'
yield_file = data_folder + 'spam2005V3r2_ASIA_Y.csv'
country_production_file = data_folder + 'fao_production_data.csv'
city_file = '../obj/cities/cities_250000.csv'

def haversine(coord_a,coord_b):
    phi_1=math.radians(coord_a[0])
    phi_2=math.radians(coord_b[0])
    delta_phi=math.radians(coord_a[0]-coord_b[0])
    delta_lambda=math.radians(coord_a[1]-coord_b[1])

    a=math.sin(delta_phi/2)**2 + math.cos(phi_1)*math.cos(phi_2)*math.sin(delta_lambda/2)**2
    c=2*math.atan2(math.sqrt(a),math.sqrt(1-a))

    return EARTH_RADIUS*c


def add_commodity_flow(ca):
    return

def create_country_list(key):
    # JM: This method creates an easy file to work with to switch from iso3 code to country name. Useful. Maybe will add in ido2
    df = pd.DataFrame(columns = ['iso2','iso3','country'])
    for index, row in key.iterrows():
        # print index
	# print key.loc[index]['ISO3']
	# print df['code']
	# print df['code'].values
        if key.loc[index]['ISO3'] not in df['iso3'].values:
            df = df.append({'iso3':row['ISO3'], 'iso2':str(row['ISO3'])[:2],'country':row['Name']}, ignore_index = True)
    df = df.set_index('iso2')
    df.to_csv('country_key.csv')
    #return df

def create_locality(ca, cell_size, radius, cities_filename,locality_file):
    ca.localities = {}
    #JM:Adds edges between respective voronoi region points.
    #   Also can add the total population and production to the region node
    #vor_dict = {}
    cities, cell_to_city = get_cities(ca, cell_size, cities_filename)
    key = pd.read_csv(KEY2, index_col=0)
    df = pd.DataFrame(columns = ['cell','is_city','city','mapspam','population'])
    for index, cell in ca.cells.iteritems():
	
	cell_lat = cell.vertices[-1][0]
	cell_lon = cell.vertices[-1][1]
	min_dist = 100000000
	city_cell_id = -1
        for ind, city in cities.items():
	    city_cell = ca.cells[city[0]]
	    country = city_cell.country
	    city_lat = city_cell.vertices[-1][0]
	    city_lon = city_cell.vertices[-1][1]
	    dist=haversine((city_lat,city_lon),(cell_lat,cell_lon))
	    if dist < min_dist and country == cell.country:
		region = ind
		city_cell_id = city[0]
		min_dist=dist
	    
	if city_cell_id==index:   # i.e. cell is a city ...
	    df = df.append({'cell':index, 'is_city':1, 'city':region, 'mapspam':cell.production['vege'], 'population':cell.population}, ignore_index = True)
	    try: ca.localities[index].append(index)
	    except: ca.localities[index] = [index]
	    
	##     # ca.add_edge(index, cell_id, 'locality', min_dist)
	elif min_dist <= radius: 
	   df = df.append({'cell':index, 'is_city':0, 'city':region, 'mapspam':cell.production['vege'], 'population':cell.population}, ignore_index = True)
	   try:
		ca.localities[city_cell_id].append(index)
	   except:
		ca.localities[city_cell_id] = [index]
	   ca.localities[index] = city_cell_id
	else: 
		df = df.append({'cell':index, 'is_city':0, 'city':'NaN', 'mapspam':cell.production['vege'], 'population':cell.population}, ignore_index = True)
	## else:
	##     if min_dist < radius and cell_id!=-1:
   ##              df = df.append({'cell':index, 'city':region, 'mapspam':cell.production['vege'], 'population':cell.population}, ignore_index = True)
   ##          else:
   ##              df = df.append({'cell':index, 'city':'NaN', 'mapspam':cell.production['vege'], 'population':cell.population}, ignore_index = True)

    df.to_csv(locality_file, index=False)
	    #if region in vor_dict.keys():
	    #	vor_dict[region].append({index : cell})
	    #else:
	    #	vor_dict[region] = [{index : cell}]

	    # ca.cells[region].population += cell.population
	    # ca.cells[region].production['vege'] += cell.production['vege']
	    # ca.cells[region].production['tomato'] += cell.production['tomato']
	    # ca.cells[region].production['eggplant'] += cell.production['eggplant']
	    # ca.cells[region].production['potato'] += cell.production['potato']
	    # ca.cells[region].production['total'] += cell.production['total']
    #return vor_dict

def fill_network(ca, network_file,locality_file):
    monthly_flows = pd.read_csv(network_file, names = ['city1','city2','weight','month'])
    monthly_flows['weight']/=monthly_flows['weight'].max()
    city_key = pd.read_csv(locality_file, usecols = ['cell_id','city_name'])
    ca.network=pd.merge(monthly_flows,city_key,left_on=['city1'],right_on=['city_name'])
    ca.network=pd.merge(ca.network,city_key,left_on=['city2'],right_on=['city_name'])
    ca.network.drop(['city_name_x','city_name_y'],axis=1,inplace=True)
    ## cell_key = pd.read_csv(locality_file, usecols = ['cell_id','city_name'], index_col = 'city_name')
    ## 
    ## 
    ## ca.network = {}
    ## for index, loc in ca.localities.items():
	 ## f type(loc) == int:
	 ##    continue
    ##     else:
	 ##    loc = index
    ##     dist_nbrs = []
    ##     if loc != 0:
    ##         try:
    ##             for index, row in distance_weights.loc[[city_key.get_value(loc,'city_name')]].iterrows():
    ##                 if index != row['city1'] and row['one'] == 1:
    ##                     dist_nbrs.append((cell_key.get_value(row['city1'],'cell_id'),row['weight']))
    ##         except: dist_nbrs = []
    ##     ca.network[loc] = dist_nbrs


    ##    cities, cell_to_city = get_cities(ca, 0.25, network_file)
    ##    df = pd.read_csv(network_file, index_col = 'id')
    ##    for index, row in df.iterrows():
    ##	source = row['city1']
    ##	destination = row['city2']
    ##	months = [row['flow ' + str(i)] for i in range(12)]
    ##	ca.network[(source, destination)] = months

    # for index, cell in ca.cells.iteritems():

    #     try: type(ca.localities[index]) == int
    #     except: continue

    #     if type(ca.localities[index]) == int:
    #         continue
    #     for index_dest, cell_dest in ca.cells.iteritems():
    #         try: type(ca.localities[index_dest]) == int
    #         except: continue
    #         if type(ca.localities[index_dest]) == int:
    #     	continue
    #         ca.network[(index, index_dest)] = 1

def add_distance_edges(ca, cell_size):
    #JM:Adds long distance edges between cities in city_files. The weight is distance between cities.
    #   distance_without is edges between cities from different countries, distance_within is edges from within a country

    city_list, cell_to_city = get_cities(ca, cell_size, city_file)
    for file in listdir(city_distance_folder):
	
	if len(file) == 28:
        #JM: The length of file ensures we read the correct file names

	    data = pd.read_csv(city_distance_folder + file, names = ['city1','city2','time1','time2'])
	    for index, connection in data.iterrows():
		#JM:Below is to only include the cities which are both in city_file and city_distance_folder

		if connection['city1'] not in city_list.keys() or connection['city2'] not in city_list.keys():
		    continue

		source = city_list[connection['city1']][0]
		destination = city_list[connection['city2']][0]
		travel_time = connection['time2']
		for source_neighbor in ca.cells[source].neighbors:
		    if type(source_neighbor) == tuple:
			continue
		    for destination_neighbor in ca.cells[destination].neighbors:
			if type(destination_neighbor) == tuple:
			    continue
			ca.add_edge(source_neighbor, destination_neighbor, 'distance', travel_time)
			
		
		   

def get_cities(ca, cell_size, filename):
    #JM: This method takes the city_file and creates a dictionary with the key as the city name and the value as a tuple:
    #    (cell index, country)
    print filename 
    city_data = pd.read_csv(filename, index_col='id')
    
    cells_with_cities= {}
    for index, row in city_data.iterrows():
        # JM: This rounds each city's location to the nearest cell centroid.

        if round(2.0*row['lt']/cell_size) % 2 == 1:
            big_lt = round(2.0*row['lt']/cell_size)/(2.0/cell_size)
        else:
            if 2.0*row['lt']/cell_size < round(2.0*row['lt']/cell_size):
                big_lt = round(2.0*row['lt']/cell_size)/(2.0/cell_size) - cell_size/2.0
            else:
                big_lt = round(2.0*row['lt']/cell_size)/(2.0/cell_size) + cell_size/2.0

        if round(2.0*row['ln']/cell_size) % 2 == 1:
            big_ln = round(2.0*row['ln']/cell_size)/(2.0/cell_size)
        else:
            if 2.0*row['ln']/cell_size < round(2.0*row['ln']/cell_size):
                big_ln = round(2.0*row['ln']/cell_size)/(2.0/cell_size) - cell_size/2.0
            else:
                big_ln = round(2.0*row['ln']/cell_size)/(2.0/cell_size) + cell_size/2.0

	cells_with_cities[(big_lt, big_ln)] = (row['name'], row['country'])
    city_dict = {}
    cell_dict = {}
    for index, cell in ca.cells.items():
        # JM: This goes through the cells and then creates a dict that relates the cell_index with the city name, dict key is city name, dict value is cell id and country
	
	lat = cell.vertices[-1][0]
	lon = cell.vertices[-1][1]
	if (lat,lon) in cells_with_cities.keys():
	    city_dict[cells_with_cities[(lat,lon)][0]] = (index,cells_with_cities[(lat,lon)][1])
	    cell_dict[index] = cells_with_cities[(lat,lon)][0]
    return city_dict, cell_dict


def fill_population(ca):
    # JM: This method resets the population values and assigns from the population files which end in .txt

    for index, cell in ca.cells.items():
	cell.population = 0

    gen = (f for f in listdir(population_folder) if f[-1]=='t')
    for f in gen:
	header = pd.read_csv(population_folder + f, delimiter = ' ', nrows = 3, names = ['min','max'])
	min_lon = float(header['min'].iloc[0])
	min_lat = float(header['min'].iloc[1])
	max_lon = float(header['max'].iloc[0])
	max_lat = float(header['max'].iloc[1])
	country_population = pd.read_csv(population_folder + f,delimiter=' ', skiprows = 3)
	country_population = country_population.fillna(0)
	
	print f
	print [min_lon, max_lon]
	print [min_lat, max_lat]
	for index, cell in ca.cells.items():
	    i = 0
	    lat = cell.vertices[-1][0]
	    lon = cell.vertices[-1][1]
	    if lat <= max_lat and lat >= min_lat and lon <= max_lon and lon >= min_lon:
		for index, row in country_population.iterrows():
		    j = 0 
		    if abs(max_lat - i*LANDSCAN_CELL_SIZE_DEGREES - lat) <= 0.125:
			for elt in row:
			    if abs(min_lon + j*LANDSCAN_CELL_SIZE_DEGREES - lon) <= 0.125:
				cell.population += elt
			    j += 1
		    i += 1
	


def fill_temperature(ca):
    """
    Fill in the temperature data given cellular obj and time(month).
    """
    for t in range(12):
        t_file = temperature_folder + str(t+1) + '.tif'
        for index,cell in ca.cells.items():
            centroid = cell.vertices[-1]
            lat = centroid[0]
            lon = centroid[1]
	    if len(cell.temperature) == t:
                cell.temperature.append(read_tiff.get_val(t_file, lat, lon))
	    else:
		cell.temperature[t] = read_tiff.get_val(t_file, lat, lon)

def fill_ndvi(ca,cell_size): # AA: HARD CODING: assumes 1x1 grid
    # JM: Changed so that there is not hard coding of 1x1 grid
    """
    Fill in ndvi data.
    """
    for t in range(12):
        ndvi_file = ndvi_folder + str(t+1) + '.TIFF'
        for index,cell in ca.cells.iteritems():
            centroid = cell.vertices[-1]
            lat = centroid[0]
            lon = centroid[1]
            # NDVI data is 0.1 arc degree. Getting the max NDVI in the grid
            maxNDVI=-1
	    
            for i in range(-1*int(cell_size*4),int(cell_size*4)+1):
                for j in range(-1*int(cell_size*4),int(cell_size*4)+1):
		    if read_tiff.get_val(ndvi_file, lat+.1*i, lon+.1*j) > 9:
			value = -1
		    else:
			value = read_tiff.get_val(ndvi_file, lat+.1*i, lon+.1*j)
                    maxNDVI=max(value,maxNDVI)
	    # JM: Below reassigns ndvi if it has already been assigned and appends it if not

	    if len(cell.ndvi) == t:
                cell.ndvi.append(maxNDVI)
	    else:
		cell.ndvi[t] = maxNDVI

int_to_month = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr',
               5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep',
               10:'Oct', 11:'Nov', 12:'Dec'}

def fill_humidity(ca):
    """
    Relative humidity data is of 1 arc degree resolution (coarser than the
    cells), assign humidity to each cell by using the value of the nearest
    geo-ref points.
    """
    df = pd.read_csv(humidity_file, delimiter=' ')
    coordinates = df[['Lat','Lon']].as_matrix()
    kdtree = scipy.spatial.KDTree(coordinates)

    for t in range(12):
        month = int_to_month[t+1]
        for index,cell in ca.cells.items():
            centroid = cell.vertices[-1]
            distance, index = kdtree.query(centroid)

	    if len(cell.humidity) == t: 
                cell.humidity.append(df.ix[index][month])
	    else:	
		cell.humidity[t] = df.ix[index][month]
def fill_yield(ca, cell_size):
    # JM: This method assigns the vegetable data from the production file. It uses the KEY file which gives names and iso codes
    key = KEY

    df = pd.read_csv(yield_file, dtype = {'cell5m':int}, index_col = 'cell5m', usecols = ['cell5m','pota','vege','name_cntr'])
    df['name_cntr'] = df['name_cntr'].astype(str)
    #df['name_cntr'] = map(lambda x: x.upper(), df['name_cntr'])
    #df['name_cntr'].replace('\s+', '', regex=True, inplace=True)
    #df['name_cntr'].replace("LAOPEOPLE'SDEMOCRATICREPUBL", 'LAOS', regex=True, inplace=True)

    frames = [df, key]
    df = pd.concat(frames, axis = 1, join = 'inner')
    production_dict = {}
    potato_dict = {}
    country_dict = {}
    for index, row in df.iterrows():
        # JM: Same as population, rounds the lat and lon of the values in the production file to match centroids

        if round(2.0*row['Y']/cell_size) % 2 == 1:
            big_lt = round(2.0*row['Y']/cell_size)/(2.0/cell_size)
        else:
            if 2.0*row['Y']/cell_size < round(2.0*row['Y']/cell_size):
                big_lt = round(2.0*row['Y']/cell_size)/(2.0/cell_size) - cell_size/2.0
            else:
                big_lt = round(2.0*row['Y']/cell_size)/(2.0/cell_size) + cell_size/2.0

        if round(2.0*row['X']/cell_size) % 2 == 1:
            big_ln = round(2.0*row['X']/cell_size)/(2.0/cell_size)
        else:
            if 2.0*row['X']/cell_size < round(2.0*row['X']/cell_size):
                big_ln = round(2.0*row['X']/cell_size)/(2.0/cell_size) - cell_size/2.0
            else:
                big_ln = round(2.0*row['X']/cell_size)/(2.0/cell_size) + cell_size/2.0
        if (big_lt,big_ln) in production_dict.keys():
            production_dict[(big_lt,big_ln)] += row['vege']
            potato_dict[(big_lt,big_ln)] += row['pota']
        else:
            production_dict[(big_lt,big_ln)] = row['vege']
            potato_dict[(big_lt,big_ln)] = row['pota']

        country_dict[(big_lt,big_ln)] = row['Name']

    for index, cell in ca.cells.iteritems():
        
        value = 0
        potato_value = 0
        distance = cell_size/2.0
        centroid = cell.vertices[-1]
        lat = centroid[0]
        lon = centroid[1]

        if (lat,lon) in production_dict.keys():
            value = production_dict[(lat,lon)]
        else:
            value = 0
	if (lat,lon) in potato_dict.keys():
	    potato_value = potato_dict[(lat,lon)]
	else:
	    potato_value = 0

        cell.production['vege_yield'] = value
	cell.production['pota_yield'] = potato_value
    return country_dict

def fill_production(ca, cell_size):
    # JM: This method assigns the vegetable data from the production file. It uses the KEY file which gives names and iso codes
    key = KEY

    df = pd.read_csv(production_file, dtype = {'cell5m':int}, index_col = 'cell5m', usecols = ['cell5m','pota','vege','name_cntr'])
    df['name_cntr'] = df['name_cntr'].astype(str)
    #df['name_cntr'] = map(lambda x: x.upper(), df['name_cntr'])
    #df['name_cntr'].replace('\s+', '', regex=True, inplace=True)
    #df['name_cntr'].replace("LAOPEOPLE'SDEMOCRATICREPUBL", 'LAOS', regex=True, inplace=True)

    frames = [df, key]
    df = pd.concat(frames, axis = 1, join = 'inner')
    production_dict = {}
    potato_dict = {}
    country_dict = {}
    for index, row in df.iterrows():
	# JM: Same as population, rounds the lat and lon of the values in the production file to match centroids

	if round(2.0*row['Y']/cell_size) % 2 == 1:
            big_lt = round(2.0*row['Y']/cell_size)/(2.0/cell_size)
        else:
            if 2.0*row['Y']/cell_size < round(2.0*row['Y']/cell_size):
                big_lt = round(2.0*row['Y']/cell_size)/(2.0/cell_size) - cell_size/2.0
            else:
                big_lt = round(2.0*row['Y']/cell_size)/(2.0/cell_size) + cell_size/2.0

        if round(2.0*row['X']/cell_size) % 2 == 1:
            big_ln = round(2.0*row['X']/cell_size)/(2.0/cell_size)
        else:
            if 2.0*row['X']/cell_size < round(2.0*row['X']/cell_size):
                big_ln = round(2.0*row['X']/cell_size)/(2.0/cell_size) - cell_size/2.0
            else:
                big_ln = round(2.0*row['X']/cell_size)/(2.0/cell_size) + cell_size/2.0
	if (big_lt,big_ln) in production_dict.keys():
	    production_dict[(big_lt,big_ln)] += row['vege']
	    potato_dict[(big_lt,big_ln)] += row['pota']
	    
	else:
	    production_dict[(big_lt,big_ln)] = row['vege']
	    potato_dict[(big_lt,big_ln)] = row['pota']
        country_dict[(big_lt,big_ln)] = row['Name']


    for index, cell in ca.cells.iteritems():
	value = 0
	potato_value = 0
	distance = cell_size/2.0
	centroid = cell.vertices[-1]
        lat = centroid[0]
        lon = centroid[1]

	if (lat,lon) in production_dict.keys():
            value = production_dict[(lat,lon)]
        else:
            value = 0
        if (lat,lon) in potato_dict.keys():
            potato_value = potato_dict[(lat,lon)]
        else:
            potato_value = 0

        cell.production['vege'] = value
	cell.production['pota'] = potato_value
    return country_dict
    

def fill_fractional_production(ca, cell_size, annual_production_file, seasonal_production_file):
    
    # JM: This method assigns the vegetable data from the production file. It uses the KEY file which gives names and iso codes
    key = KEY
    seasonal_prod = pd.read_csv(seasonal_production_file)
    df = pd.read_csv(annual_production_file, usecols = ['lat','lon','tom','pot'])
    #df['name_cntr'] = df['name_cntr'].astype(str)
    #df['name_cntr'] = map(lambda x: x.upper(), df['name_cntr'])
    #df['name_cntr'].replace('\s+', '', regex=True, inplace=True)
    #df['name_cntr'].replace("LAOPEOPLE'SDEMOCRATICREPUBL", 'LAOS', regex=True, inplace=True)

    #frames = [df, key]
    #df = pd.concat(frames, axis = 1, join = 'inner')
    production_dict = {}
    potato_dict = {}
    eggp_dict = {}
    country_dict = {}
    for index, row in df.iterrows():
        # JM: Same as population, rounds the lat and lon of the values in the production file to match centroids

        if round(2.0*row['lat']/cell_size) % 2 == 1:
            big_lt = round(2.0*row['lat']/cell_size)/(2.0/cell_size)
        else:
            if 2.0*row['lat']/cell_size < round(2.0*row['lat']/cell_size):
                big_lt = round(2.0*row['lat']/cell_size)/(2.0/cell_size) - cell_size/2.0
            else:
                big_lt = round(2.0*row['lat']/cell_size)/(2.0/cell_size) + cell_size/2.0

        if round(2.0*row['lon']/cell_size) % 2 == 1:
            big_ln = round(2.0*row['lon']/cell_size)/(2.0/cell_size)
        else:
            if 2.0*row['lon']/cell_size < round(2.0*row['lon']/cell_size):
                big_ln = round(2.0*row['lon']/cell_size)/(2.0/cell_size) - cell_size/2.0
            else:
                big_ln = round(2.0*row['lon']/cell_size)/(2.0/cell_size) + cell_size/2.0
        if (big_lt,big_ln) in production_dict.keys():
            production_dict[(big_lt,big_ln)] += row['tom']
            potato_dict[(big_lt,big_ln)] += row['pot']
            
        else:
            production_dict[(big_lt,big_ln)] = float(row['tom'])
            potato_dict[(big_lt,big_ln)] = float(row['pot'])
    sum_vege = []
    sum_pota = []
    sum_eggp = []
    for index, cell in ca.cells.iteritems():
	
        lat = cell.vertices[-1][0]
        lon = cell.vertices[-1][1]
	try: vege = production_dict[(lat,lon)]
	except: vege = 0
	try: pota = potato_dict[(lat,lon)]
	except: pota = 0
	try: eggp = eggp_dict[(lat,lon)]
	except: eggp = 0
	cell_size = 0.5
        if round(2.0*lat/cell_size)%2 == 1:
            key_lat = round(2.0*lat/cell_size)/(2.0/cell_size)
        else:
            if 2.0*lat/cell_size < round(2.0*lat/cell_size):
                key_lat = round(2.0*lat/cell_size)/(2.0/cell_size) - cell_size/2.0
            else:
                key_lat = round(2.0*lat/cell_size)/(2.0/cell_size) + cell_size/2.0

        if round(2.0*lon/cell_size)%2 == 1:
            key_lon = round(2.0*lon/cell_size)/(2.0/cell_size)
        else:
            if 2.0*lon/cell_size < round(2.0*lon/cell_size):
                key_lon = round(2.0*lon/cell_size)/(2.0/cell_size) - cell_size/2.0
            else:
                key_lon = round(2.0*lon/cell_size)/(2.0/cell_size) + cell_size/2.0
        correct_lat = seasonal_prod.loc[seasonal_prod['lat'] == key_lat]
        correct_row = correct_lat.loc[correct_lat['lon'] == key_lon]
	

        for i in range(12):
            try: r = correct_row.iloc[0][str(i+1)]
            except:
                try: sum_vege[i] += 1/12.0*float(vege)
                except: sum_vege.append(1/12.0*float(vege))
		try: sum_pota[i] += 1/12.0 * float(pota)
		except: sum_vege.append(1/12.0 * float(pota))
		try: sum_eggp[i] += 1/12.0 * float(eggp)
		except: sum_eggp[i].append(1/12.0 * float(eggp))
                continue

            try: sum_vege[i] += correct_row.iloc[0][str(i+1)]*float(vege)
            except: sum_vege.append(correct_row.iloc[0][str(i+1)]*float(vege))
            try: sum_pota[i] += correct_row.iloc[0][str(i+1)]*float(pota)
            except: sum_pota.append(correct_row.iloc[0][str(i+1)]*float(pota))
            try: sum_eggp[i] += correct_row.iloc[0][str(i+1)]*float(eggp)
            except: sum_eggp.append(correct_row.iloc[0][str(i+1)]*float(eggp))


        value = 0
        potato_value = 0
	eggp_value = 0
        distance = cell_size/2.0
        centroid = cell.vertices[-1]

	print production_dict.keys()
	print (lat,lon)
        if (lat,lon) in production_dict.keys():
            value = production_dict[(lat,lon)]
        if (lat,lon) in potato_dict.keys():
            potato_value = potato_dict[(lat,lon)]
        if (lat,lon) in eggp_dict.keys():
            eggp_value = production_dict[(lat,lon)]

	print value

        cell.production['frac_tom'] = [sum_vege[i] * value for i in range(12)]
        cell.production['frac_pot'] = [potato_value * sum_pota[j] for j in range(12)]
	cell.production['frac_eggp'] = [eggp_value * sum_eggp[k] for k in range(12)]

def fill_country(ca, country_dict):
    #JM: Fills the country each cell centroid is in
    for index, cell in ca.cells.iteritems():
        centroid = cell.vertices[-1]
        lat = centroid[0]
        lon = centroid[1]
        if (lat,lon) in country_dict.keys():
            country = country_dict[(lat,lon)]
        else:
            country = ''
        cell.country = country


def fill_adj_production(ca, cell_size):
    #JM: This reads the FAO data files and creates the tomato, eggplant and potato estimates, from the values which are filled for vegetable production

    country_list = ['BANGLADESH','CAMBODIA','INDONESIA','LAOS','MALAYSIA','MYANMAR','NEPAL','PHILIPPINES','SINGAPORE','THAILAND','VIETNAM']
    country_totals = {'BANGLADESH':0, 'CAMBODIA':0, 'INDONESIA':0, 'LAOS':0, 'MALAYSIA':0, 'MYANMAR':0, 'NEPAL':0, 'PHILIPPINES':0, 'SINGAPORE':0, 'THAILAND':0, 'VIETNAM':0}

    country_production_data = pd.read_csv(country_production_file, usecols = ['Area', 'Item', 'Value'])
    country_production_data['Area'] = map(lambda x: x.capitalize(), country_production_data['Area'])
    country_production_data['Area'].replace('\s+', '', regex=True, inplace=True)
    country_production_data['Area'].replace("Laopeople'sdemocraticrepublic", 'Laos', regex=True, inplace=True)


    df = pd.read_csv(production_file, dtype = {'cell5m':int}, index_col = 'cell5m', usecols = ['cell5m','vege','name_cntr'])
    df['name_cntr'] = df['name_cntr'].astype(str)
    df['name_cntr'] = map(lambda x: x.upper(), df['name_cntr'])
    df['name_cntr'].replace('\s+', '', regex=True, inplace=True)
    df['name_cntr'].replace("LAOPEOPLE'SDEMOCRATICREPUBL", 'LAOS', regex=True, inplace=True)


    key = pd.read_csv('../data/lut_cell5m_iso3_allockey.txt', delimiter = '\t', index_col = 'CELL5M', usecols = ['ISO3','CELL5M','X','Y','Name'],header = 0)

    frames = [df, key]
    df = pd.concat(frames, axis = 1, join = 'inner')

    for index, row in df.iterrows():
        name_cntr = str(row['name_cntr'])
        if name_cntr in country_totals.keys():
            country_totals[str.upper(row['name_cntr'])] += row['vege']

    print country_totals
    for index, cell in ca.cells.iteritems():
        value = 0
        distance = cell_size/2.0
        centroid = cell.vertices[-1]
	lat = centroid[0]
        lon = centroid[1]
        value = cell.production['vege']
        country = cell.country
        our_country_production = country_production_data.loc[country_production_data['Area']==country]
        if len(our_country_production.loc[our_country_production['Item']=='Tomatoes', 'Value']) > 0:
            cell.production['tomato'] = value/country_totals[cell.country.upper()]*our_country_production.loc[our_country_production['Item']=='Tomatoes', 'Value'].values[0]
        else:
            cell.production['tomato'] = 0

        if len(our_country_production.loc[our_country_production['Item']=='Eggplants (aubergines)', 'Value']) > 0:
             cell.production['eggplant'] += value/country_totals[cell.country.upper()]*our_country_production.loc[our_country_production['Item']=='Eggplants (aubergines)', 'Value'].values[0]
        else:
            cell.production['eggplant'] = 0

        if len(our_country_production.loc[our_country_production['Item']=='Potatoes', 'Value']) > 0:
            cell.production['potato'] = value/country_totals[cell.country.upper()]*our_country_production.loc[our_country_production['Item']=='Potatoes', 'Value'].values[0]
        else:
            cell.production['potato'] = 0

        cell.production['total'] = cell.production['tomato'] + cell.production['eggplant'] + cell.production['potato']


def load_object(filename):
    f = file(filename, 'r')
    u = pickle.Unpickler(f)
    o = u.load()
    f.close()
    return o

def dump_object(filename, obj) :
    f = open(filename, 'w')
    u = pickle.Pickler(f)
    u.dump(obj)
    f.close()

def main():
   # read in arguments
   parser=argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

   parser.add_argument("--grid_file",help="Pickle file created by \
         'create_ca.py'.", default="ca_model_moore_6_filled.pkl")
   parser.add_argument("-v", "--verbose", action="store_true")
   parser.add_argument("-o", "--output", default="ca_model_moore_6_filled.pkl")
   parser.add_argument('--ndvi', action='store_true')
   parser.add_argument('--temp', action='store_true')
   parser.add_argument('-c','--cell_size', default = 0.25, type=float)
   parser.add_argument('--hum', action='store_true', help="relative humidity")
   parser.add_argument('--prod', action='store_true', help="MAPSPAM production")
   parser.add_argument('--pop', action='store_true', help="Landscan population")
   parser.add_argument('--adj_prod', action='store_true')
   parser.add_argument('--distance', action='store_true')
   parser.add_argument('--net', action='store_true')
   parser.add_argument('--net_file', default = '../../long_distance/obj/locality_flows_b2_k300.csv', type = str)
   parser.add_argument('--loc_file', default = '../obj/locality_flows.csv', type = str)
   parser.add_argument('--ann_file', default = '../obj/annual_production.csv', type = str)
   parser.add_argument('--season_file')
   parser.add_argument('--country', action='store_true')
   parser.add_argument('--yld', action='store_true')
   parser.add_argument('--loc', action='store_true', help="Create \
         localities (requires loc_radius and loc_cities arguments)")
   parser.add_argument('--loc_radius', default=200, type=float, help="Radius of the locality in kms")
   parser.add_argument('--loc_cities', default = city_file, \
         help="File of cities ... must contain the following columns \
         <name,lt,ln,country_code_iso2>")

   args=parser.parse_args()

   # set logger
   if args.verbose:
      logging.basicConfig(level=logging.DEBUG)
   else:
      logging.basicConfig(level=logging.INFO)
   print "loading"
   ca = load_object(args.grid_file)
   print "loaded"
   start_time=time.time()
   print "filling data..."

   if args.yld:
      print "Yield..."
      a = fill_yield(ca, args.cell_size)
   if args.pop:
      print "Population..."
      fill_population(ca)
   if args.ndvi:
      print "NDVI..."
      fill_ndvi(ca,args.cell_size)
   if args.temp:
      print "Temperature..."
      fill_temperature(ca)
   if args.hum:
      print "Humidity..."
      fill_humidity(ca)
   if args.prod:
      print "Production..."
      country_dict = fill_production(ca, args.cell_size)
   if args.country:
      print "Country..."
      fill_country(ca, country_dict)
   if args.loc:
      print "Locality..."
      create_locality(ca, args.cell_size, args.loc_radius, args.loc_cities,args.loc_file)
   if args.adj_prod:
      print "Fractional Production..."
      fill_fractional_production(ca, args.cell_size, args.ann_file, args.season_file)
   if args.distance:
      print "Adding Distance Edges..."
      add_distance_edges(ca, args.cell_size) 
   if args.net:
      print "Creating Market Network..."
      fill_network(ca, args.net_file,args.loc_file)

   gridFile = args.grid_file
   fill_data_time = time.time()
   print "data filled. Time used: %.2f minutes" %((fill_data_time-start_time)/60)
   
   dump_object(args.output, ca)

if __name__ == "__main__":
    main()

