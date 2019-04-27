import sys
import pdb
import copy
import time
import argparse
import logging
#from grid import grid
import pickle
from cellular_automata import Cell, CA
from fill_data_ca import get_cities, haversine
try:
    import read_tiff
except ImportError:
    pass
import glob
import scipy.spatial
import pandas as pd
import numpy as np

adc_file = '../data/south_east_asia_adc_id_p25xp25.csv'
KEY2 = '../data/country_key.csv'

def get_moore_neighbor(matrix, ID, moore_nbd):
    size = moore_nbd
    [row, col] = matrix.shape
    if ID-1<0 or ID-1>= row*col:
        raise Exception("Error Moore neighbor: ID out of range!")
    m = (ID-1)/col #ID starts from 1
    n = (ID-1)%col
    neighbor_indexs = []
    for i in range(-1*size,size+1):
	     for j in range(-1*size,size+1):
	         if i==j and i==0:
		          continue
	         else:
	             neighbor_indexs.append(([m+i,n+j],max(abs(i),abs(j))))
    
    neighbors = list()
    weights = dict() #{neighbor_id:[short_distance, commodity, travel]}
    for ni in neighbor_indexs:
        if ni[0][0]<0 or ni[0][0]>=row or ni[0][1]<0 or ni[0][1]>=col:
            continue
        else:
            neighbor_id = (matrix[ni[0][0]][ni[0][1]],ni[1])
            weights[neighbor_id] = [1, -1, -1, -1]
            neighbors.append(neighbor_id)
    return neighbors, weights
   
def create_locality(ca, cell_size, radius, cities_filename):
    #JM:Adds edges between respective voronoi region points.
    #   Also can add the total population and production to the region node
    #vor_dict = {}
    cities, cell_to_city = get_cities(ca, cell_size, cities_filename)
    key = pd.read_csv(KEY2, index_col=0)
    df = pd.DataFrame(columns = ['cell','is_city','city','mapspam','population'])

    # Only those cells which belong to localities are selected here.
    # A dictionary indexed by cells which belong to at least one locality.
    # If the cell corresponds to a locality center, then, the value is a
    # list of cells of the locality. Otherwise, it is just an integer
    # corresponding to the locality center.
    ca.localities = {}
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
            try: ca.localities[index].append(index)
            except: ca.localities[index] = [index]

        ##     # ca.add_edge(index, cell_id, 'locality', min_dist)
        elif min_dist <= radius:
           try:
                ca.localities[city_cell_id].append(index)
           except:
                ca.localities[city_cell_id] = [index]
           ca.localities[index] = city_cell_id
        ## else:
        ##     if min_dist < radius and cell_id!=-1:
   ##              df = df.append({'cell':index, 'city':region, 'mapspam':cell.production['vege'], 'population':cell.population}, ignore_index = True)
   ##          else:
   ##              df = df.append({'cell':index, 'city':'NaN', 'mapspam':cell.production['vege'], 'population':cell.population}, ignore_index = True)

            #if region in vor_dict.keys():
            #   vor_dict[region].append({index : cell})
            #else:
            #   vor_dict[region] = [{index : cell}]

            # ca.cells[region].population += cell.population
            # ca.cells[region].production['vege'] += cell.production['vege']
            # ca.cells[region].production['tomato'] += cell.production['tomato']
            # ca.cells[region].production['eggplant'] += cell.production['eggplant']
            # ca.cells[region].production['potato'] += cell.production['potato']
            # ca.cells[region].production['total'] += cell.production['total']
    #return vor_dict


def create_grid(moore_nbd,boundingBox,clipped,degree,bd=False):
    clip = True
    # JM: Below uses column name. With some files, this is just 'grid_id'
    clipped = pd.read_csv(clipped)
    adc = pd.read_csv(adc_file, index_col = 'cell_id')
    clipped_id = clipped['cell_id'].tolist()
    dxy = degree
    cells = [] 
    ID = 1
    numCells=180*360/(degree**2+.0)
    if int(numCells)!=numCells:
        logging.error("Number of cells is a float.")
        sys.exit(1)
    matrix = np.arange(1,int(numCells)+1).reshape([int(180/(degree)),int(360/(degree))])
    dispStep=5000
    numberOfCells=0
    logging.info("Number of nodes in clipped ID before bounding box: %d" %len(clipped_id))
    for i in np.arange(-90, 90, dxy):
        for j in np.arange(-180, 180, dxy):

            if not ID % dispStep:
               logging.info("processed %d" %ID)
            if clip==True and ID not in clipped_id:
                ID += 1
                continue # skip cells disjoint with countries.
            p1 = [i,j]
            p2 = [i+dxy, j]
            p3 = [i+dxy, j+dxy]
            p4 = [i, j+dxy]
            if i+dxy<boundingBox[0] or i>boundingBox[1] or j+dxy<boundingBox[2] or j>boundingBox[3]:
               clipped_id.remove(ID)
               ID+=1
               continue # skip cell because it is outside the bounding box
            centroid = [i+dxy/2, j+dxy/2] 
            vertices = [p1, p2, p3, p4, centroid]
            
            neighbors, weights = get_moore_neighbor(matrix, ID, moore_nbd)
            cell = [ID, vertices, neighbors, weights]
	    #if bd: 
	    #    if adc.get_value(cell[0],'admin_name')[:2] == 'BD':
            #        cells.append(cell)
	    #else:
	    cells.append(cell)
            ID += 1
            numberOfCells+=1
    logging.info("Number of nodes in clipped ID after bounding box: %d" %len(clipped_id))
    logging.info("Number of cells in the grid: %d" %numberOfCells)

    logging.info("Removing neighboring cells which are out of region ...")
    if clip==True:
        cellsProcessed=1
        dispStep=numberOfCells/10
        for cell in cells:
            if not cellsProcessed % dispStep:
               logging.info("processed %d cells" %cellsProcessed)
            remove_list = list()
            for nb in cell[2]:
                if nb[0]  not in clipped_id:
                    remove_list.append(nb)
            for rm in remove_list:
                cell[2].remove(rm)
            cellsProcessed+=1
    return cells

