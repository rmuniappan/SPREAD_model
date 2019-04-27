#!/bin/bash
###########################################################################
# Analysis of clusters
###########################################################################
DB="../../cellular_automata/results/results.db"

function formatVar(){ #IGNORE
awk 'NR>1' $1 | sed  -e 's/"//g' \
    -e 's/a_long/\\$\\\\alpha_{\\\\ell d}\\$/' \
    -e 's/latency_period/\\$\\\\ell\\$/' \
    -e 's/moore/\\$r_\\\\textrm{M}\\$/' \
    -e 's/start_month/\\$t_s\\$/' \
    -e 's/a_local/\\$\\\\alpha_{\\\\ell}\\$/' \
    -e 's/a_sd/\\$\\\\alpha_{s}\\$/' \
    -e 's/beta/\\$\\\\beta\\$/' \
    -e 's/kappa/\\$\\\\kappa\\$/' \
    > $2
}

function plotRF(){ #IGNORE
../../cellular_automata/scripts/plot.sh -o $2 \
   -c mathematica \
   -T hist \
   -x "\\\%IncMSE (\\$\\\times 10^3\\$)" \
   -f "all:18" \
   -a "unset title; \
       set ytics textcolor 'black' offset .5,0; \
       set xtics font \",15\"; \
       set style data points; \
       set format x \"%.1s\"; \
       set nokey;" \
       -p "plot '< gsort -t, -k2,2 -n -r $1' u 2:(-\$0):yticlabel(1) ls $3 pt 7"
}

function preprocessAgglomerative(){ # preprocess agglomerative from Hannah
for k in `seq 2 10`
do
awk -F, -v k=$k '{for(i=1;i<=11;i++) printf "%s,",$i; printf "%s\n",$(NF+2-k)}' ../results/agglomerative/clusters_agglomerative.csv > .temp_preprocessAgglomerative
sed -e "s/CLU$k/cluster/" .temp_preprocessAgglomerative > cluster_agglomerative_$k.csv
done
}

function cartAgglomerative(){ # CART and RF for agglomerative from Hannah
for f in `find ../results/agglomerative -iname c*_agg.csv`
do
echo $f
cartFile=`basename $f | sed -e 's/^/cart_/' -e 's/csv$/pdf/'`
Rscript ../scripts/cart_cluster.R -f $f -o $cartFile
done
## awk -F, '{printf "%s",$1; for(i=2;i<13;i++) printf ",%s",$i; printf "\n"}' ../results/agglomerative/clusters_agglomerative.csv | sed -e 's/CLU10/cluster' > for_rf.csv
## Rscript ../scripts/random_forest_cluster.R -f for_rf.csv -o $rfFile
}

function rfAgglomerative(){ # CART and RF analysis of clusters for agglomerative
for f in `find ../results/agglomerative/ -iname cluster_*csv`
do
echo $f
rfFile=`basename $f | sed -e 's/cluster/rf/' -e 's/.csv/_original.csv/'`
rfFileFormatted=`echo $rfFile | sed -e 's/_original//'`
Rscript ../scripts/random_forest_cluster.R -f $f -o $rfFile
formatVar $rfFile $rfFileFormatted
plotFile=`echo $rfFile | sed -e 's/csv$/pdf/'`
done
}

function cartAndRFkmeans(){ # CART and RF analysis of clusters for kmeans
for f in `find ../results/clusters -iname cluster_*csv`
do
echo $f
cartFile=`basename $f | sed -e 's/cluster/cart/' -e 's/csv/pdf/'`
Rscript ../scripts/cart_cluster.R -f $f -o $cartFile
rfFile=`basename $f | sed -e 's/cluster/rf/' -e 's/.csv/_original.csv/'`
rfFileFormatted=`echo $rfFile | sed -e 's/_original//'`
Rscript ../scripts/random_forest_cluster.R -f $f -o $rfFile
formatVar $rfFile $rfFileFormatted
plotFile=`echo $rfFile | sed -e 's/csv$/pdf/'`
done

## for f in `ls -1 ../results/rf_*means_*csv`
## do
## echo $f 
## plotFile=`basename $f | sed -e 's/\.csv$//'`
## plotRF $f $plotFile 1
## done
}

function kmeans(){ # CART and RF for kmeans
for f in `find ../results/kmeans -iname cluster_kmeans_*.csv`
do
echo $f
cartFile=`basename $f | sed -e 's/cluster_/cart_/' -e 's/csv$/pdf/'`
Rscript ../scripts/cart_cluster.R -f $f -o $cartFile
done
exit

awk -F, '{printf "%s",$1; for(i=2;i<13;i++) printf ",%s",$i; printf "\n"}' ../results/agglomerative/clusters_agglomerative.csv | sed -e 's/CLU10/cluster' > for_rf.csv
Rscript ../scripts/random_forest_cluster.R -f for_rf.csv -o $rfFile
}

if [[ $# == 0 ]]; then
   echo "Here are the options:"
   grep "^function" $BASH_SOURCE | sed -e 's/function/  /' -e 's/[(){]//g' -e '/IGNORE/d'
else 
   eval $1 $2 $3
fi
