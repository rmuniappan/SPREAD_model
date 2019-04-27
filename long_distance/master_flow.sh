#!/bin/bash
# This script generates monthly flows between major cities
# tags: bash code
NETDIR="../inputs/network_files";
NODE_ATTRIB="$NETDIR/node_attributes";
EDGE_LISTS="$NETDIR/edge_lists";
DATA="../../data/nepal_market_network.csv";

if [ `hostname | grep sfx | wc -l` == 1 ]; then
   qsubScript=../scripts/gravity_model/qsub.1c1n.sfx.bash;
elif [ `hostname | grep hsw | wc -l` == 1 ]; then
   qsubScript=../scripts/gravity_model/qsub.1c1n.hsw.bash;
fi

function example_gravity() {   # example for gravity model
    python ../scripts/gravity_model.py -h
    python ../scripts/gravity_model.py ../obj/example/nodes.csv ../obj/example/distance_network.csv --seed
}

function monthly_flows(){   # generating monthly flows
# input locality, consumption and monthly production
prodPopFile='../../processed/locality_data.csv'
nodeAttribFile='node_attributes.csv'
distanceNetwork='../../processed/time_network_countries_separated.csv'

python ../scripts/node_attribs.py $prodPopFile -o $nodeAttribFile

# generate monthly flows
beta=$1
kappa=$2
tolerance=1000
flowFile=locality_flows_b${beta}_k${kappa}.csv
rm -f $flowFile
rm -f month_[0-9]*.csv

for m in `seq 1 12`
do
    echo "beta=$beta kappa=$kappa month=$m"
    monthlyAttrib="month_$m.csv"
    echo "node,inflow,outflow" > $monthlyAttrib
    awk -F, -v OFS=',' -v month=$m 'NR>1{print $1,$2,$(month+2)}' \
        $nodeAttribFile >> $monthlyAttrib
    python ../scripts/gravity_model.py $monthlyAttrib $distanceNetwork \
        -b $beta -k $kappa -t $tolerance
    exit
    sed -e "s/$/,$m/" out.csv >> $flowFile
done
mv $flowFile ../obj
rm month_[0-9]*.csv
}

function gravity_flows(){   # generating for various beta and kappa; monthly_flows() parallelized
# input locality, consumption and monthly production
# NOTE: All city distances are in ../../distance_matrix/results/time_distance_with_country_250000.csv
tolerance=1
distanceNetwork='../obj/time_network_countries_separated.csv'
#distanceNetwork='../obj/time_network.csv'

python ../scripts/node_attribs.py ../../cellular_automata/obj/locality_data_precip1.csv -o node_attributes_precip1.csv
python ../scripts/node_attribs.py ../../cellular_automata/obj/locality_data_uniform.csv -o node_attributes_uniform.csv

naList="precip1 uniform"
betaList="0 1 2"
kappaList="300 500 1000"
#prodPopFileList='../../cellular_automata/obj/locality_data.csv'

for na in $naList
do
for m in `seq 1 12`
do
monthlyAttrib="month_${m}_$na.csv"
echo "node,inflow,outflow" > $monthlyAttrib
awk -F, -v OFS=',' -v month=$m 'NR>1{print $1,$2,$(month+2)}' \
    node_attributes_$na.csv >> $monthlyAttrib
done
done #na

for na in $naList
do
for beta in $betaList
do
for kappa in $kappaList
dm
for m in `seq 1 12`
do
echo "beta=$beta kappa=$kappa month=$m"
outFile=out_${na}_b${beta}_k${kappa}_m${m}.csv
logFile=log_${na}_b${beta}_k${kappa}_m${m}.log
monthlyAttrib="month_${m}_$na.csv"
sbatch --account ipmmodeling -o $logFile \
    --export=command="python ../scripts/gravity_model.py \
    $monthlyAttrib $distanceNetwork \
    -b $beta -k $kappa -t $tolerance \
    -o $outFile" ../scripts/run_proc.sbatch
done    #month
done    #kappa
done    #beta
done    #na
}

function concat_flows() {   # run after gravity_flows()
rm -f locality_flows*csv

cat log_b* > logs
echo "checking for errors"
echo "####################"
grep "slurmstepd: error" logs
echo "####################"
echo "if nothing between the ####s, all seems to be well"
sleep 5

for mf in `ls -1 out_*b*.csv`
do
flowFile=`echo $mf | sed -e 's/out_/locality_flows_/' -e 's/_m[0-9]*//'`
month=`echo $mf | sed -e 's/^.*_m//' -e 's/.csv//'`
sed -e "s/$/,$month/" $mf >> $flowFile
done
mv locality_flows_*csv ../../processed/
}


if [[ $# == 0 ]]; then
   echo "Here are the options:"
   grep "^function" $BASH_SOURCE | sed -e 's/function/  /' -e 's/[(){]//g' -e '/IGNORE/d'
else 
   eval $1 $2 $3
fi

