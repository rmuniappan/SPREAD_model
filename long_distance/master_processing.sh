#!/bin/bash
DB="../../data_and_obj.db"

function export_processed_tomato(){
country=$1
sqlite3 $DB <<! #> export_processed.csv
.separator ","
SELECT "$country",sum(Value) FROM FAOSTAT_tomato_processed WHERE
ReporterCountries='$country' AND
Year=2013 AND
Element='Export Quantity';
!
}

function exp_proc_tom(){
country=$(
cat << EOF
Bangladesh
Cambodia
Indonesia
Laos
Malaysia
Myanmar
Philippines
Singapore
Thailand
Vietnam
EOF
)
for c in $country
do
export_processed_tomato $c
done
}

if [[ $# == 0 ]]; then
   echo "Here are the options:"
   grep "^function" $BASH_SOURCE | sed -e 's/function/  /' -e 's/[(){]//g' -e '/IGNORE/d'
else 
   eval $1 $2
fi
