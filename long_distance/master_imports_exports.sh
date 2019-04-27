#!/bin/bash
function mys() {
netFile='../../international_trade/results/networks/sea_2013_tomato.csv'
grep ,MYS $netFile | grep -vE 'THA|SGP|MMR|VNM|IDN|KHM|BRN' | grep -v 'MYS,MYS' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "fresh import," sum}'
grep ^MYS $netFile | grep -vE 'THA|SGP|MMR|VNM|IDN|KHM|BRN' | grep -v 'MYS,MYS' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "fresh export," sum}'
netFile=processed.csv
cat ../../international_trade/results/networks/sea_2013_tomato_juice.csv \
    ../../international_trade/results/networks/sea_2013_tomato_paste.csv \
    ../../international_trade/results/networks/sea_2013_tomato_peeled.csv \
    > $netFile
grep ,MYS $netFile | grep -vE 'THA|SGP|MMR|VNM|IDN|KHM|BRN' | grep -v 'MYS,MYS' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "processed import," sum}'
grep ^MYS $netFile | grep -vE 'THA|SGP|MMR|VNM|IDN|KHM|BRN' | grep -v 'MYS,MYS' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "processed export," sum}'
}

function idn() {
netFile='../../international_trade/results/networks/sea_2013_tomato.csv'
grep ,IDN $netFile | grep -vE 'THA|SGP|MMR|VNM|MYS|KHM|BRN' | grep -v 'IDN,IDN' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "fresh import," sum}'
grep ^IDN $netFile | grep -vE 'THA|SGP|MMR|VNM|MYS|KHM|BRN' | grep -v 'IDN,IDN' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "fresh export," sum}'
netFile=processed.csv
cat ../../international_trade/results/networks/sea_2013_tomato_juice.csv \
    ../../international_trade/results/networks/sea_2013_tomato_paste.csv \
    ../../international_trade/results/networks/sea_2013_tomato_peeled.csv \
    > $netFile
grep ,IDN $netFile | grep -vE 'THA|SGP|MMR|VNM|MYS|KHM|BRN' | grep -v 'IDN,IDN' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "processed import," sum}'
grep ^IDN $netFile | grep -vE 'THA|SGP|MMR|VNM|MYS|KHM|BRN' | grep -v 'IDN,IDN' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "processed export," sum}'
}

function sgp() {
netFile='../../international_trade/results/networks/sea_2013_tomato.csv'
grep ,SGP $netFile | grep -vE 'THA|IDN|MMR|VNM|MYS|KHM|BRN' | grep -v 'SGP,SGP' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "fresh import," sum}'
grep ^SGP $netFile | grep -vE 'THA|IDN|MMR|VNM|MYS|KHM|BRN' | grep -v 'SGP,SGP' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "fresh export," sum}'
netFile=processed.csv
cat ../../international_trade/results/networks/sea_2013_tomato_juice.csv \
    ../../international_trade/results/networks/sea_2013_tomato_paste.csv \
    ../../international_trade/results/networks/sea_2013_tomato_peeled.csv \
    > $netFile
grep ,SGP $netFile | grep -vE 'THA|IDN|MMR|VNM|MYS|KHM|BRN' | grep -v 'SGP,SGP' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "processed import," sum}'
grep ^SGP $netFile | grep -vE 'THA|IDN|MMR|VNM|MYS|KHM|BRN' | grep -v 'SGP,SGP' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "processed export," sum}'
}

function mmr() {
netFile='../../international_trade/results/networks/sea_2013_tomato.csv'
grep ,MMR $netFile | grep -vE 'SGP|IDN|THA|VNM|MYS|KHM|BRN' | grep -v 'MMR,MMR' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "fresh import," sum}'
grep ^MMR $netFile | grep -vE 'SGP|IDN|THA|VNM|MYS|KHM|BRN' | grep -v 'MMR,MMR' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "fresh export," sum}'
netFile=processed.csv
cat ../../international_trade/results/networks/sea_2013_tomato_juice.csv \
    ../../international_trade/results/networks/sea_2013_tomato_paste.csv \
    ../../international_trade/results/networks/sea_2013_tomato_peeled.csv \
    > $netFile
grep ,MMR $netFile | grep -vE 'SGP|IDN|THA|VNM|MYS|KHM|BRN' | grep -v 'MMR,MMR' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "processed import," sum}'
grep ^MMR $netFile | grep -vE 'SGP|IDN|THA|VNM|MYS|KHM|BRN' | grep -v 'MMR,MMR' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "processed export," sum}'
}

function tha() {
netFile='../../international_trade/results/networks/sea_2013_tomato.csv'
grep ,THA $netFile | grep -vE 'SGP|IDN|MMR|VNM|MYS|KHM|BRN' | grep -v 'THA,THA' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "fresh import," sum}'
grep ^THA $netFile | grep -vE 'SGP|IDN|MMR|VNM|MYS|KHM|BRN' | grep -v 'THA,THA' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "fresh export," sum}'
netFile=processed.csv
cat ../../international_trade/results/networks/sea_2013_tomato_juice.csv \
    ../../international_trade/results/networks/sea_2013_tomato_paste.csv \
    ../../international_trade/results/networks/sea_2013_tomato_peeled.csv \
    > $netFile
grep ,THA $netFile | grep -vE 'SGP|IDN|MMR|VNM|MYS|KHM|BRN' | grep -v 'THA,THA' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "processed import," sum}'
grep ^THA $netFile | grep -vE 'SGP|IDN|MMR|VNM|MYS|KHM|BRN' | grep -v 'THA,THA' | awk -F, '{m=$3; if ($4>m) m=$4; sum+=m}END{print "processed export," sum}'
}

if [[ $# == 0 ]]; then
   echo "Here are the options:"
   grep "^function" $BASH_SOURCE | sed -e 's/function/  /' -e 's/[(){]//g' -e '/IGNORE/d'
else 
   eval $1 $2
fi