def create_cellular_automata(moore_nbd,boundingBox,clipped,bd,cell_size,time=-1):
    """
    Create an empty cellular automata with only geo information and time. No
    data filled.
    """
    
    logging.info("Creating grid ...")
    geo_cells = create_grid(moore_nbd,boundingBox,clipped,cell_size,bd)
    cells = {}
    #JM: The cell is a dictionary with cell id as the index

    logging.info("Creating cells ...")
    for geo_cell in geo_cells:
        ID = geo_cell[0]
        vertices = geo_cell[1] # vertices of polygon
        neighbors = geo_cell[2] # list of neighbors ID
        weights = geo_cell[3]
        c = Cell(vertices=vertices, time=time, neighbors=neighbors,
                 weights=weights)
        cells[ID] = c
    ca = CA(time=time, cells=cells)
    return ca


## def fill_temperature(ca):
##     """
##     Fill in the temperature data given cellular obj and time(month).
##     """
##     for t in range(12):
##         t_file = temperature_folder + str(t+1) + '.tif'
##         for index, cell in ca.cells.items():
##             centroid = cell.vertices[-1]
##             lat = centroid[0]
##             lon = centroid[1]
##             cell.temperature.append(read_tiff.get_val(t_file, lat, lon))
## 
## def fill_ndvi(ca): # AA: HARD CODING: assumes 1x1 grid
##     """
##     Fill in ndvi data.
##     """
##     for t in range(12):
##         ndvi_file = ndvi_folder + str(t+1) + '.TIFF'
##         for index,cell in ca.cells.items():
##             centroid = cell.vertices[-1]
##             lat = centroid[0]
##             lon = centroid[1]
##             # NDVI data is 0.1 arc degree. Getting the max NDVI in the grid
##             maxNDVI=-1
##             for i in range(-4,5):
##                 for j in range(-4,5):
##                     maxNDVI=max(read_tiff.get_val(ndvi_file, lat+.1*i, lon+.1*j),maxNDVI)
##             cell.ndvi.append(maxNDVI)
## 
## int_to_month = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr',
##                5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep',
##                10:'Oct', 11:'Nov', 12:'Dec'}
## 
## def fill_humidity(ca):
##     """
##     Relative humidity data is of 1 arc degree resolution (coarser than the
##     cells), assign humidity to each cell by using the value of the nearest 
##     geo-ref points.
##     """
##     df = pd.read_csv(humidity_file, delimiter=' ')
##     coordinates = df[['Lat','Lon']].as_matrix()
##     kdtree = scipy.spatial.KDTree(coordinates)
## 
##     for t in range(12):
##         month = int_to_month[t+1]
##         for index,cell in ca.cells.items():
##             centroid = cell.vertices[-1]
##             distance, index = kdtree.query(centroid)
##             cell.humidity.append(df.ix[index][month])
## 
## def fill_production(ca):
##     #do not consider this temporarily
##     pass
## 
## 
## def fill_data(ca):
##     logging.info("Temperature ...") 
##     fill_temperature(ca)
##     logging.info("NDVI ...") 
##     fill_ndvi(ca)
##     logging.info("humidity ...") 
##     fill_humidity(ca)

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
                
def create_model(moore_nbd,bBox,gridFile,clipped,cell_size, rad, bd, city_file):
    start = time.time()
    print "creating cellular automata..."
    ca = create_cellular_automata(moore_nbd,bBox,clipped,bd, cell_size)
    create_locality(ca, cell_size, rad, city_file)
    ca_time = time.time()
    print "cellular automata created. Time used: %s" %(str(ca_time-start))
    dump_object(gridFile, ca)

def main():
   # read in arguments
   parser=argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

   parser.add_argument("--lat_min", default=-90, type=float)
   parser.add_argument("--lat_max", default=90, type=float)
   parser.add_argument("--lon_min", default=-180, type=float)
   parser.add_argument("--lon_max", default=180, type=float)
   parser.add_argument("-v", "--verbose", action="store_true")

   parser.add_argument("-o", "--output", default="ca_model_moore_6.pkl")
   parser.add_argument("-c", "--cell_size", default=0.25, type=float)
   parser.add_argument("-g", "--grid_file", default="../data/south_east_asia_adc_id_p25xp25.csv") 
   parser.add_argument("-m", "--moore", default=3, type = int)
   parser.add_argument("--city_file", default='../obj/cities/cities_250000.csv')
   parser.add_argument("-r", "--radius", default = 200, type = float)
   parser.add_argument("--bd", action='store_true')
   
   args=parser.parse_args()

   # set logger
   if args.verbose:
      logging.basicConfig(level=logging.DEBUG)
   else:
      logging.basicConfig(level=logging.INFO)

   boundingBox=[args.lat_min,args.lat_max,args.lon_min,args.lon_max]
   
   create_model(args.moore,boundingBox,args.output,args.grid_file,args.cell_size, args.radius, args.bd, args.city_file)
      

if __name__ == "__main__":
    main()

