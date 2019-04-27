from fill_data_ca import load_object, dump_object
import argparse
import numpy as np
import pickle
import pandas as pd


adc_file = '../data/south_east_asia_adc_id_p25xp25.csv'
data_folder = '../data/'
production_file = data_folder + 'spam2005V3r2_ASIA_P.csv'
key = pd.read_csv('../data/lut_cell_orig.txt', delimiter = '\t', index_col = 'CELL5M', usecols = ['ISO3','CELL5M','X','Y','Name'],header = 0)

def make_file(ca):
    adc_df = pd.read_csv(adc_file, index_col = 'cell_id')
    df = pd.DataFrame(columns = ['cell id','population','lon','lat','vege','pota','admin_id','admin_name'])
    i = 0
    l = len(ca.cells)
    for index, cell in ca.cells.iteritems():
	i += 1
	#print i / float(l)
	lon = cell.vertices[-1][1]
	lat = cell.vertices[-1][0]
	cell_id = index
	vege = cell.production['vege']
	pota = cell.production['pota']
	try: admin_id = adc_df.get_value(index, 'admin1_iso')
	except: continue
	admin_name = adc_df.get_value(index, 'admin1')
	if type(admin_id) == str:
	    admin_id = [admin_id]
	    admin_name = [admin_name]
	elif type(admin_id) == float:
	    continue
	else:
	    admin_list = []
	    for elt in admin_id:
		if type(elt) != float:
		    admin_list.append(elt)
	    name_list = []
	    for name in admin_name:
		if type(name) != float:
		    name_list.append(name)
	    admin_id = admin_list
	    admin_name = name_list
	    

        df = df.append({
    	    'lon':lon, 'lat':lat, 'cell id':cell_id,'population': cell.population,
	    'vege':vege, 'pota':pota, 'admin_id':admin_id[0], 'admin_name':admin_name[0]
		}, ignore_index = True)
    df.to_csv('../obj/ca_mapspam_pop.csv', index = False)

# def prod_cons(ca):
#    prod_list = ['prod_'+ str(i) for i in range(12)]
#    cons_list = ['cons_'+ str(i) for i in range(12)]
#    df = pd.DataFrame(columns = ['city'] + prod_list + cons_list)
#    for index, cell in ca.cells.iteritems():
#	for m in range(12):
#	    prod = []
#	    prod.append(cell.production['vege'])


def mk_prod():
    df = pd.read_csv(production_file, dtype = {'cell5m':int}, index_col = 'cell5m', usecols = ['cell5m','pota','vege','name_cntr','name_adm1','name_adm2'])
    frames = [df, key]
    df = pd.concat(frames, axis = 1, join = 'inner')
    df = df[['name_cntr','name_adm1','name_adm2','X','Y','pota','vege']]
    df.to_csv('../obj/mapspam_data.csv')
    print 'mapspam_data.csv'

if __name__ == "__main__":
    parser=argparse.ArgumentParser(
     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-p", "--pickle_file", default = "ca_model_moore_6_filled.csv")
    args = parser.parse_args()

    print 'loading'
    ca = load_object(args.pickle_file)
    print 'loaded'
    print 'method'
    make_file(ca)
    # mk_prod()



