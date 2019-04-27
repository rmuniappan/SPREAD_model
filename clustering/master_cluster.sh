#!/bin/bash
###########################################################################
# Clustering simulation outputs
###########################################################################
DB="../../cellular_automata/results/results.db"

function query_to_filenames(){ # extract simulation outputs from zip folders
rootDir=$1
queryResult=$2  #csv file
    
awk -F, -v OFS="_" -v prefix="$rootDir" '
NR>1{
if ($1==1) seasonInd="uniform";
if ($1==2) seasonInd="precip1";
printf "cp -n %s/res_%s_b%g_k%g_s%g_sm%g_m%g_st%g_ed%g_a-%g-%g-%g.csv results_BGD_6/\n",prefix,seasonInd,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11
}' .to_be_deleted.exp.csv > .to_be_deleted.mov.sh
wc -l .to_be_deleted.mov.sh
bash .to_be_deleted.mov.sh
}

function extract_files(){ # extract simulation outputs for parameter sets chosen by a query
rm -f .to_be_deleted.exp.csv
sqlite3 ../../cellular_automata/results/results.db <<! >> .to_be_deleted.exp.csv
.mode csv
.header on
SELECT * FROM eval_BGD WHERE 
likelihood>=6 
!
# construct filename
#query_to_filenames ../../cellular_automata/sim_out_files/results_BGD_2018-08-01 .to_be_deleted.exp.csv
#query_to_filenames ../../cellular_automata/sim_out_files/results_BGD_2018-06-19 .to_be_deleted.exp.csv
query_to_filenames ../../cellular_automata/sim_out_files/results_BGD_2018-06-18 .to_be_deleted.exp.csv
}

function process_sim(){
count=1
for f in `ls -1 results_BGD_6`
do
echo -ne "\r\033[K$count: $f"
outPrefix=rank_time_inf_BD/`echo $f | sed -e "s/.csv$//"`
python ../scripts/post_process_simfile.py \
    results_BGD_6/$f \
    -o $outPrefix -c BD
((count+=1))
done
}

function concat_ranks(){
rm -f cell_ranks_BD.csv
for f in `ls -1 rank_BD`
do
cat rank_BD/$f >> cell_ranks_BD.csv
done
}

function concat_inf(){
colNum=`seq 1 3376 | awk '{printf(",%d",$1)}END{print "\n"}'`
echo "season,beta,kappa,seed,start_month,moore,start_time,latency_period,a_sd,a_local,a_long$colNum" > infection_vector_BD.csv
for f in `find rank_time_inf_BD -iname *infvec.csv`
do
cat $f >> infection_vector_BD.csv
done
}

function concat_time(){
rm -f expected_time_BD.csv
for f in `ls -1 rank_time_BD/*time.csv`
do
tail -1 rank_time_BD/$f >> expected_time_BD.csv
done
}

function cluster(){ # cluster simulation output using different algorithms
algo=$1
echo "#!/bin/bash" > run
for k in `seq 2 30`
do
clustersFile=cluster_${algo}_$k.csv
logFile=cluster_${algo}_$k.log
cat << EOF >> run
sbatch -o $logFile \
--export=command="python ../scripts/cluster_instances.py -a $algo -k $k -o $clustersFile" \
../scripts/run_proc.sbatch
EOF
chmod +x run
done
}

function filterByCluster(){ #IGNORE
lev=$1
levCol=$((21-$lev))
cA=$2
cB=$3
outFile=c$2$3_agg.csv
echo $lev $levCol $cA $cB $outFile
echo "season,beta,kappa,seed,start_month,moore,suit_thresh,latency_period,a_sd,a_local,a_long,cluster" > $outFile
awk -F, -v parc=$levCol '{for(i=1;i<12;i++) printf "%s,",$i; cl=parc; printf "%s\n",$cl}' $clusterFile | grep -E "$2|$3" >> $outFile
}

function processAgg(){ # process agglomerative clustering results from Hannah
# clusters_Hannah.csv is Hannah's file: contains just cluster hierarchy
# Checked for consistency: grep "^10," $clusterFile | uniq
# Parameter set: awk -F, '{printf "%s", $1; for(i=2;i<12;i++) printf ",%s", $i; printf "\n"}' ../../obj/infection_vector_BD.csv > par
# Pasted parameters and clusters: paste -d',' par cl > clusters_agglomerative.csv
# transform_cluster_id.sh for making it hierarchical indices
clusterFile="../results/agglomerative/formatted_clusters_agglomerative.csv"

# Filter by hierarchy
# cluster c1
filterByCluster 1 A B 
filterByCluster 2 C D 
filterByCluster 3 E F
filterByCluster 4 G H
filterByCluster 5 I J
filterByCluster 6 K L 
filterByCluster 7 M N 
filterByCluster 8 P Q
filterByCluster 9 R S 
}

if [[ $# == 0 ]]; then
   echo "Here are the options:"
   grep "^function" $BASH_SOURCE | sed -e 's/function/  /' -e 's/[(){]//g' -e '/IGNORE/d'
else 
   eval $1 $2
fi
