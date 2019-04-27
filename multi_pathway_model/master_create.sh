#!/bin/bash
# start/intermediate files used in the pipeline
radius=100; 
beta=2;
kappa=300;
cityFile='../obj/cities/cities_250000.csv'
minCA="../obj/min_ca.pkl"
minCAProd="../obj/min_ca_prod.pkl"
seedFile="../data/seed_files/seed_Bangladesh.csv"

function create_ca() {
#sbatch --export=out_file=$outFile,radius=$radius,cityFile=$cityFile ../cellular_automata/create_ca.sbatch;
python ../cellular_automata/create_ca.py -o $minCA -r $radius --city_file $cityFile;
}

function fill_data() {
#outFile=`echo $caFile | sed -e 's/.pkl/_prod.pkl/'`
python ../cellular_automata/fill_data_ca.py --temp --hum --pop --prod --country --grid_file $minCA -o $minCAProd
# inputs to filter_mapspam: mapspam file (hardcoded), -p pickle file
}

function ann_prod(){
python ../cellular_automata/filter_mapspam.py -p $minCAProd
# output file is ../processed/ca_mapspam_pop.csv
}

function seasonal_production() {
cd ../../production/work
../cellular_automata/master_production.sh gen_prod
#python ../cellular_automata/production.py
}

function locality_data() {
python ../cellular_automata/locality_data.py \
    -p $minCAProd \
    -s ../../production/obj/seasonal_production_precip1.csv \
    -c $cityFile \
    -o ../obj/locality_data_precip1.csv
python ../cellular_automata/locality_data.py \
    -p $minCAProd \
    -s ../../production/obj/seasonal_production_uniform.csv \
    -c $cityFile \
    -o ../obj/locality_data_uniform.csv
}

function gravity_flows() {
# do this manually
cd ../../long_distance/work/
#../cellular_automata/master_flow.sh gen_distance_matrix
../cellular_automata/master_flow.sh gravity_flows
# output is ../../long_distance/obj/locality_flows_b${beta}_k${kappa}.csv
}

function concat_flows() {
# do this manually
cd ../../long_distance/work/
#../cellular_automata/master_flow.sh gen_distance_matrix
../cellular_automata/master_flow.sh concat_flows
# output is ../../long_distance/obj/locality_flows_b${beta}_k${kappa}.csv
}

function ca_for_run() {
for flows in `ls -1 ../../long_distance/obj/locality_flows_*csv`
do
caFile=`basename $flows | sed -e 's/locality_flows_/ca_/' -e 's/csv/pkl/'`
logFile=log_$caFile.log
season=`basename $flows | sed -e 's/locality_flows_//' -e 's/_.*//'`
seasonalProd="../../production/obj/seasonal_production_${season}.csv"
locFile="../obj/locality_data_${season}.csv"
sbatch --account ipmmodeling -o $logFile \
    --export=command="python ../cellular_automata/fill_data_ca.py --net --net_file $flows \
    --season_file $seasonalProd \
    --grid_file $minCA \
    --loc_file $locFile \
    -o $caFile" ../cellular_automata/run_proc.sbatch
done
}

function ca_intervene(){
for eff in `seq 50 50 100`
do
for f in `ls -1 ../obj/ca_precip1_b*pkl`
do
logFile=`basename $f | sed -e 's/.pkl/.log/'`
outFile=`echo $f | sed -e "s/precip1/precip1-out-$eff/"`
sbatch --account ipmmodeling -o $logFile \
    --export=command="python ../cellular_automata/interventions.py --grid_file $f \
    -p $eff --cities ../obj/cities_top_outflow.csv \
    -o $outFile" ../cellular_automata/run_proc.sbatch
done
done
}

if [[ $# == 0 ]]; then
   echo "Here are the options:"
   grep "^function" $BASH_SOURCE | sed -e 's/function/  /' -e 's/[(){]//g' -e '/IGNORE/d'
else 
   eval $1 $2
fi
