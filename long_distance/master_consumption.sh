#!/bin/bash
DB="../../data_and_obj.db" # This is the attached sqlite file

function gdp_production_correlation_consumption(){ # correlation test
awk -F, 'NR>1{print $1","$51","$52","$53}' ../../data/tomato_consumption_per_capita_per_year.csv | \
    grep -wE "Bangladesh|Cambodia|Indonesia|Laos|Malaysia|Myanmar|Philippines|Singapore|Thailand|Viet Nam" | \
    sort -t, -n -k4,4 > fao_consumption.csv
awk 'NR>1' ../../data/gdp.csv | \
    grep -wE "Bangladesh|Cambodia|Indonesia|Laos|Malaysia|Myanmar|Philippines|Singapore|Thailand|Viet Nam" ../../data/gdp.csv |
    sort -t, -n -k2,2 > gdp_selected.csv

grep "Tomatoes.*2013" ../../international_trade/data/FAOSTAT_solanaceae_production.csv \
    | awk -F, '{print $4","$12}' | sed -e 's/"//g' > tp.csv
python ../scripts/convert_name_to_alpha.py tp.csv | sed -e '/ZZZ/d' > production_all.csv
exit
awk -F, 'NR>3{print $1","$53}' ../../data/tomato_consumption_per_capita_per_year.csv | sort | sed -e '/\.\.\./d'> tp.csv
python ../scripts/convert_name_to_alpha.py tp.csv | sed -e '/ZZZ/d' > consumption_all.csv
awk -F, 'NR>1' ../../data/gdp.csv | sort > tp.csv
python ../scripts/convert_name_to_alpha.py tp.csv | sed -e '/ZZZ/d' > gdp_all.csv
}

function production_trade_pop_corr_consumption() { # correlation test IGNORE
# consumption
awk -F, 'NR>3{print $1","$53}' ../../data/tomato_consumption_per_capita_per_year.csv | sort | sed -e '/\.\.\./d'> tp.csv
python ../scripts/convert_name_to_alpha.py tp.csv | sed -e '/ZZZ/d' > consumption_all.csv
# tomato production
grep "Tomatoes.*2013" ../../international_trade/data/FAOSTAT_solanaceae_production.csv \
    | awk -F, '{print $4","$12}' | sed -e 's/"//g' > tp.csv
python ../scripts/convert_name_to_alpha.py tp.csv | sed -e '/ZZZ/d' > production_all.csv
# tomato import
# tomato export
# population
}

function trade_prod_pop() {  # see if import, production
country=$1
sqlite3 $DB <<!
.separator ","
CREATE TEMP TABLE finalVal(dummy text,exp real,imp real,prod real,procExp real,pop real);
INSERT INTO finalVal (dummy) VALUES ('dummy');

UPDATE finalVal SET exp=(
SELECT sum(Value) FROM FAOSTAT_solanaceae_trade_matrix WHERE
ReporterCountries='$country' AND
Year=2013 AND
Item='Tomatoes' AND
Element='Export Quantity');

UPDATE finalVal SET imp=(
SELECT sum(Value) FROM FAOSTAT_solanaceae_trade_matrix WHERE
ReporterCountries='$country' AND
Year=2013 AND
Item='Tomatoes' AND
Element='Import Quantity');

UPDATE finalVal SET procExp=(
SELECT sum(Value) FROM FAOSTAT_tomato_processed WHERE
ReporterCountries='$country' AND
Year=2013 AND
Element='Export Quantity');

UPDATE finalVal SET prod=(
SELECT max(Value) FROM FAOSTAT_solanaceae_production WHERE
Area='$country' AND
Item='Tomatoes');

UPDATE finalVal SET pop=(
SELECT Value FROM FAOSTAT_country_population WHERE
Area='$country' AND
Year=2013);

SELECT * FROM finalVal;
SELECT "$country",((COALESCE(imp,0)+COALESCE(prod,0)-COALESCE(exp,0)-COALESCE(procExp,0))/pop) FROM finalVal;
!
}

function trade_production() {  # consumption as an expression of trade, prod, pop
sqlite3 $DB <<! > to_be_deleted_countries.csv
SELECT DISTINCT Area FROM FAOSTAT_country_population
!

IFS=$'\n'
for c in `cat to_be_deleted_countries.csv`
do
trade_prod_pop "$c"
done
}

function old_create_consumption(){  # consumption for each cell #IGNORE
rm -f consumption.csv
for c in `echo "BD KH ID LA MY MM PH TH VN"`
do
sqlite3 $DB <<! >> consumption.csv
.separator ","
SELECT g.cellid,(g.population*c.consumption),c.iso2 FROM grid as g,
consumption as c
WHERE c.iso2="$c" AND
(g.admin_id LIKE "$c-%" OR g.admin_id LIKE "%|$c-%")
!
done
sqlite3 $DB <<! >> consumption.csv
.separator ","
SELECT g.cellid,(g.population*c.consumption),c.iso2 FROM grid as g,
consumption as c
WHERE c.iso2="SG" AND
(g.admin_id LIKE "SG%" OR g.admin_id LIKE "%|SG|%" OR g.admin_id LIKE "%|SG%")
!

# NEED TO TAKE MAX OF ALL CELLS
}

function consumption_gdp(){
sqlite3 $DB <<!
.separator ","
SELECT c.iso3,c.consumption FROM FAO_tomato_consumption c
INNER JOIN gdp g ON g.iso3=c.iso3
WHERE g.gdp<=$1;
SELECT avg(c.consumption) FROM FAO_tomato_consumption c
INNER JOIN gdp g ON g.iso3=c.iso3
WHERE g.gdp<=$1
!
}

function create_consumption(){  # consumption for each city
sqlite3 $DB <<!
UPDATE localities SET consumption=(SELECT c.consumption
FROM cities_250000 as city
INNER JOIN tomato_consumption_study_region as c ON city.country=c.iso3
WHERE localities.city_name=city.name)
!
}

if [[ $# == 0 ]]; then
   echo "Here are the options:"
   grep "^function" $BASH_SOURCE | sed -e 's/function/  /' -e 's/[(){]//g' -e '/IGNORE/d'
else 
   eval $1 $2
fi
