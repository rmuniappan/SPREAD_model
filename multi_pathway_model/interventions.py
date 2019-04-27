import pickle
import pandas as pd
import operator
import argparse
import pdb
from create_ca import load_object, dump_object

CITY_FILE = '../obj/cities_flows.csv'
DESC='Removes flows from localities with high outflows.'

def interventions(ca,grid_file,output, total,percent, cities, write):
    outflow = {}
    inflow = {}
    if cities == '':
        for key, value in ca.network.iterrows():
            if value['city1'] == value['city2']:
                continue
            try: outflow[value['city1']] += value['weight']
            except: outflow[value['city1']] = value['weight']
            try: inflow[value['city2']] += value['weight']
            except: inflow[value['city2']] = value['weight']
        
        outflow = dict(sorted(outflow.iteritems(), key=operator.itemgetter(1), reverse=True)[:total]) 
        inflow = pd.DataFrame.from_dict(inflow, orient='index', columns = ['inflow'])
        if write:
            df_flows = pd.DataFrame.from_dict(outflow, orient='index', columns = ['outflow'])
            df_flows.sort_values(inplace=True, ascending = False, axis=0, by = 'outflow')
            df_flows = df_flows.merge(inflow, how='inner', left_index=True, right_index = True)
            df_flows.to_csv(CITY_FILE, header=None)

    else:
        df = pd.read_csv(cities, header=None, names=['cities'])  #,'outflow','inflow'])
        for index, row in df.iterrows():
            outflow[row['cities']] = 0

    for key, value in ca.network.iterrows():
        try:
            outflow[value['city1']]
            if value['city1'] != value['city2']:
                ca.network.at[key,'weight'] *= 1.0-percent/100.0
        except:
            continue
    dump_object(output, ca)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=DESC,
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--grid_file", default="../obj/ca_uniform_b0_k500.pkl", type=str)
    parser.add_argument("-o", "--output", default = "../obj/ca_uniform_b0_k500_inter.pkl", type=str)
    parser.add_argument("-t", "--total", default = 10, type=int)
    parser.add_argument("-p", "--percent", default = 10.0, type=float)
    parser.add_argument("--cities", default = '', type=str)
    parser.add_argument("--write", action='store_true')
    
    args=parser.parse_args()
    ca = load_object(args.grid_file)

    interventions(ca, args.grid_file, args.output, args.total, args.percent, args.cities, args.write)

    '''print 'checking'
    ca_new = load_object(args.grid_file[:-4] + '_inter.pkl')
    ca = load_object(args.grid_file)
    for index, row in ca.network.iterrows():
        if ca.network.loc[index]['weight'] != ca_new.network.loc[index]['weight']:
            print ca.network.loc[index]['weight']
            print ca_new.network.loc[index]['weight']

    '''
