#!/bin/bash
# start/intermediate files used in the pipeline
function run_an_example() {
radius=100
beta=2
kappa=300
gridFile="../obj/ca_r${radius}_b${beta}_k${kappa}.pkl"
seedFile="../data/seed_files/seed_MYS_moore1.csv"
timeSteps=63
simRuns=2
startMonth=5
moore=2
suitThresh=0
expDelay=1
alphaSD=200
alphaFM=100
alphaMM=300

echo "#!/bin/bash" > run
chmod +x run

#run_an_instance
run_direct
}

function run_from_db() {
# This part selects the parameter set
rm .to_be_deleted.exp.csv
modelList="alpha_ld=0 alpha_ld>0"
#modelList="alpha_ld=0"

for model in $modelList
do
for moore in `seq 1 3`
do
sqlite3 ../results/results.db <<! >> .to_be_deleted.exp.csv
.mode csv
SELECT * FROM eval_BGD WHERE 
likelihood>6 
AND season_ind=2 
AND $model
AND relative_time<0
AND moore=$moore
ORDER BY likelihood DESC
LIMIT 50
!
echo $moore $lat `wc -l .to_be_deleted.exp.csv`
done
done

seedFileList="../data/seed_files/Myanmar_line.csv"
seasonInd="precip1 precip1-20-100"
rateList="25 50"
#"../data/seed_files/seed_BGD_moore0.csv" #../data/seed_files/seed_MYS_moore1.csv"
#seedFileList="../data/seed_files/seed_PHL-MSC.csv"
echo "#!/bin/bash" > run
chmod +x run

for rate in $rateList
do
for line in `cat .to_be_deleted.exp.csv`
do
for seedFile in $seedFileList
do
for season in $seasonInd
do
beta=`echo $line | awk -F, '{printf "%g",$2}'`
kappa=`echo $line | awk -F, '{printf "%g",$3}'`
gridFile="../obj/ca_${season}_b${beta}_k${kappa}.pkl"
timeSteps=120
simRuns=30
startMonth=`echo $line | awk -F, '{printf "%g",$5}'`
moore=`echo $line | awk -F, '{printf "%g",$6}'`
suitThresh=`echo $line | awk -F, '{printf "%g",$7}'`
expDelay=`echo $line | awk -F, '{printf "%g",$8}'`
alphaSD=`echo $line | awk -F, '{printf "%g",$9}'`
alphaFM=`echo $line | awk -F, '{printf "%g",$10}'`
alphaMM=`echo $line | awk -F, '{printf "%g",$11}'`
alphaSD=`echo $alphaSD | awk -v r=$rate '{print $1*(1+.01*r)}'`
alphaFM=`echo $alphaFM | awk -v r=$rate '{print $1*(1+.01*r)}'`
alphaMM=`echo $alphaMM | awk -v r=$rate '{print $1*(1+.01*r)}'`
run_an_instance
done # seed
done # line
done # season
done # rate
}

function run_an_instance() { #IGNORE
if [[ "$seedFile" == "../data/seed_files/seed_BGD_moore0.csv" ]]; then
    seed=0
elif [[ "$seedFile" == "../data/seed_files/seed_BGD_moore1.csv" ]]; then
    seed=1
elif [[ "$seedFile" == "../data/seed_files/seed_MYS_moore1.csv" ]]; then
    seed=2
elif [[ "$seedFile" == "../data/seed_files/seed_PHL-MSC.csv" ]]; then
    seed=3
elif [[ "$seedFile" == "../data/seed_files/Myanmar_line.csv" ]]; then
    seed=4
else
    echo "Wrong seed file"
fi

outFile=results_sea_s4_${rate}p_rep$simRuns/`basename $gridFile | sed -e 's/ca_/res_/'\
    -e 's/.pkl//'`_s${seed}_sm${startMonth}_m${moore}_st${suitThresh}_ed${expDelay}_a-${alphaSD}-${alphaFM}-${alphaMM}.csv
logFile=`echo $outFile | sed -e 's/.csv/.log/'`
echo $outFile

if [[ -a $outFile ]]; then
    echo "file exists. skipping ..."
    return
fi

cat << EOF >> run
sbatch --account ndssl -o $logFile \
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
alpha_mm=$alphaMM ../scripts/run_ca.sbatch
qreg
EOF
}

function run_direct() { #IGNORE
outFile=`basename $gridFile | sed -e 's/ca_/res_/'\
    -e 's/.pkl//'`_sm${startMonth}_m${moore}_st${suitThresh}_ed${expDelay}_a-${alphaSD}-${alphaFM}-${alphaMM}.csv
echo $outFile

python ../scripts/run_ca.py\
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
beta=2
kappa=300
gridFile="../obj/ca_r${radius}_b${beta}_k${kappa}.pkl"
seedFile="../data/seed_files/seed_BGD_moore1.csv"
timeSteps=15
simRuns=100
startMonthList="5"
mooreList="1 2"
suitThreshList="0"
expDelayList=`seq 2 2`
alphaSDList=`seq 250 20 350` 
alphaFMList=`seq 0 .2 1` 
alphaMMList=`seq 0 10 100`

echo "#!/bin/bash" > run
chmod +x run

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
}

function total_inf(){
fList=total_inf_list.txt
rm -f $fList
for f in `ls -1 ../results/results_SEA_2018-05-13/res_*csv`
do
for time in `seq 12 12 72`
do
for thresh in `seq .25 .25 .5`
do
    logFile=`basename $f | sed -e "s/^/tot_inf\/inf_${time}_${thresh}_/"`
    if [[ -a $logFile ]]; then
        echo "$logFile exists. skipping ..."
        continue
    fi
    echo $logFile >> $fList
    sbatch --account ndssl -o $logFile \
        --export=command="python ../scripts/evaluate_probs.py --spread --time $time --threshold $thresh $f" \
        ../scripts/run_proc.sbatch
    # file names to be inserted into DB will be in $fList. However, not foolproof.
done    # threshold
done    # time
done    # all files 
}

function updateDB(){
cat $(cat total_inf_list.txt) > .to_be_deleted.tot_inf
sqlite3 ../results/results.db < .to_be_deleted.tot_inf
}

function haversine(){
fList=haversine_list.txt
for f in `ls -1 ./results_sea_s4_50p_rep5/res_*csv`
do
for time in `seq 12 24 120`
do
    logFile=`basename $f | sed -e "s/^/dist_inf\/inf_${time}_/"`
    if [[ -a $logFile ]]; then
        echo "$logFile exists. skipping ..."
        continue
    fi
    echo $logFile >> $fList
    sbatch --account ndssl -o $logFile \
        --export=command="python ../scripts/haversine.py $f $time" \
        ../scripts/run_proc.sbatch
done    # time
done    # all files 
}

function haversineDB(){
cat $(cat haversine_list.txt) | grep INSERT > .to_be_deleted.dist_inf
sqlite3 ../results/results.db < .to_be_deleted.dist_inf
}


function check_errors(){
tail -n1 -q results/res*log | grep -v "simulation ended"
}

function error_debug(){
for f in `ls -1 results/res*log`
do
    chkErr=`grep "simulation ended" $f | wc -l`
    if [[ $chkErr == 0 ]]; then
        echo $f
        exit
    fi
done
}

if [[ $# == 0 ]]; then
   echo "Here are the options:"
   grep "^function" $BASH_SOURCE | sed -e 's/function/  /' -e 's/[(){]//g' -e '/IGNORE/d'
else 
   eval $1 $2
fi
