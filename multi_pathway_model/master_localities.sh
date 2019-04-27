#!/bin/bash
function cities_thresh(){ # cities filtered by population threshold
cities='../../data/cities.csv'
for pt in `echo "100000 250000 500000 1000000"`
do
    head -n1 $cities > cities_$pt.csv
    grep -E 'VNM|LAO|BGD|THA|MYS|KHM|MMR|PHL|BRN|IDN|SGP' $cities \
        | awk -F, -v t=$pt '{if ($6>=t) print}' >> cities_$pt.csv
done
}

function ca_cities_radius(){ # generate CA with different city lists and radius
for city in `ls -1 ../obj/cities/cities_*csv`
do
    for rad in `echo "50 75 100"`
    do
        output=localities_${rad}_`basename $city`
        echo $city $rad
        if [ -a ../results/cities/$output ]; then
            echo "$output already exists. Skipping ..."
            continue
        fi
        python ../scripts/fill_data_ca.py --grid_file ../obj/ca_model_moore_6_filled.pkl --loc --loc_cities $city --loc_radius $rad
        mv localities.csv $output
    done
done
}

function plot_localities(){ # plotting localities
for f in `ls -1 ../results/cities/localities*csv`
do
    out=`echo $f | sed -e 's/.csv/.png/'`
    if [ -a ../results/cities/$out ]; then
        echo "$output already exists. Skipping ..."
        continue
    fi
    python ../scripts/plot_ca.py --cities -c $f -o $out
done
}

function multiplot_localities(){ # one figure for locality dist.
multiplot_localities.sh -x pop_thresh -y radius -p "100000 250000 500000" -r "50 75 100"
}

function concentrations(){   # concentration of population/production in localities
out=concentrations.csv
echo "#radius,pop_thresh,prod,pop" > $out
for f in `ls -1 ../results/cities/localities*csv | sort -t_ -n -k2,2 -k4,4`
do
    radius=`basename $f | sed -e 's/localities_//' -e 's/_.*//'`;
    pt=`basename $f | sed -e 's/^.*cities_//' -e 's/.csv//'`;
    vals=`awk -F, 'NR>1{totProd+=$4; totPop+=$5; if ($3!='NaN') {locProd+=$4; locPop+=$5}} \
        END{printf "%f,%f",locProd/totProd,locPop/totPop}' $f`
    echo "$radius,$pt,$vals" >> $out
done

ptList="100000 250000 500000"
rList="50 75 100"
ptFiles=""
rFiles=""
for pt in $ptList
do
    df=concentrations_pt$pt.csv
    echo $pt > $df
    grep ",$pt," $out >> $df
    ptFiles="$ptFiles $df"
done

for r in $rList
do
    df=concentrations_r$r.csv
    echo $r > $df
    grep "^$r," $out >> $df
    rFiles="$rFiles $df"
done

../scripts/plot.sh -o concentration_with_radius \
    -t "Production and population" \
    -x "radius" \
    -y "concentration" \
    -a "set style line 1 lw 7 ps 2.75 pi -1 pt 5 lc rgb '#5e82b5'; \
        set style line 2 lw 7 ps 2.75 pi -1 pt 7 lc rgb '#e09c24'; \
        set style line 3 lw 7 ps 2.75 pi -1 pt 13 lc rgb '#8fb030'; \
        set style line 4 lw 7 ps 2.75 pi -1 pt 5 lc rgb '#5e82b5'; \
        set style line 5 lw 7 ps 2.75 pi -1 pt 7 lc rgb '#e09c24'; \
        set style line 6 lw 7 ps 2.75 pi -1 pt 13 lc rgb '#8fb030'; \
        set style increment user;
        set key r b width 8;
        set yrange [0:1];
        set xrange [50:100];
        " \
    -p "plot for [file in \"`echo $ptFiles`\"] file u 1:3 ti columnheader(1), \
        for [file in \"`echo $ptFiles`\"] file u 1:4 noti dashtype 2;"

../scripts/plot.sh -o concentration_with_popthresh \
    -t "Production and population" \
    -x "pop. threshold." \
    -y "concentration" \
    -a "set style line 1 lw 7 ps 2.75 pi -1 pt 5 lc rgb '#5e82b5'; \
        set style line 2 lw 7 ps 2.75 pi -1 pt 7 lc rgb '#e09c24'; \
        set style line 3 lw 7 ps 2.75 pi -1 pt 13 lc rgb '#8fb030'; \
        set style line 4 lw 7 ps 2.75 pi -1 pt 5 lc rgb '#5e82b5'; \
        set style line 5 lw 7 ps 2.75 pi -1 pt 7 lc rgb '#e09c24'; \
        set style line 6 lw 7 ps 2.75 pi -1 pt 13 lc rgb '#8fb030'; \
        set style increment user;
        set key r b width 8;
        set yrange [0:1];
        set xrange [100000:];
        set xtics 500000;
        " \
    -p "plot for [file in \"`echo $rFiles`\"] file u 2:3 ti columnheader(1), \
        for [file in \"`echo $rFiles`\"] file u 2:4 noti dashtype 2;"
}

if [[ $# == 0 ]]; then
   echo "Here are the options:"
   grep "^function" $BASH_SOURCE | sed -e 's/function/  /' -e 's/[(){]//g' -e '/IGNORE/d'
else 
   eval $1 $2
fi

