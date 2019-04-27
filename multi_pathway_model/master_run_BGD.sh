#!/bin/bash
# start/intermediate files used in the pipeline
function run_an_example() {
radius=100
beta=2
kappa=300
gridFile="../obj/ca_r${radius}_b${beta}_k${kappa}.pkl"
seedFile="../data/seed_files/seed_BGD_first_report.csv"
timeSteps=10
simRuns=1
startMonth=5
moore=1
suitThresh=0
expDelay=2
alphaSD=20
alphaFM=10
alphaMM=15

echo "#!/bin/bash" > run
chmod +x run

run_an_instance
#run_direct
}

function run_direct() { #IGNORE
outFile=`basename $gridFile | sed -e 's/ca_/res_/'\
    -e 's/.pkl//'`_sm${startMonth}_m${moore}_st${suitThresh}_ed${expDelay}_a-${alphaSD}-${alphaFM}-${alphaMM}.csv
echo $outFile

python ../multi_pathway_model/run_ca.py\
    --bgd\
    --grid_file $gridFile\
    --seed_file $seedFile\
    -o $outFile\
    -n $timeSteps\
    --sim_runs $simRuns\
    -s $startMonth\
    -m $moore\
    --suitability_threshold $suitThresh\
    --exp_delay $expDelay\
    --alpha_sd $alphaSD\
    --alpha_fm $alphaFM\
    --alpha_mm $alphaMM
}

function run_batch() {
radius=100
seedFileList="../data/seed_files/seed_BGD_moore0.csv ../data/seed_files/seed_BGD_moore1.csv"
timeSteps=15
simRuns=100
startMonthList="3 4 5"
mooreList="1 2"
suitThreshList="0"
betaList="0 1 2"
kappaList="500 1000"
seasonInd="precip1 uniform"
expDelayList=`seq 2 2`
alphaSDList=`seq 0 5 25` 
alphaFMList=`seq 0 5 25` 
alphaMMList=`seq 0 5 50`

echo "#!/bin/bash" > run
chmod +x run

for beta in $betaList
do
for kappa in $kappaList
do
for season in $seasonInd
do
gridFile="../obj/ca_${season}_b${beta}_k${kappa}.pkl"
for seedFile in $seedFileList
do
for startMonth in $startMonthList 
do
for moore in $mooreList 
do
for suitThresh in $suitThreshList 
do
for expDelay in $expDelayList 
do
for alphaSD in $alphaSDList 
do
for alphaFM in $alphaFMList 
do
for alphaMM in $alphaMMList 
do
alphaSD=`echo $alphaSD | awk '{printf "%g",$1}'`
alphaFM=`echo $alphaFM | awk '{printf "%g",$1}'`
alphaMM=`echo $alphaMM | awk '{printf "%g",$1}'`
run_an_instance
done #alphaMM
done #alphaFM
done #alphaSD
done #expDelay
done #suitThresh
done #moore
done #startMonth
done #seed
done #season
done #kappa
done #beta
}

function run_from_db() {
# select statement to generate
sqlite3 ../results/results.db <<!
.header on
.mode csv
.output .to_be_deleted.db_rows.csv
SELECT * FROM eval_BGD
where exp_delay=2;
!

echo "#!/bin/bash" > run
chmod +x run
seedFileList="../data/seed_files/seed_BGD_moore0.csv ../data/seed_files/seed_BGD_moore1.csv"

for line in `awk 'NR>1' .to_be_deleted.db_rows.csv`
do
for seedFile in $seedFileList
do
radius=`echo $line | awk -F, '{printf "%g",$1}'`
beta=`echo $line | awk -F, '{printf "%g",$2}'`
kappa=`echo $line | awk -F, '{printf "%g",$3}'`
gridFile="../obj/ca_r${radius}_b${beta}_k${kappa}.pkl"
timeSteps=15
simRuns=100
startMonth=`echo $line | awk -F, '{printf "%g",$5}'`
moore=`echo $line | awk -F, '{printf "%g",$6}'`
suitThresh=`echo $line | awk -F, '{printf "%g",$7}'`
expDelay=1
alphaSD=`echo $line | awk -F, '{printf "%g",$9}'`
alphaFM=`echo $line | awk -F, '{printf "%g",$10}'`
alphaMM=`echo $line | awk -F, '{printf "%g",$11}'`
run_an_instance
done
done
}

function run_an_instance() { #IGNORE
if [[ "$seedFile" == "../data/seed_files/seed_BGD_moore0.csv" ]]; then
    seed=0
elif [[ "$seedFile" == "../data/seed_files/seed_BGD_moore1.csv" ]]; then
    seed=1
else
    echo "Wrong seed file"
    exit
fi

outFile=results_BGD/`basename $gridFile | sed -e 's/ca_/res_/'\
    -e 's/.pkl//'`_s${seed}_sm${startMonth}_m${moore}_st${suitThresh}_ed${expDelay}_a-${alphaSD}-${alphaFM}-${alphaMM}.csv
logFile=`echo $outFile | sed -e 's/.csv/.log/'`
echo $outFile

if [[ -a $outFile ]]; then
    echo "file exists. skipping ..."
    return
fi

cat << EOF >> run
sbatch -o $logFile \
--export=grid_file=$gridFile,\
seed_file=$seedFile,\
out_file=$outFile,\
time_steps=$timeSteps,\
sim_runs=$simRuns,\
start_month=$startMonth,\
moore=$moore,\
suit_thresh=$suitThresh,\
exp_delay=$expDelay,\
alpha_sd=$alphaSD,\
alpha_fm=$alphaFM,\
alpha_mm=$alphaMM ../multi_pathway_model/run_ca_BGD.sbatch
qreg
EOF
}

function evaluate(){
fList=eval_list.txt
rm -f $fList
for f in `ls -1 ../results/results_BGD_2018-06-18/res_*csv`
do
for t in `seq 2 2`
do
    logFile=`basename $f | sed -e "s/^/evals\/ev_${t}_/"`
    if [[ -a $logFile ]]; then
        echo "$logFile exists. skipping ..."
        continue
    fi
    echo $logFile >> $fList
    sbatch -o $logFile \
        --export=command="python ../multi_pathway_model/evaluate_probs.py --time_window $t $f" \
        ../multi_pathway_model/run_proc.sbatch
    # file names to be inserted into DB will be in $fList. However, not fool proof.
done
done
}

function updateDB(){
cat $(cat eval_list.txt) > .to_be_deleted.update_db
sqlite3 ../results/results.db < .to_be_deleted.update_db
}

function check_errors(){
tail -n1 -q results_BGD/res*log | grep -v "simulation ended"
}

function error_debug(){
for f in `ls -1 results_BGD/res*log`
do
    chkErr=`grep "simulation ended" $f | wc -l`
    if [[ $chkErr == 0 ]]; then
        echo $f
        exit
    fi
done
}

function create_sim_out(){
sqlite3 ../results/results.db <<!
.mode csv
.header on
.output simulation_output.csv
SELECT * FROM eval_BGD WHERE likelihood > 5.5;
!
#SELECT * FROM eval_BGD WHERE likelihood>6.5;
#sed -i 's/exp_delay/latency_period/' simulation_output.csv
}

if [[ $# == 0 ]]; then
   echo "Here are the options:"
   grep "^function" $BASH_SOURCE | sed -e 's/function/  /' -e 's/[(){]//g' -e '/IGNORE/d'
else 
   eval $1 $2
fi
