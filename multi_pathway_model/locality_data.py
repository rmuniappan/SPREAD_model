from fill_data_ca import load_object, dump_object, get_cities
import argparse
import numpy as np
import pickle
import pandas as pd
import pdb

DESC='Assigning locality attributes.'

def create_locality_file(ca, season_file, city_file, out_file):
    seasonal_prod = pd.read_csv(season_file)
    ## for index,row in rows.iterrows():
    ##    seasonal_prod[row[0]]=list(row[2:14])
    city_to_cell, cell_to_city = get_cities(ca, 0.25, city_file)
    tom_prod_list = ['tom_prod_month_' + str(i) for i in range(12)]
    df = pd.DataFrame(columns = ['cell_id','city_name','pop',]+tom_prod_list)
    for index, locality in ca.localities.iteritems():
	try: 
	    city = cell_to_city[index]
	except: continue
	sum_tom = [0]*12
	sum_pop = 0
	if type(locality)==int:
	    continue
	for cell in locality:
	    pop = ca.cells[cell].population
	    sum_pop += pop

	    cell_row = seasonal_prod.loc[seasonal_prod['cell_id'] == cell]
	    
	    for i in range(12):
	      try:
		      sum_tom[i] += cell_row.iloc[0]['T'+str(i+1)]
	      except:
	         continue

		## try: sum_tom[i] += cell_row.iloc[0][str(i+1)]*vege
		## except: sum_tom.append(cell_row.iloc[0][str(i+1)]*vege)
		## try: r = cell_row.iloc[0][str(i+1)]
                ## except:
                ##     try: sum_eggp[i] += 1/12.0*vege
                ##     except: sum_eggp.append(1/12.0*vege)
                ##     continue

                ## try: sum_eggp[i] += cell_row.iloc[0][str(i+1)]*vege
                ## except: sum_eggp.append(cell_row.iloc[0][str(i+1)]*vege)
		## try: r = cell_row.iloc[0][str(i+1)]
                ## except:
                ##     try: sum_[i] += 1/12.0*vege
                ##     except: sum_vege.append(1/12.0*vege)
                ##     continue

                ## try: sum_vege[i] += cell_row.iloc[0][str(i+1)]*vege
                ## except: sum_vege.append(cell_row.iloc[0][str(i+1)]*vege)
		
	df = df.append({ 'cell_id':int(index),'city_name':city,'pop':sum_pop, 
	    'tom_prod_month_0':sum_tom[0], 'tom_prod_month_1':sum_tom[1],
	    'tom_prod_month_2':sum_tom[2], 'tom_prod_month_3':sum_tom[3],
            'tom_prod_month_4':sum_tom[4], 'tom_prod_month_5':sum_tom[5],
       	    'tom_prod_month_6':sum_tom[6], 'tom_prod_month_7':sum_tom[7],
	    'tom_prod_month_8':sum_tom[8], 'tom_prod_month_9':sum_tom[9],
            'tom_prod_month_10':sum_tom[10], 'tom_prod_month_11':sum_tom[11]
}, ignore_index = True)
    df.to_csv(out_file, index = False)
    print out_file

if __name__ == "__main__":
    parser=argparse.ArgumentParser(
     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-p", "--pickle_file", default = "ca_model_moore_6_filled.pkl")
    parser.add_argument("-s", "--season_file", default = "../processed/obj/ca_seasonal_production.csv")
    parser.add_argument("-c", "--city_file", default = "../processed/cities_250000.csv")
    parser.add_argument("-o", "--out_file", default = "locality_data.csv")
    args = parser.parse_args()

    ca = load_object(args.pickle_file)
    create_locality_file(ca, args.season_file, args.city_file, args.out_file)
