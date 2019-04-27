#!/bin/bash
country=PH

function run_from_db() {
# This part selects the parameter set
rm .to_be_deleted.exp.csv
#modelList="alpha_ld=0 alpha_ld>0"
modelList="alpha_ld>0"

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
ORDER BY likelihood DESC;
!
echo $moore $lat `wc -l .to_be_deleted.exp.csv`
done
done

seedFileList="../data/seed_files/seed_${country}_radial.csv"
#seedFileList="../data/seed_files/seed_BGD_moore0.csv"
#seedFileList="../data/seed_files/seed_PHL-MSC.csv"
seasonInd="precip1 precip1-out-50 precip1-out-100"
echo "#!/bin/bash" > run
chmod +x run

for line in `awk 'NR>1' .to_be_deleted.exp.csv`
do
for seedFile in $seedFileList
do
for season in $seasonInd
do
beta=`echo $line | awk -F, '{printf "%g",$2}'`
kappa=`echo $line | awk -F, '{printf "%g",$3}'`
gridFile="../obj/ca_${season}_b${beta}_k${kappa}.pkl"
timeSteps=50
simRuns=20
startMonth=`echo $line | awk -F, '{printf "%g",$5}'`
moore=`echo $line | awk -F, '{printf "%g",$6}'`
suitThresh=`echo $line | awk -F, '{printf "%g",$7}'`
expDelay=`echo $line | awk -F, '{printf "%g",$8}'`
alphaSD=`echo $line | awk -F, '{printf "%g",$9}'`
alphaFM=`echo $line | awk -F, '{printf "%g",$10}'`
alphaMM=`echo $line | awk -F, '{printf "%g",$11}'`

## seed=`echo $line | awk -F, '{printf "%g",$4}'`
## if [[ "$seed" == 0 ]]; then
##  	seedFile="../data/seed_files/seed_BGD_moore0.csv"
## elif [[ "$seed" == 1 ]]; then
##  	seedFile="../data/seed_files/seed_BGD_moore1.csv"
## fi
run_an_instance
done # season
done # seed
done # line
}

function run_an_instance() { #IGNORE
if [[ "$seedFile" == "../data/seed_files/seed_BGD_moore0.csv" ]]; then
    seed=0
elif [[ "$seedFile" == "../data/seed_files/seed_BGD_moore1.csv" ]]; then
    seed=1
elif [[ "$seedFile" == "../data/seed_files/seed_MYS_moore1.csv" ]]; then
    seed=2
elif [[ "$seedFile" == "../data/seed_files/seed_PHL-MSC.csv" ]]; then
    seed=103
elif [[ "$seedFile" == "../data/seed_files/seed_TH_radial.csv" ]]; then
    seed=101
elif [[ "$seedFile" == "../data/seed_files/seed_PH_radial.csv" ]]; then
    seed=102
elif [[ "$seedFile" == "../data/seed_files/seed_VN_radial.csv" ]]; then
    seed=104
elif [[ "$seedFile" == "../data/seed_files/seed_BD_radial.csv" ]]; then
    seed=0
else
    echo "Wrong seed file"
    exit
fi

outFile=results_$country/`basename $gridFile | sed -e 's/ca_/res_/'\
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
country=$country,\
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
alpha_mm=$alphaMM ../scripts/run_ca_countries.sbatch
qreg
EOF
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
    sbatch -o $logFile \
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
fList=haversine_list_${country}.txt
for f in `ls -1 ./results_${country}/res_*csv`
do
for time in `seq 6 6 50`
do
    logFile=`basename $f | sed -e "s/^/dist_inf_${country}\/inf_${time}_/"`
    if [[ -a $logFile ]]; then
        echo "$logFile exists. skipping ..."
        continue
    fi

    seed=`echo $f | sed -e 's/^.*_\(s[0-9]*\)_.*/\1/' -e 's/s//'`
    if [[ "$seed" == 0 ]]; then
     	seedFile="../data/seed_files/seed_BGD_moore0.csv"
    elif [[ "$seed" == 1 ]]; then
     	seedFile="../data/seed_files/seed_BGD_moore1.csv"
    elif [[ "$seed" == 2 ]]; then
     	seedFile="../data/seed_files/seed_MYS_moore1.csv"
    elif [[ "$seed" == 103 ]]; then
     	seedFile="../data/seed_files/seed_PHL-MSC.csv"
    elif [[ "$seed" == 102 ]]; then
     	seedFile="../data/seed_files/seed_PH_radial.csv"
    elif [[ "$seed" == 101 ]]; then
     	seedFile="../data/seed_files/seed_TH_radial.csv"
    elif [[ "$seed" == 104 ]]; then
     	seedFile="../data/seed_files/seed_VN_radial.csv"
    else
        echo "Wrong seed file"
        exit
    fi
    echo $logFile >> $fList
    sbatch --account ndssl -o $logFile \
        --export=command="python ../scripts/haversine_country.py $f $time \
	$country $seedFile" \
        ../scripts/run_proc.sbatch
    ##     ../scripts/run_proc.sbatch
    # file names to be inserted into DB will be in $fList. However, not foolproof.
done    # time
done    # all files 
}

function haversineDB(){
cat $(cat haversine_list_${country}.txt) | grep INSERT > .to_be_deleted.dist_inf
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
